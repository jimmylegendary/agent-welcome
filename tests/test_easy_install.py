import io
import json
import os
import re
import subprocess
import tempfile
import urllib.error
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from agent_welcome.easy_install import (
    EasyInstallError,
    FIRST_TASK_TIMEOUT_SECONDS,
    _first_task_adapter,
    _run,
    _verify_first_task_proof,
    easy_resume,
    easy_start,
    easy_status,
    load_targets,
)
from agent_welcome.environment import observe


def mac_observation():
    return {
        'kernel_os': 'darwin', 'host_os': 'macos', 'architecture': 'aarch64',
        'runtime_kind': 'native', 'provenance': {'kind': 'fixture'},
    }


def windows_observation():
    return {
        'kernel_os': 'windows', 'host_os': 'windows', 'architecture': 'x86_64',
        'runtime_kind': 'native', 'provenance': {'kind': 'fixture'},
    }


class Response(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *_args):
        self.close()


class RedirectResponse(Response):
    def geturl(self):
        return 'https://unapproved.example/installer.sh'


class ApprovedCodexResponse(Response):
    def geturl(self):
        return 'https://releases.openai.com/codex/install.ps1'


def opener(_request, timeout):
    assert timeout == 30
    return Response(b'#!/bin/sh\nexit 0\n')


