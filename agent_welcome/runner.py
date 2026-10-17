"""Persistent, bounded setup state machine for recipe-owned runtime actions."""

import contextlib
import hashlib
import json
import os
import re
import tempfile
from pathlib import Path

from . import artifacts
from .catalog import CatalogError, validate_recipe
from .conditions import ConditionError, evaluate_condition, validate_observations
from .environment import observe as observe_environment


STATE_NAME = 'state.json'
LOCK_NAME = '.agent-welcome.lock'
STATES = {
    'READY', 'RUNNING', 'WAITING_USER', 'SUCCEEDED', 'NOT_APPLICABLE',
    'UNSUPPORTED', 'FAILED', 'NEEDS_DIAGNOSIS',
}


class RunError(RuntimeError):
    pass


@contextlib.contextmanager
def locked_state_dir(state_dir):
    root = Path(state_dir).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    lock_path = root / LOCK_NAME
    if lock_path.is_symlink():
        raise RunError('state lock path must not be a symbolic link')
    stream = lock_path.open('a+b')
    try:
        try:
            if os.name == 'nt':
                import msvcrt
                stream.seek(0)
                if stream.read(1) == b'':
                    stream.write(b'0')
                    stream.flush()
                stream.seek(0)
                msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except (BlockingIOError, OSError) as exc:
            raise RunError(f'state directory is locked: {root}') from exc
        yield root
    finally:
        try:
            if os.name == 'nt':
                import msvcrt
                stream.seek(0)
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl
                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)
        except OSError:
            pass
        stream.close()


def _canonical_hash(value):
    payload = json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False)
    return hashlib.sha256(payload.encode('utf-8')).hexdigest()


def _state_path(root):
    return Path(root) / STATE_NAME


def _save_state(root, state):
    path = _state_path(root)
    fd, name = tempfile.mkstemp(prefix='.state-', suffix='.tmp', dir=root)
    temp = Path(name)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            json.dump(state, stream, sort_keys=True, ensure_ascii=False)
            stream.write('\n')
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temp, 0o600)
        os.replace(temp, path)
    except BaseException:
        try:
            temp.unlink()
        except FileNotFoundError:
            pass
        raise


def _read_state(root):
    path = _state_path(root)
    if path.is_symlink():
        raise RunError('state file must not be a symbolic link')
    try:
        state = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError) as exc:
        raise RunError(f'cannot read state file: {exc}') from exc
    if state.get('schema_version') != '1.0' or state.get('status') not in STATES:
        raise RunError('state file has an unsupported schema or status')
    return state


def status(state_dir):
    root = Path(state_dir).expanduser().resolve()
    if not _state_path(root).is_file():
        raise RunError(f'no setup state in {root}')
    return _read_state(root)


def _new_state(recipe, observation):
    return {
        'schema_version': '1.0',
        'run_id': hashlib.sha256(os.urandom(32)).hexdigest()[:24],
        'recipe_id': recipe['id'],
        'recipe_version': recipe['version'],
        'recipe_sha256': _canonical_hash(recipe),
        'environment_fingerprint': _canonical_hash(observation),
        'environment': observation,
        'status': 'READY',
        'success_scope': recipe['success_scope'],
        'current_step': 'binary_installation',
        'completed_steps': [],
        'attempts': {'total': 0, 'by_step': {}},
        'checks': {
            'binary_installation': 'pending',
            'api_authentication': 'not_checked',
            'python_kernel': 'not_checked',
            'model_task': 'not_checked',
        },
        'published_sha256': recipe['artifact']['published_sha256'],
        'observed_sha256': None,
        'failure_evidence': None,
        'failure_history': [],
        'artifact_integrity_verified': False,
        'download_verified': False,
        'artifact_source': None,
        'waiting': None,
        'error': None,
        'recipe_drift': False,
        'environment_drift': False,
        'retry_exhausted': False,
        'fixture_or_device_evidence': observation.get('provenance', {}).get('kind'),
    }


def _eligibility_status(recipe, observation):
    result = evaluate_condition(recipe['applicability'], observation)
    if result['status'] == 'pass':
        return 'READY', result
    if result['status'] == 'unknown':
        return 'NEEDS_DIAGNOSIS', result
    if observation.get('kernel_os') != recipe['artifact']['os'] or (
        observation.get('architecture') != recipe['artifact']['architecture']
    ):
        return 'NOT_APPLICABLE', result
    return 'UNSUPPORTED', result


def _required_checks_pass(recipe, state):
    return all(
        state.get('checks', {}).get(check_id) == 'pass'
        for check_id in recipe.get('required_checks', [])
    )


def _resolve_artifact(root, artifact, artifact_file, download):
    if artifact_file is not None:
        path = Path(artifact_file).expanduser()
        if not path.is_file():
            raise RunError(f'artifact_file does not exist: {path}')
        return path.absolute()
    if download:
        try:
            return artifacts.download_artifact(artifact, root)
        except artifacts.InstallError:
            raise
        except OSError as exc:
            raise RunError(str(exc)) from exc
    return None


