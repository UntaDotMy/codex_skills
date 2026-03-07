# Windows Git Workflows

## Windows-Specific Considerations

### Line Endings

**The Problem:**
- Windows uses CRLF (`\r\n`) for line endings
- Unix/Mac uses LF (`\n`) for line endings
- Git can convert between them, causing confusion

**The Solution:**

**Global Configuration (Recommended):**
```bash
# Windows: Convert LF to CRLF on checkout, CRLF to LF on commit
git config --global core.autocrlf true

# Unix/Mac: Convert CRLF to LF on commit, no conversion on checkout
git config --global core.autocrlf input
```

**Per-Repository (.gitattributes):**
```
# Auto detect text files and normalize line endings to LF
* text=auto

# Force LF for specific files
*.sh text eol=lf
*.bash text eol=lf

# Force CRLF for Windows-specific files
*.bat text eol=crlf
*.cmd text eol=crlf
*.ps1 text eol=crlf

# Binary files
*.png binary
*.jpg binary
*.exe binary
*.dll binary
```

**Best Practice:**
- Use `.gitattributes` in repository (consistent for all developers)
- Set `core.autocrlf=true` on Windows
- Set `core.autocrlf=input` on Unix/Mac

### Path Handling

**Windows Paths:**
```bash
# Windows uses backslashes
C:\Users\username\project

# Git uses forward slashes (Unix-style)
/c/Users/username/project

# In Git commands, use forward slashes
git add src/components/Button.jsx
```

**Long Paths:**
Windows has 260-character path limit by default.

**Enable long paths:**
```bash
# Enable long paths in Git
git config --global core.longpaths true

# Enable long paths in Windows (requires admin)
# Run in PowerShell as Administrator:
New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name "LongPathsEnabled" -Value 1 -PropertyType DWORD -Force
```

**Case Sensitivity:**
Windows file system is case-insensitive, but Git is case-sensitive.

**Problem:**
```bash
# Rename file from Button.jsx to button.jsx
# Windows sees them as the same file
# Git sees them as different files
```

**Solution:**
```bash
# Use git mv for renaming
git mv Button.jsx button.jsx

# Or configure Git to be case-insensitive
git config core.ignorecase true
```

### Shell Integration

**Git Bash:**
- Comes with Git for Windows
- Unix-like shell on Windows
- Supports Unix commands (ls, grep, etc.)
- Use for Git commands and Unix-style scripting

**PowerShell:**
- Native Windows shell
- More powerful than CMD
- Better for Windows-specific tasks
- Use for Windows automation

**CMD:**
- Legacy Windows shell
- Limited functionality
- Avoid for Git workflows

**Choosing the Right Shell:**

```bash
# Git Bash (recommended for Git operations)
git status
git commit -m "message"

# PowerShell (for Windows tasks)
powershell.exe -NoProfile -Command "Get-Process"

# CMD (avoid if possible)
cmd.exe /c dir
```

### File Permissions

**The Problem:**
Windows doesn't have Unix-style file permissions (755, 644, etc.)

**Git Behavior:**
- Git tracks executable bit on Unix/Mac
- Windows doesn't have executable bit
- Can cause issues when collaborating

**Solution:**
```bash
# Disable filemode tracking (Windows)
git config core.filemode false

# This prevents Git from tracking permission changes
```

### Symbolic Links

**The Problem:**
- Unix uses symbolic links (symlinks)
- Windows has symlinks but requires admin privileges
- Git can't create symlinks on Windows by default

**Solution:**
```bash
# Enable symlink support (requires admin)
git config --global core.symlinks true

# Or use Git Bash with admin privileges
```

**Alternative:**
- Avoid symlinks in cross-platform projects
- Use relative paths instead

## PowerShell Git Workflows

### Basic Commands

```powershell
# Clone repository
git clone https://github.com/user/repo.git

# Check status
git status

# Stage files
git add .

# Commit
git commit -m "Commit message"

# Push
git push origin main

# Pull
git pull origin main
```

### PowerShell-Specific Tips

**Escaping Special Characters:**
```powershell
# Use quotes for commit messages with special characters
git commit -m "Fix: Handle `$variable` properly"

# Or use single quotes (no variable expansion)
git commit -m 'Fix: Handle $variable properly'
```

**Piping Output:**
```powershell
# Get list of modified files
git status --short | Select-String "M "

# Count commits
git log --oneline | Measure-Object -Line
```

**Aliases:**
```powershell
# Add to PowerShell profile ($PROFILE)
function gs { git status }
function ga { git add $args }
function gc { git commit -m $args }
function gp { git push }
function gl { git log --oneline -10 }
```

### PowerShell Scripts

**Automated Commit Script:**
```powershell
# commit.ps1
param(
    [Parameter(Mandatory=$true)]
    [string]$Message
)

git add .
git commit -m $Message
git push

Write-Host "Changes committed and pushed successfully" -ForegroundColor Green
```

**Usage:**
```powershell
.\commit.ps1 -Message "Add new feature"
```

## Git Bash Workflows

### Why Use Git Bash?

