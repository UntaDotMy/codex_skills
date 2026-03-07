# Merge Conflict Resolution

## Understanding Merge Conflicts

### What is a Merge Conflict?

A merge conflict occurs when Git cannot automatically resolve differences between two commits. This happens when:
- Two branches modify the same line in a file
- One branch deletes a file while another modifies it
- Two branches create files with the same name

### When Do Conflicts Occur?

**During Merge:**
```bash
git checkout main
git merge feature-branch
# CONFLICT (content): Merge conflict in file.txt
```

**During Rebase:**
```bash
git checkout feature-branch
git rebase main
# CONFLICT (content): Merge conflict in file.txt
```

**During Cherry-Pick:**
```bash
git cherry-pick abc123
# CONFLICT (content): Merge conflict in file.txt
```

**During Pull:**
```bash
git pull origin main
# CONFLICT (content): Merge conflict in file.txt
```

## Merge vs Rebase: When to Use What

### Merge

**What it does:**
- Creates a merge commit
- Preserves complete history
- Shows when branches were merged

**When to use:**
- Merging feature branches into main
- Integrating changes from main into feature branch
- When history preservation is important
- When working on shared branches

**Pros:**
- Safe (non-destructive)
- Preserves context
- Easy to understand

**Cons:**
- Creates merge commits (cluttered history)
- Non-linear history

**Example:**
```bash
git checkout main
git merge feature-branch
```

**Result:**
```
*   Merge branch 'feature-branch' into main
|\
| * Feature commit 2
| * Feature commit 1
* | Main commit 2
* | Main commit 1
|/
* Common ancestor
```

### Rebase

**What it does:**
- Replays commits on top of another branch
- Rewrites history
- Creates linear history

**When to use:**
- Updating feature branch with latest main
- Cleaning up local commits before pushing
- When linear history is preferred
- **NEVER on shared/public branches**

**Pros:**
- Clean, linear history
- Easier to follow
- No merge commits

**Cons:**
- Rewrites history (dangerous on shared branches)
- Can lose context
- More complex conflict resolution

**Example:**
```bash
git checkout feature-branch
git rebase main
```

**Result:**
```
* Feature commit 2 (rebased)
* Feature commit 1 (rebased)
* Main commit 2
* Main commit 1
* Common ancestor
```

### Decision Matrix

| Scenario | Use Merge | Use Rebase |
|----------|-----------|------------|
| Integrating feature into main | ✓ | ✗ |
| Updating feature with latest main | ✓ | ✓ |
| Cleaning up local commits | ✗ | ✓ |
| Working on shared branch | ✓ | ✗ |
| Working on private branch | ✓ | ✓ |
| Want to preserve history | ✓ | ✗ |
| Want linear history | ✗ | ✓ |

**Golden Rule:** Never rebase commits that have been pushed to a shared branch.

## Identifying Conflicts

### Check Status

```bash
git status
```

**Output:**
```
On branch main
You have unmerged paths.
  (fix conflicts and run "git commit")
  (use "git merge --abort" to abort the merge)

Unmerged paths:
  (use "git add <file>..." to mark resolution)
        both modified:   src/app.js
        both modified:   README.md

no changes added to commit
```

### View Conflicted Files

```bash
# List conflicted files
git diff --name-only --diff-filter=U

# Show conflicts
git diff
```

## Conflict Markers

### Understanding the Markers

```javascript
<<<<<<< HEAD (Current Change)
const greeting = "Hello, World!";
=======
const greeting = "Hi there!";
>>>>>>> feature-branch (Incoming Change)
```

**Breakdown:**
- `<<<<<<< HEAD`: Start of your changes (current branch)
- `=======`: Separator between changes
- `>>>>>>> feature-branch`: End of incoming changes (other branch)

### Multiple Conflicts in Same File

```javascript
// Conflict 1
<<<<<<< HEAD
function add(a, b) {
  return a + b;
}
=======
function sum(a, b) {
  return a + b;
}
>>>>>>> feature-branch

// Conflict 2
<<<<<<< HEAD
const result = add(2, 3);
=======
const result = sum(2, 3);
>>>>>>> feature-branch
```

