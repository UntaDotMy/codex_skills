param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$ArgumentList
)

$defaultRepositoryUrl = "https://github.com/UntaDotMy/codex_skills.git"
$defaultRepositoryBranch = "main"

function Test-RepositoryLayoutComplete {
    param([string]$RepositoryPath)

    return (Test-Path (Join-Path $RepositoryPath "AGENTS.md")) -and
        (Test-Path (Join-Path $RepositoryPath "README.md")) -and
        (Test-Path (Join-Path $RepositoryPath "00-skill-routing-and-escalation.md")) -and
        (Test-Path (Join-Path $RepositoryPath "sync-skills.sh")) -and
        (Test-Path (Join-Path $RepositoryPath "reviewer\SKILL.md"))
}

function Get-RequestedRepositoryPath {
    if ($env:CODEX_SKILLS_REPOSITORY_PATH) {
        return $env:CODEX_SKILLS_REPOSITORY_PATH
    }

    return $null
}

function Test-BootstrapRepositoryPathIsPersistent {
    return [bool]$env:CODEX_SKILLS_REPOSITORY_PATH
}

function Ensure-BootstrapGitAvailable {
    if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
        Write-Error "Git is required when sync-skills.ps1 is used as a standalone bootstrap entrypoint."
        exit 1
    }
}

function Prepare-BootstrapRepositoryForRun {
    param(
        [string]$RepositoryUrl,
        [string]$RepositoryBranch,
        [string]$CurrentScriptRoot
    )

    $requestedRepositoryPath = Get-RequestedRepositoryPath
    if ($requestedRepositoryPath) {
        if ((Test-Path (Join-Path $requestedRepositoryPath '.git')) -and (Test-RepositoryLayoutComplete -RepositoryPath $requestedRepositoryPath)) {
            return $requestedRepositoryPath
        }

        if ($requestedRepositoryPath -eq $CurrentScriptRoot) {
            Write-Error "Standalone bootstrap cannot reuse the current script directory as the requested repository path: $requestedRepositoryPath"
            exit 1
        }

        $repositoryParentPath = Split-Path -Parent $requestedRepositoryPath
        if (-not (Test-Path $repositoryParentPath)) {
            New-Item -ItemType Directory -Path $repositoryParentPath -Force | Out-Null
        }

        if ((Test-Path $requestedRepositoryPath) -and (Get-ChildItem -Force -ErrorAction SilentlyContinue $requestedRepositoryPath | Select-Object -First 1)) {
            Write-Error "Requested bootstrap repository path exists but is not a valid codex_skills Git clone: $requestedRepositoryPath"
            Write-Error "Remove that path or choose a clean CODEX_SKILLS_REPOSITORY_PATH before retrying."
            exit 1
        }

        Write-Host "[INFO] Cloning requested codex_skills repo into $requestedRepositoryPath"
        & git clone --branch $RepositoryBranch --single-branch $RepositoryUrl $requestedRepositoryPath
        if ($LASTEXITCODE -ne 0) {
            exit $LASTEXITCODE
        }
        return $requestedRepositoryPath
    }

    $temporaryRepositoryPath = Join-Path ([System.IO.Path]::GetTempPath()) ("codex_skills.bootstrap." + [System.Guid]::NewGuid().ToString("N"))
    Write-Host "[INFO] Cloning fresh temporary codex_skills repo for this run"
    & git clone --branch $RepositoryBranch --single-branch $RepositoryUrl $temporaryRepositoryPath
    if ($LASTEXITCODE -ne 0) {
        if (Test-Path $temporaryRepositoryPath) {
            Remove-Item -Recurse -Force $temporaryRepositoryPath
        }
        exit $LASTEXITCODE
    }
    return $temporaryRepositoryPath
}

function Remove-BootstrapRuntimeRepository {
    $runtimeRepositoryPath = $env:CODEX_BOOTSTRAP_RUNTIME_REPOSITORY_PATH
    if (-not $runtimeRepositoryPath) {
        return
    }

    if ($env:CODEX_BOOTSTRAP_RUNTIME_REPOSITORY_PERSISTENT -eq "true") {
        return
    }

    if (-not (Test-CurrentScriptOwnsRuntimeRepository -CurrentScriptPath $script:CurrentBootstrapScriptPath)) {
        return
    }

    if (Test-Path $runtimeRepositoryPath) {
        Remove-Item -Recurse -Force $runtimeRepositoryPath
    }
}