class EasyInstallTests(unittest.TestCase):
    def _agent(self, root, command):
        path = Path(root) / command
        path.write_text('fixture', encoding='utf-8')
        return path

    @staticmethod
    def runner(stdout='1.2.3'):
        def run(argv, **kwargs):
            assert kwargs['shell'] is False
            assert kwargs['timeout'] == 30
            assert Path(kwargs['cwd']).is_dir()
            return SimpleNamespace(returncode=0, stdout=stdout, stderr='')
        return run

    @staticmethod
    def task_runner(argv, **kwargs):
        assert kwargs['shell'] is False
        assert kwargs['stdin'] is subprocess.DEVNULL
        if argv[1:] == ['--version']:
            assert kwargs['timeout'] == 30
            return SimpleNamespace(returncode=0, stdout='1.2.3', stderr='')
        assert kwargs['timeout'] == FIRST_TASK_TIMEOUT_SECONDS
        prompt = argv[-1]
        match = re.search(r'(agent-welcome-proof-([0-9a-f]+)\.txt).*exactly ([0-9a-f]+)', prompt)
        if match is None or match.group(2) != match.group(3):
            raise AssertionError(f'fixed task prompt malformed: {prompt!r}')
        (Path(kwargs['cwd']) / match.group(1)).write_text(match.group(2), encoding='utf-8')
        return SimpleNamespace(returncode=0, stdout=match.group(2), stderr='')

    def test_catalog_has_all_twelve_implemented_routes_without_runtime_claims(self):
        catalog = load_targets()
        self.assertEqual(len(catalog['targets']), 12)
        self.assertEqual(
            {(item['os'], item['agent']) for item in catalog['targets']},
            {(os_name, agent) for os_name in ('macos', 'windows', 'android', 'ios')
             for agent in ('claude-code', 'codex', 'prime-agent')},
        )
        self.assertTrue(all(item['host']['same_device_route'] != 'remote' for item in catalog['targets']))
        support = json.loads((Path(__file__).parents[1] / 'catalog' / 'support-targets.json').read_text())
        self.assertEqual(len(support['targets']), 12)
        self.assertTrue(all(item['runtime_verified'] is False for item in support['targets']))

    def test_missing_agent_waits_for_explicit_installer_consent(self):
        with tempfile.TemporaryDirectory() as temp:
            state = easy_start('macos-codex', Path(temp) / 'state', mac_observation())
            self.assertEqual(state['status'], 'WAITING_USER')
            self.assertEqual(state['waiting']['reason'], 'installer_consent')
            self.assertIn('chatgpt.com/codex/install.sh', state['waiting']['instructions']['download_url'])
            self.assertEqual(state['attempts']['total'], 0)
            self.assertFalse((Path(temp) / 'state' / 'downloads').exists())

    def test_fixture_installer_never_creates_upstream_or_direct_evidence(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            agent = self._agent(root, 'codex')
            state_dir = root / 'state'
            easy_start('macos-codex', state_dir, mac_observation())
            with mock.patch('agent_welcome.easy_install.shutil.which', side_effect=[None, str(agent)]):
                state = easy_resume(
                    state_dir, mac_observation(), approve_install=True,
                    runner=self.runner(), opener=opener,
                )
            self.assertEqual(state['status'], 'WAITING_USER')
            self.assertEqual(state['waiting']['reason'], 'provider_authentication')
            self.assertEqual(state['installer_evidence']['kind'], 'fixture_installer')
            self.assertEqual(state['installation_evidence']['kind'], 'fixture_version_probe')
            self.assertTrue(state['evidence']['fixture'])
            self.assertFalse(state['evidence']['actual_os'])
            self.assertFalse(state['evidence']['upstream_binary'])
            self.assertEqual(state['evidence']['binary_provenance'], 'unverified_local_executable')

    def test_fixed_task_requires_consent_and_fixture_success_is_unverified(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            agent = self._agent(root, 'claude')
            state_dir = root / 'state'
            waiting = easy_start(
                'macos-claude-code', state_dir, mac_observation(),
                agent_executable=str(agent), runner=self.task_runner,
            )
            self.assertEqual(waiting['waiting']['reason'], 'provider_authentication')
            self.assertNotIn('evidence_template', waiting['waiting']['instructions'])
            self.assertNotIn('first-task-command', json.dumps(waiting))
            completed = easy_resume(
                state_dir, mac_observation(), approve_first_task=True,
                runner=self.task_runner,
            )
            self.assertEqual(completed['status'], 'COMPLETED_UNVERIFIED_PROVENANCE')
            self.assertEqual(completed['first_task_evidence']['kind'], 'fixture_fixed_adapter')
            self.assertEqual(completed['first_task_evidence']['timeout_seconds'], FIRST_TASK_TIMEOUT_SECONDS)
            self.assertEqual(completed['first_task_evidence']['argv'][1:-1], [
                '-p', '--bare', '--tools', 'Write', '--allowedTools', 'Write',
                '--permission-prompts', 'none',
            ])
            self.assertEqual(completed['evidence']['authentication'], 'fixture_fixed_agent_task')
            self.assertFalse(completed['evidence']['actual_os'])
            self.assertFalse(completed['evidence']['upstream_binary'])

    def test_legacy_attestation_or_custom_argv_success_is_reclassified(self):
        with tempfile.TemporaryDirectory() as temp:
            state_dir = Path(temp) / 'state'
            state = easy_start('macos-codex', state_dir, mac_observation())
            state['status'] = 'SUCCEEDED'
            state['first_task_evidence'] = {'kind': 'direct_subprocess'}
            state['binary_provenance'] = {'kind': 'unverified_local_executable'}
            (state_dir / 'easy-state.json').write_text(json.dumps(state), encoding='utf-8')
            migrated = easy_resume(state_dir, mac_observation())
            self.assertEqual(migrated['status'], 'COMPLETED_UNVERIFIED_PROVENANCE')
            self.assertTrue(migrated['legacy_evidence_reclassified'])
            self.assertFalse(migrated['evidence']['upstream_binary'])

    def test_arbitrary_executable_and_short_output_cannot_pass_identity_probe(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            fake = self._agent(root, 'arbitrary-executable')
            state = easy_start(
                'macos-codex', root / 'state', mac_observation(),
                agent_executable=str(fake), runner=self.runner('1.2.3'),
            )
            self.assertEqual(state['status'], 'FAILED')
            self.assertEqual(state['failure_evidence']['kind'], 'version_probe')
            self.assertIn('does not identify codex', state['error'])
            self.assertFalse(state['evidence']['upstream_binary'])

    def test_windows_codex_approved_release_redirect_is_allowed(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            agent = self._agent(root, 'codex')
            state_dir = root / 'state'
            easy_start('windows-codex', state_dir, windows_observation())
            with mock.patch('agent_welcome.easy_install.shutil.which', side_effect=[None, str(agent)]):
                state = easy_resume(
                    state_dir, windows_observation(), approve_install=True,
                    runner=self.runner(),
                    opener=lambda _request, timeout: ApprovedCodexResponse(b'Write-Output installer'),
                )
            self.assertEqual(state['status'], 'WAITING_USER')
            self.assertEqual(state['installer_evidence']['url'], 'https://releases.openai.com/codex/install.ps1')

    def test_cross_host_installer_redirect_is_rejected_before_execution(self):
        with tempfile.TemporaryDirectory() as temp:
            state_dir = Path(temp) / 'state'
            easy_start('macos-codex', state_dir, mac_observation())
            with mock.patch('agent_welcome.easy_install.shutil.which', return_value=None):
                failed = easy_resume(
                    state_dir, mac_observation(), approve_install=True,
                    opener=lambda _request, timeout: RedirectResponse(b'installer'),
                )
            self.assertEqual(failed['status'], 'FAILED')
            self.assertIn('approved HTTPS host', failed['error'])
            self.assertFalse((state_dir / 'downloads' / 'official-installer.sh').exists())

    def test_run_keeps_required_windows_profile_variables_without_secrets(self):
        seen = {}

        def runner(argv, **kwargs):
            seen.update(kwargs['env'])
            return SimpleNamespace(returncode=0, stdout='ok', stderr='')

        with tempfile.TemporaryDirectory() as temp:
            with mock.patch.dict(os.environ, {
                'USERPROFILE': r'C:\\Users\\fixture',
                'CODEX_HOME': r'C:\\Users\\fixture\\.codex',
                'OPENAI_API_KEY': 'must-not-leak',
            }, clear=False):
                self.assertEqual(_run(['fixture'], temp, runner=runner), 'ok')
        self.assertEqual(seen['USERPROFILE'], r'C:\\Users\\fixture')
        self.assertEqual(seen['CODEX_HOME'], r'C:\\Users\\fixture\\.codex')
        self.assertNotIn('OPENAI_API_KEY', seen)

    def test_first_task_adapters_use_minimum_noninteractive_write_contracts(self):
        catalog = load_targets()['targets']
        targets = {target['agent']: target for target in catalog if target['os'] == 'macos'}
        expected = {
            'claude-code': [
                '/agents/claude', '-p', '--bare', '--tools', 'Write',
                '--allowedTools', 'Write', '--permission-prompts', 'none',
            ],
            'codex': [
                '/agents/codex', 'exec', '--sandbox', 'workspace-write',
                '--ask-for-approval', 'never', '--skip-git-repo-check',
            ],
            'prime-agent': ['/agents/prime-agent', '--print'],
        }
        with tempfile.TemporaryDirectory() as temp:
            for agent, prefix in expected.items():
                with self.subTest(agent=agent):
                    state_root = Path(temp) / agent
                    state_root.mkdir()
                    _workspace, _marker, nonce, argv = _first_task_adapter(
                        targets[agent], {'agent_executable': prefix[0]}, state_root,
                    )
                    self.assertEqual(argv[:-1], prefix)
                    self.assertIn(nonce, argv[-1])
                    self.assertNotIn('--dangerously-skip-permissions', argv)
                    self.assertNotIn('--dangerously-bypass-approvals-and-sandbox', argv)

    def test_first_task_rejects_stdout_that_is_not_exactly_the_nonce(self):
        with tempfile.TemporaryDirectory() as temp:
            marker = Path(temp) / 'proof.txt'
            marker.write_text('nonce', encoding='utf-8')
            with self.assertRaisesRegex(EasyInstallError, 'exactly match'):
                _verify_first_task_proof(marker, 'nonce', 'nonce with extra output')

    @unittest.skipIf(os.name == 'nt', 'creating the Unix Claude installer symlink layout requires Unix semantics')
    def test_claude_official_user_local_symlink_preserves_invocation_and_binary_paths(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            home = root / 'home'
            launcher = home / '.local' / 'bin' / 'claude'
            binary = home / '.local' / 'share' / 'claude' / 'versions' / '1.2.3'
            launcher.parent.mkdir(parents=True)
            binary.parent.mkdir(parents=True)
            binary.write_text('fixture', encoding='utf-8')
            launcher.symlink_to(binary)
            with mock.patch.dict(os.environ, {'HOME': str(home)}, clear=False):
                state = easy_start(
                    'macos-claude-code', root / 'state', mac_observation(),
                    agent_executable=str(launcher), runner=self.runner('Claude Code 1.2.3'),
                )
            self.assertEqual(state['status'], 'WAITING_USER')
            self.assertEqual(state['agent_executable'], str(launcher))
            self.assertEqual(state['agent_invocation_path'], str(launcher))
            self.assertEqual(state['agent_resolved_path'], str(binary))
            self.assertEqual(state['installation_evidence']['invocation_path'], str(launcher))
            self.assertEqual(state['installation_evidence']['resolved_path'], str(binary))

    def test_interrupted_installer_is_not_automatically_replayed(self):
        with tempfile.TemporaryDirectory() as temp:
            state_dir = Path(temp) / 'state'
            easy_start('macos-codex', state_dir, mac_observation())

            def interrupted(*_args, **_kwargs):
                raise KeyboardInterrupt()

            with mock.patch('agent_welcome.easy_install.shutil.which', return_value=None):
                with self.assertRaises(KeyboardInterrupt):
                    easy_resume(state_dir, mac_observation(), approve_install=True, runner=interrupted, opener=opener)
                recovered = easy_resume(state_dir, mac_observation())
            self.assertEqual(recovered['status'], 'WAITING_USER')
            self.assertEqual(recovered['waiting']['reason'], 'installer_outcome_unknown')

    def test_download_failure_is_recorded_and_does_not_leave_an_unknown_process(self):
        with tempfile.TemporaryDirectory() as temp:
            state_dir = Path(temp) / 'state'
            easy_start('macos-codex', state_dir, mac_observation())

            def disconnected(_request, timeout):
                raise urllib.error.URLError('fixture disconnect')

            with mock.patch('agent_welcome.easy_install.shutil.which', return_value=None):
                failed = easy_resume(state_dir, mac_observation(), approve_install=True, opener=disconnected)
            self.assertEqual(failed['status'], 'FAILED')
            self.assertFalse(failed['installer_execution_pending'])
            self.assertEqual(failed['failure_evidence']['kind'], 'installer_execution')

    def test_target_and_environment_drift_stop_before_a_second_install(self):
        with tempfile.TemporaryDirectory() as temp:
            state_dir = Path(temp) / 'state'
            easy_start('macos-codex', state_dir, mac_observation())
            wrong = dict(mac_observation())
            wrong['architecture'] = 'x86_64'
            drift = easy_resume(state_dir, wrong)
            self.assertEqual(drift['status'], 'NEEDS_DIAGNOSIS')
            self.assertIn('environment changed', drift['error'])
            with self.assertRaises(EasyInstallError):
                easy_start('macos-claude-code', state_dir, mac_observation())

    def test_mobile_target_requires_same_device_guest_observation(self):
        observation = {
            'kernel_os': 'linux', 'host_os': 'android', 'architecture': 'aarch64',
            'runtime_kind': 'native', 'provenance': {'kind': 'fixture'},
        }
        with tempfile.TemporaryDirectory() as temp:
            state = easy_start('android-codex', Path(temp) / 'state', observation)
            self.assertEqual(state['status'], 'WAITING_USER')
            self.assertEqual(state['waiting']['reason'], 'same_device_guest')
            self.assertTrue(state['waiting']['instructions']['same_device_only'])

    def test_android_prerequisites_are_consent_gated_and_resume_in_same_device_guest(self):
        termux = {
            'kernel_os': 'linux', 'host_os': 'android', 'architecture': 'aarch64',
            'runtime_kind': 'linux_userland', 'provenance': {'kind': 'fixture'},
        }
        guest = dict(termux, runtime_kind='proot')
        calls = []

        def runner(argv, **kwargs):
            self.assertEqual(kwargs['timeout'], 900)
            calls.append(argv)
            return SimpleNamespace(returncode=0, stdout='prepared', stderr='')

        with tempfile.TemporaryDirectory() as temp:
            state_dir = Path(temp) / 'state'
            waiting = easy_start('android-codex', state_dir, termux)
            self.assertEqual(waiting['waiting']['reason'], 'android_prerequisite_consent')
            prepared = easy_resume(
                state_dir, termux, approve_prerequisites=True, runner=runner,
            )
            self.assertEqual(prepared['waiting']['reason'], 'enter_android_guest')
            self.assertEqual(calls, [
                ['pkg', 'install', '-y', 'proot-distro'],
                ['proot-distro', 'install', 'ubuntu'],
            ])
            self.assertEqual(prepared['android_prerequisite_evidence']['kind'], 'fixture_subprocess')
            in_guest = easy_resume(state_dir, guest)
            self.assertEqual(in_guest['waiting']['reason'], 'installer_consent')
            self.assertEqual(in_guest['environment_transition'], 'termux_to_same_device_proot_guest')

    def test_android_prerequisite_failure_and_interrupt_are_durable(self):
        termux = {
            'kernel_os': 'linux', 'host_os': 'android', 'architecture': 'aarch64',
            'runtime_kind': 'linux_userland', 'provenance': {'kind': 'fixture'},
        }
        with tempfile.TemporaryDirectory() as temp:
            state_dir = Path(temp) / 'failed'
            easy_start('android-codex', state_dir, termux)
            failed = easy_resume(
                state_dir, termux, approve_prerequisites=True,
                runner=lambda *_args, **_kwargs: SimpleNamespace(returncode=1, stdout='', stderr='fixture failure'),
            )
            self.assertEqual(failed['status'], 'FAILED')
            self.assertFalse(failed['android_prerequisite_pending'])
            self.assertEqual(failed['failure_evidence']['kind'], 'android_prerequisite_execution')
            self.assertEqual(easy_status(state_dir)['status'], 'FAILED')

            interrupted_dir = Path(temp) / 'interrupted'
            easy_start('android-codex', interrupted_dir, termux)
            with self.assertRaises(KeyboardInterrupt):
                easy_resume(
                    interrupted_dir, termux, approve_prerequisites=True,
                    runner=lambda *_args, **_kwargs: (_ for _ in ()).throw(KeyboardInterrupt()),
                )
            recovered = easy_resume(interrupted_dir, termux)
            self.assertEqual(recovered['status'], 'WAITING_USER')
            self.assertTrue(recovered['android_prerequisite_pending'])
            self.assertEqual(recovered['waiting']['reason'], 'android_guest_outcome_unknown')

    def test_mobile_prime_requires_observed_glibc_floor(self):
        base = {
            'kernel_os': 'linux', 'host_os': 'android', 'architecture': 'aarch64',
            'runtime_kind': 'proot', 'provenance': {'kind': 'fixture'},
        }
        with tempfile.TemporaryDirectory() as temp:
            musl = dict(base, libc={'family': 'musl', 'version': '1.2'})
            unsupported = easy_start('android-prime-agent', Path(temp) / 'musl', musl)
            self.assertEqual(unsupported['status'], 'UNSUPPORTED')
            glibc = dict(base, libc={'family': 'glibc', 'version': '2.35'})
            waiting = easy_start('android-prime-agent', Path(temp) / 'glibc', glibc)
            self.assertEqual(waiting['waiting']['reason'], 'installer_consent')

    def test_termux_and_ios_guest_observations_are_explicitly_labelled(self):
        with mock.patch('agent_welcome.environment.platform.system', return_value='Linux'):
            with mock.patch.dict(os.environ, {'TERMUX_VERSION': '0.118'}, clear=False):
                android = observe()
            self.assertEqual((android['host_os'], android['runtime_kind']), ('android', 'linux_userland'))
            with mock.patch.dict(os.environ, {'AGENT_WELCOME_IOS_GUEST': '1'}, clear=False):
                ios = observe()
            self.assertEqual((ios['host_os'], ios['runtime_kind']), ('ios', 'linux_guest'))
            self.assertEqual(ios['provenance']['host_os_evidence'], 'user_marker')


if __name__ == '__main__':
    unittest.main()