def _set_waiting(state, reason, resume_at):
    state['status'] = 'WAITING_USER'
    state['waiting'] = {'reason': reason, 'resume_at': resume_at}
    state['current_step'] = resume_at
    return state


def _continue_locked(
    recipe, root, observation, state, artifact_file=None, download=False,
    after_install=None, user_action_completed=False,
):
    current_recipe_hash = _canonical_hash(recipe)
    current_env_hash = _canonical_hash(observation)
    if state['recipe_sha256'] != current_recipe_hash:
        state['status'] = 'NEEDS_DIAGNOSIS'
        state['recipe_drift'] = True
        state['error'] = 'recipe changed since this run was created'
        _save_state(root, state)
        return state
    if state['environment_fingerprint'] != current_env_hash:
        state['status'] = 'NEEDS_DIAGNOSIS'
        state['environment_drift'] = True
        state['error'] = 'environment changed since this run was created'
        _save_state(root, state)
        return state
    install_parent = root / 'install'
    if install_parent.is_symlink() or (
        install_parent.exists() and not install_parent.is_dir()
    ):
        state['status'] = 'NEEDS_DIAGNOSIS'
        state['error'] = 'state-local install path must be a real directory'
        _save_state(root, state)
        return state
    install_dir = install_parent / recipe['artifact']['id']
    needs_install_reconciliation = (
        state['status'] == 'SUCCEEDED'
        or (state['status'] == 'FAILED' and state.get('install_evidence_invalidated'))
    )
    if needs_install_reconciliation:
        was_succeeded = state['status'] == 'SUCCEEDED'
        check = artifacts.inspect_installation(
            recipe['artifact'], install_dir, current_recipe_hash, state['observed_sha256'],
        )
        if check['valid']:
            if was_succeeded:
                if _required_checks_pass(recipe, state):
                    return state
                state['status'] = 'NEEDS_DIAGNOSIS'
                state['error'] = 'a required recipe check is not recorded as passed'
                _save_state(root, state)
                return state
            if not _required_checks_pass(recipe, state):
                state['status'] = 'NEEDS_DIAGNOSIS'
                state['error'] = 'a required recipe check is not recorded as passed'
                _save_state(root, state)
                return state
            state['status'] = 'SUCCEEDED'
            state['completed_steps'] = ['binary_installation']
            state['checks']['binary_installation'] = 'pass'
            state['error'] = None
            _save_state(root, state)
            return state
        state['checks']['binary_installation'] = 'fail'
        state['completed_steps'] = []
        state['error'] = check['reason']
        state['install_evidence_invalidated'] = True
        state['status'] = 'FAILED'
        missing_install = not install_dir.exists() and not install_dir.is_symlink()
        if not check['owned'] and not missing_install:
            state['status'] = 'NEEDS_DIAGNOSIS'
            _save_state(root, state)
            return state
        if artifact_file is None and not download:
            _save_state(root, state)
            return state
        if check['owned']:
            try:
                artifacts.remove_owned_installation(
                    recipe['artifact'], install_dir, current_recipe_hash,
                    state['observed_sha256'],
                )
            except artifacts.InstallError as exc:
                state['status'] = 'NEEDS_DIAGNOSIS'
                state['error'] = str(exc)
                _save_state(root, state)
                return state
        _save_state(root, state)
    if state['status'] in {'NOT_APPLICABLE', 'UNSUPPORTED', 'NEEDS_DIAGNOSIS'}:
        return state
    if state['status'] == 'WAITING_USER' and state.get('waiting', {}).get('reason') not in {
        'artifact_file', 'download',
    }:
        if not user_action_completed:
            return state
        state['previous_wait'] = state['waiting']
        state['waiting'] = None
        state['status'] = 'NEEDS_DIAGNOSIS'
        state['error'] = (
            'user action was acknowledged; credential validity still requires an independent verifier'
        )
        _save_state(root, state)
        return state
    archive = None
    if artifact_file is None and not download:
        _set_waiting(state, 'artifact_file', 'binary_installation')
        _save_state(root, state)
        return state
    if artifact_file is not None:
        archive = _resolve_artifact(root, recipe['artifact'], artifact_file, False)
    step = 'binary_installation'
    install_dir = root / 'install' / recipe['artifact']['id']
    reconciling = state['status'] == 'RUNNING' and state.get('current_step') == step and install_dir.exists()
    attempts = state['attempts']
    step_count = attempts['by_step'].get(step, 0)
    if step_count:
        artifacts.cleanup_staging(
            install_dir.parent,
            run_id=state['run_id'],
            attempts=range(1, step_count + 1),
            allowed_root=root,
        )
    per_step_max = int(recipe.get('retry_budget', {}).get('per_step', 2))
    total_max = int(recipe.get('retry_budget', {}).get('total', 6))
    if not reconciling and (step_count >= per_step_max or attempts['total'] >= total_max):
        state['status'] = 'FAILED'
        state['retry_exhausted'] = True
        state['error'] = 'retry budget exhausted'
        _save_state(root, state)
        return state
    if not reconciling:
        attempts['total'] += 1
        attempts['by_step'][step] = step_count + 1
    stage_attempt = step_count if reconciling else step_count + 1
    state['status'] = 'RUNNING'
    state['current_step'] = step
    state['waiting'] = None
    state['error'] = None
    _save_state(root, state)
    try:
        if install_parent.is_symlink():
            raise RunError('state-local install path became a symbolic link')
        install_parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        if archive is None:
            archive = _resolve_artifact(root, recipe['artifact'], None, True)
        result = artifacts.verify_extract_and_probe(
            recipe['artifact'], archive, install_dir, recipe_sha256=current_recipe_hash,
            allowed_root=root, run_id=state['run_id'], attempt=stage_attempt,
        )
        if after_install is not None:
            after_install(result)
        state['observed_sha256'] = result['observed_sha256']
        state['artifact_integrity_verified'] = True
        state['download_verified'] = bool(download)
        state['artifact_source'] = 'download' if download else 'supplied_file'
        state['completed_steps'] = ['binary_installation']
        state['checks']['binary_installation'] = 'pass'
        if not _required_checks_pass(recipe, state):
            state['status'] = 'NEEDS_DIAGNOSIS'
            state['error'] = 'a required recipe check is not recorded as passed'
            state['current_step'] = step
            state['install_evidence'] = {
                'version': result['version'],
                'payload_path': result['payload_path'],
                'reused_after_interruption': result['reused'],
                'success_scope': 'binary_installation',
            }
            _save_state(root, state)
            return state
        state['status'] = 'SUCCEEDED'
        state['current_step'] = None
        state['error'] = None
        state['waiting'] = None
        state['install_evidence'] = {
            'version': result['version'],
            'payload_path': result['payload_path'],
            'reused_after_interruption': result['reused'],
            'success_scope': 'binary_installation',
        }
    except (artifacts.InstallError, OSError, RunError) as exc:
        state['status'] = 'FAILED'
        state['checks']['binary_installation'] = 'fail'
        state['error'] = str(exc)
        evidence = getattr(exc, 'evidence', None)
        if evidence:
            record = {
                'step': step,
                'attempt': attempts['by_step'].get(step, 0),
                **evidence,
            }
            state['failure_evidence'] = record
            state['failure_history'].append(record)
    _save_state(root, state)
    return state