function Test-CurrentScriptOwnsRuntimeRepository {
    param([string]$CurrentScriptPath)

    if (-not $env:CODEX_BOOTSTRAP_RUNTIME_REPOSITORY_PATH) {
        return $false
    }

    $runtimeEntryScriptPath = if ($env:CODEX_BOOTSTRAP_RUNTIME_ENTRY_SCRIPT_PATH) {
        $env:CODEX_BOOTSTRAP_RUNTIME_ENTRY_SCRIPT_PATH
    } else {
        $env:CODEX_BOOTSTRAP_ORIGINAL_SCRIPT_PATH
    }
    if (-not $runtimeEntryScriptPath -or -not $CurrentScriptPath) {
        return $false
    }

    return [System.IO.Path]::GetFullPath($runtimeEntryScriptPath) -eq [System.IO.Path]::GetFullPath($CurrentScriptPath)
}

$script:BootstrapExternalScriptRefreshResult = "unchanged"

function Sync-ExternalBootstrapScriptCopy {
    param(
        [string]$ExternalScriptPath,
        [string]$ManagedScriptPath
    )

    $script:BootstrapExternalScriptRefreshResult = "unchanged"

    if (-not $ExternalScriptPath -or -not (Test-Path $ExternalScriptPath) -or -not (Test-Path $ManagedScriptPath)) {
        return
    }

    if ([System.IO.Path]::GetFullPath($ExternalScriptPath) -eq [System.IO.Path]::GetFullPath($ManagedScriptPath)) {
        return
    }

    $externalHash = (Get-FileHash -Algorithm SHA256 $ExternalScriptPath).Hash
    $managedHash = (Get-FileHash -Algorithm SHA256 $ManagedScriptPath).Hash
    if ($externalHash -eq $managedHash) {
        return
    }

    $temporaryScriptPath = "$ExternalScriptPath.codex-refresh.tmp"
    try {
        Copy-Item -Path $ManagedScriptPath -Destination $temporaryScriptPath -Force
        Move-Item -Path $temporaryScriptPath -Destination $ExternalScriptPath -Force
        Write-Host "[INFO] Refreshed standalone entry script from the staged bootstrap repo: $ExternalScriptPath"
        $script:BootstrapExternalScriptRefreshResult = "refreshed"
    } catch {
        if (Test-Path $temporaryScriptPath) {
            Remove-Item -Force $temporaryScriptPath
        }
        $script:BootstrapExternalScriptRefreshResult = "failed"
        Write-Host "[INFO] Staged bootstrap repo is newer, but the standalone entry script could not be refreshed automatically: $ExternalScriptPath"
    }
}

function Invoke-BootstrapDelegateFromRepository {
    param(
        [string]$RepositoryPath,
        [string]$DelegateScriptName,
        [string[]]$DelegateArguments
    )

    $delegateScriptPath = Join-Path $RepositoryPath $DelegateScriptName
    if (-not (Test-Path $delegateScriptPath)) {
        Write-Error "Staged bootstrap repository is missing $DelegateScriptName: $RepositoryPath"
        Remove-BootstrapRuntimeRepository
        exit 1
    }

    Write-Host "[INFO] Using staged bootstrap repo: $RepositoryPath"
    try {
        & $delegateScriptPath @DelegateArguments
        return $LASTEXITCODE
    } finally {
        Remove-BootstrapRuntimeRepository
    }
}

function Refresh-BootstrapEntryScriptFromRepo {
    param([string]$CurrentScriptRoot)

    $externalScriptPath = $env:CODEX_BOOTSTRAP_ORIGINAL_SCRIPT_PATH
    if (-not $externalScriptPath) {
        return
    }

    $managedScriptPath = Join-Path $CurrentScriptRoot (Split-Path -Leaf $externalScriptPath)
    Sync-ExternalBootstrapScriptCopy -ExternalScriptPath $externalScriptPath -ManagedScriptPath $managedScriptPath
}

