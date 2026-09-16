---
name: tmux-peer-agent
description: Hand a design review or a coding task to the other agent (Codex or Claude Code) in a visible tmux pane and get its result back. Use when the user asks for a cross-agent, adversarial, or second-opinion review, or wants the other agent to do a piece of work.
---

# Tmux Peer Agent

## Overview

You are the requester. `scripts/peer_agent.py` sends a brief to the other agent in a tmux pane next to yours and hands back its result file. When Codex runs this skill, Claude Code is the peer; when Claude Code runs it, Codex is. The pane stays interactive, so the user can watch and step in at any time.

Two modes:

- `--mode review` (default): the peer critiques a plan or code design and edits nothing. It answers with `VERDICT: APPROVE | REVISE | BLOCKED`.
- `--mode task`: the peer does the work in this worktree. It answers with `STATUS: DONE | PARTIAL | BLOCKED`, listing what it changed and how it verified.

The script handles one round per `send` + `wait`. You drive the rounds.

Replace `<skill-dir>` below with the absolute path of the directory that contains this `SKILL.md`. Run every command from the repo or worktree being worked on, not from `<skill-dir>`: the script puts `.peer-agent/` in the current git root.

## Requirements

- Run inside tmux, or pass `--target` or `--pane`.
- The peer starts by typing `codex` or `claude` into an interactive shell, so the user's aliases apply. Override with `PEER_AGENT_CODEX_CMD` or `PEER_AGENT_CLAUDE_CMD`.
- The peer writes to `.peer-agent/<session>/` in the repo root. If its permission mode asks first, the user approves in the pane. The script adds `/.peer-agent/` to `.git/info/exclude`.

## Send And Wait

1. Pick a short session slug. Omit `--agent` unless the user names one. Pass `--pane` only when the user points at a pane, such as "use the pane on the right" (`{right-of}`) or "pane 3" (`.3`); then the peer is whatever agent runs there. Otherwise the script detects the caller and picks the other agent.
2. Write the brief from the matching template below. Point to files, docs, and commands such as `git diff main...HEAD` instead of pasting them; the peer shares the worktree.
3. Send the brief through stdin so no stray brief files land in the repo:

   ```bash
   python3 <skill-dir>/scripts/peer_agent.py send --mode task --session <slug> --message-file - <<'BRIEF'
   # Task: ...
   BRIEF
   ```

   The script picks the peer pane in this order:
   1. `--pane`.
   2. The pane this session used in earlier rounds.
   3. An idle pane in your window, inside this repo, that this skill already marked as the peer.
   4. A new split of the largest pane in your window: side by side when that pane is wide, stacked otherwise. The existing layout is left alone.

   The chosen pane gets the tmux pane option `@peer-agent`. Unmarked panes are never picked automatically, because the user may be using them for other work. Busy panes are never used, and `--new-pane` forces a split.

4. Wait:

   ```bash
   python3 <skill-dir>/scripts/peer_agent.py wait --session <slug>
   ```

   Claude Code can run this in the background. On exit 3, run it again.

## Review Mode

1. Fill in Review focus and Settled / out of scope. They keep the peer on the questions that matter instead of drifting into details.
2. Adjudicate every blocker and major finding. Verify each one against the code yourself before deciding:
   - ACCEPTED: fix it and note what changed.
   - REJECTED: give evidence (`path:line`, command output, a stated requirement). Do not concede because the peer sounds confident, and do not reject a finding just to finish.
   - DEFERRED: the user must decide.

   Edit scope: revise the plan or design docs by default. Edit code only when the user's request authorizes it. Minor items never justify another round; list them in the final report.
3. If the verdict is REVISE and you accepted or rejected a blocker or major, write a response brief and send it with the same `--session`. The same pane is reused, so the peer keeps its context.
4. Stop when any of these holds:
   - The verdict is APPROVE.
   - The verdict is BLOCKED, or only DEFERRED items remain.
   - The same disagreement repeats without new evidence.
   - Three rounds are done, unless the user set another limit.

Round 1 brief:

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

## Task Mode

1. Name the files the peer owns. You keep working in the same worktree, so **do not touch those files until its report arrives**, and give it work that does not overlap yours. If you cannot split the work cleanly, do it yourself instead.
2. Give it a definition of done and the commands that prove it. A task without a check comes back unverified.
3. When the report arrives, verify it yourself: read `git diff` for the files it names and run the verification commands. Treat the report as a claim, not as evidence.
4. Send a follow-up round with the same `--session` when the work is PARTIAL, a check fails, or your review finds problems. Say exactly what to fix and what to leave alone.
5. Stop when the work passes your own verification, when BLOCKED needs the user, or after three rounds. Then report to the user: what the peer changed, what you verified and how, and what is still open.

Round 1 brief:

```markdown
# Task: <title>

## Task
<what to build or change, and why>

## Scope
- <the files or directories the peer owns>
- Out of scope: <what it must not touch>

## Definition of done
- <observable result>

## Verification
- `<command>` → <expected result>

## Constraints
- <existing patterns to follow, decisions already made>
```

Round 2 and later:

```markdown
# Round <N> feedback: <title>

## Accepted
- <what is done and verified; leave it alone>

## To fix
1. <problem, evidence from the diff or a failing command, and what "fixed" means>

## Still out of scope
- <unchanged boundaries>
```

## Human Intervention

- The user's messages in the peer pane override the protocol.
- `wait` exit 4 means the peer stopped without writing a result: it was interrupted, redirected, or is asking something. Read the printed pane tail, then follow the user's new direction or ask the user. Do not resend the same round blindly.
- `peek --session <slug>` prints the last pane lines at any time. `wait` and `peek` default to the most recently sent session.

## Script Reference

`send`
- `--mode review|task` picks the protocol appended to the brief; a session stays in the mode it started with. Do not restate the protocol in the brief.
- `--agent codex|claude` overrides the peer.
- `--pane <target>` accepts any tmux pane target (`%12`, `.3`, `{right-of}`, `{down-of}`), uses that pane, and marks it. If it runs a shell, the agent is launched there. It cannot be the requester's own pane.
- `--new-pane` skips reusing a marked peer pane. Unmark a pane with `tmux set-option -pu -t <target> @peer-agent`.
- `--direction auto|right|below` sets how a new split cuts the largest pane.
- Refuses a busy pane.
- Fails with the pane tail if the agent shows a trust prompt or the request never starts.

`wait` exit codes:

| Code | Meaning |
| --- | --- |
| 0 | Result printed. |
| 2 | Error, such as the peer pane being gone. |
| 3 | Timeout (`--timeout`, default 540s) while the peer is still working. Run `wait` again. |
| 4 | The pane went idle (`--idle`, default 30s) without a result file. |
| 5 | The first line is not the expected `VERDICT:` or `STATUS:` line. Treat the round as unfinished. |
