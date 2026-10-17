import io
import json
import os
import tempfile
import urllib.error
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from agent_welcome.easy_install import (
    EasyInstallError,
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


class Response(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *_args):
        self.close()


class RedirectResponse(Response):
    def geturl(self):
        return 'https://unapproved.example/installer.sh'


def opener(_request, timeout):
    assert timeout == 30
    return Response(b'#!/bin/sh\nexit 0\n')


class EasyInstallTests(unittest.TestCase):
    def _agent(self, root):
        path = Path(root) / 'fake-agent'
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

    def test_explicit_consent_runs_official_script_then_requires_authentication(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            agent = self._agent(root)
            state_dir = root / 'state'
            easy_start('macos-codex', state_dir, mac_observation())
            with mock.patch('agent_welcome.easy_install.shutil.which', side_effect=[None, str(agent)]):
                state = easy_resume(
                    state_dir, mac_observation(), approve_install=True,
                    runner=self.runner(), opener=opener,
                )
            self.assertEqual(state['status'], 'WAITING_USER')
            self.assertEqual(state['waiting']['reason'], 'provider_authentication')
            self.assertEqual(state['installer_evidence']['bytes'], len(b'#!/bin/sh\nexit 0\n'))
            self.assertTrue((state_dir / 'downloads' / 'official-installer.sh').is_file())
            self.assertTrue(Path(state['launcher_path']).is_file())
            self.assertTrue(state['evidence']['upstream_binary'])

    def test_auth_and_task_attestations_are_non_secret_and_not_direct_success(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            agent = self._agent(root)
            state_dir = root / 'state'
            state = easy_start(
                'macos-claude-code', state_dir, mac_observation(),
                agent_executable=str(agent), runner=self.runner(),
            )
            self.assertEqual(state['waiting']['reason'], 'provider_authentication')
            bad = root / 'bad.json'
            bad.write_text(json.dumps({'target_id': 'macos-claude-code', 'event': 'provider_authentication', 'status': 'completed', 'method': 'browser', 'token': 'do-not-save'}))
            rejected = easy_resume(state_dir, mac_observation(), auth_evidence=bad)
            self.assertEqual(rejected['status'], 'FAILED')
            self.assertNotIn('do-not-save', json.dumps(rejected))
            auth = root / 'auth.json'
            auth.write_text(json.dumps({'target_id': 'macos-claude-code', 'event': 'provider_authentication', 'status': 'completed', 'method': 'browser_login'}))
            waiting = easy_resume(state_dir, mac_observation(), auth_evidence=auth)
            self.assertEqual(waiting['waiting']['reason'], 'minimal_first_task')
            task = root / 'task.json'
            task.write_text(json.dumps({'target_id': 'macos-claude-code', 'event': 'minimal_first_task', 'status': 'completed', 'method': 'interactive_read_only_task'}))
            attested = easy_resume(state_dir, mac_observation(), first_task_evidence=task)
            self.assertEqual(attested['status'], 'USER_ATTESTED')
            self.assertEqual(attested['evidence']['authentication'], 'user_attestation')
            self.assertEqual(attested['evidence']['first_task'], 'user_attestation')
            self.assertFalse(attested['evidence']['actual_os'])

    def test_direct_task_needs_separate_billable_consent(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            agent = self._agent(root)
            state_dir = root / 'state'
            easy_start('macos-prime-agent', state_dir, mac_observation(), agent_executable=str(agent), runner=self.runner())
            auth = root / 'auth.json'
            auth.write_text(json.dumps({'target_id': 'macos-prime-agent', 'event': 'provider_authentication', 'status': 'completed', 'method': 'interactive_login'}))
            easy_resume(state_dir, mac_observation(), auth_evidence=auth)
            command = json.dumps([str(agent), 'read-only prompt'])
            waiting = easy_resume(state_dir, mac_observation(), first_task_command=command)
            self.assertEqual(waiting['waiting']['reason'], 'billable_first_task_consent')
            done = easy_resume(
                state_dir, mac_observation(), first_task_command=command,
                allow_billable_first_task=True, runner=self.runner('done'),
            )
            self.assertEqual(done['status'], 'SUCCEEDED')
            self.assertEqual(done['evidence']['first_task'], 'direct_subprocess')

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
            self.assertNotIn('Bearer', json.dumps(failed))

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
                ['proot-distro', 'install', 'ubuntu:24.04'],
            ])
            in_guest = easy_resume(state_dir, guest)
            self.assertEqual(in_guest['waiting']['reason'], 'installer_consent')
            self.assertEqual(in_guest['environment_transition'], 'termux_to_same_device_proot_guest')

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
