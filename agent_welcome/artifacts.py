"""Pinned artifact download, digest validation, safe extraction, and version probe."""

import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import tarfile
import tempfile
import urllib.request
from pathlib import Path, PurePosixPath


class InstallError(RuntimeError):
    def __init__(self, message, evidence=None):
        super().__init__(message)
        self.evidence = evidence or {}


MANIFEST_NAME = '.agent-welcome-manifest.json'
STAGE_OWNER_NAME = '.agent-welcome-stage-owner.json'
PINNED_ARTIFACT_NAME = 'prime-agent-0.10.0-linux-arm64.tar.gz'
PINNED_ARTIFACT_URL = (
    'https://github.com/PrimeIntellect-ai/prime-agent/releases/download/v0.10.0/'
    'prime-agent-0.10.0-linux-arm64.tar.gz'
)


def _state_relative_path(path, root, label):
    """Return a canonical relative path while rejecting lexical link escapes.

    Windows can expose the same directory through a DOS 8.3 alias (for example
    ``C:\\Users\\NAME~1``) and its long form.  A plain ``Path.relative_to`` on
    those two spellings rejects an in-tree path.  Compare resolved canonical
    paths, but separately walk the caller's lexical components and reject any
    symbolic-link/reparse-point component before a write or deletion is allowed.
    """
    candidate = Path(os.path.abspath(path))
    canonical_root = Path(root).resolve()
    try:
        canonical_candidate = candidate.resolve()
        relative = canonical_candidate.relative_to(canonical_root)
    except (OSError, ValueError) as exc:
        raise InstallError(f'{label} is outside the explicit state directory') from exc
    cursor = candidate
    while True:
        if cursor.is_symlink():
            raise InstallError(f'{label} contains a symbolic link inside the state directory')
        try:
            if cursor.resolve() == canonical_root:
                break
        except OSError as exc:
            raise InstallError(f'cannot inspect {label} safely: {exc}') from exc
        parent = cursor.parent
        if parent == cursor:
            raise InstallError(f'{label} is outside the explicit state directory')
        cursor = parent
    return relative


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def _sha256_regular_file_nonblocking(path):
    """Hash an existing cache entry without opening a FIFO or device."""
    descriptor = None
    try:
        flags = (
            os.O_RDONLY
            | getattr(os, 'O_NOFOLLOW', 0)
            | getattr(os, 'O_NONBLOCK', 0)
        )
        descriptor = os.open(os.fspath(path), flags)
        file_stat = os.fstat(descriptor)
        if not stat.S_ISREG(file_stat.st_mode):
            raise InstallError('cached artifact path must be a regular file')
        digest = hashlib.sha256()
        with os.fdopen(descriptor, 'rb') as stream:
            descriptor = None
            for chunk in iter(lambda: stream.read(1024 * 1024), b''):
                digest.update(chunk)
        return digest.hexdigest(), file_stat
    except InstallError:
        raise
    except OSError as exc:
        raise InstallError(f'cannot read cached artifact safely: {exc}') from exc
    finally:
        if descriptor is not None:
            os.close(descriptor)


