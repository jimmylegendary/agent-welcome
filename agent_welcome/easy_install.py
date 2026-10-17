"""Evidence-aware orchestration for twelve consent-gated Easy Install targets.

An installer is downloaded from a listed official HTTPS endpoint into the explicit
state directory and is run only after a product-level consent flag.  The adapter
records endpoint, byte count, and digest before execution, never uses a shell
pipeline, and reconciles interruption with a version probe before another attempt.
Login and billable first work remain separate consent boundaries.
"""

import contextlib
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from .catalog import ROOT


EASY_STATE_NAME = 'easy-state.json'
EASY_LOCK_NAME = '.agent-welcome-easy.lock'
EASY_STATES = {
    'READY', 'RUNNING', 'WAITING_USER', 'SUCCEEDED', 'USER_ATTESTED',
    'NOT_APPLICABLE', 'UNSUPPORTED', 'FAILED', 'NEEDS_DIAGNOSIS',
}
STEPS = ('environment', 'prerequisites', 'agent_installation', 'path_config',
         'provider_authentication', 'minimal_first_task')
SECRET_KEY_RE = re.compile(r'(token|secret|password|authorization|cookie|api[_-]?key|code)', re.I)
SECRET_VALUE_RE = re.compile(r'(bearer\s+|sk-[A-Za-z0-9_-]{8,}|eyJ[A-Za-z0-9_-]{8,})', re.I)


class EasyInstallError(RuntimeError):
    pass


def _canonical(value):
    return hashlib.sha256(json.dumps(
        value, sort_keys=True, separators=(',', ':'), ensure_ascii=False,
    ).encode('utf-8')).hexdigest()


def _safe_message(value):
    return SECRET_VALUE_RE.sub('[redacted]', str(value))[:500]


def _read_json(path):
    try:
        return json.loads(Path(path).read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError) as exc:
        raise EasyInstallError(f'cannot read JSON {path}: {exc}') from exc


def load_targets(path=None):
    data = _read_json(path or ROOT / 'catalog' / 'easy-install-targets.json')
    validate_targets(data)
    return data


def validate_targets(data):
    if not isinstance(data, dict) or data.get('schema_version') != '1.0':
        raise EasyInstallError('easy install catalog schema_version must be 1.0')
    sources = data.get('sources')
    targets = data.get('targets')
    if not isinstance(sources, dict) or not isinstance(targets, list):
        raise EasyInstallError('easy install catalog needs sources and targets')
    expected = {(os_name, agent) for os_name in ('macos', 'windows', 'android', 'ios')
                for agent in ('claude-code', 'codex', 'prime-agent')}
    seen = set()
    for target in targets:
        required = {'id', 'os', 'agent', 'command', 'host', 'source_refs',
                    'version_policy', 'manual_install', 'login_instruction',
                    'first_task_instruction', 'recovery'}
        if not isinstance(target, dict) or required - set(target):
            raise EasyInstallError('easy install target is missing required fields')
        pair = (target['os'], target['agent'])
        if pair not in expected or pair in seen:
            raise EasyInstallError(f'invalid or duplicate easy install target: {pair}')
        seen.add(pair)
        host = target['host']
        if not isinstance(host, dict) or host.get('same_device_route') not in {
            'native', 'termux_proot_linux_userland', 'utm_linux_guest',
        }:
            raise EasyInstallError(f'{target["id"]} must declare a same-device route')
        if host.get('host_os') != target['os']:
            raise EasyInstallError(f'{target["id"]} host_os must equal its target OS')
        if not isinstance(target['command'], str) or not re.fullmatch(r'[a-z][a-z0-9-]*', target['command']):
            raise EasyInstallError(f'{target["id"]} has an unsafe command name')
        if not isinstance(target['source_refs'], list) or not target['source_refs']:
            raise EasyInstallError(f'{target["id"]} needs official source references')
        for source_id in target['source_refs']:
            source = sources.get(source_id)
            if not isinstance(source, dict) or source.get('kind', '').startswith('community'):
                raise EasyInstallError(f'{target["id"]} has no official source {source_id}')
            if not str(source.get('url', '')).startswith('https://'):
                raise EasyInstallError(f'{target["id"]} source must use HTTPS')
        if not isinstance(target['version_policy'], dict) or target['version_policy'].get('probe') != ['--version']:
            raise EasyInstallError(f'{target["id"]} needs a --version policy')
        if not all(isinstance(target[key], str) and target[key] for key in (
            'manual_install', 'login_instruction', 'first_task_instruction',
        )) or not isinstance(target['recovery'], list) or not target['recovery']:
            raise EasyInstallError(f'{target["id"]} is missing executable guidance')
    if seen != expected:
        raise EasyInstallError('easy install catalog must contain exactly 4 OS x 3 agent targets')
    return True


