#!/usr/bin/env python3
"""Drive a Codex or Claude Code peer in a tmux pane: review a design, or hand it a task."""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Callable, NoReturn


WORK_DIR = ".peer-agent"
PANE_MARK = "@peer-agent"  # tmux pane option naming the peer agent; only marked panes are reused
SHELLS = {"zsh", "bash", "fish", "sh", "dash", "-zsh", "-bash", "login"}
LAUNCH_ENV = {"codex": "PEER_AGENT_CODEX_CMD", "claude": "PEER_AGENT_CLAUDE_CMD"}
# Codex: "Working (9s • esc to interrupt)". Claude Code: "· Effecting… (13s · ↓ 267 tokens · ...)".
BUSY = re.compile(r"esc to interrupt|…\s*\((?:\d+[hms]\s*)+·", re.IGNORECASE)
STARTUP_TIMEOUT = 90
POLL_INTERVAL = 3
TRUST_PROMPT = re.compile(r"\btrust\b", re.IGNORECASE)
RESULT_NAME = {"review": "review", "task": "report"}
RESULT_LINE = {
    "review": re.compile(r"^VERDICT:\s*(APPROVE|REVISE|BLOCKED)\s*$"),
    "task": re.compile(r"^STATUS:\s*(DONE|PARTIAL|BLOCKED)\s*$"),
}

REVIEW_PROTOCOL = """

---

## Reviewer protocol (tmux-agent-review)

You are the adversarial reviewer. The requester is another coding agent in this
worktree. A human may also type in this pane; their messages override this protocol.

Goal: find what would make this plan or design fail, cause real rework, or cost more
complexity than it earns. Try to break it, not to polish it.

Review top-down, and do not descend to a lower level while material findings remain above it:
1. Direction: does it solve the stated goal? Wrong assumptions, missing requirements, a simpler approach.
2. Design: boundaries, data flow, failure modes, compatibility, migration, security, concurrency.
3. Implementation: only defects with a concrete failure scenario.

Rules:
- Stay inside the brief's review focus. Do not reopen settled or out-of-scope items
  unless you have evidence they break the goal.
- Verify against the code, docs, and commands; do not take the brief on trust.
- Every finding needs evidence and a concrete consequence ("when X, Y goes wrong").
  No consequence, no finding. Style, naming, and formatting are never findings.
- blocker: wrong direction, or it will fail. major: significant risk, rework, or needless
  complexity if not fixed now. minor: worth knowing; never blocks.
- Report at most 5 blocker/major findings, most severe first. List at most 3 minor items, one line each.
- Do not edit project files.

Session `{session}`, round {round}.{followup}

Verdict: APPROVE when no blocker or major remains; REVISE when the requester can fix them;
BLOCKED when progress needs a human decision or information neither agent has.

Write your result to `{out}` in the language of the brief. The first line must be the verdict:

```
VERDICT: APPROVE | REVISE | BLOCKED

## Findings
1. [blocker|major] <title>
   Evidence: `path:line`, command output, or doc reference
   Consequence: ...
   Suggestion: ...

## Minor
- ...

## Questions for the human
- ...
```

Write the file atomically: write `{out}.tmp`, then `mv {out}.tmp {out}`.
The requester is polling for `{out}`. After the move, reply here with one line:
`review written: {out}`.
"""

REVIEW_FOLLOWUP = """

This round answers your previous review ({previous}). Start Findings by marking each
earlier blocker/major RESOLVED, WITHDRAWN (the response convinced you), or MAINTAINED
(say why the response fails). Do not repeat a point without new evidence. Add a new
finding only if it is blocker or major."""


