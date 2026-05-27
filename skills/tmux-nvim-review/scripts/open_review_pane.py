#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path


SKIP_PARTS = {".git", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"}
SKIP_NAMES = {".DS_Store"}
SKIP_SUFFIXES = {".pyc", ".pyo", ".o", ".class", ".DS_Store"}


def run(command: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=str(cwd) if cwd else None,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def git_root(base_dir: Path) -> Path:
    result = run(["git", "rev-parse", "--show-toplevel"], cwd=base_dir)
    if result.returncode != 0:
        return base_dir.resolve()
    return Path(result.stdout.strip()).resolve()


def add_unique(items: list[Path], seen: set[str], path: Path) -> None:
    key = path.as_posix()
    if key not in seen:
        seen.add(key)
        items.append(path)


def normalize_explicit_files(files: list[str], base_dir: Path, root: Path) -> list[Path]:
    normalized: list[Path] = []
    seen: set[str] = set()

    for raw in files:
        path = Path(raw)
        absolute = path if path.is_absolute() else base_dir / path
        try:
            relative = absolute.resolve().relative_to(root)
        except ValueError:
            relative = absolute.resolve()
        add_unique(normalized, seen, relative)

    return normalized


def is_reviewable(path: Path, root: Path) -> bool:
    absolute = path if path.is_absolute() else root / path
    if any(part in SKIP_PARTS for part in absolute.parts):
        return False
    if absolute.name in SKIP_NAMES:
        return False
    if absolute.suffix in SKIP_SUFFIXES:
        return False
    if not absolute.exists() or absolute.is_dir():
        return False
    return True


def display_path(path: Path) -> str:
    return str(path) if path.is_absolute() else path.as_posix()


def editor_shell_command(editor: str, root: Path, files: list[Path]) -> str:
    editor_parts = shlex.split(editor)
    if not editor_parts:
        raise ValueError("editor command is empty")

    editor_command = " ".join(shlex.quote(part) for part in editor_parts)
    quoted_files = " ".join(shlex.quote(display_path(path)) for path in files)
    return f"cd {shlex.quote(str(root))} && {editor_command} -- {quoted_files}"


def tmux_command(args: argparse.Namespace, root: Path, shell_command: str) -> list[str]:
    split_flag = "-h" if args.direction == "right" else "-v"
    command = ["tmux", "split-window", split_flag, "-c", str(root)]
    if args.detached:
        command.append("-d")
    if args.size:
        command.extend(["-l", args.size])
    if args.target:
        command.extend(["-t", args.target])
    command.append(shell_command)
    return command


def shell_join(command: list[str]) -> str:
    return " ".join(shlex.quote(part) for part in command)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Open explicit files in a new tmux pane with nvim for review."
    )
    parser.add_argument(
        "files",
        nargs="+",
        help="Files changed in the current agent turn to open for review.",
    )
    parser.add_argument(
        "--base-dir",
        default=os.getcwd(),
        help="Directory used to resolve relative paths and find the Git repo.",
    )
    parser.add_argument(
        "--editor",
        default=os.environ.get("NVIM_REVIEW_EDITOR", "nvim"),
        help="Editor command to run inside the tmux pane. Defaults to nvim.",
    )
    parser.add_argument(
        "--direction",
        choices=("right", "below"),
        default="right",
        help="Where to create the new pane. Defaults to right.",
    )
    parser.add_argument("--size", help="Optional tmux pane size, such as 40%%.")
    parser.add_argument("--target", help="Optional tmux target pane/session/window.")
    parser.add_argument(
        "--detached",
        action="store_true",
        help="Create the pane without selecting it.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the tmux command without opening a pane.",
    )
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    base_dir = Path(args.base_dir).resolve()
    root = git_root(base_dir)

    raw_files = normalize_explicit_files(args.files, base_dir, root)
    files = [path for path in raw_files if is_reviewable(path, root)]

    if not files:
        print("No reviewable files found from the explicit arguments.")
        return 1

    try:
        shell_command = editor_shell_command(args.editor, root, files)
    except ValueError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    command = tmux_command(args, root, shell_command)
    if args.dry_run:
        print(shell_join(command))
        return 0

    editor_binary = shlex.split(args.editor)[0]
    if shutil.which(editor_binary) is None:
        print(f"error: editor not found: {editor_binary}", file=sys.stderr)
        print(f"fallback: {shell_command}")
        return 2

    if shutil.which("tmux") is None:
        print("error: tmux not found", file=sys.stderr)
        print(f"fallback: {shell_command}")
        return 2

    if not os.environ.get("TMUX") and not args.target:
        print(
            "error: not running inside tmux; pass --target or run from a tmux pane",
            file=sys.stderr,
        )
        print(f"fallback: {shell_command}")
        return 2

    result = run(command)
    if result.returncode != 0:
        print(result.stderr.strip() or "error: tmux split-window failed", file=sys.stderr)
        print(f"fallback: {shell_command}")
        return result.returncode

    print(f"Opened tmux nvim review pane with {len(files)} file(s):")
    for path in files:
        print(f"- {display_path(path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
