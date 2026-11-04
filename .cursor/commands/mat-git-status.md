# MAT Git Status

Provide a quick summary of the current git repository state.

## Usage

```
/mat-git-status
```

## Instructions

Run the following commands and summarize the results:

1. **Current branch** — `git branch --show-current`
2. **Working tree status** — `git status`
3. **Diff from origin/main** — `git diff HEAD origin/main` (if the remote exists)
4. **Recent commits** — `git log --oneline -10`
5. **Read README.md** — For project context

### Report Format

```
## Git Status Report

### Branch
<current branch name>

### Working Tree
- Staged: <count> files
- Modified: <count> files
- Untracked: <count> files

### Changed Files
<list of modified/staged/untracked files with status>

### Recent Commits
<last 10 commits, one-line format>

### Drift from origin/main
<summary of differences, or "up to date" / "remote not configured">

### Suggested Actions
- <any recommended next steps based on the state>
```

---

## Rules

- Read-only — do NOT make any commits or changes
- If origin/main does not exist, note it and skip the diff
- Keep the summary concise and actionable