TASK_PROTOCOL = """

---

## Worker protocol (tmux-peer-agent)

You are the worker. Another coding agent in this worktree delegated the task above.
A human may also type in this pane; their messages override this protocol.

Rules:
- Work only inside the scope the brief gives you. The requester is working in the same
  worktree at the same time, so touching files outside your scope loses their work.
  If the task needs changes outside the scope, stop and report instead of widening it.
- Do not commit, push, stash, revert, or switch branches.
- Verify with the commands the brief names, and report their real output. Never report
  a check you did not run.
- When something blocks you, such as a missing decision, credential, or broken
  dependency, stop and report it instead of guessing around it.

Session `{session}`, round {round}.{followup}

Status: DONE when the whole scope is finished and verified; PARTIAL when some of it is;
BLOCKED when you could not start or continue.

Write your report to `{out}` in the language of the brief. The first line must be the status:

```
STATUS: DONE | PARTIAL | BLOCKED

## Changes
- `path:line` — what changed and why

## Verification
- <command> → <result>

## Left open
- <what remains, or a decision the requester or the human has to make>
```

Write the file atomically: write `{out}.tmp`, then `mv {out}.tmp {out}`.
The requester is polling for `{out}`. After the move, reply here with one line:
`report written: {out}`.
"""

TASK_FOLLOWUP = """

This round is feedback on your previous report ({previous}). Fix what it asks for and
leave the rest alone; do not redo work it accepted."""

PROTOCOLS = {"review": (REVIEW_PROTOCOL, REVIEW_FOLLOWUP), "task": (TASK_PROTOCOL, TASK_FOLLOWUP)}


def fail(message: str, code: int = 2) -> NoReturn:
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(code)


def tmux(*args: str, stdin: str | None = None) -> str:
    result = subprocess.run(["tmux", *args], input=stdin, text=True, capture_output=True)
    if result.returncode != 0:
        fail(f"tmux {args[0]} failed: {result.stderr.strip()}")
    return result.stdout.rstrip("\n")


def pane_info(pane: str) -> dict[str, str] | None:
    fmt = "#{pane_id}\t#{pane_dead}\t#{pane_in_mode}\t#{pane_current_command}"
    result = subprocess.run(
        ["tmux", "display-message", "-p", "-t", pane, fmt], text=True, capture_output=True
    )
    parts = result.stdout.rstrip("\n").split("\t")
    if result.returncode != 0 or len(parts) != 4 or parts[0] != pane or parts[1] == "1":
        return None
    return {"id": parts[0], "in_mode": parts[2], "command": parts[3]}


def capture(pane: str) -> str:
    return tmux("capture-pane", "-p", "-t", pane).rstrip()


def tail(pane: str, lines: int) -> str:
    return "\n".join(capture(pane).splitlines()[-lines:])


def wait_for(predicate: Callable[[], bool], timeout: float, interval: float = 0.5) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(interval)
    return False


def project_root() -> Path:
    result = subprocess.run(["git", "rev-parse", "--show-toplevel"], text=True, capture_output=True)
    return Path(result.stdout.strip()) if result.returncode == 0 else Path.cwd()


def exclude_review_dir(root: Path) -> None:
    result = subprocess.run(
        ["git", "rev-parse", "--git-path", "info/exclude"], cwd=root, text=True, capture_output=True
    )
    if result.returncode != 0:
        return
    exclude = root / result.stdout.strip()
    lines = exclude.read_text().splitlines() if exclude.exists() else []
    if f"/{WORK_DIR}/" not in lines:
        exclude.parent.mkdir(parents=True, exist_ok=True)
        with exclude.open("a") as handle:
            handle.write(f"/{WORK_DIR}/\n")


def session_dir(session: str | None) -> Path:
    if session:
        return project_root() / WORK_DIR / session
    states = sorted((project_root() / WORK_DIR).glob("*/state.json"), key=lambda path: path.stat().st_mtime)
    if not states:
        fail(f"no sessions under {project_root() / WORK_DIR}")
    return states[-1].parent


def load_state(directory: Path) -> dict:
    path = directory / "state.json"
    return json.loads(path.read_text()) if path.exists() else {}