def download_artifact(artifact, state_dir, timeout=30):
    """Fetch only the recipe-pinned HTTPS URL into the explicit state directory."""
    if (
        artifact.get('name') != PINNED_ARTIFACT_NAME
        or artifact.get('url') != PINNED_ARTIFACT_URL
    ):
        raise InstallError('download name/URL is not the pinned Prime v0.10.0 artifact')
    root = Path(state_dir).resolve()
    target_dir = root / 'downloads'
    if target_dir.is_symlink():
        raise InstallError('state-local downloads directory must not be a symbolic link')
    _state_relative_path(target_dir, root, 'downloads directory')
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / artifact['name']
    if target.is_symlink():
        raise InstallError('cached artifact path must not be a symbolic link')
    _state_relative_path(target, root, 'final artifact path')
    if target.exists():
        observed, cache_stat = _sha256_regular_file_nonblocking(target)
        if observed == artifact['published_sha256']:
            return target
        try:
            current_stat = os.stat(target, follow_symlinks=False)
        except OSError as exc:
            raise InstallError(f'cached artifact changed before replacement: {exc}') from exc
        if (
            not stat.S_ISREG(current_stat.st_mode)
            or (current_stat.st_dev, current_stat.st_ino)
            != (cache_stat.st_dev, cache_stat.st_ino)
        ):
            raise InstallError('cached artifact changed before replacement')
        target.unlink()
    limit = int(artifact.get('max_archive_bytes', artifact['size_bytes']))
    fd, temp_name = tempfile.mkstemp(prefix='.download-', dir=target_dir)
    temp = Path(temp_name)
    digest = hashlib.sha256()
    count = 0
    fd_open = True
    try:
        request = urllib.request.Request(
            artifact['url'],
            headers={'User-Agent': 'agent-welcome-reference/0.1'},
        )
        with os.fdopen(fd, 'wb') as output:
            fd_open = False
            with urllib.request.urlopen(request, timeout=timeout) as response:
                while True:
                    chunk = response.read(64 * 1024)
                    if not chunk:
                        break
                    count += len(chunk)
                    if count > limit:
                        raise InstallError('download exceeds configured byte limit')
                    digest.update(chunk)
                    output.write(chunk)
                output.flush()
                os.fsync(output.fileno())
        if count != artifact['size_bytes']:
            raise InstallError('download byte count does not match published size')
        observed = digest.hexdigest()
        if observed != artifact['published_sha256']:
            raise InstallError(
                'download SHA-256 does not match published digest',
                evidence={
                    'stage': 'published_digest_comparison',
                    'candidate_sha256': observed,
                    'verified': False,
                },
            )
        os.replace(temp, target)
        return target
    except BaseException:
        if fd_open:
            os.close(fd)
        try:
            temp.unlink()
        except FileNotFoundError:
            pass
        raise


def _member_path(member):
    raw = member.name
    if not isinstance(raw, str) or not raw or '\\' in raw or raw.startswith('/'):
        raise InstallError(f'unsafe archive path: {raw!r}')
    if any(':' in part for part in raw.split('/')):
        raise InstallError(f'absolute archive path is forbidden: {raw!r}')
    parts = raw.split('/')
    if member.isdir() and parts and parts[-1] == '':
        parts.pop()
    if not parts or any(
        part in {'', '.', '..'} or part.endswith((' ', '.'))
        or part.split('.')[0].upper() in {
            'CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4',
            'COM5', 'COM6', 'COM7', 'COM8', 'COM9', 'LPT1', 'LPT2',
            'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9',
        }
        for part in parts
    ):
        raise InstallError(f'unsafe archive path: {raw!r}')
    return PurePosixPath(*parts)


def _validate_archive(archive_path, artifact):
    max_archive = int(artifact.get('max_archive_bytes', 64 * 1024 * 1024))
    max_expanded = int(artifact.get('max_expanded_bytes', 128 * 1024 * 1024))
    max_members = int(artifact.get('max_members', 2048))
    try:
        archive_size = Path(archive_path).stat().st_size
    except OSError as exc:
        raise InstallError(f'cannot stat archive: {exc}') from exc
    if archive_size > max_archive:
        raise InstallError('archive exceeds configured byte limit')
    members = []
    seen = {}
    total = 0
    try:
        with tarfile.open(archive_path, mode='r:gz') as stream:
            while True:
                member = stream.next()
                if member is None:
                    break
                if len(members) >= max_members:
                    raise InstallError('archive exceeds configured member limit')
                path = _member_path(member)
                key = path.as_posix()
                if key == MANIFEST_NAME:
                    raise InstallError('archive uses a reserved installation manifest path')
                if key in seen:
                    raise InstallError(f'duplicate archive path: {key}')
                if not (member.isdir() or member.isfile()):
                    raise InstallError(f'archive member type is forbidden: {key}')
                for parent in path.parents:
                    parent_key = parent.as_posix()
                    if parent_key == '.':
                        continue
                    if seen.get(parent_key) == 'file':
                        raise InstallError(f'archive file/directory conflict: {parent_key}')
                if member.isfile():
                    if member.size < 0:
                        raise InstallError(f'negative archive member size: {key}')
                    total += member.size
                    if total > max_expanded:
                        raise InstallError('archive exceeds expanded byte limit')
                    if any(existing.startswith(key + '/') for existing in seen):
                        raise InstallError(f'archive file/directory conflict: {key}')
                    seen[key] = 'file'
                else:
                    seen[key] = 'directory'
                members.append((member, path))
    except InstallError:
        raise
    except (tarfile.TarError, OSError, EOFError) as exc:
        raise InstallError(f'invalid tar archive: {exc}') from exc
    if not members:
        raise InstallError('archive is empty')
    return members


