"""State-local, integrity-pinned preparation helpers for standalone launchers.

The PowerShell and POSIX launchers have to operate before this package can be
imported.  This module keeps their security contract executable in regression
tests: downloaders and process probes are supplied by callers, all staging is
under the explicit state directory, and a downloaded repository is never
allowed to replace an existing directory.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import stat
import tempfile
import zipfile
from pathlib import Path


class BootstrapError(RuntimeError):
    """A bootstrap input cannot safely produce a state-local checkout."""


def _sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_member_path(root, name):
    member = Path(name)
    if not name or '\\' in name or member.is_absolute() or '..' in member.parts:
        raise BootstrapError(f'unsafe archive member: {name!r}')
    candidate = (root / member).resolve(strict=False)
    try:
        candidate.relative_to(root.resolve(strict=False))
    except ValueError as exc:
        raise BootstrapError(f'archive member escapes extraction root: {name!r}') from exc
    return candidate


def _extract_zip(archive, destination, prefix):
    destination.mkdir(mode=0o700, parents=True, exist_ok=False)
    with zipfile.ZipFile(archive) as source:
        for info in source.infolist():
            if stat.S_ISLNK(info.external_attr >> 16):
                raise BootstrapError(f'archive symlink is not allowed: {info.filename!r}')
            if not (info.filename == prefix + '/' or info.filename.startswith(prefix + '/')):
                raise BootstrapError(f'archive member is outside expected revision root: {info.filename!r}')
            target = _safe_member_path(destination, info.filename)
            if info.is_dir():
                target.mkdir(mode=0o700, parents=True, exist_ok=True)
                continue
            target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            with source.open(info) as input_file, target.open('xb') as output_file:
                shutil.copyfileobj(input_file, output_file)


def _write_json_atomically(path, value):
    path = Path(path)
    encoded = json.dumps(value, sort_keys=True, separators=(',', ':')).encode('utf-8')
    descriptor, temporary = tempfile.mkstemp(prefix='.bootstrap-', suffix='.tmp', dir=path.parent)
    try:
        with os.fdopen(descriptor, 'wb') as output:
            output.write(encoded)
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, path)
    except BaseException:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def _marker_matches(path, manifest):
    try:
        saved = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError):
        return False
    return saved == {
        'revision': manifest['revision'],
        'archive_sha256': manifest['archive_sha256'].lower(),
    }


def prepare_repository(state_dir, manifest, downloader):
    """Download, verify, and atomically stage one pinned repository revision.

    ``downloader(url, destination)`` must only return after the destination is
    fully written.  It is deliberately injected so tests never make a network
    request and a caller can apply its own transport policy.
    """
    required = {'revision', 'archive_url', 'archive_sha256', 'archive_prefix'}
    missing = required.difference(manifest)
    if missing:
        raise BootstrapError(f'bootstrap manifest missing: {", ".join(sorted(missing))}')
    root = Path(state_dir).resolve()
    root.mkdir(mode=0o700, parents=True, exist_ok=True)
    repository = root / 'repository'
    marker = repository / '.agent-welcome-bootstrap.json'
    if repository.exists():
        if repository.is_symlink() or marker.is_symlink():
            raise BootstrapError('bootstrap repository path must not be symbolic link')
        if repository.is_dir() and _marker_matches(marker, manifest):
            return {'kind': 'reused', 'repository': str(repository), 'revision': manifest['revision']}
        raise BootstrapError('existing repository directory is not this pinned bootstrap; preserving it')
    stage = Path(tempfile.mkdtemp(prefix='.bootstrap-stage-', dir=root))
    try:
        archive = stage / 'repository.zip'
        downloader(manifest['archive_url'], archive)
        if not archive.is_file():
            raise BootstrapError('downloader did not create the repository archive')
        actual_hash = _sha256(archive)
        if actual_hash.lower() != manifest['archive_sha256'].lower():
            raise BootstrapError('repository archive SHA-256 did not match the pinned revision')
        extracted = stage / 'extracted'
        _extract_zip(archive, extracted, manifest['archive_prefix'])
        payload = extracted / manifest['archive_prefix']
        if not payload.is_dir() or payload.is_symlink():
            raise BootstrapError('pinned repository archive did not contain its expected root directory')
        _write_json_atomically(payload / '.agent-welcome-bootstrap.json', {
            'revision': manifest['revision'],
            'archive_sha256': manifest['archive_sha256'].lower(),
        })
        os.replace(payload, repository)
    finally:
        shutil.rmtree(stage, ignore_errors=True)
    return {'kind': 'prepared', 'repository': str(repository), 'revision': manifest['revision']}


def find_python_runtime(candidates, process_runner, minimum=(3, 11)):
    """Return the first injected noninteractive probe reporting Python >= minimum."""
    for executable, prefix in candidates:
        result = process_runner([executable, *prefix, '-c',
            'import sys; print(f"{sys.version_info[0]}.{sys.version_info[1]}.{sys.version_info[2]}|{sys.executable}")'])
        if not isinstance(result, dict) or result.get('returncode') != 0:
            continue
        try:
            version_text, path = result.get('stdout', '').strip().split('|', 1)
            version = tuple(int(part) for part in version_text.split('.'))
        except (AttributeError, ValueError):
            continue
        if version >= minimum and path:
            return {'executable': executable, 'prefix': list(prefix), 'version': version_text, 'resolved_path': path}
    return None
