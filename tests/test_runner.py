import hashlib
import io
import json
import multiprocessing
import os
import tarfile
import tempfile
import unittest
from pathlib import Path

from agent_welcome.catalog import CatalogError, load_recipe
from agent_welcome.runner import (
    RunError,
    record_user_wait,
    resume,
    start,
    status,
    locked_state_dir,
)
from agent_welcome.runner import RunError


ROOT = Path(__file__).resolve().parents[1]


def make_archive():
    stream = io.BytesIO()
    payload = b'#!/bin/sh\necho 0.10.0\n'
    with tarfile.open(fileobj=stream, mode='w:gz') as tar:
        info = tarfile.TarInfo('prime-agent')
        info.size = len(payload)
        info.mode = 0o755
        tar.addfile(info, io.BytesIO(payload))
    return stream.getvalue()


def make_counting_archive():
    stream = io.BytesIO()
    payload = b'#!/bin/sh\necho run >> probe-count\necho 0.10.0\n'
    with tarfile.open(fileobj=stream, mode='w:gz') as tar:
        info = tarfile.TarInfo('prime-agent')
        info.size = len(payload)
        info.mode = 0o755
        tar.addfile(info, io.BytesIO(payload))
    return stream.getvalue()


def _try_concurrent_start(queue, recipe, state_dir):
    try:
        start(recipe, state_dir, compatible_observation())
        queue.put('acquired')
    except RunError:
        queue.put('locked')


def compatible_observation():
    return {
        'kernel_os': 'linux',
        'host_os': 'android',
        'architecture': 'aarch64',
        'runtime_kind': 'proot',
        'libc': {'family': 'glibc', 'version': '2.35'},
        'capabilities': {},
        'auth': {'failure_stage': 'none'},
        'provenance': {'kind': 'fixture', 'runtime_tested': False},
    }


def recipe_for(blob):
    recipe = json.loads(
        (ROOT / 'recipes' / 'prime-agent-0.10.0-linux-arm64.json').read_text()
    )
    recipe['artifact']['published_sha256'] = hashlib.sha256(blob).hexdigest()
    return recipe


class RunnerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.recipe = load_recipe(ROOT / 'recipes' / 'prime-agent-0.10.0-linux-arm64.json')

    @unittest.skipIf(os.name == 'nt', 'reference fixture executes a Linux ARM shell payload')
    def test_missing_artifact_waits_then_resume_installs_once(self):
        blob = make_archive()
        recipe = recipe_for(blob)
        with tempfile.TemporaryDirectory() as temp:
            state_dir = Path(temp) / 'state'
            waiting = start(recipe, state_dir, compatible_observation())
            self.assertEqual(waiting['status'], 'WAITING_USER')
            self.assertEqual(waiting['waiting']['reason'], 'artifact_file')
            self.assertEqual(waiting['attempts']['total'], 0)
            archive = Path(temp) / 'provided.tar.gz'
            archive.write_bytes(blob)
            done = resume(recipe, state_dir, compatible_observation(), artifact_file=archive)
            self.assertEqual(done['status'], 'SUCCEEDED')
            self.assertEqual(done['success_scope'], 'binary_installation')
            self.assertEqual(done['checks']['api_authentication'], 'not_checked')
            self.assertEqual(done['checks']['python_kernel'], 'not_checked')
            self.assertEqual(done['attempts']['total'], 1)
            again = resume(recipe, state_dir, compatible_observation(), artifact_file=archive)
            self.assertEqual(again['attempts']['total'], 1)
            self.assertEqual(again['completed_steps'], ['binary_installation'])

    def test_wait_for_user_preserves_attempts_checkpoint_and_resume_location(self):
        with tempfile.TemporaryDirectory() as temp:
            state_dir = Path(temp) / 'state'
            current = start(self.recipe, state_dir, compatible_observation())
            current['attempts'] = {'total': 3, 'by_step': {'binary_installation': 1}}
            current['current_step'] = 'binary_installation'
            from agent_welcome.runner import _save_state
            _save_state(state_dir, current)
            waited = record_user_wait(state_dir, 'mfa_required', 'binary_installation')
            self.assertEqual(waited['status'], 'WAITING_USER')
            self.assertEqual(waited['attempts']['total'], 3)
            self.assertEqual(waited['current_step'], 'binary_installation')
            self.assertEqual(waited['waiting']['resume_at'], 'binary_installation')
            acknowledged = resume(
                self.recipe, state_dir, compatible_observation(),
                user_action_completed=True,
            )
            self.assertEqual(acknowledged['status'], 'NEEDS_DIAGNOSIS')
            self.assertEqual(acknowledged['attempts']['total'], 3)
            self.assertEqual(acknowledged['checks']['api_authentication'], 'not_checked')
            self.assertIn('independent verifier', acknowledged['error'])

    def test_retry_budget_and_recipe_or_environment_drift_are_persisted(self):
        blob = make_archive()
        recipe = recipe_for(blob)
        with tempfile.TemporaryDirectory() as temp:
            state_dir = Path(temp) / 'state'
            start(recipe, state_dir, compatible_observation())
            archive = Path(temp) / 'wrong.tar.gz'
            archive.write_bytes(b'not the matching bytes')
            failed = resume(recipe, state_dir, compatible_observation(), artifact_file=archive)
            self.assertEqual(failed['status'], 'FAILED')
            self.assertEqual(failed['attempts']['total'], 1)
            self.assertIsNone(failed['observed_sha256'])
            self.assertEqual(
                failed['failure_evidence']['candidate_sha256'],
                hashlib.sha256(b'not the matching bytes').hexdigest(),
            )
            drift_observation = compatible_observation()
            drift_observation['libc']['version'] = '2.36'
            drift = resume(recipe, state_dir, drift_observation, artifact_file=archive)
            self.assertEqual(drift['status'], 'NEEDS_DIAGNOSIS')
            self.assertTrue(drift.get('environment_drift'))
        with tempfile.TemporaryDirectory() as temp:
            state_dir = Path(temp) / 'state'
            bad_blob = b'wrong archive bytes'
            recipe = recipe_for(blob)
            start(recipe, state_dir, compatible_observation())
            archive = Path(temp) / 'bad.tar.gz'
            archive.write_bytes(bad_blob)
            first = resume(recipe, state_dir, compatible_observation(), artifact_file=archive)
            second = resume(recipe, state_dir, compatible_observation(), artifact_file=archive)
            third = resume(recipe, state_dir, compatible_observation(), artifact_file=archive)
            self.assertEqual(first['attempts']['by_step']['binary_installation'], 1)
            self.assertEqual(second['attempts']['by_step']['binary_installation'], 2)
            self.assertTrue(third.get('retry_exhausted'))
            self.assertEqual(third['attempts']['total'], 2)
            no_artifact = resume(recipe, state_dir, compatible_observation())
            self.assertEqual(no_artifact['status'], 'FAILED')
            self.assertTrue(no_artifact['retry_exhausted'])
            self.assertNotEqual(no_artifact['status'], 'WAITING_USER')

    @unittest.skipIf(os.name == 'nt', 'reference fixture executes a Linux ARM shell payload')
    def test_digest_failure_can_resume_with_correct_archive_without_stale_success_record(self):
        blob = make_archive()
        recipe = recipe_for(blob)
        with tempfile.TemporaryDirectory() as temp:
            state_dir = Path(temp) / 'state'
            bad = Path(temp) / 'bad.tar.gz'
            good = Path(temp) / 'good.tar.gz'
            bad.write_bytes(b'corrupted or unrelated artifact')
            good.write_bytes(blob)
            start(recipe, state_dir, compatible_observation())
            failed = resume(recipe, state_dir, compatible_observation(), artifact_file=bad)
            self.assertEqual(failed['status'], 'FAILED')
            self.assertEqual(failed['completed_steps'], [])
            self.assertIsNone(failed['observed_sha256'])
            recovered = resume(recipe, state_dir, compatible_observation(), artifact_file=good)
            self.assertEqual(recovered['status'], 'SUCCEEDED')
            self.assertEqual(recovered['attempts']['total'], 2)
            self.assertEqual(recovered['observed_sha256'], hashlib.sha256(blob).hexdigest())
            self.assertEqual(
                recovered['failure_history'][0]['candidate_sha256'],
                hashlib.sha256(b'corrupted or unrelated artifact').hexdigest(),
            )
            self.assertIsNone(recovered['failure_evidence'])
            self.assertEqual(len(recovered['failure_history']), 1)

    @unittest.skipIf(os.name == 'nt', 'reference fixture executes a Linux ARM shell payload')
    def test_modified_installed_payload_invalidates_success_and_can_be_repaired(self):
        blob = make_archive()
        recipe = recipe_for(blob)
        with tempfile.TemporaryDirectory() as temp:
            state_dir = Path(temp) / 'state'
            archive = Path(temp) / 'provided.tar.gz'
            archive.write_bytes(blob)
            start(recipe, state_dir, compatible_observation())
            resume(
                recipe, state_dir, compatible_observation(), artifact_file=archive,
            )
            payload = state_dir / 'install' / recipe['artifact']['id'] / 'prime-agent'
            payload.write_bytes(b'changed after the successful install')
            invalidated = resume(recipe, state_dir, compatible_observation())
            self.assertEqual(invalidated['status'], 'FAILED')
            self.assertTrue(invalidated['install_evidence_invalidated'])
            self.assertNotEqual(invalidated['status'], 'SUCCEEDED')
            repaired = resume(
                recipe, state_dir, compatible_observation(), artifact_file=archive,
            )
            self.assertEqual(repaired['status'], 'SUCCEEDED')
            self.assertEqual(repaired['attempts']['total'], 2)

    @unittest.skipIf(os.name == 'nt', 'reference fixture executes a Linux ARM shell payload')
    def test_invalid_recovery_input_preserves_owned_installation(self):
        blob = make_archive()
        recipe = recipe_for(blob)
        with tempfile.TemporaryDirectory() as temp:
            state_dir = Path(temp) / 'state'
            archive = Path(temp) / 'provided.tar.gz'
            archive.write_bytes(blob)
            start(recipe, state_dir, compatible_observation())
            installed = resume(
                recipe, state_dir, compatible_observation(), artifact_file=archive,
            )
            payload = state_dir / 'install' / recipe['artifact']['id'] / 'prime-agent'
            payload.write_bytes(b'changed after the successful install')
            invalidated = resume(recipe, state_dir, compatible_observation())
            self.assertEqual(invalidated['status'], 'FAILED')
            missing = Path(temp) / 'does-not-exist.tar.gz'
            with self.assertRaises(RunError):
                resume(
                    recipe, state_dir, compatible_observation(), artifact_file=missing,
                )
            self.assertTrue(payload.exists())
            self.assertEqual(payload.read_bytes(), b'changed after the successful install')
            self.assertTrue((state_dir / 'install' / recipe['artifact']['id']).exists())

    @unittest.skipIf(os.name == 'nt', 'reference fixture executes a Linux ARM shell payload')
    def test_exhausted_repair_budget_preserves_owned_installation(self):
        blob = make_archive()
        recipe = recipe_for(blob)
        with tempfile.TemporaryDirectory() as temp:
            state_dir = Path(temp) / 'state'
            archive = Path(temp) / 'provided.tar.gz'
            archive.write_bytes(blob)
            start(recipe, state_dir, compatible_observation())
            resume(recipe, state_dir, compatible_observation(), artifact_file=archive)
            payload = state_dir / 'install' / recipe['artifact']['id'] / 'prime-agent'
            payload.write_bytes(b'changed after the successful install')
            invalidated = resume(recipe, state_dir, compatible_observation())
            self.assertEqual(invalidated['status'], 'FAILED')
            invalidated['attempts'] = {
                'total': 2,
                'by_step': {'binary_installation': 2},
            }
            from agent_welcome.runner import _save_state
            _save_state(state_dir, invalidated)
            exhausted = resume(
                recipe, state_dir, compatible_observation(), artifact_file=archive,
            )
            self.assertEqual(exhausted['status'], 'FAILED')
            self.assertTrue(exhausted['retry_exhausted'])
            self.assertTrue(payload.exists())
            self.assertEqual(payload.read_bytes(), b'changed after the successful install')

    def test_recipe_rejects_glibc_231_and_writes_only_under_state_dir(self):
        wrong = compatible_observation()
        wrong['libc']['version'] = '2.31'
        with tempfile.TemporaryDirectory() as temp:
            state_dir = Path(temp) / 'state'
            result = start(self.recipe, state_dir, wrong)
            self.assertEqual(result['status'], 'UNSUPPORTED')
            self.assertEqual(list(Path(temp).iterdir()), [state_dir])
            self.assertTrue((state_dir / 'state.json').exists())

    @unittest.skipIf(os.name == 'nt', 'symlink creation may require elevated Windows privileges')
    def test_state_local_install_symlink_cannot_redirect_writes_outside_state_dir(self):
        blob = make_archive()
        recipe = recipe_for(blob)
        with tempfile.TemporaryDirectory() as temp:
            state_dir = Path(temp) / 'state'
            outside = Path(temp) / 'outside'
            outside.mkdir()
            start(recipe, state_dir, compatible_observation())
            (state_dir / 'install').symlink_to(outside, target_is_directory=True)
            archive = Path(temp) / 'provided.tar.gz'
            archive.write_bytes(blob)
            result = resume(
                recipe, state_dir, compatible_observation(), artifact_file=archive,
            )
            self.assertEqual(result['status'], 'NEEDS_DIAGNOSIS')
            self.assertEqual(list(outside.iterdir()), [])

    def test_recipe_drift_is_not_reused(self):
        blob = make_archive()
        recipe = recipe_for(blob)
        with tempfile.TemporaryDirectory() as temp:
            state_dir = Path(temp) / 'state'
            start(recipe, state_dir, compatible_observation())
            changed = json.loads(json.dumps(recipe))
            changed['retry_budget']['total'] = 5
            result = resume(changed, state_dir, compatible_observation())
            self.assertEqual(result['status'], 'NEEDS_DIAGNOSIS')
            self.assertTrue(result['recipe_drift'])
            self.assertEqual(result['attempts']['total'], 0)

    def test_start_rejects_malformed_known_observation_fields_before_state_creation(self):
        observation = compatible_observation()
        observation['runtime_kind'] = 123
        observation['capabilities'] = 'bad'
        with tempfile.TemporaryDirectory() as temp:
            state_dir = Path(temp) / 'state'
            with self.assertRaises(RunError):
                start(self.recipe, state_dir, observation)
            self.assertFalse(state_dir.exists())

    def test_null_provenance_is_unobserved_and_waits_for_artifact(self):
        observation = compatible_observation()
        observation['provenance'] = None
        with tempfile.TemporaryDirectory() as temp:
            state = start(
                self.recipe, Path(temp) / 'state', observation,
            )
            self.assertEqual(state['status'], 'WAITING_USER')
            self.assertIsNone(state['fixture_or_device_evidence'])

    def test_runner_rejects_unimplemented_required_check_before_any_success_path(self):
        recipe = json.loads(json.dumps(self.recipe))
        recipe['required_checks'].append('check_sandbox')
        with tempfile.TemporaryDirectory() as temp:
            state_dir = Path(temp) / 'state'
            with self.assertRaises(CatalogError):
                start(recipe, state_dir, compatible_observation())
            self.assertFalse(state_dir.exists())

    @unittest.skipIf(os.name == 'nt', 'reference fixture executes a Linux ARM shell payload')
    def test_interrupted_install_reconciles_manifest_without_duplicate_probe(self):
        blob = make_counting_archive()
        recipe = recipe_for(blob)
        with tempfile.TemporaryDirectory() as temp:
            state_dir = Path(temp) / 'state'
            start(recipe, state_dir, compatible_observation())
            archive = Path(temp) / 'fixture.tar.gz'
            archive.write_bytes(blob)

            def interrupt_after_install(_result):
                raise KeyboardInterrupt()

            with self.assertRaises(KeyboardInterrupt):
                resume(
                    recipe, state_dir, compatible_observation(), artifact_file=archive,
                    _after_install=interrupt_after_install,
                )
            interrupted = status(state_dir)
            self.assertEqual(interrupted['status'], 'RUNNING')
            self.assertEqual(interrupted['attempts']['total'], 1)
            probe_count = state_dir / 'install' / recipe['artifact']['id'] / 'probe-count'
            self.assertEqual(probe_count.read_text().splitlines(), ['run'])
            completed = resume(
                recipe, state_dir, compatible_observation(), artifact_file=archive,
            )
            self.assertEqual(completed['status'], 'SUCCEEDED')
            self.assertEqual(completed['attempts']['total'], 1)
            self.assertTrue(completed['install_evidence']['reused_after_interruption'])
            self.assertEqual(probe_count.read_text().splitlines(), ['run'])

    def test_concurrent_state_directory_run_is_rejected(self):
        recipe = self.recipe
        with tempfile.TemporaryDirectory() as temp:
            state_dir = Path(temp) / 'state'
            context = multiprocessing.get_context(
                'fork' if 'fork' in multiprocessing.get_all_start_methods() else 'spawn'
            )
            queue = context.Queue()
            with locked_state_dir(state_dir):
                process = context.Process(
                    target=_try_concurrent_start, args=(queue, recipe, state_dir)
                )
                process.start()
                outcome = queue.get(timeout=10)
                process.join(timeout=10)
                if process.is_alive():
                    process.terminate()
                    process.join(timeout=5)
            self.assertEqual(outcome, 'locked')
            self.assertEqual(process.exitcode, 0)

    def test_state_and_recipe_hash_are_atomic_json_and_match_saved_recipe(self):
        with tempfile.TemporaryDirectory() as temp:
            state_dir = Path(temp) / 'state'
            state = start(self.recipe, state_dir, compatible_observation())
            saved = json.loads((state_dir / 'state.json').read_text())
            self.assertEqual(saved['recipe_sha256'], state['recipe_sha256'])
            self.assertNotIn('token', json.dumps(saved).lower())
            self.assertEqual(status(state_dir), saved)


if __name__ == '__main__':
    unittest.main()
