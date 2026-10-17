[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$Target,
    [string]$StateDir = (Join-Path (Get-Location) '.agent-welcome\easy'),
    [string]$AgentExecutable,
    [switch]$ApproveInstall,
    [switch]$ApprovePrerequisites,
    [switch]$ApproveFirstTask
)

# This launcher records the target plan in the explicit state directory.  An
# installer runs only when the caller explicitly passes -ApproveInstall.
# Find the checked-out module without requiring the caller to cd to its root.
$env:PYTHONPATH = $PSScriptRoot
$python = Get-Command py -ErrorAction SilentlyContinue
if ($null -ne $python) {
    & py -3 -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)'
    if ($LASTEXITCODE -eq 0) {
        $pythonArgs = @('-3', '-m', 'agent_welcome', 'easy-start', '--target', $Target, '--state-dir', $StateDir)
        if ($AgentExecutable) { $pythonArgs += @('--agent-executable', $AgentExecutable) }
        if ($ApproveInstall) { $pythonArgs += '--approve-install' }
        if ($ApprovePrerequisites) { $pythonArgs += '--approve-prerequisites' }
        if ($ApproveFirstTask) { $pythonArgs += '--approve-first-task' }
        & py @pythonArgs
        exit $LASTEXITCODE
    }
}

$python = Get-Command python -ErrorAction SilentlyContinue
if ($null -ne $python) {
    & python -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)'
    if ($LASTEXITCODE -eq 0) {
        $pythonArgs = @('-m', 'agent_welcome', 'easy-start', '--target', $Target, '--state-dir', $StateDir)
        if ($AgentExecutable) { $pythonArgs += @('--agent-executable', $AgentExecutable) }
        if ($ApproveInstall) { $pythonArgs += '--approve-install' }
        if ($ApprovePrerequisites) { $pythonArgs += '--approve-prerequisites' }
        if ($ApproveFirstTask) { $pythonArgs += '--approve-first-task' }
        & python @pythonArgs
        exit $LASTEXITCODE
    }
}
if ($null -eq $python -or $LASTEXITCODE -ne 0) {
    Write-Error 'Python 3.11+ is required. Run .\easy-bootstrap.ps1 with an explicit state directory to prepare or use a state-local pinned runtime, then rerun this launcher.'
    exit 2
}
