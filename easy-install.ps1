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
    $pythonArgs = @('-3', '-m', 'agent_welcome', 'easy-start', '--target', $Target, '--state-dir', $StateDir)
    if ($AgentExecutable) { $pythonArgs += @('--agent-executable', $AgentExecutable) }
    if ($ApproveInstall) { $pythonArgs += '--approve-install' }
    if ($ApprovePrerequisites) { $pythonArgs += '--approve-prerequisites' }
    if ($ApproveFirstTask) { $pythonArgs += '--approve-first-task' }
    & py @pythonArgs
    exit $LASTEXITCODE
}

$python = Get-Command python -ErrorAction SilentlyContinue
if ($null -eq $python) {
    Write-Error 'Python 3.11+ is required. Install it through a user-approved Windows source, then rerun this launcher.'
    exit 2
}
$pythonArgs = @('-m', 'agent_welcome', 'easy-start', '--target', $Target, '--state-dir', $StateDir)
if ($AgentExecutable) { $pythonArgs += @('--agent-executable', $AgentExecutable) }
if ($ApproveInstall) { $pythonArgs += '--approve-install' }
if ($ApprovePrerequisites) { $pythonArgs += '--approve-prerequisites' }
if ($ApproveFirstTask) { $pythonArgs += '--approve-first-task' }
& python @pythonArgs
exit $LASTEXITCODE
