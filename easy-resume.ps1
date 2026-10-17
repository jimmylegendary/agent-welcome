[CmdletBinding()]
param(
    [string]$StateDir = (Join-Path (Get-Location) '.agent-welcome\easy'),
    [string]$AgentExecutable,
    [switch]$ApproveInstall,
    [switch]$ApprovePrerequisites,
    [switch]$ApproveFirstTask
)

$env:PYTHONPATH = $PSScriptRoot

$python = Get-Command py -ErrorAction SilentlyContinue
if ($null -ne $python) {
    $pythonExe = 'py'
    $pythonPrefix = @('-3')
} else {
    $python = Get-Command python -ErrorAction SilentlyContinue
    if ($null -eq $python) { Write-Error 'Python 3.11+ is required.'; exit 2 }
    $pythonExe = 'python'
    $pythonPrefix = @()
}
$arguments = @('-m', 'agent_welcome', 'easy-resume', '--state-dir', $StateDir)
if ($AgentExecutable) { $arguments += @('--agent-executable', $AgentExecutable) }
if ($ApproveInstall) { $arguments += '--approve-install' }
if ($ApprovePrerequisites) { $arguments += '--approve-prerequisites' }
if ($ApproveFirstTask) { $arguments += '--approve-first-task' }
& $pythonExe @pythonPrefix @arguments
exit $LASTEXITCODE
