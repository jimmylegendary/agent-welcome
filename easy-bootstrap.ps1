[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$Target,
    [string]$StateDir = (Join-Path (Get-Location) '.agent-welcome\bootstrap'),
    [switch]$ApproveRuntimeDownload,
    [switch]$ApproveRepositoryDownload,
    [switch]$StartEasyInstall,
    # Test-only injection points. They are usable only by dot-sourcing the
    # script; normal -File execution always uses the pinned manifest below.
    [scriptblock]$Downloader,
    [scriptblock]$ProcessRunner
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$defaultManifest = @{
    Repository = @{
        Revision = 'ceb6d3803b12d41d429dc3188e9a20ac8f220780'
        ArchiveUrl = 'https://codeload.github.com/jimmylegendary/agent-welcome/zip/ceb6d3803b12d41d429dc3188e9a20ac8f220780'
        ArchiveSha256 = '38d359aa0b05ae6bed5214a1b845e67477332c17cc291fc1727969aff648891d'
        ArchivePrefix = 'agent-welcome-ceb6d3803b12d41d429dc3188e9a20ac8f220780'
    }
    WindowsRuntime = @{
        Version = '3.13.5'
        Architecture = 'AMD64'
        ArchiveUrl = 'https://www.python.org/ftp/python/3.13.5/python-3.13.5-embed-amd64.zip'
        ArchiveSha256 = '7d2650fd9d1b9d002d4a315d5f354247fd6a44f30517c7ef577b08f57a0fb6d9'
    }
}

function Get-Sha256([string]$Path) {
    $stream = [IO.File]::OpenRead($Path)
    $hash = [Security.Cryptography.SHA256]::Create()
    try {
        return ([BitConverter]::ToString($hash.ComputeHash($stream)) -replace '-', '').ToLowerInvariant()
    } finally {
        $hash.Dispose()
        $stream.Dispose()
    }
}

function Write-JsonAtomically([string]$Path, [object]$Value) {
    $temporary = Join-Path (Split-Path -Parent $Path) ('.bootstrap-' + [guid]::NewGuid().ToString('N') + '.tmp')
    [IO.File]::WriteAllText($temporary, ($Value | ConvertTo-Json -Depth 8 -Compress), [Text.Encoding]::UTF8)
    Move-Item -LiteralPath $temporary -Destination $Path -Force
}

function Invoke-Download([string]$Url, [string]$Destination) {
    if ($null -ne $Downloader) {
        & $Downloader $Url $Destination
        return
    }
    Invoke-WebRequest -Uri $Url -OutFile $Destination -UseBasicParsing
}

function Expand-SafeZip([string]$Archive, [string]$Destination, [string]$ExpectedPrefix = '') {
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    New-Item -ItemType Directory -Path $Destination -ErrorAction Stop | Out-Null
    $destinationFull = [IO.Path]::GetFullPath($Destination)
    $allowedPrefix = $destinationFull + [IO.Path]::DirectorySeparatorChar
    $zip = [IO.Compression.ZipFile]::OpenRead($Archive)
    try {
        foreach ($entry in $zip.Entries) {
            $name = $entry.FullName
            if ([string]::IsNullOrWhiteSpace($name) -or $name.Contains('\') -or [IO.Path]::IsPathRooted($name)) {
                throw "unsafe ZIP member: $name"
            }
            if ($ExpectedPrefix -and -not ($name -eq "$ExpectedPrefix/" -or $name.StartsWith("$ExpectedPrefix/", [StringComparison]::Ordinal))) {
                throw "ZIP member is outside the pinned repository root: $name"
            }
            $mode = ($entry.ExternalAttributes -shr 16) -band 0xF000
            if ($mode -eq 0xA000) {
                throw "symbolic-link ZIP member is not allowed: $name"
            }
            $target = [IO.Path]::GetFullPath([IO.Path]::Combine($destinationFull, $name))
            if (-not ($target -eq $destinationFull -or $target.StartsWith($allowedPrefix, [StringComparison]::OrdinalIgnoreCase))) {
                throw "ZIP member escapes extraction root: $name"
            }
            if ($name.EndsWith('/')) {
                New-Item -ItemType Directory -Path $target -Force | Out-Null
                continue
            }
            New-Item -ItemType Directory -Path (Split-Path -Parent $target) -Force | Out-Null
            $input = $entry.Open()
            try {
                $output = [IO.File]::Open($target, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::None)
                try { $input.CopyTo($output) } finally { $output.Dispose() }
            } finally { $input.Dispose() }
        }
    } finally { $zip.Dispose() }
}

function Test-BootstrapMarker([string]$Path, [hashtable]$Expected) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { return $false }
    try {
        $saved = Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json
        return $saved.revision -eq $Expected.Revision -and $saved.archive_sha256 -eq $Expected.ArchiveSha256.ToLowerInvariant()
    } catch { return $false }
}

function Prepare-Repository([string]$Root, [hashtable]$Manifest) {
    $repository = Join-Path $Root 'repository'
    $marker = Join-Path $repository '.agent-welcome-bootstrap.json'
    if (Test-Path -LiteralPath $repository) {
        if (((Get-Item -LiteralPath $repository -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
            throw 'bootstrap repository path must not be a symbolic link'
        }
        if ((Test-Path -LiteralPath $repository -PathType Container) -and (Test-BootstrapMarker $marker $Manifest)) {
            return @{ kind = 'reused'; repository = $repository; revision = $Manifest.Revision }
        }
        throw 'existing repository directory is not this pinned bootstrap; preserving it'
    }
    $stage = Join-Path $Root ('.bootstrap-stage-' + [guid]::NewGuid().ToString('N'))
    try {
        New-Item -ItemType Directory -Path $stage -ErrorAction Stop | Out-Null
        $archive = Join-Path $stage 'repository.zip'
        Invoke-Download $Manifest.ArchiveUrl $archive
        if (-not (Test-Path -LiteralPath $archive -PathType Leaf)) { throw 'downloader did not create repository archive' }
        if ((Get-Sha256 $archive) -ne $Manifest.ArchiveSha256.ToLowerInvariant()) { throw 'repository archive SHA-256 did not match pinned revision' }
        $extracted = Join-Path $stage 'extracted'
        Expand-SafeZip $archive $extracted $Manifest.ArchivePrefix
        $payload = Join-Path $extracted $Manifest.ArchivePrefix
        if (-not (Test-Path -LiteralPath $payload -PathType Container)) { throw 'repository archive is missing pinned root' }
        Write-JsonAtomically (Join-Path $payload '.agent-welcome-bootstrap.json') @{
            revision = $Manifest.Revision; archive_sha256 = $Manifest.ArchiveSha256.ToLowerInvariant()
        }
        Move-Item -LiteralPath $payload -Destination $repository -ErrorAction Stop
    } finally {
        if (Test-Path -LiteralPath $stage) { Remove-Item -LiteralPath $stage -Recurse -Force }
    }
    return @{ kind = 'prepared'; repository = $repository; revision = $Manifest.Revision }
}

function Invoke-BootstrapProcess([string]$FilePath, [string[]]$ArgumentList) {
    if ($null -ne $ProcessRunner) { return & $ProcessRunner $FilePath $ArgumentList }
    $output = & $FilePath @ArgumentList 2>&1
    return @{ returncode = $LASTEXITCODE; stdout = ($output -join "`n") }
}

function Find-PythonRuntime {
    foreach ($candidate in @(@{ file = 'py'; prefix = @('-3') }, @{ file = 'python'; prefix = @() })) {
        if ($null -eq $ProcessRunner -and $null -eq (Get-Command $candidate.file -ErrorAction SilentlyContinue)) { continue }
        # Windows PowerShell's legacy native-argument forwarding can strip
        # embedded quotes from a `python -c` value.  This equivalent probe uses
        # character codes so the argv remains a single quote-free argument.
        $probe = 'import sys; print(*sys.version_info[:3], sep=chr(46), end=chr(124)); print(sys.executable)'
        $arguments = @($candidate.prefix) + @('-c', $probe)
        if ($null -ne $ProcessRunner) {
            $result = Invoke-BootstrapProcess $candidate.file $arguments
        } elseif ($candidate.file -eq 'py') {
            $output = & py -3 -c $probe 2>&1
            $result = @{ returncode = $LASTEXITCODE; stdout = ($output -join "`n") }
        } else {
            $output = & python -c $probe 2>&1
            $result = @{ returncode = $LASTEXITCODE; stdout = ($output -join "`n") }
        }
        if ($result.returncode -ne 0) { continue }
        $parts = [string]$result.stdout -split '\|', 2
        if ($parts.Count -ne 2) { continue }
        try { $version = [Version]$parts[0].Trim() } catch { continue }
        if ($version -ge [Version]'3.11') {
            return @{ kind = 'existing'; executable = $candidate.file; prefix = @($candidate.prefix); version = $version.ToString(); resolved_path = $parts[1].Trim() }
        }
    }
    return $null
}

function Prepare-WindowsRuntime([string]$Root, [hashtable]$Manifest) {
    if ($env:PROCESSOR_ARCHITECTURE -notin @('AMD64', '')) { throw 'state-local Python archive is pinned only for Windows AMD64' }
    $runtime = Join-Path $Root ('runtime\python-' + $Manifest.Version + '-amd64')
    $marker = Join-Path $runtime '.agent-welcome-runtime.json'
    if (Test-Path -LiteralPath $runtime) {
        if (((Get-Item -LiteralPath $runtime -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
            throw 'bootstrap runtime path must not be a symbolic link'
        }
        if ((Test-Path -LiteralPath (Join-Path $runtime 'python.exe') -PathType Leaf) -and (Test-BootstrapMarker $marker @{
                    Revision = $Manifest.Version; ArchiveSha256 = $Manifest.ArchiveSha256 })) {
            return @{ kind = 'reused'; executable = (Join-Path $runtime 'python.exe'); prefix = @(); version = $Manifest.Version }
        }
        throw 'existing runtime directory is not this pinned bootstrap; preserving it'
    }
    $stage = Join-Path $Root ('.runtime-stage-' + [guid]::NewGuid().ToString('N'))
    try {
        New-Item -ItemType Directory -Path $stage -ErrorAction Stop | Out-Null
        $archive = Join-Path $stage 'python-embed.zip'
        Invoke-Download $Manifest.ArchiveUrl $archive
        if (-not (Test-Path -LiteralPath $archive -PathType Leaf)) { throw 'downloader did not create runtime archive' }
        if ((Get-Sha256 $archive) -ne $Manifest.ArchiveSha256.ToLowerInvariant()) { throw 'runtime archive SHA-256 did not match pinned official runtime' }
        $extracted = Join-Path $stage 'extracted'
        Expand-SafeZip $archive $extracted
        if (-not (Test-Path -LiteralPath (Join-Path $extracted 'python.exe') -PathType Leaf)) { throw 'official runtime archive is missing python.exe' }
        Write-JsonAtomically (Join-Path $extracted '.agent-welcome-runtime.json') @{
            revision = $Manifest.Version; archive_sha256 = $Manifest.ArchiveSha256.ToLowerInvariant()
        }
        New-Item -ItemType Directory -Path (Split-Path -Parent $runtime) -Force | Out-Null
        Move-Item -LiteralPath $extracted -Destination $runtime -ErrorAction Stop
    } finally {
        if (Test-Path -LiteralPath $stage) { Remove-Item -LiteralPath $stage -Recurse -Force }
    }
    return @{ kind = 'prepared'; executable = (Join-Path $runtime 'python.exe'); prefix = @(); version = $Manifest.Version }
}

function Enable-EmbeddedRepository([string]$PythonExecutable, [string]$Repository) {
    $runtimeRoot = Split-Path -Parent $PythonExecutable
    $pth = Get-ChildItem -LiteralPath $runtimeRoot -Filter 'python*._pth' | Select-Object -First 1
    if ($null -eq $pth) { throw 'pinned embedded Python is missing its _pth configuration' }
    $repositoryFull = [IO.Path]::GetFullPath($Repository)
    $content = Get-Content -LiteralPath $pth.FullName
    if ($content -notcontains $repositoryFull) {
        Add-Content -LiteralPath $pth.FullName -Value $repositoryFull
    }
}

function Invoke-EasyBootstrap {
    $manifest = $defaultManifest
    $root = [IO.Path]::GetFullPath($StateDir)
    New-Item -ItemType Directory -Path $root -Force | Out-Null
    $pending = @()
    $runtime = Find-PythonRuntime
    if ($null -eq $runtime) {
        if ($ApproveRuntimeDownload) {
            $runtime = Prepare-WindowsRuntime $root $manifest.WindowsRuntime
            $runtime.kind = 'state_local_embedded'
        } else {
            $pending += @{ kind = 'runtime_download_consent'; url = $manifest.WindowsRuntime.ArchiveUrl; sha256 = $manifest.WindowsRuntime.ArchiveSha256; scope = 'state-local embedded Python only'; consent = 'Re-run with -ApproveRuntimeDownload to download and unpack this pinned official archive beneath StateDir.' }
        }
    }
    $repository = $null
    $repoPath = Join-Path $root 'repository'
    if (Test-Path -LiteralPath $repoPath) {
        $repository = Prepare-Repository $root $manifest.Repository
    } elseif ($ApproveRepositoryDownload) {
        $repository = Prepare-Repository $root $manifest.Repository
    } else {
        $pending += @{ kind = 'repository_download_consent'; url = $manifest.Repository.ArchiveUrl; sha256 = $manifest.Repository.ArchiveSha256; revision = $manifest.Repository.Revision; scope = 'state-local repository checkout only'; consent = 'Re-run with -ApproveRepositoryDownload to prepare this pinned repository archive beneath StateDir.' }
    }
    if ($pending.Count) {
        $result = @{ status = 'WAITING_USER'; state_dir = $root; pending = $pending }
        Write-JsonAtomically (Join-Path $root 'bootstrap-state.json') $result
        return $result
    }
    if ($runtime.kind -eq 'state_local_embedded') { Enable-EmbeddedRepository $runtime.executable $repository.repository }
    $easyState = Join-Path $root 'easy-state'
    $command = @($runtime.prefix) + @('-m', 'agent_welcome', 'easy-start', '--target', $Target, '--state-dir', $easyState)
    $result = @{ status = 'READY'; state_dir = $root; runtime = $runtime; repository = $repository; next_argv = @($runtime.executable) + $command }
    Write-JsonAtomically (Join-Path $root 'bootstrap-state.json') $result
    if ($StartEasyInstall) {
        $started = Invoke-BootstrapProcess $runtime.executable $command
        if ($started.returncode -ne 0) { throw "easy-start failed after bootstrap: $($started.stdout)" }
        $result.easy_start_stdout = $started.stdout
    }
    return $result
}

if ($MyInvocation.InvocationName -ne '.') {
    try {
        Invoke-EasyBootstrap | ConvertTo-Json -Depth 8
    } catch {
        @{ status = 'FAILED'; error = $_.Exception.Message } | ConvertTo-Json -Compress
        exit 2
    }
}
