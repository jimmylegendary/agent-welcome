import hashlib
import io
import json
import os
import subprocess
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agent_welcome import artifacts as artifacts_module
from agent_welcome.artifacts import (
    InstallError,
    cleanup_staging,
    download_artifact,
    verify_extract_and_probe,
)


VERSION_SCRIPT = b'#!/bin/sh\nprintf "0.10.0\\n"\n'


def archive_bytes(entries):
    stream = io.BytesIO()
    with tarfile.open(fileobj=stream, mode='w:gz') as tar:
        for name, kind, data in entries:
            info = tarfile.TarInfo(name)
            if kind == 'file':
                info.size = len(data)
                info.mode = 0o755
                tar.addfile(info, io.BytesIO(data))
            elif kind == 'symlink':
                info.type = tarfile.SYMTYPE
                info.linkname = data.decode()
                tar.addfile(info)
            elif kind == 'hardlink':
                info.type = tarfile.LNKTYPE
                info.linkname = data.decode()
                tar.addfile(info)
            elif kind == 'directory':
                info.type = tarfile.DIRTYPE
                tar.addfile(info)
    return stream.getvalue()


def artifact_for(blob):
    return {
        'id': 'fixture-prime',
        'version': '0.10.0',
        'published_sha256': hashlib.sha256(blob).hexdigest(),
        'payload_path': 'prime-agent',
        'max_archive_bytes': 1024 * 1024,
        'max_expanded_bytes': 1024 * 1024,
        'max_members': 20,
        'probe_timeout_seconds': 3,
    }