def get_target(target_id, catalog=None):
    catalog = catalog or load_targets()
    for target in catalog['targets']:
        if target['id'] == target_id:
            return target
    raise EasyInstallError(f'unknown easy install target: {target_id}')


@contextlib.contextmanager
def _locked_state_dir(state_dir):
    root = Path(state_dir).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    lock = root / EASY_LOCK_NAME
    if lock.is_symlink():
        raise EasyInstallError('easy install lock path must not be a symbolic link')
    stream = lock.open('a+b')
    try:
        try:
            if os.name == 'nt':
                import msvcrt
                stream.seek(0)
                if not stream.read(1):
                    stream.write(b'0')
                    stream.flush()
                stream.seek(0)
                msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except (BlockingIOError, OSError) as exc:
            raise EasyInstallError(f'easy install state directory is locked: {root}') from exc
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


def _state_path(root):
    return Path(root) / EASY_STATE_NAME


def _save(root, state):
    path = _state_path(root)
    fd, name = tempfile.mkstemp(prefix='.easy-state-', suffix='.tmp', dir=root)
    temp = Path(name)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            json.dump(state, stream, ensure_ascii=False, sort_keys=True)
            stream.write('\n')
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temp, stat.S_IRUSR | stat.S_IWUSR)
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
        raise EasyInstallError('easy install state file must not be a symbolic link')
    state = _read_json(path)
    if state.get('schema_version') != 'easy-1.0' or state.get('status') not in EASY_STATES:
        raise EasyInstallError('easy install state has an unsupported schema or status')
    return state


def easy_status(state_dir):
    root = Path(state_dir).expanduser().resolve()
    if not _state_path(root).is_file():
        raise EasyInstallError(f'no easy install state in {root}')
    return _read_state(root)


def _host_fingerprint(observation):
    return {
        key: observation.get(key)
        for key in ('kernel_os', 'host_os', 'architecture', 'runtime_kind')
    }


def _new_state(target, observation):
    return {
        'schema_version': 'easy-1.0',
        'target_id': target['id'],
        'target_sha256': _canonical(target),
        'environment_fingerprint': _canonical(_host_fingerprint(observation)),
        'environment': _host_fingerprint(observation),
        'status': 'READY',
        'current_step': 'environment',
        'completed_steps': [],
        'waiting': None,
        'error': None,
        'attempts': {'total': 0, 'by_step': {}},
        'retry_budget': {'per_step': 2, 'total': 6},
        'checks': {step: 'pending' for step in STEPS},
        'failure_evidence': None,
        'failure_history': [],
        'agent_executable': None,
        'launcher_path': None,
        'evidence': {
            'implementation': 'local_code',
            'fixture': False,
            'actual_os': False,
            'upstream_binary': False,
            'authentication': 'not_checked',
            'first_task': 'not_checked',
        },
    }


def _fail(state, step, message, kind='runtime_error'):
    record = {'step': step, 'kind': kind, 'message': _safe_message(message)}
    state['status'] = 'FAILED'
    state['error'] = record['message']
    state['checks'][step] = 'fail'
    state['failure_evidence'] = record
    state['failure_history'].append(record)
    return state


