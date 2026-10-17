import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

from agent_welcome.bootstrap import BootstrapError, find_python_runtime, prepare_repository


REVISION = '7997bd35756ee5fbf6fb4759e9ab6dd17b917665'
PREFIX = f'agent-welcome-{REVISION}'
SCRIPT_REVISION = 'ceb6d3803b12d41d429dc3188e9a20ac8f220780'
SCRIPT_PREFIX = f'agent-welcome-{SCRIPT_REVISION}'


def fixture_archive(path, members):
    with zipfile.ZipFile(path, 'w') as archive:
        for name, content in members.items():
            archive.writestr(name, content)
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def fixture_agent_welcome_archive(path, prefix):
    """Build a minimal runnable checkout for standalone-process tests."""
    root = Path(__file__).parents[1]
    with zipfile.ZipFile(path, 'w') as archive:
        for source in (root / 'agent_welcome').rglob('*.py'):
            archive.write(source, f'{prefix}/{source.relative_to(root)}')
        source = root / 'catalog' / 'easy-install-targets.json'
        archive.write(source, f'{prefix}/{source.relative_to(root)}')
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_executable(path, body):
    path.write_text('#!/bin/sh\nset -eu\n' + body, encoding='utf-8')
    path.chmod(0o700)


def fixture_unix_bootstrap(path, repository_digest, macos_digest=None):
    source = Path(__file__).parents[1] / 'easy-bootstrap.sh'
    script = source.read_text(encoding='utf-8')
    script = script.replace(
        'archive_sha256=38d359aa0b05ae6bed5214a1b845e67477332c17cc291fc1727969aff648891d',
        f'archive_sha256={repository_digest}',
        1,
    )
    if macos_digest:
        script = script.replace(
            'macos_archive_sha256=e754d6cae3f2810dd1818c1395a7ff50ce79ade3ec4887f7ce23ad581cc12e3a',
            f'macos_archive_sha256={macos_digest}',
            1,
        )
    path.write_text(script, encoding='utf-8')
    path.chmod(0o700)
    return path