class ArtifactTests(unittest.TestCase):
    def test_download_rejects_path_escape_and_unpinned_url_before_touching_sentinel(self):
        blob = archive_bytes([('prime-agent', 'file', VERSION_SCRIPT)])
        cases = [
            ('../../outside.bin', artifacts_module.PINNED_ARTIFACT_URL, 'outside.bin'),
            (
                artifacts_module.PINNED_ARTIFACT_NAME,
                'https://attacker.invalid/payload.tar.gz',
                f'downloads/{artifacts_module.PINNED_ARTIFACT_NAME}',
            ),
        ]
        for name, url, sentinel_relative in cases:
            with self.subTest(name=name, url=url), tempfile.TemporaryDirectory() as temp:
                state_dir = Path(temp) / 'state'
                sentinel = state_dir / sentinel_relative
                sentinel.parent.mkdir(parents=True, exist_ok=True)
                sentinel.write_bytes(b'keep this user file')
                artifact = artifact_for(blob)
                artifact['name'] = name
                artifact['url'] = url
                with patch(
                    'agent_welcome.artifacts.urllib.request.urlopen',
                    side_effect=AssertionError('network must not be reached'),
                ) as request:
                    with self.assertRaises(InstallError):
                        download_artifact(artifact, state_dir)
                request.assert_not_called()
                self.assertEqual(sentinel.read_bytes(), b'keep this user file')

    def test_source_replacement_after_digest_cannot_change_installed_snapshot(self):
        original_payload = VERSION_SCRIPT
        replaced_payload = b'#!/bin/sh\nprintf "0.10.0\\n"\n# replaced after digest\n'
        original_blob = archive_bytes([('prime-agent', 'file', original_payload)])
        replaced_blob = archive_bytes([('prime-agent', 'file', replaced_payload)])
        artifact = artifact_for(original_blob)
        with tempfile.TemporaryDirectory() as temp:
            archive = Path(temp) / 'source.tar.gz'
            archive.write_bytes(original_blob)
            real_validate = artifacts_module._validate_archive

            def replace_external_path_before_archive_read(path, selected_artifact):
                archive.write_bytes(replaced_blob)
                return real_validate(path, selected_artifact)

            with patch.object(
                artifacts_module,
                '_validate_archive',
                side_effect=replace_external_path_before_archive_read,
            ):
                result = verify_extract_and_probe(
                    artifact, archive, Path(temp) / 'install', allowed_root=temp,
                )
            installed_payload = Path(temp) / 'install' / 'prime-agent'
            self.assertEqual(result['status'], 'pass')
            self.assertEqual(result['observed_sha256'], hashlib.sha256(original_blob).hexdigest())
            self.assertEqual(installed_payload.read_bytes(), original_payload)
            self.assertEqual(archive.read_bytes(), replaced_blob)

    def test_staging_cleanup_only_removes_exact_registered_run_owned_stage(self):
        run_id = 'a' * 24
        with tempfile.TemporaryDirectory() as temp:
            parent = Path(temp) / 'install'
            parent.mkdir()
            stage = parent / f'.prime-stage-{run_id}-1'
            stage.mkdir()
            (stage / '.agent-welcome-stage-owner.json').write_text(
                json.dumps({'run_id': run_id, 'attempt': 1})
            )
            user_backup = parent / '.prime-stage-user-backup'
            user_backup.mkdir()
            (user_backup / 'keep.txt').write_text('preserve')
            cleanup_staging(parent, run_id=run_id, attempts=[1], allowed_root=temp)
            self.assertFalse(stage.exists())
            self.assertEqual((user_backup / 'keep.txt').read_text(), 'preserve')

    @unittest.skipIf(os.name == 'nt', 'symlink creation may require elevated Windows privileges')
    def test_staging_cleanup_never_follows_symlinked_parent_outside_state_root(self):
        run_id = 'b' * 24
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / 'state'
            root.mkdir()
            outside = Path(temp) / 'outside-install'
            outside.mkdir()
            stage = outside / f'.prime-stage-{run_id}-1'
            stage.mkdir()
            (stage / '.agent-welcome-stage-owner.json').write_text(
                json.dumps({'run_id': run_id, 'attempt': 1})
            )
            (stage / 'keep.txt').write_text('preserve')
            (root / 'install').symlink_to(outside, target_is_directory=True)
            cleanup_staging(
                root / 'install', run_id=run_id, attempts=[1], allowed_root=root,
            )
            self.assertEqual((stage / 'keep.txt').read_text(), 'preserve')

    def test_download_is_bounded_and_replaces_a_bad_state_local_cache(self):
        blob = archive_bytes([('prime-agent', 'file', VERSION_SCRIPT)])
        artifact = artifact_for(blob)
        artifact['name'] = artifacts_module.PINNED_ARTIFACT_NAME
        artifact['url'] = artifacts_module.PINNED_ARTIFACT_URL
        artifact['size_bytes'] = len(blob)
        with tempfile.TemporaryDirectory() as temp:
            cached = Path(temp) / 'downloads' / artifact['name']
            cached.parent.mkdir()
            cached.write_bytes(b'corrupt cache')
            with patch(
                'agent_welcome.artifacts.urllib.request.urlopen',
                return_value=io.BytesIO(blob),
            ):
                downloaded = download_artifact(artifact, temp)
            self.assertEqual(downloaded.read_bytes(), blob)
            self.assertEqual(downloaded.parent.parent, Path(temp).resolve())
            self.assertEqual(hashlib.sha256(downloaded.read_bytes()).hexdigest(),
                             artifact['published_sha256'])

        artifact['max_archive_bytes'] = 4
        with tempfile.TemporaryDirectory() as temp:
            with patch(
                'agent_welcome.artifacts.urllib.request.urlopen',
                return_value=io.BytesIO(blob),
            ):
                with self.assertRaises(InstallError):
                    download_artifact(artifact, temp)
            self.assertEqual(list((Path(temp) / 'downloads').iterdir()), [])

    @unittest.skipUnless(hasattr(os, 'mkfifo'), 'requires POSIX FIFO support')
    def test_cached_fifo_is_rejected_without_blocking(self):
        script = (
            'import os, sys\n'
            'from pathlib import Path\n'
            'from agent_welcome.artifacts import (InstallError, PINNED_ARTIFACT_NAME, '
            'PINNED_ARTIFACT_URL, download_artifact)\n'
            'root = Path(sys.argv[1])\n'
            'fifo = root / "downloads" / PINNED_ARTIFACT_NAME\n'
            'fifo.parent.mkdir(parents=True)\n'
            'os.mkfifo(fifo)\n'
            'artifact = {"name": PINNED_ARTIFACT_NAME, "url": PINNED_ARTIFACT_URL, '
            '"published_sha256": "0" * 64, "size_bytes": 1, "max_archive_bytes": 1}\n'
            'try:\n'
            '    download_artifact(artifact, root)\n'
            'except InstallError:\n'
            '    print("rejected")\n'
            'else:\n'
            '    raise SystemExit("FIFO cache was accepted")\n'
        )
        with tempfile.TemporaryDirectory() as temp:
            try:
                result = subprocess.run(
                    [sys.executable, '-c', script, temp],
                    capture_output=True, text=True, timeout=2,
                )
            except subprocess.TimeoutExpired:
                self.fail('cached FIFO open blocked instead of rejecting the non-regular cache')
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), 'rejected')

    def test_valid_fixture_extracts_and_requires_exact_version_output(self):
        blob = archive_bytes([('prime-agent', 'file', VERSION_SCRIPT)])
        with tempfile.TemporaryDirectory() as temp:
            archive = Path(temp) / 'fixture.tar.gz'
            archive.write_bytes(blob)
            result = verify_extract_and_probe(
                artifact_for(blob), archive, Path(temp) / 'owned-install'
            )
            self.assertEqual(result['status'], 'pass')
            self.assertEqual(result['version'], '0.10.0')
            self.assertEqual(result['observed_sha256'], hashlib.sha256(blob).hexdigest())
            self.assertTrue((Path(temp) / 'owned-install' / 'prime-agent').exists())

    def test_probe_ignores_inherited_pi_package_dir_override(self):
        payload = (
            b'#!/bin/sh\n'
            b'if [ -n "${PI_PACKAGE_DIR:-}" ]; then echo 9.9.9; '
            b'else echo 0.10.0; fi\n'
        )
        blob = archive_bytes([('prime-agent', 'file', payload)])
        with tempfile.TemporaryDirectory() as temp:
            archive = Path(temp) / 'fixture.tar.gz'
            archive.write_bytes(blob)
            with patch.dict(os.environ, {'PI_PACKAGE_DIR': '/outside/untrusted-version'}):
                result = verify_extract_and_probe(
                    artifact_for(blob), archive, Path(temp) / 'install', allowed_root=temp,
                )
            self.assertEqual(result['status'], 'pass')
            self.assertEqual(result['version'], '0.10.0')

    @unittest.skipUnless(hasattr(os, 'mkfifo') and os.name != 'nt', 'requires POSIX FIFO support')
    def test_fifo_artifact_is_rejected_without_blocking_and_snapshot_is_cleaned(self):
        script = (
            'import sys\n'
            'from pathlib import Path\n'
            'from agent_welcome.artifacts import InstallError, verify_extract_and_probe\n'
            'artifact = {"id":"fifo-fixture","version":"0.10.0",'
            '"published_sha256":"' + ('0' * 64) + '",'
            '"payload_path":"prime-agent","max_archive_bytes":1024,'
            '"max_expanded_bytes":1024,"max_members":4}\n'
            'try:\n'
            ' verify_extract_and_probe(artifact, Path(sys.argv[2]), '
            'Path(sys.argv[1]) / "install", allowed_root=sys.argv[1])\n'
            'except InstallError:\n'
            ' print("rejected")\n'
            'else:\n'
            ' raise SystemExit("FIFO was accepted")\n'
        )
        with tempfile.TemporaryDirectory() as temp:
            state_dir = Path(temp) / 'state'
            state_dir.mkdir()
            fifo = Path(temp) / 'artifact.fifo'
            os.mkfifo(fifo)
            try:
                result = subprocess.run(
                    [sys.executable, '-c', script, str(state_dir), str(fifo)],
                    capture_output=True, text=True, timeout=2,
                )
            except subprocess.TimeoutExpired:
                self.fail('FIFO open blocked instead of rejecting the non-regular source')
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), 'rejected')
            snapshots = state_dir / '.archive-snapshots'
            self.assertTrue(snapshots.is_dir())
            self.assertEqual(list(snapshots.iterdir()), [])

    def test_wrong_digest_does_not_extract_or_execute(self):
        with tempfile.TemporaryDirectory() as temp:
            marker_path = Path(temp) / 'probe-ran'
            marker = (
                '#!/bin/sh\nprintf "0.10.0\\n"\nprintf invoked > '
                + str(marker_path)
                + '\n'
            ).encode()
            blob = archive_bytes([('prime-agent', 'file', marker)])
            artifact = artifact_for(blob)
            artifact['published_sha256'] = '0' * 64
            archive = Path(temp) / 'fixture.tar.gz'
            archive.write_bytes(blob)
            destination = Path(temp) / 'install'
            with self.assertRaises(InstallError):
                verify_extract_and_probe(artifact, archive, destination)
            self.assertFalse(destination.exists())
            self.assertFalse(marker_path.exists())

    def test_rejects_traversal_absolute_links_duplicates_and_budget_overrun(self):
        malicious = [
            [('../escape', 'file', b'x')],
            [('/absolute', 'file', b'x')],
            [('prime-agent', 'file', VERSION_SCRIPT),
             ('prime-agent', 'file', VERSION_SCRIPT)],
            [('link', 'symlink', b'/tmp/outside')],
            [('hard', 'hardlink', b'prime-agent')],
        ]
        for entries in malicious:
            with self.subTest(entries=entries):
                blob = archive_bytes(entries)
                with tempfile.TemporaryDirectory() as temp:
                    archive = Path(temp) / 'bad.tar.gz'
                    archive.write_bytes(blob)
                    with self.assertRaises(InstallError):
                        verify_extract_and_probe(
                            artifact_for(blob), archive, Path(temp) / 'install'
                        )
                    self.assertFalse((Path(temp) / 'escape').exists())
        blob = archive_bytes([('prime-agent', 'file', VERSION_SCRIPT)])
        artifact = artifact_for(blob)
        artifact['max_expanded_bytes'] = 2
        with tempfile.TemporaryDirectory() as temp:
            archive = Path(temp) / 'large.tar.gz'
            archive.write_bytes(blob)
            with self.assertRaises(InstallError):
                verify_extract_and_probe(artifact, archive, Path(temp) / 'install')
        artifact = artifact_for(blob)
        artifact['max_members'] = 1
        too_many = archive_bytes([
            ('prime-agent', 'file', VERSION_SCRIPT),
            ('extra', 'file', b'x'),
        ])
        with tempfile.TemporaryDirectory() as temp:
            archive = Path(temp) / 'many.tar.gz'
            archive.write_bytes(too_many)
            with self.assertRaises(InstallError):
                verify_extract_and_probe(artifact, archive, Path(temp) / 'install')

    def test_version_mismatch_is_not_install_success(self):
        blob = archive_bytes([('prime-agent', 'file', b'#!/bin/sh\necho 0.9.9\n')])
        with tempfile.TemporaryDirectory() as temp:
            archive = Path(temp) / 'fixture.tar.gz'
            archive.write_bytes(blob)
            with self.assertRaises(InstallError):
                verify_extract_and_probe(artifact_for(blob), archive, Path(temp) / 'install')


if __name__ == '__main__':
    unittest.main()
