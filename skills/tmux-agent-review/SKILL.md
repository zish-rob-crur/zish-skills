---
name: tmux-agent-review
description: Run a multi-round adversarial review of a plan or code design with Codex or Claude Code in a visible tmux pane. Use when the user asks for a cross-agent, adversarial, or second-opinion review inside tmux.
---

# Tmux Agent Review

## Overview

You are the requester. `scripts/agent_review.py` sends a review brief to the other agent in a tmux pane next to yours and hands back its verdict file. When Codex runs this skill, Claude Code reviews; when Claude Code runs it, Codex reviews. The pane stays interactive, so the user can watch and step in at any time.

The script handles one round per `send` + `wait`. You drive the rounds.

Replace `<skill-dir>` below with the absolute path of the directory that contains this `SKILL.md`. Run every command from the repo or worktree under review, not from `<skill-dir>`: the script puts `.agent-review/` in the current git root.

## Requirements

- Run inside tmux, or pass `--target` or `--pane`.
- The reviewer starts by typing `codex` or `claude` into an interactive shell, so the user's aliases apply. Override with `AGENT_REVIEW_CODEX_CMD` or `AGENT_REVIEW_CLAUDE_CMD`.
- The reviewer writes to `.agent-review/<session>/` in the repo root. If its permission mode asks first, the user approves in the pane. The script adds `/.agent-review/` to `.git/info/exclude`.

## Workflow

1. Pick a short session slug. Omit `--agent` unless the user names a reviewer. Pass `--pane` only when the user points at a pane, such as "use the pane on the right" (`{right-of}`) or "pane 3" (`.3`); the reviewer is whatever agent runs there. Otherwise the script detects the caller and picks the other agent.
2. Write the round 1 brief from the template below.
   - Point to files, docs, and commands such as `git diff main...HEAD` instead of pasting them; the reviewer shares the worktree.
   - Always fill in Review focus and Settled / out of scope. They keep the reviewer on the questions that matter instead of drifting into details.
3. Send the brief through stdin so no stray brief files land in the repo:

   ```bash
   python3 <skill-dir>/scripts/agent_review.py send --session <slug> --message-file - <<'BRIEF'
   # Review brief: ...
   BRIEF
   ```

   The script picks the reviewer pane in this order:
   1. `--pane`.
   2. The pane this session used in earlier rounds.
   3. An idle pane in your window, inside this repo, that this skill already marked as the reviewer.
   4. A new split of the largest pane in your window: side by side when that pane is wide, stacked otherwise. The existing layout is left alone.

   The chosen pane gets the tmux pane option `@agent-review`. Unmarked panes are never picked automatically, because the user may be using them for other work. Busy panes are never used, and `--new-pane` forces a split.

4. Wait:

   ```bash
   python3 <skill-dir>/scripts/agent_review.py wait --session <slug>
   ```

   Claude Code can run this in the background. On exit 3, run it again.
5. Adjudicate every blocker and major finding. Verify each one against the code yourself before deciding:
   - ACCEPTED: fix it and note what changed.
   - REJECTED: give evidence (`path:line`, command output, a stated requirement). Do not concede because the reviewer sounds confident, and do not reject a finding just to finish.
   - DEFERRED: the user must decide.

   Edit scope: revise the plan or design docs by default. Edit code only when the user's request authorizes it. Minor items never justify another round; list them in the final report.
6. If the verdict is REVISE and you accepted or rejected a blocker or major, write a response brief and send it with the same `--session`. The same pane is reused, so the reviewer keeps its context.
7. Stop when any of these holds:
   - The verdict is APPROVE.
   - The verdict is BLOCKED, or only DEFERRED items remain.
   - The same disagreement repeats without new evidence.
   - Three rounds are done, unless the user set another limit.
8. Report to the user:
   - The final verdict and the number of rounds.
   - Accepted changes.
   - Rejected findings and why.
   - Open disagreements and questions that need their decision.
   - The `.agent-review/<slug>/` path.

   Leave the reviewer pane open.

## Human Intervention

- The user's messages in the reviewer pane override the protocol.
- `wait` exit 4 means the reviewer stopped without writing a result: it was interrupted, redirected, or is asking something. Read the printed pane tail, then follow the user's new direction or ask the user. Do not resend the same round blindly.
- `peek --session <slug>` prints the last pane lines at any time. `wait` and `peek` default to the most recently sent session.

## Brief Templates

Round 1:

```markdown
# Review brief: <title>

## Goal
<the problem and what success looks like>

## Material
- <plan doc, files, or `git diff main...HEAD`>

## Review focus
1. <the one to three questions that matter most>

## Settled / out of scope
- <decisions and constraints not to reopen>
```

Round 2 and later:

```markdown
# Round <N> response: <title>

## Response to round <N-1>
1. [major] <finding> — ACCEPTED: <what changed, where>
2. [blocker] <finding> — REJECTED: <evidence>
3. [major] <finding> — DEFERRED: <decision the user must make>

## Changed since last round
- <files or doc sections to re-check>
```

`send` appends the reviewer protocol to every brief, so do not restate it. The protocol covers top-down review, evidence plus a concrete consequence for each finding, at most five blocker/major and three minor findings, the verdict format, and the atomic file write.

## Script Reference

`send`
- `--agent codex|claude` overrides the reviewer.
- `--pane <target>` accepts any tmux pane target (`%12`, `.3`, `{right-of}`, `{down-of}`), uses that pane, and marks it. If it runs a shell, the agent is launched there. It cannot be the requester's own pane.
- `--new-pane` skips reusing a marked reviewer pane. Unmark a pane with `tmux set-option -pu -t <target> @agent-review`.
- `--direction auto|right|below` sets how a new split cuts the largest pane.
- Refuses a busy pane.
- Fails with the pane tail if the agent shows a trust prompt or the request never starts.

`wait` exit codes:

| Code | Meaning |
| --- | --- |
| 0 | Review printed. |
| 2 | Error, such as the reviewer pane being gone. |
| 3 | Timeout (`--timeout`, default 540s) while the reviewer is still working. Run `wait` again. |
| 4 | The pane went idle (`--idle`, default 30s) without a review file. |
| 5 | The first line is not `VERDICT: APPROVE\|REVISE\|BLOCKED`. Treat the round as not approved. |