def _complete(state, step):
    state['checks'][step] = 'pass'
    if step not in state['completed_steps']:
        state['completed_steps'].append(step)
    state['current_step'] = None
    state['failure_evidence'] = None
    state['error'] = None


def _wait(state, reason, step, instructions):
    state['status'] = 'WAITING_USER'
    state['current_step'] = step
    state['waiting'] = {'reason': reason, 'resume_at': step, 'instructions': instructions}
    return state


def _target_matches(target, observation):
    expected = target['host']
    unknown = []
    for field in ('kernel_os', 'host_os'):
        actual = observation.get(field)
        if actual is None:
            unknown.append(field)
        elif actual != expected[field]:
            return 'NOT_APPLICABLE', f'{field}={actual!r} does not match {expected[field]!r}'
    if unknown:
        return 'NEEDS_DIAGNOSIS', f'missing direct observation: {", ".join(unknown)}'
    route = expected['same_device_route']
    runtime = observation.get('runtime_kind')
    if route == 'termux_proot_linux_userland' and runtime not in {'proot', 'linux_userland'}:
        return 'WAITING_USER', 'same-device Termux/PRoot Linux userland is not observed'
    if route == 'utm_linux_guest' and runtime != 'linux_guest':
        return 'WAITING_USER', 'same-device UTM Linux guest marker is not observed'
    return 'READY', None


def _version_at_least(value, minimum):
    try:
        actual_parts = tuple(int(part) for part in value.split('.'))
        minimum_parts = tuple(int(part) for part in minimum.split('.'))
    except (AttributeError, ValueError):
        return None
    length = max(len(actual_parts), len(minimum_parts))
    return actual_parts + (0,) * (length - len(actual_parts)) >= minimum_parts + (0,) * (length - len(minimum_parts))


def _android_prerequisite_plan(target):
    return {
        'same_device_only': True,
        'commands': [
            ['pkg', 'install', '-y', 'proot-distro'],
            ['proot-distro', 'install', 'ubuntu:24.04'],
        ],
        'scope': 'Installs the Termux PRoot-Distro package and a Linux guest in the current Android device Termux storage. It does not use a remote host or change Android security settings.',
        'after_completion': 'Run proot-distro login ubuntu:24.04, then start this same Easy Install state directory from inside that guest.',
        'recovery': target['recovery'],
    }


def _step_attempt_allowed(state, step):
    attempts = state['attempts']
    if attempts['by_step'].get(step, 0) >= state['retry_budget']['per_step'] or attempts['total'] >= state['retry_budget']['total']:
        state['status'] = 'FAILED'
        state['error'] = 'retry budget exhausted'
        state['retry_exhausted'] = True
        return False
    return True