def start(
    recipe, state_dir, observation=None, artifact_file=None, download=False,
    _after_install=None, user_action_completed=False,
):
    validate_recipe(recipe)
    observation = observation if observation is not None else observe_environment()
    if not isinstance(observation, dict):
        raise RunError('environment observation must be an object')
    try:
        validate_observations(observation)
    except ConditionError as exc:
        raise RunError(str(exc)) from exc
    with locked_state_dir(state_dir) as root:
        path = _state_path(root)
        if path.exists():
            state = _read_state(root)
            return _continue_locked(
                recipe, root, observation, state, artifact_file, download,
                _after_install, user_action_completed,
            )
        state = _new_state(recipe, observation)
        eligibility, evidence = _eligibility_status(recipe, observation)
        state['eligibility'] = evidence
        state['status'] = eligibility
        _save_state(root, state)
        if eligibility != 'READY':
            return state
        return _continue_locked(
            recipe, root, observation, state, artifact_file, download,
            _after_install, user_action_completed,
        )


def resume(
    recipe, state_dir, observation=None, artifact_file=None, download=False,
    _after_install=None, user_action_completed=False,
):
    validate_recipe(recipe)
    observation = observation if observation is not None else observe_environment()
    if not isinstance(observation, dict):
        raise RunError('environment observation must be an object')
    try:
        validate_observations(observation)
    except ConditionError as exc:
        raise RunError(str(exc)) from exc
    with locked_state_dir(state_dir) as root:
        if not _state_path(root).is_file():
            raise RunError(f'no setup state in {root}')
        state = _read_state(root)
        return _continue_locked(
            recipe, root, observation, state, artifact_file, download,
            _after_install, user_action_completed,
        )


def record_user_wait(state_dir, reason, resume_at):
    """Persist a user-owned checkpoint without consuming an action retry."""
    safe_reason = isinstance(reason, str) and re.fullmatch(r'[a-z][a-z0-9_]{0,63}', reason)
    safe_resume = resume_at in {
        'artifact_file', 'binary_installation', 'provider_authentication', 'python_kernel',
    }
    if not safe_reason or not safe_resume:
        raise RunError('wait reason and resume location must be non-empty strings')
    with locked_state_dir(state_dir) as root:
        state = _read_state(root)
        if state['status'] == 'SUCCEEDED':
            raise RunError('a completed run cannot be changed into a user wait')
        attempts = json.loads(json.dumps(state['attempts']))
        current_step = state['current_step']
        _set_waiting(state, reason, resume_at)
        _save_state(root, state)
        assert state['attempts'] == attempts
        if current_step and current_step != resume_at:
            state['checkpoint_before_wait'] = current_step
            _save_state(root, state)
        return state