$script:CurrentBootstrapScriptPath = $MyInvocation.MyCommand.Path
$scriptRoot = Split-Path -Parent $script:CurrentBootstrapScriptPath
if (-not (Test-RepositoryLayoutComplete -RepositoryPath $scriptRoot)) {
    $currentScriptPath = $script:CurrentBootstrapScriptPath
    Ensure-BootstrapGitAvailable

    $runtimeRepositoryPath = $env:CODEX_BOOTSTRAP_RUNTIME_REPOSITORY_PATH
    if ($runtimeRepositoryPath -and -not (Test-CurrentScriptOwnsRuntimeRepository -CurrentScriptPath $currentScriptPath)) {
        Remove-Item Env:CODEX_BOOTSTRAP_RUNTIME_REPOSITORY_PATH -ErrorAction SilentlyContinue
        Remove-Item Env:CODEX_BOOTSTRAP_RUNTIME_REPOSITORY_PERSISTENT -ErrorAction SilentlyContinue
        Remove-Item Env:CODEX_BOOTSTRAP_RUNTIME_ENTRY_SCRIPT_PATH -ErrorAction SilentlyContinue
        Remove-Item Env:CODEX_BOOTSTRAP_ORIGINAL_SCRIPT_PATH -ErrorAction SilentlyContinue
        $runtimeRepositoryPath = $null
    }
    if ($runtimeRepositoryPath) {
        if (-not (Test-RepositoryLayoutComplete -RepositoryPath $runtimeRepositoryPath)) {
            Write-Error "Staged bootstrap repository is missing the required codex_skills files: $runtimeRepositoryPath"
            exit 1
        }

        $delegateExitCode = Invoke-BootstrapDelegateFromRepository -RepositoryPath $runtimeRepositoryPath -DelegateScriptName "sync-skills.ps1" -DelegateArguments $ArgumentList
        exit $delegateExitCode
    }

    $repositoryUrl = if ($env:CODEX_SKILLS_REPOSITORY_URL) { $env:CODEX_SKILLS_REPOSITORY_URL } else { $defaultRepositoryUrl }
    $repositoryBranch = if ($env:CODEX_SKILLS_REPOSITORY_BRANCH) { $env:CODEX_SKILLS_REPOSITORY_BRANCH } else { $defaultRepositoryBranch }
    $runtimeRepositoryPath = Prepare-BootstrapRepositoryForRun -RepositoryUrl $repositoryUrl -RepositoryBranch $repositoryBranch -CurrentScriptRoot $scriptRoot
    $env:CODEX_BOOTSTRAP_ORIGINAL_SCRIPT_PATH = $currentScriptPath
    $env:CODEX_BOOTSTRAP_RUNTIME_REPOSITORY_PATH = $runtimeRepositoryPath
    $env:CODEX_BOOTSTRAP_RUNTIME_ENTRY_SCRIPT_PATH = $currentScriptPath
    $env:CODEX_BOOTSTRAP_RUNTIME_REPOSITORY_PERSISTENT = if (Test-BootstrapRepositoryPathIsPersistent) { "true" } else { "false" }

    Sync-ExternalBootstrapScriptCopy -ExternalScriptPath $currentScriptPath -ManagedScriptPath (Join-Path $runtimeRepositoryPath (Split-Path -Leaf $currentScriptPath))
    if ($script:BootstrapExternalScriptRefreshResult -eq "refreshed") {
        Write-Host "[INFO] Restarting into the refreshed standalone entry script before continuing."
        & $currentScriptPath @ArgumentList
        exit $LASTEXITCODE
    }

    $delegateExitCode = Invoke-BootstrapDelegateFromRepository -RepositoryPath $runtimeRepositoryPath -DelegateScriptName "sync-skills.ps1" -DelegateArguments $ArgumentList
    exit $delegateExitCode
}
Refresh-BootstrapEntryScriptFromRepo -CurrentScriptRoot $scriptRoot
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
Refresh-BootstrapEntryScriptFromRepo -CurrentScriptRoot $scriptRoot
exit $LASTEXITCODE