def start_agent(pane: str, agent: str) -> None:
    command = os.environ.get(LAUNCH_ENV[agent], agent)
    # Type into an interactive shell so the user's aliases apply and the pane survives agent exit.
    wait_for(lambda: capture(pane) != "", 10)
    tmux("send-keys", "-t", pane, "-l", command)
    tmux("send-keys", "-t", pane, "Enter")

    if not wait_for(lambda: (pane_info(pane) or {}).get("command") not in SHELLS, STARTUP_TIMEOUT):
        fail(f"`{command}` did not start in pane {pane}:\n{tail(pane, 20)}")

    previous = ""
    stable_checks = 0
    deadline = time.monotonic() + STARTUP_TIMEOUT
    while stable_checks < 2:
        if time.monotonic() > deadline:
            fail(f"{agent} in pane {pane} never settled:\n{tail(pane, 20)}")
        time.sleep(1)
        screen = capture(pane)
        stable_checks = stable_checks + 1 if screen and screen == previous else 0
        previous = screen

    if TRUST_PROMPT.search(previous):
        fail(f"{agent} in pane {pane} shows a trust prompt. Answer it there, then rerun send with --pane {pane}.")


def submit(pane: str, text: str, out: Path) -> None:
    if pane_info(pane)["in_mode"] == "1":  # type: ignore[index]
        tmux("send-keys", "-t", pane, "-X", "cancel")
    if BUSY.search(capture(pane)):
        fail(f"pane {pane} is busy; wait for it to finish or pass another --pane")

    buffer = f"agent-review-{os.getpid()}"
    tmux("load-buffer", "-b", buffer, "-", stdin=text)
    tmux("paste-buffer", "-p", "-d", "-b", buffer, "-t", pane)
    for _ in range(2):
        # An Enter that arrives with the end of a bracketed paste is swallowed by both TUIs.
        time.sleep(1)
        tmux("send-keys", "-t", pane, "Enter")
        if wait_for(lambda: out.exists() or bool(BUSY.search(capture(pane))), 6):
            return
    fail(f"the request did not start in pane {pane}; check the pane:\n{tail(pane, 20)}")


def command_agent(command: str) -> str | None:
    words = command.split()
    for word in words[:2]:  # the binary itself, or a script run by node
        name = Path(word).name
        if name == "codex" or name.startswith("codex-"):
            return "codex"
        if name == "claude" or "/claude/versions/" in word:
            return "claude"
    return None


def caller_agent() -> str | None:
    """Find the nearest Codex or Claude Code process that ran this script."""
    result = subprocess.run(["ps", "-axo", "pid=,ppid=,command="], text=True, capture_output=True)
    processes = {}
    for line in result.stdout.splitlines():
        parts = line.split(None, 2)
        if len(parts) == 3:
            processes[parts[0]] = (parts[1], parts[2])
    pid = str(os.getppid())
    while pid in processes and pid not in {"0", "1"}:
        parent, command = processes[pid]
        agent = command_agent(command)
        if agent:
            return agent
        pid = parent
    return None


def pane_agent(command: str) -> str | None:
    # Claude Code shows up in tmux as its version number, e.g. "2.1.272".
    if command == "claude" or re.fullmatch(r"\d+\.\d+\.\d+", command):
        return "claude"
    return "codex" if command == "codex" or command.startswith("codex-") else None


def find_idle_pane(agent: str, root: Path, target: str) -> tuple[str | None, list[str]]:
    """Return an idle peer pane marked for this agent in the target's window and repo, plus busy ones."""
    fmt = f"#{{pane_id}}\t#{{{PANE_MARK}}}\t#{{pane_current_command}}\t#{{pane_current_path}}"
    busy = []
    for line in tmux("list-panes", "-t", target, "-F", fmt).splitlines():
        pane, mark, command, path = line.split("\t", 3)
        inside = Path(path).resolve() == root.resolve() or root.resolve() in Path(path).resolve().parents
        running = pane_agent(command) == agent or command in SHELLS
        if pane == target or mark != agent or not running or not inside:
            continue
        if BUSY.search(capture(pane)):
            busy.append(pane)
        else:
            return pane, busy
    return None, busy


def resolve_pane(target: str) -> str:
    """Turn any tmux target ("%12", ".3", "{right-of}") into a live pane id."""
    result = subprocess.run(["tmux", "display-message", "-p", "-t", target, "#{pane_id}"], text=True, capture_output=True)
    pane = result.stdout.strip()
    if result.returncode != 0 or not pane_info(pane):
        fail(f"pane {target} does not exist")
    return pane


