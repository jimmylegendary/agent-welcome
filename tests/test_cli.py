import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class CliTests(unittest.TestCase):
    def run_cli(self, *args):
        env = dict(os.environ)
        env['PYTHONPATH'] = str(ROOT)
        return subprocess.run(
            [sys.executable, '-m', 'agent_welcome', *args],
            cwd=ROOT,
            env=env,
            text=True,
            capture_output=True,
        )

    def test_validate_and_diagnose_need_no_target_agent_or_credentials(self):
        validate = self.run_cli('validate')
        self.assertEqual(validate.returncode, 0, validate.stderr)
        self.assertEqual(json.loads(validate.stdout)['status'], 'VALID')
        diagnose = self.run_cli(
            'diagnose', '--recipe', 'prime-agent-0.10.0-linux-arm64'
        )
        self.assertEqual(diagnose.returncode, 0, diagnose.stderr)
        self.assertIn(
            json.loads(diagnose.stdout)['status'],
            {'NOT_APPLICABLE', 'UNSUPPORTED', 'NEEDS_DIAGNOSIS'},
        )

    def test_external_observations_are_diagnose_only(self):
        with tempfile.TemporaryDirectory() as temp:
            state = str(Path(temp) / 'state')
            result = self.run_cli(
                'start', '--recipe', 'prime-agent-0.10.0-linux-arm64',
                '--state-dir', state, '--observations', str(Path(temp) / 'obs.json'),
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(Path(state).exists())

    def test_start_resume_and_status_use_only_the_explicit_state_directory(self):
        with tempfile.TemporaryDirectory() as temp:
            state_dir = Path(temp) / 'chosen-state'
            started = self.run_cli(
                'start', '--recipe', 'prime-agent-0.10.0-linux-arm64',
                '--state-dir', str(state_dir),
            )
            self.assertEqual(started.returncode, 0, started.stderr)
            start_state = json.loads(started.stdout)
            self.assertTrue((state_dir / 'state.json').is_file())
            resumed = self.run_cli('resume', '--state-dir', str(state_dir))
            self.assertEqual(resumed.returncode, 0, resumed.stderr)
            resume_state = json.loads(resumed.stdout)
            queried = self.run_cli('status', '--state-dir', str(state_dir))
            self.assertEqual(queried.returncode, 0, queried.stderr)
            status_state = json.loads(queried.stdout)
            self.assertEqual(start_state['recipe_id'], resume_state['recipe_id'])
            self.assertEqual(resume_state, status_state)
            self.assertEqual(list(Path(temp).iterdir()), [state_dir])


if __name__ == '__main__':
    unittest.main()
