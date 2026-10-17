import hashlib
import io
import os
import tarfile
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agent_welcome.artifacts import (
    InstallError,
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
    def test_download_is_bounded_and_replaces_a_bad_state_local_cache(self):
        blob = archive_bytes([('prime-agent', 'file', VERSION_SCRIPT)])
        artifact = artifact_for(blob)
        artifact['name'] = 'fixture.tar.gz'
        artifact['url'] = 'https://downloads.invalid/fixture.tar.gz'
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