def split_largest_pane(target: str, root: Path, direction: str) -> str:
    fmt = "#{pane_id}\t#{pane_width}\t#{pane_height}"
    panes = [line.split("\t") for line in tmux("list-panes", "-t", target, "-F", fmt).splitlines()]
    pane, width, height = max(panes, key=lambda row: int(row[1]) * int(row[2]))
    if direction == "auto":
        # Terminal cells are about twice as tall as wide; only split side by side when both halves stay wide.
        direction = "right" if int(width) > 2.5 * int(height) else "below"
    split = "-h" if direction == "right" else "-v"
    return tmux("split-window", split, "-d", "-t", pane, "-c", str(root), "-P", "-F", "#{pane_id}")


def choose_pane(args: argparse.Namespace, state: dict, agent: str, root: Path, caller_pane: str) -> str:
    if state.get("pane"):
        if pane_info(state["pane"]):
            return state["pane"]
        print(f"note: previous peer pane {state['pane']} is gone", file=sys.stderr)
    if not args.new_pane:
        pane, busy = find_idle_pane(agent, root, caller_pane)
        if pane:
            print(f"note: reusing idle {agent} peer pane {pane}", file=sys.stderr)
            return pane
        if busy:
            print(f"note: {agent} peer pane(s) {', '.join(busy)} busy; opening a new pane", file=sys.stderr)
    return split_largest_pane(caller_pane, root, args.direction)


def cmd_send(args: argparse.Namespace) -> int:
    root = project_root()
    session = args.session or datetime.now().strftime("%Y%m%d-%H%M%S")
    directory = root / WORK_DIR / session
    state = load_state(directory)

    mode = args.mode or state.get("mode", "review")
    if state and mode != state.get("mode", "review"):
        fail(f"session {session} is a {state.get('mode', 'review')} session")

    body = sys.stdin.read() if args.message_file == "-" else Path(args.message_file).read_text()
    if not body.strip():
        fail("brief is empty")

    target = args.target or os.environ.get("TMUX_PANE")
    if not target and not args.pane:
        fail("not inside tmux; pass --target or --pane")
    caller_pane = resolve_pane(target) if target else None
    pane = resolve_pane(args.pane) if args.pane else None
    if pane and pane == caller_pane:
        fail(f"pane {args.pane} is the requester's own pane")

    agent = args.agent or state.get("agent") or (pane and pane_agent(pane_info(pane)["command"]))  # type: ignore[index]
    if not agent:
        caller = caller_agent()
        if not caller:
            fail("cannot tell whether Codex or Claude Code is calling; pass --agent")
        agent = "claude" if caller == "codex" else "codex"
    if state and agent != state["agent"]:
        fail(f"session {session} already uses {state['agent']}")

    pane = pane or choose_pane(args, state, agent, root, caller_pane)  # type: ignore[arg-type]
    running = pane_agent(pane_info(pane)["command"])  # type: ignore[index]
    if running and running != agent:
        fail(f"pane {pane} runs {running}, not {agent}")
    tmux("set-option", "-p", "-t", pane, PANE_MARK, agent)
    if pane_info(pane)["command"] in SHELLS:  # type: ignore[index]
        start_agent(pane, agent)

    round_number = state.get("round", 0) + 1
    protocol, follow = PROTOCOLS[mode]
    out = directory / f"round-{round_number}.{RESULT_NAME[mode]}.md"
    request = directory / f"round-{round_number}.request.md"
    followup = follow.format(previous=directory / f"round-{round_number - 1}.{RESULT_NAME[mode]}.md") if round_number > 1 else ""

    directory.mkdir(parents=True, exist_ok=True)
    exclude_review_dir(root)
    request.write_text(body.rstrip() + protocol.format(session=session, round=round_number, followup=followup, out=out))
    out.unlink(missing_ok=True)

    (directory / "state.json").write_text(
        json.dumps({"agent": agent, "mode": mode, "pane": pane, "round": round_number}, indent=2) + "\n"
    )
    kind = "Adversarial review request" if mode == "review" else "Task request"
    submit(pane, f"{kind}: read {request} and follow the protocol at the end of it.", out)

    print(f"session: {session}\nagent: {agent}\nmode: {mode}\npane: {pane}\nround: {round_number}")
    print(f"request: {request}\nresult: {out}")
    return 0


