---
name: tmux-nvim-review
description: Open files changed by Codex in a new tmux pane with nvim so the user can review edits from their CLI workflow. Use after coding changes when the user wants a tmux/nvim review pane, or when they ask to review agent edits in Vim/Neovim.
---

# Tmux Nvim Review

## Overview

Open the files Codex changed in a new tmux pane using `nvim`, so the user can review edits without manually launching an editor.

## Workflow

1. Finish the requested code changes and run the required verification first.
2. Identify the exact files changed in the current agent turn.
   - Pass those files explicitly to the script.
   - Do not rely on broad Git dirty-state scanning; the user's workspace may already contain unrelated changes.
   - Skip generated caches, deleted files, directories, secrets, and unrelated files.
3. Run `scripts/open_review_pane.py` from this skill.
4. Report whether the pane opened, and include the fallback `nvim` command if tmux or nvim is unavailable.

## Script

Script: `scripts/open_review_pane.py`

Open the files changed in the current turn:

```bash
python3 scripts/open_review_pane.py README.md src/app.ts
```

Preview the tmux command without opening a pane:

```bash
python3 scripts/open_review_pane.py --dry-run README.md src/app.ts
```

Open the pane below instead of on the right:

```bash
python3 scripts/open_review_pane.py --direction below README.md src/app.ts
```

## Behavior

- The script requires explicit file arguments and never auto-opens every dirty Git file.
- It requires `tmux` and `nvim`; when either is missing, it prints the exact editor command to run manually.
- It creates a side-by-side tmux pane by default. Use `--direction below` for a bottom pane.
- It exits after creating the pane; it does not wait for the user to finish reviewing.
- It does not commit, push, or modify files.