def cleanup_staging(parent_dir, *, run_id, attempts, allowed_root):
    """Remove only exact, state-local stage paths owned by this run and attempt."""
    if not isinstance(run_id, str) or not re.fullmatch(r'[0-9a-f]{24}', run_id):
        return
    root = Path(allowed_root).resolve()
    parent = Path(os.path.abspath(parent_dir))
    try:
        relative_parent = _state_relative_path(parent, root, 'staging parent')
    except InstallError:
        return
    cursor = root
    for part in relative_parent.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            return
    if not parent.exists() or not parent.is_dir():
        return
    for attempt in attempts:
        if type(attempt) is not int or attempt < 1:
            continue
        child = parent / f'.prime-stage-{run_id}-{attempt}'
        try:
            if child.parent != parent or child.is_symlink() or not child.is_dir():
                continue
            owner_path = child / STAGE_OWNER_NAME
            if owner_path.is_symlink() or not owner_path.is_file():
                continue
            owner = json.loads(owner_path.read_text(encoding='utf-8'))
            if owner != {'run_id': run_id, 'attempt': attempt}:
                continue
            shutil.rmtree(child)
        except FileNotFoundError:
            continue
        except (OSError, json.JSONDecodeError):
            continue


def _read_manifest(destination):
    path = Path(destination) / MANIFEST_NAME
    if path.is_symlink():
        return None
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError):
        return None


def _inventory(root):
    files = {}
    directories = []
    for current, dirnames, filenames in os.walk(root, topdown=True, followlinks=False):
        current_path = Path(current)
        for name in list(dirnames):
            path = current_path / name
            if path.is_symlink():
                raise InstallError(f'installed directory was replaced by a link: {path.name}')
            directories.append(path.relative_to(root).as_posix())
        for name in filenames:
            path = current_path / name
            if path.name == MANIFEST_NAME and path.parent == Path(root):
                continue
            if path.is_symlink() or not path.is_file():
                raise InstallError(f'installed file is not a regular file: {path.name}')
            files[path.relative_to(root).as_posix()] = {
                'sha256': sha256_file(path),
                'mode': path.stat().st_mode & 0o777,
            }
    return {'files': dict(sorted(files.items())), 'directories': sorted(directories)}


def inspect_installation(artifact, destination, recipe_sha256, observed_sha256):
    """Check an already-owned installation without running the payload."""
    destination = Path(destination)
    if destination.is_symlink() or not destination.is_dir():
        return {'owned': False, 'valid': False, 'reason': 'install directory is missing or redirected'}
    manifest = _read_manifest(destination)
    if not manifest:
        return {'owned': False, 'valid': False, 'reason': 'owned manifest is missing or invalid'}
    owned = (
        manifest.get('artifact_id') == artifact['id']
        and manifest.get('version') == artifact['version']
        and manifest.get('published_sha256') == artifact['published_sha256']
        and manifest.get('observed_sha256') == observed_sha256
        and manifest.get('recipe_sha256') == recipe_sha256
        and manifest.get('payload_path') == artifact['payload_path']
        and manifest.get('success_scope') == 'binary_installation'
    )
    if not owned:
        return {'owned': False, 'valid': False, 'reason': 'manifest belongs to a different recipe'}
    payload = destination / artifact['payload_path']
    if payload.is_symlink() or not payload.is_file():
        return {'owned': True, 'valid': False, 'reason': 'installed payload is missing or redirected'}
    try:
        payload_digest = sha256_file(payload)
    except OSError:
        return {'owned': True, 'valid': False, 'reason': 'installed payload cannot be read'}
    if payload_digest != manifest.get('payload_sha256'):
        return {'owned': True, 'valid': False, 'reason': 'installed payload digest changed'}
    if manifest.get('version_output') != artifact['version']:
        return {'owned': True, 'valid': False, 'reason': 'installed version evidence changed'}
    try:
        inventory = _inventory(destination)
    except (OSError, InstallError) as exc:
        return {'owned': True, 'valid': False, 'reason': str(exc)}
    if (
        inventory['files'] != manifest.get('files')
        or inventory['directories'] != manifest.get('directories')
    ):
        return {'owned': True, 'valid': False, 'reason': 'installed tree changed after verification'}
    return {'owned': True, 'valid': True, 'reason': None}


