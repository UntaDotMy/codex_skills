param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$ArgumentList
)

$defaultRepositoryUrl = "https://github.com/UntaDotMy/codex_skills.git"
$defaultRepositoryBranch = "main"

function Get-DefaultManagedRepositoryPath {
    return (Join-Path $HOME ".codex-skill-pack-repos\codex_skills")
}

function Test-RepositoryLayoutComplete {
    param([string]$RepositoryPath)

    return (Test-Path (Join-Path $RepositoryPath "AGENTS.md")) -and
        (Test-Path (Join-Path $RepositoryPath "README.md")) -and
        (Test-Path (Join-Path $RepositoryPath "00-skill-routing-and-escalation.md")) -and
        (Test-Path (Join-Path $RepositoryPath "sync-skills.sh")) -and
        (Test-Path (Join-Path $RepositoryPath "reviewer\SKILL.md"))
}

function Get-ManagedRepositoryPath {
    if ($env:CODEX_SKILLS_REPOSITORY_PATH) {
        return $env:CODEX_SKILLS_REPOSITORY_PATH
    }

    return (Get-DefaultManagedRepositoryPath)
}

function Test-ManagedRepositoryPathRepairable {
    param([string]$RepositoryPath)

    return $RepositoryPath -eq (Get-DefaultManagedRepositoryPath)
}

function Ensure-BootstrapGitAvailable {
    if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
        Write-Error "Git is required when sync-skills.ps1 is used as a standalone bootstrap entrypoint."
        exit 1
    }
}

function Ensure-ManagedRepositoryClone {
    param(
        [string]$RepositoryPath,
        [string]$RepositoryUrl,
        [string]$RepositoryBranch,
        [string]$CurrentScriptRoot
    )

    $temporaryRepositoryPath = $null

    if ((Test-Path (Join-Path $RepositoryPath '.git')) -and (Test-RepositoryLayoutComplete -RepositoryPath $RepositoryPath)) {
        return
    }

    if ($RepositoryPath -eq $CurrentScriptRoot) {
        Write-Error "Standalone bootstrap cannot reuse the current script directory as the managed clone path: $RepositoryPath"
        exit 1
    }

    $repositoryParentPath = Split-Path -Parent $RepositoryPath
    if (-not (Test-Path $repositoryParentPath)) {
        New-Item -ItemType Directory -Path $repositoryParentPath -Force | Out-Null
    }

    if ((Test-Path $RepositoryPath) -and (Get-ChildItem -Force -ErrorAction SilentlyContinue $RepositoryPath | Select-Object -First 1)) {
        if (Test-ManagedRepositoryPathRepairable -RepositoryPath $RepositoryPath) {
            Write-Host "[INFO] Repairing invalid managed clone path: $RepositoryPath"
            Remove-Item -Recurse -Force $RepositoryPath
        } else {
            Write-Error "Managed clone path exists but is not a valid codex_skills Git clone: $RepositoryPath"
            Write-Error "Remove that path or choose a clean CODEX_SKILLS_REPOSITORY_PATH before retrying."
            exit 1
        }
    }

    $temporaryRepositoryPath = Join-Path $repositoryParentPath ([System.IO.Path]::GetRandomFileName())
    New-Item -ItemType Directory -Path $temporaryRepositoryPath -Force | Out-Null
    Write-Host "[INFO] Cloning managed codex_skills repo into $RepositoryPath"
    try {
        & git clone --branch $RepositoryBranch --single-branch $RepositoryUrl $temporaryRepositoryPath
        if ($LASTEXITCODE -ne 0) {
            exit $LASTEXITCODE
        }

        if (Test-Path $RepositoryPath) {
            Remove-Item -Recurse -Force $RepositoryPath
        }

        Move-Item -Path $temporaryRepositoryPath -Destination $RepositoryPath
        $temporaryRepositoryPath = $null
    } finally {
        if ($temporaryRepositoryPath -and (Test-Path $temporaryRepositoryPath)) {
            Remove-Item -Recurse -Force $temporaryRepositoryPath
        }
    }
}

function Sync-ExternalBootstrapScriptCopy {
    param(
        [string]$ExternalScriptPath,
        [string]$ManagedScriptPath
    )

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
        Write-Host "[INFO] Refreshed standalone entry script from managed clone: $ExternalScriptPath"
    } catch {
        if (Test-Path $temporaryScriptPath) {
            Remove-Item -Force $temporaryScriptPath
        }
        Write-Host "[INFO] Managed clone is newer, but the standalone entry script could not be refreshed automatically: $ExternalScriptPath"
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

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not (Test-RepositoryLayoutComplete -RepositoryPath $scriptRoot)) {
    $env:CODEX_BOOTSTRAP_ORIGINAL_SCRIPT_PATH = $MyInvocation.MyCommand.Path
    Ensure-BootstrapGitAvailable

    $repositoryUrl = if ($env:CODEX_SKILLS_REPOSITORY_URL) { $env:CODEX_SKILLS_REPOSITORY_URL } else { $defaultRepositoryUrl }
    $repositoryBranch = if ($env:CODEX_SKILLS_REPOSITORY_BRANCH) { $env:CODEX_SKILLS_REPOSITORY_BRANCH } else { $defaultRepositoryBranch }
    $managedRepositoryPath = Get-ManagedRepositoryPath

    Ensure-ManagedRepositoryClone -RepositoryPath $managedRepositoryPath -RepositoryUrl $repositoryUrl -RepositoryBranch $repositoryBranch -CurrentScriptRoot $scriptRoot

    $delegateScriptPath = Join-Path $managedRepositoryPath "sync-skills.ps1"
    if (-not (Test-Path $delegateScriptPath)) {
        Write-Error "Managed clone is missing sync-skills.ps1: $managedRepositoryPath"
        exit 1
    }

    Write-Host "[INFO] Using managed clone: $managedRepositoryPath"
    & $delegateScriptPath @ArgumentList
    exit $LASTEXITCODE
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