- Unix-like environment on Windows
- Supports Unix commands (ls, grep, cat, etc.)
- Better for Git operations
- Consistent with Unix/Mac workflows

### Common Commands

```bash
# Navigate
cd /c/Users/username/project
pwd
ls -la

# Git operations
git status
git log --oneline --graph --all
git diff

# File operations
cat README.md
grep "TODO" src/**/*.js
find . -name "*.test.js"
```

### Bash Scripts

**Automated Workflow:**
```bash
#!/bin/bash
# deploy.sh

# Pull latest changes
git pull origin main

# Install dependencies
npm install

# Run tests
npm test

# Build
npm run build

# Deploy
npm run deploy

echo "Deployment complete!"
```

**Make executable:**
```bash
chmod +x deploy.sh
./deploy.sh
```

## Common Windows Git Issues

### Issue 1: CRLF Line Ending Warnings

**Problem:**
```
warning: LF will be replaced by CRLF in file.txt
```

**Solution:**
```bash
# Configure line ending handling
git config --global core.autocrlf true

# Add .gitattributes to repository
echo "* text=auto" > .gitattributes
git add .gitattributes
git commit -m "Add .gitattributes"
```

### Issue 2: Permission Changes Showing as Modified

**Problem:**
```
modified:   script.sh (mode change 100644 => 100755)
```

**Solution:**
```bash
# Disable filemode tracking
git config core.filemode false
```

### Issue 3: Filename Too Long

**Problem:**
```
error: unable to create file: Filename too long
```

**Solution:**
```bash
# Enable long paths
git config --global core.longpaths true
```

### Issue 4: SSL Certificate Errors

**Problem:**
```
SSL certificate problem: unable to get local issuer certificate
```

**Solution:**
```bash
# Temporary fix (not recommended for production)
git config --global http.sslVerify false

# Better solution: Update Git or install proper certificates
```

### Issue 5: Slow Git Operations

**Problem:**
Git commands are slow on Windows

**Solutions:**
```bash
# Disable Git status in PowerShell prompt
# (if using posh-git)

# Use Git Bash instead of PowerShell for Git operations

# Exclude antivirus scanning for .git directory

# Enable Git's built-in file system cache
git config --global core.fscache true

# Enable parallel index preload
git config --global core.preloadindex true
```

## Best Practices for Windows

### 1. Use .gitattributes

Always include `.gitattributes` in your repository:

```
* text=auto
*.sh text eol=lf
*.bat text eol=crlf
*.ps1 text eol=crlf
*.png binary
*.jpg binary
```

### 2. Configure Git Properly

```bash
# Line endings
git config --global core.autocrlf true

# Long paths
git config --global core.longpaths true

# File mode
git config --global core.filemode false

# Performance
git config --global core.fscache true
git config --global core.preloadindex true

# Default editor (VS Code)
git config --global core.editor "code --wait"
```

### 3. Use Git Bash for Git Operations

- More reliable than PowerShell for Git
- Consistent with Unix/Mac workflows
- Better for scripting

### 4. Exclude .git from Antivirus

Add `.git` directory to antivirus exclusions for better performance.

### 5. Use SSH Instead of HTTPS

```bash
# Generate SSH key
ssh-keygen -t ed25519 -C "your_email@example.com"

# Add to ssh-agent
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519

# Add public key to GitHub/GitLab
cat ~/.ssh/id_ed25519.pub

# Clone with SSH
git clone git@github.com:user/repo.git
```

### 6. Use Git Credential Manager

Git for Windows includes Git Credential Manager:

```bash
# Should be enabled by default
git config --global credential.helper manager

# Test by cloning a private repo
# Credentials will be stored securely
```

## PowerShell vs Git Bash Comparison

| Feature | PowerShell | Git Bash |
|---------|-----------|----------|
| Git operations | ✓ Works | ✓ Better |
| Unix commands | ✗ Limited | ✓ Full support |
| Windows integration | ✓ Excellent | ✗ Limited |
| Scripting | ✓ PowerShell | ✓ Bash |
| Performance | ✓ Fast | ✓ Fast |
| Learning curve | Medium | Easy (if know Unix) |

**Recommendation:**
- Use Git Bash for Git operations and Unix-style scripting
- Use PowerShell for Windows-specific tasks and automation

## Troubleshooting Commands

```bash
# Check Git configuration
git config --list --show-origin

# Check line ending configuration
git config core.autocrlf

# Check file mode configuration
git config core.filemode

# Check long paths configuration
git config core.longpaths

# Verify Git installation
git --version

# Check Git Bash version
bash --version

# Check PowerShell version
$PSVersionTable.PSVersion
```

## Resources

- [Git for Windows](https://gitforwindows.org/)
- [Git Configuration](https://git-scm.com/book/en/v2/Customizing-Git-Git-Configuration)
- [Git Attributes](https://git-scm.com/docs/gitattributes)
- [PowerShell Documentation](https://docs.microsoft.com/en-us/powershell/)
- [Git Credential Manager](https://github.com/GitCredentialManager/git-credential-manager)