def cmd_wait(args: argparse.Namespace) -> int:
    directory = session_dir(args.session)
    state = load_state(directory)
    if not state:
        fail(f"no session state in {directory}")
    pane = state["pane"]
    mode = state.get("mode", "review")
    out = directory / f"round-{args.round or state['round']}.{RESULT_NAME[mode]}.md"

    deadline = time.monotonic() + args.timeout
    idle_since: float | None = None
    previous = ""
    while not out.exists():
        if not pane_info(pane):
            fail(f"peer pane {pane} is gone and {out} was never written")
        screen = capture(pane)
        if BUSY.search(screen) or screen != previous:
            idle_since = None
        elif idle_since is None:
            idle_since = time.monotonic()
        elif time.monotonic() - idle_since >= args.idle:
            print(f"idle: {state['agent']} stopped without writing {out}. A human may have stepped in, "
                  f"or it is waiting for input. Last lines of pane {pane}:\n")
            print(tail(pane, 40))
            return 4
        previous = screen
        if time.monotonic() > deadline:
            print(f"timeout: {out} is not written yet and {state['agent']} is still working. Run wait again.")
            return 3
        time.sleep(POLL_INTERVAL)

    text = out.read_text()
    print(f"# {out}\n\n{text}")
    first_line = next((line for line in text.splitlines() if line.strip()), "")
    if not RESULT_LINE[mode].match(first_line.strip()):
        expected = "VERDICT: APPROVE|REVISE|BLOCKED" if mode == "review" else "STATUS: DONE|PARTIAL|BLOCKED"
        print(f"\nerror: first line is not `{expected}`; treat this round as unfinished.", file=sys.stderr)
        return 5
    return 0


def cmd_peek(args: argparse.Namespace) -> int:
    directory = session_dir(args.session)
    state = load_state(directory)
    if not state:
        fail(f"no session state in {directory}")
    if not pane_info(state["pane"]):
        fail(f"peer pane {state['pane']} is gone")
    print(tail(state["pane"], args.lines))
    return 0


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    send = sub.add_parser("send", help="Send a review brief or a task brief to a Codex/Claude pane.")
    send.add_argument("--mode", choices=sorted(PROTOCOLS), help="review (default): the peer critiques and edits nothing. task: the peer does the work.")
    send.add_argument("--agent", choices=sorted(LAUNCH_ENV), help="Peer agent. Defaults to the other agent than the caller.")
    send.add_argument("--session", help="Session slug; reuse it for later rounds. Defaults to a timestamp.")
    send.add_argument("--message-file", required=True, help="Markdown review brief, or - for stdin.")
    send.add_argument("--pane", help='Peer pane as any tmux target ("%%12", ".3", "{right-of}"); marked for later reuse.')
    send.add_argument("--new-pane", action="store_true", help="Open a new pane instead of reusing an idle peer pane.")
    send.add_argument("--target", help="Requester pane whose window is searched or split. Defaults to $TMUX_PANE.")
    send.add_argument("--direction", choices=("auto", "right", "below"), default="auto", help="How to split the largest pane.")
    send.set_defaults(func=cmd_send)

    wait = sub.add_parser("wait", help="Wait for a round's result file and print it.")
    wait.add_argument("--session", help="Defaults to the most recently sent session.")
    wait.add_argument("--round", type=int, help="Defaults to the latest round.")
    wait.add_argument("--timeout", type=float, default=540, help="Exit 3 after this many seconds.")
    wait.add_argument("--idle", type=float, default=30, help="Exit 4 when the pane is idle this long without a result file.")
    wait.set_defaults(func=cmd_wait)

    peek = sub.add_parser("peek", help="Print the last lines of the peer pane.")
    peek.add_argument("--session", help="Defaults to the most recently sent session.")
    peek.add_argument("--lines", type=int, default=40)
    peek.set_defaults(func=cmd_peek)

    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