## Resolving Conflicts

### Manual Resolution

**1. Open the conflicted file**

**2. Choose which changes to keep:**

**Option A: Keep your changes (HEAD)**
```javascript
const greeting = "Hello, World!";
```

**Option B: Keep their changes (incoming)**
```javascript
const greeting = "Hi there!";
```

**Option C: Keep both (combine)**
```javascript
const greeting = "Hello, World!";
const alternativeGreeting = "Hi there!";
```

**Option D: Write new solution**
```javascript
const greeting = "Hello there, World!";
```

**3. Remove conflict markers**

Remove `<<<<<<<`, `=======`, and `>>>>>>>` lines.

**4. Stage the resolved file**
```bash
git add src/app.js
```

**5. Continue the merge/rebase**
```bash
# For merge
git commit

# For rebase
git rebase --continue
```

### Using Git Commands

**Accept yours (current branch):**
```bash
git checkout --ours src/app.js
git add src/app.js
```

**Accept theirs (incoming branch):**
```bash
git checkout --theirs src/app.js
git add src/app.js
```

**Note:** `--ours` and `--theirs` are swapped during rebase!

### Using Merge Tools

**Configure merge tool:**
```bash
# VS Code
git config --global merge.tool vscode
git config --global mergetool.vscode.cmd 'code --wait $MERGED'

# Vim
git config --global merge.tool vimdiff

# Meld (GUI)
git config --global merge.tool meld
```

**Launch merge tool:**
```bash
git mergetool
```

**VS Code Merge Editor:**
- Shows 3-way diff (yours, theirs, result)
- Click "Accept Current Change" or "Accept Incoming Change"
- Or manually edit the result
- Save and close

## Conflict Resolution Strategies

### Strategy 1: Accept All Yours

```bash
# Accept all conflicts from current branch
git merge -X ours feature-branch

# Or during conflict
git checkout --ours .
git add .
git commit
```

### Strategy 2: Accept All Theirs

```bash
# Accept all conflicts from incoming branch
git merge -X theirs feature-branch

# Or during conflict
git checkout --theirs .
git add .
git commit
```

### Strategy 3: Manual Review (Recommended)

Review each conflict individually and make informed decisions.

### Strategy 4: Abort and Retry

```bash
# Abort merge
git merge --abort

# Abort rebase
git rebase --abort

# Abort cherry-pick
git cherry-pick --abort
```

## Complex Conflict Scenarios

### Scenario 1: File Deleted in One Branch, Modified in Another

**Conflict:**
```
CONFLICT (modify/delete): file.txt deleted in HEAD and modified in feature-branch
```

**Resolution:**
```bash
# Keep the file (modified version)
git add file.txt

# Delete the file
git rm file.txt

# Then continue
git commit
```

### Scenario 2: File Renamed in One Branch, Modified in Another

**Conflict:**
```
CONFLICT (rename/modify): file.txt renamed to newfile.txt in HEAD and modified in feature-branch
```

**Resolution:**
```bash
# Git usually handles this automatically
# If not, manually resolve and stage
git add newfile.txt
git commit
```

### Scenario 3: Binary File Conflicts

**Problem:** Can't merge binary files (images, PDFs, etc.)

**Resolution:**
```bash
# Choose one version
git checkout --ours image.png
# or
git checkout --theirs image.png

git add image.png
git commit
```

### Scenario 4: Multiple Conflicts Across Many Files

**Strategy:**
1. Resolve one file at a time
2. Test after each resolution
3. Stage resolved files incrementally
4. Use `git status` frequently

```bash
# Resolve file1.js
git add file1.js

# Resolve file2.js
git add file2.js

# Check remaining conflicts
git status

# Continue when all resolved
git commit
```

## Best Practices

### 1. Communicate with Team

Before resolving conflicts:
- Understand why the conflict occurred
- Talk to the person who made the conflicting changes
- Agree on the resolution approach

### 2. Test After Resolution

```bash
# After resolving conflicts
npm test
npm run build

# Ensure everything works
```

### 3. Keep Commits Small

Smaller commits = fewer conflicts

### 4. Pull/Rebase Frequently