def _run(argv, root, runner=subprocess.run):
    if not isinstance(argv, list) or not argv or not all(isinstance(value, str) and value for value in argv):
        raise EasyInstallError('subprocess command must be a non-empty argv list')
    safe_env = {'PATH': os.environ.get('PATH', ''), 'HOME': os.environ.get('HOME', '')}
    if os.name == 'nt':
        safe_env['SystemRoot'] = os.environ.get('SystemRoot', r'C:\\Windows')
    try:
        completed = runner(
            argv, cwd=str(root), env=safe_env, shell=False, text=True,
            capture_output=True, timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise EasyInstallError(_safe_message(exc)) from exc
    if completed.returncode != 0:
        raise EasyInstallError(_safe_message(completed.stderr or completed.stdout or f'exit {completed.returncode}'))
    return completed.stdout.strip()


def _installer_spec(target):
    """Return a non-shell argv prefix and a pinned-to-vendor installer URL."""
    urls = {
        'claude-code': {
            'unix': 'https://claude.ai/install.sh',
            'windows': 'https://claude.ai/install.ps1',
        },
        'codex': {
            'unix': 'https://chatgpt.com/codex/install.sh',
            'windows': 'https://chatgpt.com/codex/install.ps1',
        },
        'prime-agent': {
            'unix': 'https://app.primeintellect.ai/prime-agent/install.sh',
            'windows': 'https://app.primeintellect.ai/prime-agent/install.ps1',
        },
    }
    platform_key = 'windows' if target['os'] == 'windows' else 'unix'
    url = urls[target['agent']][platform_key]
    if platform_key == 'windows':
        # Do not add an execution-policy bypass or alter a system policy.  A
        # blocked invocation becomes durable evidence with recovery guidance.
        argv_prefix = ['powershell.exe', '-NoProfile', '-File']
        filename = 'official-installer.ps1'
    else:
        argv_prefix = ['bash' if target['agent'] == 'claude-code' else 'sh']
        filename = 'official-installer.sh'
    return {
        'url': url,
        'expected_host': urllib.parse.urlsplit(url).hostname,
        'argv_prefix': argv_prefix,
        'filename': filename,
    }


def _download_official_installer(root, target, opener=urllib.request.urlopen):
    spec = _installer_spec(target)
    destination_dir = root / 'downloads'
    if destination_dir.is_symlink():
        raise EasyInstallError('state-local download directory must not be a symbolic link')
    destination_dir.mkdir(mode=0o700, exist_ok=True)
    destination = destination_dir / spec['filename']
    if destination.is_symlink():
        raise EasyInstallError('state-local installer path must not be a symbolic link')
    digest = hashlib.sha256()
    total = 0
    fd, temp_name = tempfile.mkstemp(prefix='.installer-', suffix='.tmp', dir=destination_dir)
    temp = Path(temp_name)
    try:
        request = urllib.request.Request(spec['url'], headers={'User-Agent': 'agent-welcome-easy-install/1'})
        # Open the local descriptor first.  If the transport connection fails
        # before entering its context manager, this still closes the Windows
        # handle before the cleanup path tries to unlink the temp file.
        with os.fdopen(fd, 'wb') as stream:
            with opener(request, timeout=30) as response:
                resolved_url = response.geturl() if hasattr(response, 'geturl') else spec['url']
                resolved = urllib.parse.urlsplit(resolved_url)
                if resolved.scheme != 'https' or resolved.hostname != spec['expected_host']:
                    raise EasyInstallError('official installer redirect left the approved HTTPS host')
                while True:
                    chunk = response.read(64 * 1024)
                    if not chunk:
                        break
                    total += len(chunk)
                    if total > 5 * 1024 * 1024:
                        raise EasyInstallError('official installer exceeded the 5 MiB safety limit')
                    digest.update(chunk)
                    stream.write(chunk)
                stream.flush()
                os.fsync(stream.fileno())
        if total == 0:
            raise EasyInstallError('official installer download was empty')
        os.chmod(temp, 0o700)
        os.replace(temp, destination)
    except (OSError, urllib.error.URLError) as exc:
        try:
            temp.unlink()
        except FileNotFoundError:
            pass
        raise EasyInstallError(_safe_message(exc)) from exc
    except BaseException:
        try:
            temp.unlink()
        except FileNotFoundError:
            pass
        raise
    return {
        'path': str(destination), 'url': spec['url'], 'argv_prefix': spec['argv_prefix'],
        'bytes': total, 'sha256': digest.hexdigest(),
    }


def _execute_installer(installer, root, runner=subprocess.run):
    # The installer is an explicit argv element; no vendor-provided string is
    # interpolated into a shell command.
    return _run([*installer['argv_prefix'], installer['path']], root, runner=runner)


def _resolve_executable(command, explicit=None):
    candidate = Path(explicit).expanduser() if explicit else None
    if candidate is not None:
        if not candidate.is_absolute() or not candidate.is_file():
            raise EasyInstallError('agent executable must be an existing absolute file')
        return str(candidate.resolve())
    discovered = shutil.which(command)
    return str(Path(discovered).resolve()) if discovered else None


def _write_launcher(root, target, executable):
    launcher_root = root / 'bin'
    if launcher_root.is_symlink():
        raise EasyInstallError('state-local launcher directory must not be a symbolic link')
    launcher_root.mkdir(mode=0o700, exist_ok=True)
    if os.name == 'nt':
        if '"' in executable:
            raise EasyInstallError('agent executable path cannot contain a double quote')
        path = launcher_root / f'agent-welcome-{target["command"]}.cmd'
        path.write_text(f'@echo off\r\n"{executable}" %*\r\n', encoding='utf-8')
    else:
        import shlex
        path = launcher_root / f'agent-welcome-{target["command"]}'
        path.write_text('#!/bin/sh\nexec ' + shlex.quote(executable) + ' "$@"\n', encoding='utf-8')
        path.chmod(0o700)
    return str(path)


def _attestation(path, target_id, event):
    data = _read_json(path)
    if not isinstance(data, dict) or set(data) != {'target_id', 'event', 'status', 'method'}:
        raise EasyInstallError('evidence must contain only target_id, event, status, and method')
    if data['target_id'] != target_id or data['event'] != event or data['status'] != 'completed':
        raise EasyInstallError('evidence does not match this target and event')
    if not isinstance(data['method'], str) or not data['method'] or len(data['method']) > 80:
        raise EasyInstallError('evidence method must be a short non-secret description')
    if any(SECRET_KEY_RE.search(str(key)) or SECRET_VALUE_RE.search(str(value)) for key, value in data.items()):
        raise EasyInstallError('evidence must not contain credentials, authorization codes, or tokens')
    return {'kind': 'user_attestation', 'event': event, 'method': data['method'], 'sha256': _canonical(data)}


def _continue(target, root, observation, state, agent_executable=None,
              auth_evidence=None, first_task_evidence=None, first_task_command=None,
              allow_billable_first_task=False, approve_install=False,
              approve_prerequisites=False,
              runner=subprocess.run, opener=urllib.request.urlopen):
    if state['target_sha256'] != _canonical(target):
        state['status'] = 'NEEDS_DIAGNOSIS'
        state['error'] = 'target recipe changed since this run was created'
        _save(root, state)
        return state
    observed_fingerprint = _canonical(_host_fingerprint(observation))
    if state['environment_fingerprint'] != observed_fingerprint:
        previous = state.get('environment', {})
        expected_android_guest_transition = (
            target['os'] == 'android'
            and state.get('android_prerequisite_completed')
            and previous.get('kernel_os') == observation.get('kernel_os') == 'linux'
            and previous.get('host_os') == observation.get('host_os') == 'android'
            and previous.get('runtime_kind') == 'linux_userland'
            and observation.get('runtime_kind') == 'proot'
        )
        if expected_android_guest_transition:
            state['environment'] = _host_fingerprint(observation)
            state['environment_fingerprint'] = observed_fingerprint
            state['environment_transition'] = 'termux_to_same_device_proot_guest'
        else:
            state['status'] = 'NEEDS_DIAGNOSIS'
            state['error'] = 'host environment changed since this run was created'
            _save(root, state)
            return state
    if state['status'] in {'SUCCEEDED', 'USER_ATTESTED', 'NOT_APPLICABLE', 'UNSUPPORTED', 'NEEDS_DIAGNOSIS'}:
        return state
    outcome, reason = _target_matches(target, observation)
    if outcome != 'READY':
        if outcome == 'WAITING_USER':
            instructions = _mobile_instructions(target)
            _wait(state, 'same_device_guest', 'prerequisites', instructions)
        else:
            state['status'] = outcome
            state['error'] = reason
        _save(root, state)
        return state
    if 'environment' not in state['completed_steps']:
        _complete(state, 'environment')
    if 'prerequisites' not in state['completed_steps']:
        try:
            if target['os'] == 'android' and observation.get('runtime_kind') == 'linux_userland':
                if state.get('android_prerequisite_pending'):
                    _wait(state, 'android_guest_outcome_unknown', 'prerequisites', {
                        'instruction': 'The prior Termux guest preparation may have completed before its response was recorded. Inspect the same device Termux state, enter the guest, and resume there. It will not run again automatically.',
                        'recovery': target['recovery'],
                    })
                    _save(root, state)
                    return state
                if state.get('android_prerequisite_completed'):
                    _wait(state, 'enter_android_guest', 'prerequisites', _android_prerequisite_plan(target))
                    _save(root, state)
                    return state
                plan = _android_prerequisite_plan(target)
                if not approve_prerequisites:
                    _wait(state, 'android_prerequisite_consent', 'prerequisites', {
                        **plan,
                        'consent': 'Re-run with --approve-prerequisites to execute these exact argv commands on this Android device.',
                    })
                    _save(root, state)
                    return state
                if not _step_attempt_allowed(state, 'prerequisites'):
                    _save(root, state)
                    return state
                state['attempts']['total'] += 1
                state['attempts']['by_step']['prerequisites'] = state['attempts']['by_step'].get('prerequisites', 0) + 1
                state['status'] = 'RUNNING'
                state['current_step'] = 'prerequisites'
                state['waiting'] = None
                state['android_prerequisite_pending'] = True
                _save(root, state)
                try:
                    outputs = [_run(argv, root, runner=runner) for argv in plan['commands']]
                except EasyInstallError:
                    state['android_prerequisite_pending'] = False
                    raise
                state['android_prerequisite_pending'] = False
                state['android_prerequisite_completed'] = True
                state['android_prerequisite_evidence'] = {
                    'kind': 'direct_subprocess',
                    'argv': plan['commands'],
                    'stdout_sha256': [hashlib.sha256(value.encode('utf-8')).hexdigest() for value in outputs],
                }
                _wait(state, 'enter_android_guest', 'prerequisites', plan)
                _save(root, state)
                return state
            if target['agent'] == 'prime-agent' and target['os'] in {'android', 'ios'}:
                libc = observation.get('libc') if isinstance(observation.get('libc'), dict) else {}
                if libc.get('family') != 'glibc':
                    state['status'] = 'UNSUPPORTED' if libc.get('family') else 'NEEDS_DIAGNOSIS'
                    state['error'] = 'Prime mobile guest requires an observed GNU/glibc runtime'
                    _save(root, state)
                    return state
                compatible = _version_at_least(libc.get('version'), '2.35')
                if compatible is not True:
                    state['status'] = 'UNSUPPORTED' if compatible is False else 'NEEDS_DIAGNOSIS'
                    state['error'] = 'Prime mobile guest requires observed glibc >= 2.35'
                    _save(root, state)
                    return state
            if shutil.disk_usage(root).free < 256 * 1024 * 1024:
                _fail(state, 'prerequisites', 'at least 256 MiB free state-directory space is required', 'insufficient_disk')
                _save(root, state)
                return state
        except OSError as exc:
            _fail(state, 'prerequisites', exc, 'prerequisite_probe')
            _save(root, state)
            return state
        _complete(state, 'prerequisites')
    if 'agent_installation' not in state['completed_steps']:
        if not _step_attempt_allowed(state, 'agent_installation'):
            _save(root, state)
            return state
        try:
            executable = _resolve_executable(target['command'], agent_executable or state.get('agent_executable'))
            if not executable:
                if state.get('installer_execution_pending'):
                    _wait(state, 'installer_outcome_unknown', 'agent_installation', {
                        'safety': 'The prior installer process may have completed before its response was recorded. It will not be run again automatically.',
                        'after_completion': 'resume with --agent-executable ABSOLUTE_PATH after locating the installed binary',
                        'recovery': target['recovery'],
                    })
                    _save(root, state)
                    return state
                if not approve_install:
                    spec = _installer_spec(target)
                    _wait(state, 'installer_consent', 'agent_installation', {
                        'official_command_equivalent': target['manual_install'],
                        'download_url': spec['url'],
                        'execution_argv': [*spec['argv_prefix'], '<state-dir>/downloads/' + spec['filename']],
                        'scope': 'The official installer may write the vendor default user installation and PATH locations. Agent Welcome itself writes its download record and launcher only beneath state-dir.',
                        'consent': 'Re-run with --approve-install to download and execute this official installer without a shell pipeline.',
                        'recovery': target['recovery'],
                    })
                    _save(root, state)
                    return state
                if not _step_attempt_allowed(state, 'agent_installation'):
                    _save(root, state)
                    return state
                state['attempts']['total'] += 1
                state['attempts']['by_step']['agent_installation'] = state['attempts']['by_step'].get('agent_installation', 0) + 1
                state['status'] = 'RUNNING'
                state['current_step'] = 'agent_installation'
                state['waiting'] = None
                state['installer_execution_pending'] = True
                state['installer_attempted'] = True
                _save(root, state)
                try:
                    installer = _download_official_installer(root, target, opener=opener)
                    output = _execute_installer(installer, root, runner=runner)
                except EasyInstallError:
                    # Download and ordinary subprocess failures are known
                    # outcomes; an interrupted process intentionally leaves
                    # the pending marker for conservative reconciliation.
                    state['installer_execution_pending'] = False
                    raise
                state['installer_execution_pending'] = False
                state['installer_evidence'] = {
                    'kind': 'direct_subprocess', 'url': installer['url'],
                    'bytes': installer['bytes'], 'sha256': installer['sha256'],
                    'argv': [*installer['argv_prefix'], installer['path']],
                    'stdout_sha256': hashlib.sha256(output.encode('utf-8')).hexdigest(),
                }
                executable = _resolve_executable(target['command'], None)
                if not executable:
                    _wait(state, 'locate_installed_agent', 'agent_installation', {
                        'instruction': 'The official installer exited, but the executable is not on this process PATH. Resume with --agent-executable ABSOLUTE_PATH.',
                        'recovery': target['recovery'],
                    })
                    _save(root, state)
                    return state
            if not state['attempts']['by_step'].get('agent_installation'):
                state['attempts']['total'] += 1
                state['attempts']['by_step']['agent_installation'] = 1
            version = _run([executable, '--version'], root, runner=runner)
            if not version or len(version) > 200:
                raise EasyInstallError('agent --version output is empty or implausibly long')
            state['agent_executable'] = executable
            state['installation_evidence'] = {
                'kind': 'direct_subprocess', 'argv': [executable, '--version'],
                'version_sha256': hashlib.sha256(version.encode('utf-8')).hexdigest(),
            }
            state['evidence']['upstream_binary'] = True
            _complete(state, 'agent_installation')
        except EasyInstallError as exc:
            _fail(
                state, 'agent_installation', exc,
                'installer_execution' if state.get('installer_attempted') else 'version_probe',
            )
            _save(root, state)
            return state
    if 'path_config' not in state['completed_steps']:
        try:
            state['launcher_path'] = _write_launcher(root, target, state['agent_executable'])
            _complete(state, 'path_config')
        except (EasyInstallError, OSError) as exc:
            _fail(state, 'path_config', exc, 'state_local_launcher')
            _save(root, state)
            return state
    if 'provider_authentication' not in state['completed_steps']:
        if not auth_evidence:
            _wait(state, 'provider_authentication', 'provider_authentication', {
                'instruction': target['login_instruction'],
                'safety': 'Do not put passwords, tokens, cookies, MFA codes, or authorization codes in the state directory or evidence file.',
                'evidence_template': {'target_id': target['id'], 'event': 'provider_authentication', 'status': 'completed', 'method': 'browser_login'},
            })
            _save(root, state)
            return state
        try:
            state['authentication_evidence'] = _attestation(auth_evidence, target['id'], 'provider_authentication')
            state['evidence']['authentication'] = 'user_attestation'
            _complete(state, 'provider_authentication')
        except EasyInstallError as exc:
            _fail(state, 'provider_authentication', exc, 'invalid_attestation')
            _save(root, state)
            return state
    if 'minimal_first_task' not in state['completed_steps']:
        if first_task_command:
            if not allow_billable_first_task:
                _wait(state, 'billable_first_task_consent', 'minimal_first_task', {
                    'instruction': target['first_task_instruction'],
                    'safety': 'A direct first task can use provider credentials or incur cost. Re-run with --allow-billable-first-task only after explicit approval.',
                })
                _save(root, state)
                return state
            try:
                argv = json.loads(first_task_command)
                if not isinstance(argv, list) or not argv or Path(argv[0]).resolve() != Path(state['agent_executable']).resolve():
                    raise EasyInstallError('first task command must be a JSON argv list beginning with the verified agent executable')
                if not _step_attempt_allowed(state, 'minimal_first_task'):
                    _save(root, state)
                    return state
                state['attempts']['total'] += 1
                state['attempts']['by_step']['minimal_first_task'] = state['attempts']['by_step'].get('minimal_first_task', 0) + 1
                output = _run(argv, root, runner=runner)
                state['first_task_evidence'] = {'kind': 'direct_subprocess', 'stdout_sha256': hashlib.sha256(output.encode('utf-8')).hexdigest()}
                state['evidence']['actual_os'] = 'direct_process_observation'
                state['evidence']['first_task'] = 'direct_subprocess'
                _complete(state, 'minimal_first_task')
                state['status'] = 'SUCCEEDED'
                state['waiting'] = None
            except (EasyInstallError, json.JSONDecodeError) as exc:
                _fail(state, 'minimal_first_task', exc, 'first_task_probe')
                _save(root, state)
                return state
        elif first_task_evidence:
            try:
                state['first_task_evidence'] = _attestation(first_task_evidence, target['id'], 'minimal_first_task')
                state['evidence']['first_task'] = 'user_attestation'
                _complete(state, 'minimal_first_task')
                state['status'] = 'USER_ATTESTED'
                state['waiting'] = None
            except EasyInstallError as exc:
                _fail(state, 'minimal_first_task', exc, 'invalid_attestation')
                _save(root, state)
                return state
        else:
            _wait(state, 'minimal_first_task', 'minimal_first_task', {
                'instruction': target['first_task_instruction'],
                'direct_command_option': '--first-task-command JSON_ARGV --allow-billable-first-task',
                'evidence_template': {'target_id': target['id'], 'event': 'minimal_first_task', 'status': 'completed', 'method': 'interactive_read_only_task'},
            })
    _save(root, state)
    return state


def _mobile_instructions(target):
    if target['os'] == 'android':
        return {
            'same_device_only': True,
            'instruction': 'On this Android device install Termux, then run pkg install proot-distro; proot-distro install ubuntu:24.04; proot-distro login ubuntu. Run this launcher inside that guest.',
            'completion_probe': 'TERMUX_VERSION plus a PRoot/Linux-userland observation',
            'source_refs': target['source_refs'],
        }
    return {
        'same_device_only': True,
        'instruction': 'On this iOS device install/open UTM, import and boot a Linux guest, then run this launcher in the guest with AGENT_WELCOME_IOS_GUEST=1.',
        'completion_probe': 'Linux guest plus AGENT_WELCOME_IOS_GUEST=1 marker',
        'source_refs': target['source_refs'],
    }


def easy_start(target_id, state_dir, observation, **kwargs):
    target = get_target(target_id)
    if not isinstance(observation, dict):
        raise EasyInstallError('environment observation must be an object')
    with _locked_state_dir(state_dir) as root:
        if _state_path(root).exists():
            state = _read_state(root)
            if state.get('target_id') != target_id:
                raise EasyInstallError('state directory already belongs to another easy install target')
        else:
            state = _new_state(target, observation)
            _save(root, state)
        return _continue(target, root, observation, state, **kwargs)


def easy_resume(state_dir, observation, **kwargs):
    with _locked_state_dir(state_dir) as root:
        state = _read_state(root)
        target = get_target(state['target_id'])
        return _continue(target, root, observation, state, **kwargs)
