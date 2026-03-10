param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$ArgumentList
)

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$gitBashCandidates = @(
    (Join-Path $env:ProgramFiles "Git\\bin\\bash.exe"),
    (Join-Path $env:ProgramW6432 "Git\\bin\\bash.exe"),
    (Join-Path $env:LOCALAPPDATA "Programs\\Git\\bin\\bash.exe")
) | Where-Object { $_ -and (Test-Path $_) }

$gitBashPath = $gitBashCandidates | Select-Object -First 1
if (-not $gitBashPath) {
    Write-Error "Git Bash was not found. Install Git for Windows or run sync-skills.sh from an existing Bash shell."
    exit 1
}

$bashScriptPath = Join-Path $scriptRoot "sync-skills.sh"
if (-not (Test-Path $bashScriptPath)) {
    Write-Error "sync-skills.sh was not found next to sync-skills.ps1."
    exit 1
}

& $gitBashPath $bashScriptPath @ArgumentList
exit $LASTEXITCODE