```bash
# Update your branch regularly
git pull origin main
# or
git fetch origin
git rebase origin/main
```

### 5. Use Feature Branches

- Keep main stable
- Work on feature branches
- Merge when ready

### 6. Review Conflicts Carefully

Don't blindly accept one side. Understand the changes.

### 7. Use .gitattributes for Merge Strategies

```
# .gitattributes
package-lock.json merge=ours
yarn.lock merge=ours
```

## Preventing Conflicts

### 1. Coordinate with Team

- Communicate about what you're working on
- Avoid working on the same files simultaneously
- Use code ownership (CODEOWNERS file)

### 2. Modularize Code

- Small, focused files
- Clear module boundaries
- Reduce coupling

### 3. Pull Before Push

```bash
git pull origin main
# Resolve any conflicts
git push origin main
```

### 4. Use Linting and Formatting

- Consistent code style prevents formatting conflicts
- Use Prettier, ESLint, etc.
- Configure in .editorconfig

### 5. Rebase Feature Branches Regularly

```bash
# Keep feature branch up to date
git checkout feature-branch
git rebase main
```

## When to Ask for Help

**Ask for help when:**
- Conflict involves critical business logic
- You don't understand the conflicting changes
- Conflict affects many files
- You're unsure which version is correct
- Conflict involves code you didn't write

**How to ask:**
- Describe the conflict clearly
- Show the conflicting code
- Explain what you're trying to achieve
- Ask the original author if possible

## Troubleshooting

### Conflict Markers Still Present After Resolution

**Problem:** Forgot to remove `<<<<<<<`, `=======`, `>>>>>>>` markers

**Solution:**
```bash
# Search for conflict markers
grep -r "<<<<<<< HEAD" .
grep -r "=======" .
grep -r ">>>>>>>" .

# Remove them manually
```

### Accidentally Committed Conflict Markers

**Problem:** Committed file with conflict markers

**Solution:**
```bash
# Fix the file
# Remove conflict markers

# Amend the commit (if not pushed)
git add file.txt
git commit --amend

# Or create a new commit (if pushed)
git add file.txt
git commit -m "Fix: Remove conflict markers"
```

### Lost Changes During Conflict Resolution

**Problem:** Accidentally deleted important changes

**Solution:**
```bash
# Check reflog
git reflog

# Find the commit before conflict
git show HEAD@{1}

# Restore if needed
git reset --hard HEAD@{1}
```

### Merge/Rebase Taking Too Long

**Problem:** Too many conflicts, getting overwhelmed

**Solution:**
```bash
# Abort and try a different approach
git merge --abort
# or
git rebase --abort

# Try merging instead of rebasing
# Or break into smaller merges
```

## Tools and Resources

### GUI Tools

- **VS Code**: Built-in merge editor
- **GitKraken**: Visual merge conflict resolution
- **Sourcetree**: Visual Git client with merge tools
- **Meld**: 3-way merge tool
- **Beyond Compare**: Commercial merge tool

### Command Line Tools

```bash
# View conflicts
git diff

# List conflicted files
git diff --name-only --diff-filter=U

# Show conflict in specific file
git diff file.txt

# Use merge tool
git mergetool
```

### Learning Resources

- [Git Documentation - Merge Conflicts](https://git-scm.com/docs/git-merge#_how_conflicts_are_presented)
- [Atlassian Git Tutorial - Merge Conflicts](https://www.atlassian.com/git/tutorials/using-branches/merge-conflicts)
- [GitHub Docs - Resolving Merge Conflicts](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/addressing-merge-conflicts)

## Summary

**Key Takeaways:**
1. Understand merge vs rebase trade-offs
2. Never rebase shared branches
3. Resolve conflicts carefully, don't rush
4. Test after resolution
5. Communicate with team
6. Pull frequently to minimize conflicts
7. Use appropriate tools for your workflow
8. When in doubt, ask for help

**Quick Reference:**
```bash
# Check conflicts
git status

# Resolve manually
# Edit files, remove markers

# Stage resolved files
git add <file>

# Continue
git commit  # for merge
git rebase --continue  # for rebase

# Abort if needed
git merge --abort
git rebase --abort
```