class BootstrapTests(unittest.TestCase):
    def _manifest(self, archive, digest):
        return {
            'revision': REVISION,
            'archive_url': 'https://fixture.invalid/repository.zip',
            'archive_sha256': digest,
            'archive_prefix': PREFIX,
        }

    def test_pinned_archive_is_verified_staged_and_idempotent(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            archive = root / 'fixture.zip'
            digest = fixture_archive(archive, {f'{PREFIX}/README.md': 'fixture'})
            calls = []

            def downloader(url, destination):
                calls.append(url)
                Path(destination).write_bytes(archive.read_bytes())

            first = prepare_repository(root / 'state', self._manifest(archive, digest), downloader)
            second = prepare_repository(root / 'state', self._manifest(archive, digest), downloader)
            self.assertEqual(first['kind'], 'prepared')
            self.assertEqual(second['kind'], 'reused')
            self.assertEqual(calls, ['https://fixture.invalid/repository.zip'])
            self.assertEqual((root / 'state' / 'repository' / 'README.md').read_text(), 'fixture')

    def test_bad_hash_network_failure_and_existing_directory_preserve_user_data(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            archive = root / 'fixture.zip'
            digest = fixture_archive(archive, {f'{PREFIX}/README.md': 'fixture'})
            manifest = self._manifest(archive, '0' * 64)
            with self.assertRaisesRegex(BootstrapError, 'SHA-256'):
                prepare_repository(root / 'bad-hash', manifest, lambda _url, path: Path(path).write_bytes(archive.read_bytes()))
            self.assertFalse((root / 'bad-hash' / 'repository').exists())
            with self.assertRaises(OSError):
                prepare_repository(root / 'network', self._manifest(archive, digest), lambda _url, _path: (_ for _ in ()).throw(OSError('offline')))
            self.assertFalse((root / 'network' / 'repository').exists())
            preserved = root / 'preserved' / 'repository'
            preserved.mkdir(parents=True)
            (preserved / 'user.txt').write_text('do not replace', encoding='utf-8')
            with self.assertRaisesRegex(BootstrapError, 'preserving'):
                prepare_repository(root / 'preserved', self._manifest(archive, digest), lambda _url, path: Path(path).write_bytes(archive.read_bytes()))
            self.assertEqual((preserved / 'user.txt').read_text(), 'do not replace')

    def test_zip_slip_and_unexpected_root_are_rejected_before_repository_creation(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for name in ('../outside.txt', 'other-root/file.txt'):
                with self.subTest(name=name):
                    archive = root / (hashlib.sha256(name.encode()).hexdigest() + '.zip')
                    digest = fixture_archive(archive, {name: 'malicious'})
                    state = root / (archive.stem + '-state')
                    with self.assertRaises(BootstrapError):
                        prepare_repository(state, self._manifest(archive, digest), lambda _url, path: Path(path).write_bytes(archive.read_bytes()))
                    self.assertFalse((state / 'repository').exists())

    @unittest.skipIf(os.name == 'nt', 'symlink creation may require elevated Windows privileges')
    def test_existing_repository_symlink_is_rejected_without_following_it(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            archive = root / 'fixture.zip'
            digest = fixture_archive(archive, {f'{PREFIX}/README.md': 'fixture'})
            outside = root / 'outside'
            outside.mkdir()
            state = root / 'state'
            state.mkdir()
            (state / 'repository').symlink_to(outside, target_is_directory=True)
            with self.assertRaisesRegex(BootstrapError, 'symbolic link'):
                prepare_repository(state, self._manifest(archive, digest), lambda _url, path: Path(path).write_bytes(archive.read_bytes()))
            self.assertFalse((outside / 'README.md').exists())

    def test_runtime_probe_uses_injected_process_and_requires_minimum_version(self):
        seen = []

        def runner(argv):
            seen.append(argv)
            if argv[0] == 'old-python':
                return {'returncode': 0, 'stdout': '3.10.9|/old/python'}
            if argv[0] == 'python3':
                return {'returncode': 0, 'stdout': '3.13.5|/runtime/python'}
            return {'returncode': 1, 'stdout': ''}

        result = find_python_runtime([('old-python', ()), ('python3', ())], runner)
        self.assertEqual(result['resolved_path'], '/runtime/python')
        self.assertEqual([call[0] for call in seen], ['old-python', 'python3'])

    def test_standalone_scripts_match_the_committed_pinned_manifest(self):
        root = Path(__file__).parents[1]
        manifest = json.loads((root / 'bootstrap-manifest.json').read_text(encoding='utf-8'))
        repository = manifest['repository']
        unix_runtime = manifest['unix_runtime']
        macos_runtime = unix_runtime['macos_official_installer']
        self.assertEqual(len(repository['revision']), 40)
        self.assertRegex(repository['archive_sha256'], r'^[0-9a-f]{64}$')
        for name in ('easy-bootstrap.ps1', 'easy-bootstrap.sh'):
            script = (root / name).read_text(encoding='utf-8')
            self.assertIn(repository['revision'], script)
            self.assertIn(repository['archive_sha256'], script)
            self.assertTrue(
                repository['archive_prefix'] in script or 'agent-welcome-$revision' in script,
                f'{name} must derive or embed the pinned archive root',
            )
        unix_script = (root / 'easy-bootstrap.sh').read_text(encoding='utf-8')
        self.assertIn('--approve-runtime-install', unix_script)
        self.assertIn(macos_runtime['archive_url'], unix_script)
        self.assertIn(macos_runtime['archive_sha256'], unix_script)
        self.assertIn('pkgutil --check-signature', unix_script)
        self.assertEqual(
            unix_runtime['supported_package_manager_plans']['apt-get'],
            ['sudo', 'apt-get', 'install', '-y', 'python3', 'curl', 'unzip'],
        )

    @unittest.skipIf(os.name == 'nt', 'POSIX shell bootstrap integration requires Unix')
    def test_unix_bootstrap_existing_python_runs_cli_from_outside_checkout(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            archive = root / 'repository.zip'
            digest = fixture_agent_welcome_archive(archive, SCRIPT_PREFIX)
            script = fixture_unix_bootstrap(root / 'easy-bootstrap-fixture.sh', digest)
            fakebin = root / 'bin'
            fakebin.mkdir()
            write_executable(fakebin / 'curl', """
destination=
while [ "$#" -gt 0 ]; do
  case "$1" in --output) destination=$2; shift 2 ;; *) shift ;; esac
done
cp "$FIXTURE_REPOSITORY_ARCHIVE" "$destination"
""")
            state = root / 'state'
            outside = root / 'outside'
            outside.mkdir()
            environment = os.environ.copy()
            environment.update({
                'PATH': str(fakebin) + os.pathsep + environment['PATH'],
                'FIXTURE_REPOSITORY_ARCHIVE': str(archive),
                'PYTHONPATH': '',
            })
            completed = subprocess.run(
                [str(script), '--target', 'windows-codex', '--state-dir', str(state),
                 '--approve-repository-download', '--start-easy-install'],
                cwd=outside, env=environment, text=True, capture_output=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)
            self.assertTrue((state / 'easy-state' / 'easy-state.json').is_file())
            result = json.loads((state / 'easy-state' / 'easy-state.json').read_text(encoding='utf-8'))
            self.assertEqual(result['target_id'], 'windows-codex')
            self.assertEqual(json.loads((state / 'bootstrap-state.json').read_text())['runtime'], 'existing')

    @unittest.skipIf(os.name == 'nt', 'POSIX shell bootstrap integration requires Unix')
    def test_unix_approved_runtime_install_runs_fixture_and_rechecks_python(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            archive = root / 'repository.zip'
            digest = fixture_agent_welcome_archive(archive, SCRIPT_PREFIX)
            script = fixture_unix_bootstrap(root / 'easy-bootstrap-fixture.sh', digest)
            fakebin = root / 'bin'
            fakebin.mkdir()
            marker = root / 'python-installed'
            package_log = root / 'package-manager.log'
            write_executable(fakebin / 'python3', """
if [ -f "$FIXTURE_RUNTIME_MARKER" ]; then exec "$REAL_PYTHON" "$@"; fi
exit 1
""")
            write_executable(fakebin / 'python', """
if [ -f "$FIXTURE_RUNTIME_MARKER" ]; then exec "$REAL_PYTHON" "$@"; fi
exit 1
""")
            write_executable(fakebin / 'sudo', 'exec "$@"\n')
            write_executable(fakebin / 'apt-get', """
printf '%s\\n' "$@" > "$FIXTURE_PACKAGE_LOG"
: > "$FIXTURE_RUNTIME_MARKER"
""")
            write_executable(fakebin / 'curl', """
destination=
while [ "$#" -gt 0 ]; do
  case "$1" in --output) destination=$2; shift 2 ;; *) shift ;; esac
done
cp "$FIXTURE_REPOSITORY_ARCHIVE" "$destination"
""")
            state = root / 'state'
            outside = root / 'outside'
            outside.mkdir()
            environment = os.environ.copy()
            environment.update({
                'PATH': str(fakebin) + os.pathsep + environment['PATH'],
                'FIXTURE_REPOSITORY_ARCHIVE': str(archive),
                'FIXTURE_RUNTIME_MARKER': str(marker),
                'FIXTURE_PACKAGE_LOG': str(package_log),
                'REAL_PYTHON': sys.executable,
                'PYTHONPATH': '',
            })
            completed = subprocess.run(
                [str(script), '--target', 'windows-codex', '--state-dir', str(state),
                 '--approve-runtime-install', '--approve-repository-download', '--start-easy-install'],
                cwd=outside, env=environment, text=True, capture_output=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)
            self.assertEqual(
                package_log.read_text(encoding='utf-8').splitlines(),
                ['install', '-y', 'python3', 'curl', 'unzip'],
            )
            self.assertTrue((state / 'easy-state' / 'easy-state.json').is_file())
            self.assertEqual(
                json.loads((state / 'bootstrap-state.json').read_text())['runtime'],
                'installed_apt',
            )

    @unittest.skipIf(os.name == 'nt', 'POSIX shell bootstrap integration requires Unix')
    def test_macos_runtime_fixture_is_verified_before_os_approved_installer(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repository_archive = root / 'repository.zip'
            repository_digest = fixture_agent_welcome_archive(repository_archive, SCRIPT_PREFIX)
            runtime_archive = root / 'python.pkg'
            runtime_archive.write_bytes(b'fixture CPython package')
            runtime_digest = hashlib.sha256(runtime_archive.read_bytes()).hexdigest()
            script = fixture_unix_bootstrap(
                root / 'easy-bootstrap-fixture.sh', repository_digest, runtime_digest,
            )
            fakebin = root / 'bin'
            fakebin.mkdir()
            marker = root / 'python-installed'
            log = root / 'macos-runtime.log'
            write_executable(fakebin / 'uname', """
case "$1" in -s) echo Darwin ;; -m) echo arm64 ;; *) exit 2 ;; esac
""")
            write_executable(fakebin / 'python3', """
if [ -f "$FIXTURE_RUNTIME_MARKER" ]; then exec "$REAL_PYTHON" "$@"; fi
exit 1
""")
            write_executable(fakebin / 'python', """
if [ -f "$FIXTURE_RUNTIME_MARKER" ]; then exec "$REAL_PYTHON" "$@"; fi
exit 1
""")
            write_executable(fakebin / 'sudo', 'printf "sudo %s\\n" "$*" >> "$FIXTURE_MACOS_LOG"\nexec "$@"\n')
            write_executable(fakebin / 'pkgutil', 'printf "pkgutil %s\\n" "$*" >> "$FIXTURE_MACOS_LOG"\n')
            write_executable(fakebin / 'installer', 'printf "installer %s\\n" "$*" >> "$FIXTURE_MACOS_LOG"\n: > "$FIXTURE_RUNTIME_MARKER"\n')
            write_executable(fakebin / 'curl', """
destination=
url=
while [ "$#" -gt 0 ]; do
  case "$1" in --output) destination=$2; shift 2 ;; *) url=$1; shift ;; esac
done
case "$url" in *macos11.pkg) cp "$FIXTURE_RUNTIME_ARCHIVE" "$destination" ;; *) cp "$FIXTURE_REPOSITORY_ARCHIVE" "$destination" ;; esac
""")
            state = root / 'state'
            environment = os.environ.copy()
            environment.update({
                'PATH': str(fakebin) + os.pathsep + environment['PATH'],
                'FIXTURE_REPOSITORY_ARCHIVE': str(repository_archive),
                'FIXTURE_RUNTIME_ARCHIVE': str(runtime_archive),
                'FIXTURE_RUNTIME_MARKER': str(marker),
                'FIXTURE_MACOS_LOG': str(log),
                'REAL_PYTHON': sys.executable,
                'PYTHONPATH': '',
            })
            completed = subprocess.run(
                [str(script), '--target', 'macos-codex', '--state-dir', str(state),
                 '--approve-runtime-install', '--approve-repository-download'],
                cwd=root, env=environment, text=True, capture_output=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)
            lines = log.read_text(encoding='utf-8').splitlines()
            self.assertTrue(any(line.startswith('pkgutil --check-signature ') for line in lines))
            self.assertTrue(any(line.startswith('installer -pkg ') and line.endswith(' -target /') for line in lines))
            self.assertEqual(
                json.loads((state / 'bootstrap-state.json').read_text())['runtime'],
                'installed_macos_pkg',
            )

    @unittest.skipUnless(os.name == 'nt', 'PowerShell standalone bootstrap is Windows-specific')
    def test_powershell_bootstrap_uses_injected_downloader_and_preserves_pinned_repository(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            archive = root / 'fixture.zip'
            digest = fixture_archive(archive, {f'{PREFIX}/README.md': 'fixture'})
            state = root / 'state'
            script = Path(__file__).parents[1] / 'easy-bootstrap.ps1'

            def ps(value):
                return str(value).replace("'", "''")

            driver = root / 'driver.ps1'
            driver.write_text(f"""
$ErrorActionPreference = 'Stop'
$fixture = '{ps(archive)}'
$manifest = @{{
  Repository = @{{ Revision = '{REVISION}'; ArchiveUrl = 'https://fixture.invalid/repository.zip'; ArchiveSha256 = '{digest}'; ArchivePrefix = '{PREFIX}' }}
  WindowsRuntime = @{{ Version = '3.13.5'; Architecture = 'AMD64'; ArchiveUrl = 'https://fixture.invalid/python.zip'; ArchiveSha256 = '{'0' * 64}' }}
}}
$script:downloads = 0
$downloader = {{ param($url, $destination) $script:downloads += 1; Copy-Item -LiteralPath $fixture -Destination $destination }}
$runner = {{ param($file, $probeArguments) return @{{ returncode = 0; stdout = '3.13.5|C:\\fixture\\python.exe' }} }}
. '{ps(script)}' -Target windows-codex -StateDir '{ps(state)}' -ApproveRepositoryDownload -Downloader $downloader -ProcessRunner $runner
$defaultManifest = $manifest
$first = Invoke-EasyBootstrap
$second = Invoke-EasyBootstrap
@{{ first = $first; second = $second; downloads = $script:downloads }} | ConvertTo-Json -Depth 9 -Compress
""", encoding='utf-8')
            completed = subprocess.run(
                ['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', str(driver)],
                text=True, capture_output=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)
            result = json.loads(completed.stdout)
            self.assertEqual(result['downloads'], 1)
            self.assertEqual(result['first']['repository']['kind'], 'prepared')
            self.assertEqual(result['second']['repository']['kind'], 'reused')
            self.assertEqual((state / 'repository' / 'README.md').read_text(), 'fixture')

    @unittest.skipUnless(os.name == 'nt', 'PowerShell standalone bootstrap is Windows-specific')
    def test_powershell_existing_python_starts_cli_from_outside_checkout(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            archive = root / 'fixture.zip'
            digest = fixture_agent_welcome_archive(archive, PREFIX)
            state = root / 'state'
            outside = root / 'outside'
            outside.mkdir()
            script = Path(__file__).parents[1] / 'easy-bootstrap.ps1'

            def ps(value):
                return str(value).replace("'", "''")

            driver = root / 'outside-driver.ps1'
            driver.write_text(f"""
$ErrorActionPreference = 'Stop'
$fixture = '{ps(archive)}'
$manifest = @{{
  Repository = @{{ Revision = '{REVISION}'; ArchiveUrl = 'https://fixture.invalid/repository.zip'; ArchiveSha256 = '{digest}'; ArchivePrefix = '{PREFIX}' }}
  WindowsRuntime = @{{ Version = '3.13.5'; Architecture = 'AMD64'; ArchiveUrl = 'https://fixture.invalid/python.zip'; ArchiveSha256 = '{'0' * 64}' }}
}}
$downloader = {{ param($url, $destination) Copy-Item -LiteralPath $fixture -Destination $destination }}
. '{ps(script)}' -Target windows-codex -StateDir '{ps(state)}' -ApproveRepositoryDownload -StartEasyInstall -Downloader $downloader
$defaultManifest = $manifest
$env:PYTHONPATH = ''
Set-Location -LiteralPath '{ps(outside)}'
$result = Invoke-EasyBootstrap
$result | ConvertTo-Json -Depth 9 -Compress
""", encoding='utf-8')
            completed = subprocess.run(
                ['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', str(driver)],
                text=True, capture_output=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)
            result = json.loads(completed.stdout)
            self.assertEqual(result['runtime']['kind'], 'existing')
            self.assertTrue(os.path.samefile(result['next_environment']['PYTHONPATH'], state / 'repository'))
            self.assertEqual(json.loads(result['easy_start_stdout'])['target_id'], 'windows-codex')
            self.assertTrue((state / 'easy-state' / 'easy-state.json').is_file())

    @unittest.skipUnless(os.name == 'nt', 'PowerShell standalone bootstrap is Windows-specific')
    def test_powershell_bootstrap_unpacks_only_a_pinned_state_local_runtime(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repository_archive = root / 'repository.zip'
            repository_digest = fixture_archive(repository_archive, {f'{PREFIX}/README.md': 'fixture'})
            runtime_archive = root / 'runtime.zip'
            runtime_digest = fixture_archive(runtime_archive, {
                'python.exe': 'fixture executable', 'python313._pth': 'python313.zip\n.\n',
            })
            state = root / 'state'
            script = Path(__file__).parents[1] / 'easy-bootstrap.ps1'

            def ps(value):
                return str(value).replace("'", "''")

            driver = root / 'runtime-driver.ps1'
            driver.write_text(f"""
$ErrorActionPreference = 'Stop'
$repositoryArchive = '{ps(repository_archive)}'
$runtimeArchive = '{ps(runtime_archive)}'
$manifest = @{{
  Repository = @{{ Revision = '{REVISION}'; ArchiveUrl = 'https://fixture.invalid/repository.zip'; ArchiveSha256 = '{repository_digest}'; ArchivePrefix = '{PREFIX}' }}
  WindowsRuntime = @{{ Version = '3.13.5'; Architecture = 'AMD64'; ArchiveUrl = 'https://fixture.invalid/python.zip'; ArchiveSha256 = '{runtime_digest}' }}
}}
$script:downloads = 0
$downloader = {{ param($url, $destination) $script:downloads += 1; if ($url -like '*repository*') {{ Copy-Item $repositoryArchive $destination }} else {{ Copy-Item $runtimeArchive $destination }} }}
$runner = {{ param($file, $probeArguments) return @{{ returncode = 1; stdout = '' }} }}
. '{ps(script)}' -Target windows-codex -StateDir '{ps(state)}' -ApproveRuntimeDownload -ApproveRepositoryDownload -Downloader $downloader -ProcessRunner $runner
$defaultManifest = $manifest
$first = Invoke-EasyBootstrap
$second = Invoke-EasyBootstrap
@{{ first = $first; second = $second; downloads = $script:downloads }} | ConvertTo-Json -Depth 9 -Compress
""", encoding='utf-8')
            completed = subprocess.run(
                ['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', str(driver)],
                text=True, capture_output=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)
            result = json.loads(completed.stdout)
            self.assertEqual(result['downloads'], 2)
            self.assertEqual(result['first']['runtime']['kind'], 'state_local_embedded')
            self.assertEqual(result['second']['runtime']['kind'], 'state_local_embedded')
            pth = next((state / 'runtime').rglob('python313._pth'))
            self.assertTrue(
                pth.read_text(encoding='utf-8').splitlines()[-1].lower().endswith('\\state\\repository')
            )


if __name__ == '__main__':
    unittest.main()