def remove_owned_installation(artifact, destination, recipe_sha256, observed_sha256):
    destination = Path(destination)
    result = inspect_installation(artifact, destination, recipe_sha256, observed_sha256)
    if not result['owned'] or result['valid']:
        raise InstallError('refusing to remove an unowned or valid installation')
    shutil.rmtree(destination)
    return result


def _reuse_existing(artifact, archive_digest, destination, recipe_sha256):
    manifest = _read_manifest(destination)
    if not manifest:
        raise InstallError('owned install path exists without a valid manifest')
    if (
        manifest.get('artifact_id') != artifact['id']
        or manifest.get('version') != artifact['version']
        or manifest.get('observed_sha256') != archive_digest
        or manifest.get('published_sha256') != artifact['published_sha256']
        or manifest.get('recipe_sha256') != recipe_sha256
        or manifest.get('payload_path') != artifact['payload_path']
        or manifest.get('version_output') != artifact['version']
        or manifest.get('success_scope') != 'binary_installation'
    ):
        raise InstallError('existing install manifest does not match this recipe and artifact')
    inspection = inspect_installation(
        artifact, destination, recipe_sha256, archive_digest,
    )
    if not inspection['valid']:
        raise InstallError(inspection['reason'])
    return {
        'status': 'pass',
        'version': artifact['version'],
        'observed_sha256': archive_digest,
        'payload_path': artifact['payload_path'],
        'reused': True,
    }


def _snapshot_archive(source_path, state_root, max_bytes):
    root = Path(state_root).resolve()
    snapshot_dir = root / '.archive-snapshots'
    if snapshot_dir.is_symlink():
        raise InstallError('state-local archive snapshot path must not be a symbolic link')
    snapshot_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    _state_relative_path(snapshot_dir, root, 'archive snapshot directory')
    out_fd, snapshot_name = tempfile.mkstemp(prefix='.archive-', suffix='.tmp', dir=snapshot_dir)
    snapshot = Path(snapshot_name)
    source_fd = None
    out_open = True
    source_open = False
    try:
        flags = (
            os.O_RDONLY
            | getattr(os, 'O_NOFOLLOW', 0)
            | getattr(os, 'O_NONBLOCK', 0)
        )
        source_fd = os.open(os.fspath(source_path), flags)
        source_open = True
        source_stat = os.fstat(source_fd)
        if not stat.S_ISREG(source_stat.st_mode):
            raise InstallError('artifact_file must be a regular file')
        if source_stat.st_size > max_bytes:
            raise InstallError('archive exceeds configured byte limit')
        digest = hashlib.sha256()
        count = 0
        with os.fdopen(source_fd, 'rb') as source, os.fdopen(out_fd, 'wb') as output:
            source_open = False
            out_open = False
            while True:
                chunk = source.read(64 * 1024)
                if not chunk:
                    break
                count += len(chunk)
                if count > max_bytes:
                    raise InstallError('archive exceeds configured byte limit')
                digest.update(chunk)
                output.write(chunk)
            final_stat = os.fstat(source.fileno())
            if (
                final_stat.st_size != source_stat.st_size
                or final_stat.st_mtime_ns != source_stat.st_mtime_ns
            ):
                raise InstallError('artifact_file changed while making a private snapshot')
            output.flush()
            os.fsync(output.fileno())
        return snapshot, digest.hexdigest(), count
    except BaseException:
        if source_open and source_fd is not None:
            os.close(source_fd)
        if out_open:
            os.close(out_fd)
        try:
            snapshot.unlink()
        except FileNotFoundError:
            pass
        raise


def verify_extract_and_probe(
    artifact, archive_path, destination_dir, recipe_sha256=None, allowed_root=None,
    run_id=None, attempt=None,
):
    """Install a verified archive into a private destination and check exact --version output."""
    archive_path = Path(archive_path)
    destination = Path(os.path.abspath(destination_dir))
    if destination.is_symlink():
        raise InstallError('install destination must not be a symbolic link')
    root = Path(allowed_root).resolve() if allowed_root is not None else destination.parent.resolve()
    relative_destination = _state_relative_path(destination, root, 'install destination')
    cursor = root
    for part in relative_destination.parts[:-1]:
        cursor = cursor / part
        if cursor.is_symlink():
            raise InstallError('install path contains a symbolic link inside the state directory')
    max_archive = int(artifact.get('max_archive_bytes', 64 * 1024 * 1024))
    snapshot, observed, _snapshot_size = _snapshot_archive(archive_path, root, max_archive)
    try:
        if observed != artifact['published_sha256']:
            raise InstallError(
                'artifact SHA-256 does not match published digest',
                evidence={
                    'stage': 'published_digest_comparison',
                    'candidate_sha256': observed,
                    'verified': False,
                },
            )
        if destination.exists():
            return _reuse_existing(artifact, observed, destination, recipe_sha256)
        members = _validate_archive(snapshot, artifact)
        destination.parent.mkdir(parents=True, exist_ok=True)
        if run_id is None and attempt is None:
            stage = Path(tempfile.mkdtemp(prefix='.prime-stage-', dir=destination.parent))
        elif (
            isinstance(run_id, str)
            and re.fullmatch(r'[0-9a-f]{24}', run_id)
            and type(attempt) is int
            and attempt > 0
        ):
            stage = destination.parent / f'.prime-stage-{run_id}-{attempt}'
            stage.mkdir(mode=0o700)
            (stage / STAGE_OWNER_NAME).write_text(
                json.dumps({'run_id': run_id, 'attempt': attempt}, sort_keys=True) + '\n',
                encoding='utf-8',
            )
        else:
            raise InstallError('staging ownership requires a valid run id and attempt')
        try:
            with tarfile.open(snapshot, mode='r:gz') as stream:
                for original, relative in members:
                    target = stage.joinpath(*relative.parts)
                    if original.isdir():
                        target.mkdir(parents=True, exist_ok=True)
                        continue
                    target.parent.mkdir(parents=True, exist_ok=True)
                    source = stream.extractfile(original)
                    if source is None:
                        raise InstallError(f'cannot read archive member: {relative.as_posix()}')
                    remaining = original.size
                    with source, target.open('xb') as output:
                        while remaining:
                            chunk = source.read(min(64 * 1024, remaining))
                            if not chunk:
                                raise InstallError(f'truncated archive member: {relative.as_posix()}')
                            output.write(chunk)
                            remaining -= len(chunk)
                        if source.read(1):
                            raise InstallError(f'archive member size mismatch: {relative.as_posix()}')
                    mode = original.mode & 0o777 & ~0o6000
                    os.chmod(target, mode)
            payload = stage.joinpath(*PurePosixPath(artifact['payload_path']).parts)
            if not payload.is_file():
                raise InstallError(f'archive does not contain payload {artifact["payload_path"]!r}')
            timeout = int(artifact.get('probe_timeout_seconds', 10))
            try:
                probe = subprocess.run(
                    [str(payload), '--version'],
                    cwd=stage,
                    env={
                        'PATH': os.defpath,
                        'HOME': str(stage),
                        'LANG': 'C',
                        'TMPDIR': str(stage),
                        'TMP': str(stage),
                        'TEMP': str(stage),
                    },
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    check=False,
                    shell=False,
                    close_fds=True,
                )
            except (OSError, subprocess.TimeoutExpired) as exc:
                raise InstallError(f'owned payload version probe failed: {exc}') from exc
            version_output = probe.stdout.strip()
            if probe.returncode != 0 or version_output != artifact['version']:
                raise InstallError(
                    f'owned payload version mismatch: exit={probe.returncode}, '
                    f'stdout={version_output!r}, expected={artifact["version"]!r}'
                )
            inventory = _inventory(stage)
            manifest = {
                'artifact_id': artifact['id'],
                'version': artifact['version'],
                'observed_sha256': observed,
                'published_sha256': artifact['published_sha256'],
                'recipe_sha256': recipe_sha256,
                'payload_path': artifact['payload_path'],
                'payload_sha256': sha256_file(payload),
                'version_output': version_output,
                'success_scope': 'binary_installation',
                'files': inventory['files'],
                'directories': inventory['directories'],
            }
            with (stage / MANIFEST_NAME).open('w', encoding='utf-8') as stream:
                json.dump(manifest, stream, sort_keys=True)
                stream.write('\n')
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(stage, destination)
            return {
                'status': 'pass',
                'version': version_output,
                'observed_sha256': observed,
                'payload_path': artifact['payload_path'],
                'reused': False,
            }
        except BaseException:
            shutil.rmtree(stage, ignore_errors=True)
            raise
    finally:
        try:
            snapshot.unlink()
        except FileNotFoundError:
            pass
