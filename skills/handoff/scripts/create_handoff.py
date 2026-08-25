#!/usr/bin/env python3
from __future__ import annotations

import argparse
import fnmatch
import hashlib
import os
import re
import shutil
import subprocess
import sys
import zipfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Sequence


LANGUAGE_BY_SUFFIX = {
    ".bash": "bash",
    ".c": "c",
    ".cc": "cpp",
    ".cpp": "cpp",
    ".css": "css",
    ".go": "go",
    ".h": "c",
    ".html": "html",
    ".java": "java",
    ".js": "javascript",
    ".json": "json",
    ".jsx": "jsx",
    ".kt": "kotlin",
    ".md": "markdown",
    ".mjs": "javascript",
    ".py": "python",
    ".rb": "ruby",
    ".rs": "rust",
    ".sh": "bash",
    ".sql": "sql",
    ".swift": "swift",
    ".toml": "toml",
    ".ts": "ts",
    ".tsx": "tsx",
    ".txt": "text",
    ".xml": "xml",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".zsh": "bash",
}

CONTEXT_SPEC_RE = re.compile(r"^(?P<path>.+?)(?::(?P<start>\d+)(?:-(?P<end>\d+))?)?$")
SIZE_SPEC_RE = re.compile(r"^\s*(?P<value>\d+(?:\.\d+)?)\s*(?P<unit>[kmg]?i?b?)\s*$", re.IGNORECASE)
CLIPBOARD_COMMANDS = (
    ["pbcopy"],
    ["wl-copy"],
    ["xclip", "-selection", "clipboard"],
    ["xsel", "--clipboard", "--input"],
)
INTENTS = ("continue", "review", "escalate", "archive")

SIZE_UNITS = {
    "": 1,
    "b": 1,
    "k": 1024,
    "kb": 1024,
    "kib": 1024,
    "m": 1024**2,
    "mb": 1024**2,
    "mib": 1024**2,
    "g": 1024**3,
    "gb": 1024**3,
    "gib": 1024**3,
}

DEFAULT_MAX_FILE_SIZE = "1MB"
DEFAULT_MAX_TOTAL_SIZE = "20MB"

BUNDLE_EXCLUDE_DIRS = frozenset(
    {
        ".git",
        ".gradle",
        ".idea",
        ".mypy_cache",
        ".next",
        ".pytest_cache",
        ".ruff_cache",
        ".terraform",
        ".tox",
        ".turbo",
        ".venv",
        "__pycache__",
        "build",
        "coverage",
        "dist",
        "node_modules",
        "target",
        "venv",
        "vendor",
    }
)

BUNDLE_EXCLUDE_FILE_PATTERNS = (
    ".ds_store",
    "*.bin",
    "*.class",
    "*.dll",
    "*.dylib",
    "*.exe",
    "*.jar",
    "*.log",
    "*.mp4",
    "*.pyc",
    "*.pyo",
    "*.so",
    "*.sqlite",
    "*.sqlite3",
    "*.tar",
    "*.tar.gz",
    "*.tgz",
    "*.zip",
)

SENSITIVE_FILE_PATTERNS = (
    ".env",
    ".env.*",
    "*.env",
    ".netrc",
    ".npmrc",
    ".pypirc",
    "*.jks",
    "*.key",
    "*.keystore",
    "*.p12",
    "*.pem",
    "*.pfx",
    "*.ppk",
    "*credentials*",
    "*secret*",
    "*service-account*.json",
    "id_dsa*",
    "id_ecdsa*",
    "id_ed25519*",
    "id_rsa*",
)


@dataclass(frozen=True)
class ContextSpec:
    raw: str
    path: Path
    start_line: int | None
    end_line: int | None


@dataclass(frozen=True)
class CommandCapture:
    command: str
    exit_code: int
    stdout: str
    stderr: str


@dataclass(frozen=True)
class BundleCandidate:
    path: Path
    origin: str
    explicit: bool


@dataclass(frozen=True)
class BundleEntry:
    source: Path
    arcname: str
    origin: str
    size: int
    digest: str


@dataclass(frozen=True)
class BundleSkip:
    display: str
    reason: str


@dataclass(frozen=True)
class BundlePlan:
    zip_path: Path
    archive_root: str
    entries: tuple[BundleEntry, ...]
    skipped: tuple[BundleSkip, ...]
    total_bytes: int


@dataclass(frozen=True)
class BundleOptions:
    enabled: bool
    zip_out: str | None
    includes: tuple[str, ...]
    git_changed_ref: str | None
    git_changed_enabled: bool
    include_contexts: bool
    excludes: tuple[str, ...]
    max_file_bytes: int
    max_total_bytes: int
    allow_sensitive: bool


@dataclass(frozen=True)
class HandoffResult:
    markdown_path: Path
    bundle_path: Path | None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a Markdown handoff with status, next steps, context, command outputs, and an optional code bundle.",
    )
    parser.add_argument("--title", required=True, help="One-line handoff title.")
    parser.add_argument(
        "--summary",
        required=True,
        help="Why this handoff exists and what the receiver needs to know.",
    )
    parser.add_argument(
        "--intent",
        choices=INTENTS,
        default="continue",
        help="Handoff intent. Defaults to continue.",
    )
    parser.add_argument(
        "--status",
        action="append",
        default=[],
        help="Completed work or current state. Repeat for multiple entries.",
    )
    parser.add_argument(
        "--next-step",
        action="append",
        default=[],
        help="Concrete continuation step. Repeat for multiple entries.",
    )
    parser.add_argument(
        "--open-question",
        action="append",
        default=[],
        help="Unresolved question, blocker, or escalation point. Repeatable.",
    )
    parser.add_argument(
        "--decision",
        action="append",
        default=[],
        help="Decision already made. Repeatable.",
    )
    parser.add_argument(
        "--risk",
        action="append",
        default=[],
        help="Risk, assumption, constraint, or tradeoff. Repeatable.",
    )
    parser.add_argument(
        "--note",
        action="append",
        default=[],
        help="Additional note to include in the handoff. Repeatable.",
    )
    parser.add_argument(
        "--context",
        action="append",
        default=[],
        metavar="PATH[:START[-END]]",
        help="Attach a file or line range. Examples: foo.py, foo.py:12, foo.py:12-40.",
    )
    parser.add_argument(
        "--command",
        action="append",
        default=[],
        help="Read-only command to execute and include in the handoff. Repeatable.",
    )
    parser.add_argument(
        "--base-dir",
        default=".",
        help="Base directory used to resolve context paths and run commands. Defaults to cwd.",
    )
    parser.add_argument(
        "--out-dir",
        default="_handoffs",
        help="Output directory for generated handoffs. Relative paths resolve from base-dir.",
    )
    parser.add_argument(
        "--slug",
        help="Optional filename slug. Defaults to a slugified title.",
    )
    parser.add_argument(
        "--no-clipboard",
        action="store_true",
        help="Do not copy the generated Markdown handoff to the system clipboard.",
    )

    bundle = parser.add_argument_group("code bundle")
    bundle.add_argument(
        "--zip",
        action="store_true",
        help="Also write a zip bundle with the full source of the referenced files.",
    )
    bundle.add_argument(
        "--zip-out",
        metavar="PATH",
        help="Explicit zip path. Relative paths resolve from base-dir. Implies --zip.",
    )
    bundle.add_argument(
        "--zip-include",
        action="append",
        default=[],
        metavar="PATH_OR_GLOB",
        help="Extra file, directory, or glob to bundle. Repeatable. Implies --zip.",
    )
    bundle.add_argument(
        "--zip-git-changed",
        nargs="?",
        const="",
        metavar="REF",
        help="Bundle files changed in the working tree, or changed against REF. Implies --zip.",
    )
    bundle.add_argument(
        "--no-zip-context",
        action="store_true",
        help="Do not bundle the files referenced by --context.",
    )
    bundle.add_argument(
        "--zip-exclude",
        action="append",
        default=[],
        metavar="GLOB",
        help="Skip bundled paths matching this glob. Repeatable.",
    )
    bundle.add_argument(
        "--zip-max-file-size",
        type=size_argument,
        default=DEFAULT_MAX_FILE_SIZE,
        metavar="SIZE",
        help=f"Per-file size cap for the bundle. Defaults to {DEFAULT_MAX_FILE_SIZE}.",
    )
    bundle.add_argument(
        "--zip-max-total-size",
        type=size_argument,
        default=DEFAULT_MAX_TOTAL_SIZE,
        metavar="SIZE",
        help=f"Total size cap for the bundle. Defaults to {DEFAULT_MAX_TOTAL_SIZE}.",
    )
    bundle.add_argument(
        "--zip-allow-sensitive",
        action="store_true",
        help="Bundle files whose names look like secrets. Off by default.",
    )
    return parser.parse_args()


def slugify(value: str) -> str:
    slug = re.sub(r"[^\w]+", "-", value.strip().lower(), flags=re.UNICODE)
    slug = slug.replace("_", "-")
    slug = re.sub(r"-{2,}", "-", slug).strip("-")
    return slug or "handoff"


def parse_size(value: str) -> int:
    match = SIZE_SPEC_RE.match(value)
    if not match:
        raise ValueError(f"Invalid size value: {value}")
    unit = match.group("unit").lower()
    if unit not in SIZE_UNITS:
        raise ValueError(f"Unknown size unit in: {value}")
    size = float(match.group("value")) * SIZE_UNITS[unit]
    if size <= 0:
        raise ValueError(f"Size must be positive: {value}")
    return int(size)


def size_argument(value: str) -> int:
    try:
        return parse_size(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError(str(error)) from error


def human_size(num_bytes: int) -> str:
    size = float(num_bytes)
    for unit in ("B", "KB", "MB"):
        if size < 1024:
            return f"{size:.0f} {unit}" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} GB"


def display_path(path: Path, base_dir: Path) -> str:
    try:
        return str(path.relative_to(base_dir))
    except ValueError:
        return str(path)


def parse_context_spec(raw: str, base_dir: Path) -> ContextSpec:
    match = CONTEXT_SPEC_RE.match(raw.strip())
    if not match:
        raise ValueError(f"Invalid context spec: {raw}")

    raw_path = match.group("path")
    if not raw_path:
        raise ValueError(f"Missing path in context spec: {raw}")

    start = int(match.group("start")) if match.group("start") else None
    end = int(match.group("end")) if match.group("end") else start
    if start is not None and end is not None and start > end:
        raise ValueError(f"Invalid line range in context spec: {raw}")

    path = Path(raw_path)
    resolved_path = path if path.is_absolute() else (base_dir / path)
    resolved_path = resolved_path.resolve()

    if not resolved_path.exists():
        raise FileNotFoundError(f"Context path does not exist: {resolved_path}")
    if not resolved_path.is_file():
        raise ValueError(f"Context path is not a file: {resolved_path}")

    return ContextSpec(raw=raw, path=resolved_path, start_line=start, end_line=end)


def detect_language(path: Path) -> str:
    return LANGUAGE_BY_SUFFIX.get(path.suffix.lower(), "text")


def numbered_lines(lines: Sequence[str], start_line: int) -> str:
    if not lines:
        return ""
    width = len(str(start_line + len(lines) - 1))
    return "\n".join(
        f"{line_no:>{width}} | {line}"
        for line_no, line in enumerate(lines, start=start_line)
    )


def read_context_block(spec: ContextSpec, base_dir: Path) -> str:
    text = spec.path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()

    start = spec.start_line or 1
    end = spec.end_line or len(lines)
    if start < 1:
        raise ValueError(f"Line numbers are 1-based: {spec.raw}")
    if end < start:
        raise ValueError(f"Invalid line range in context spec: {spec.raw}")
    if lines and end > len(lines):
        raise ValueError(
            f"Line range {start}-{end} exceeds file length {len(lines)} for {spec.path}"
        )
    if not lines and spec.start_line is not None:
        raise ValueError(f"Cannot read line range from empty file: {spec.path}")

    selected_lines = lines[start - 1 : end]
    range_label = f"lines {start}-{end}" if spec.start_line is not None else "full file"
    visible_path = display_path(spec.path, base_dir)
    language = detect_language(spec.path)
    code_block = numbered_lines(selected_lines, start)

    return "\n".join(
        [
            f"### `{visible_path}` ({range_label})",
            f"Resolved path: `{spec.path}`",
            "",
            f"```{language}",
            code_block,
            "```",
        ]
    )


def run_command(command: str, base_dir: Path) -> CommandCapture:
    completed = subprocess.run(
        command,
        shell=True,
        cwd=base_dir,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    return CommandCapture(
        command=command,
        exit_code=completed.returncode,
        stdout=completed.stdout.rstrip("\n"),
        stderr=completed.stderr.rstrip("\n"),
    )


def safe_git_value(base_dir: Path, *args: str) -> str | None:
    completed = subprocess.run(
        ["git", *args],
        cwd=base_dir,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if completed.returncode != 0:
        return None
    value = completed.stdout.strip()
    return value or None


def git_lines(base_dir: Path, *args: str) -> list[str]:
    value = safe_git_value(base_dir, *args)
    if not value:
        return []
    return [line.strip() for line in value.splitlines() if line.strip()]


def git_changed_paths(base_dir: Path, ref: str | None) -> list[Path]:
    repo_root_value = safe_git_value(base_dir, "rev-parse", "--show-toplevel")
    if not repo_root_value:
        raise RuntimeError("--zip-git-changed requires a Git repository.")
    repo_root = Path(repo_root_value)

    if ref:
        names = git_lines(base_dir, "diff", "--name-only", "--diff-filter=d", ref)
        if not names:
            names = git_lines(base_dir, "diff", "--name-only", "--diff-filter=d", f"{ref}...HEAD")
    else:
        names = git_lines(base_dir, "diff", "--name-only", "--diff-filter=d", "HEAD")
        names += git_lines(base_dir, "ls-files", "--others", "--exclude-standard")

    resolved: list[Path] = []
    for name in names:
        candidate = (repo_root / name).resolve()
        if candidate.is_file():
            resolved.append(candidate)
    return resolved


def expand_include_spec(raw: str, base_dir: Path) -> tuple[list[BundleCandidate], list[BundleSkip]]:
    spec = raw.strip()
    if not spec:
        return [], []

    path = Path(spec)
    target = path if path.is_absolute() else (base_dir / path)

    if target.is_file():
        return [BundleCandidate(path=target.resolve(), origin="include", explicit=True)], []
    if target.is_dir():
        return (
            [
                BundleCandidate(path=found, origin="include", explicit=False)
                for found in walk_directory(target.resolve())
            ],
            [],
        )

    matches = sorted(base_dir.glob(spec)) if not path.is_absolute() else sorted(Path(path.anchor).glob(str(path.relative_to(path.anchor))))
    candidates: list[BundleCandidate] = []
    for match in matches:
        if match.is_dir():
            candidates.extend(
                BundleCandidate(path=found, origin="include", explicit=False)
                for found in walk_directory(match.resolve())
            )
        elif match.is_file():
            candidates.append(BundleCandidate(path=match.resolve(), origin="include", explicit=False))

    if not candidates:
        return [], [BundleSkip(display=spec, reason="no file matched this --zip-include spec")]
    return candidates, []


def walk_directory(directory: Path) -> list[Path]:
    collected: list[Path] = []
    for current_root, dirnames, filenames in os.walk(directory):
        dirnames[:] = sorted(name for name in dirnames if name not in BUNDLE_EXCLUDE_DIRS)
        for filename in sorted(filenames):
            candidate = Path(current_root) / filename
            if candidate.is_file():
                collected.append(candidate.resolve())
    return collected


def is_sensitive_name(name: str) -> bool:
    lowered = name.lower()
    return any(fnmatch.fnmatch(lowered, pattern) for pattern in SENSITIVE_FILE_PATTERNS)


def default_exclude_reason(path: Path, base_dir: Path) -> str | None:
    try:
        parts = path.relative_to(base_dir).parts[:-1]
    except ValueError:
        parts = ()
    for part in parts:
        if part in BUNDLE_EXCLUDE_DIRS:
            return f"inside excluded directory `{part}`"

    lowered = path.name.lower()
    for pattern in BUNDLE_EXCLUDE_FILE_PATTERNS:
        if fnmatch.fnmatch(lowered, pattern):
            return f"matches excluded pattern `{pattern}`"
    return None


def user_exclude_reason(display: str, name: str, patterns: Sequence[str]) -> str | None:
    for pattern in patterns:
        if fnmatch.fnmatch(display, pattern) or fnmatch.fnmatch(name, pattern):
            return f"matches --zip-exclude `{pattern}`"
    return None


def bundle_arcname(path: Path, base_dir: Path, repo_root: Path | None) -> str:
    for anchor in (base_dir, repo_root):
        if anchor is None:
            continue
        try:
            relative = path.relative_to(anchor)
        except ValueError:
            continue
        return PurePosixPath(*relative.parts).as_posix()

    parts = [part.replace(":", "") for part in path.parts if part not in ("/", "\\", "..")]
    return PurePosixPath("_external", *parts).as_posix()


def file_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def collect_bundle_candidates(
    *,
    options: BundleOptions,
    contexts: Sequence[ContextSpec],
    base_dir: Path,
) -> tuple[list[BundleCandidate], list[BundleSkip]]:
    candidates: list[BundleCandidate] = []
    skipped: list[BundleSkip] = []

    if options.include_contexts:
        candidates.extend(
            BundleCandidate(path=spec.path, origin="context", explicit=True) for spec in contexts
        )

    for spec in options.includes:
        found, misses = expand_include_spec(spec, base_dir)
        candidates.extend(found)
        skipped.extend(misses)

    if options.git_changed_enabled:
        candidates.extend(
            BundleCandidate(path=path, origin="git", explicit=False)
            for path in git_changed_paths(base_dir, options.git_changed_ref)
        )

    return candidates, skipped


def build_bundle_plan(
    *,
    options: BundleOptions,
    contexts: Sequence[ContextSpec],
    base_dir: Path,
    zip_path: Path,
    archive_root: str,
) -> BundlePlan:
    repo_root_value = safe_git_value(base_dir, "rev-parse", "--show-toplevel")
    repo_root = Path(repo_root_value).resolve() if repo_root_value else None

    candidates, skipped = collect_bundle_candidates(
        options=options, contexts=contexts, base_dir=base_dir
    )

    entries: list[BundleEntry] = []
    seen_paths: set[Path] = set()
    used_arcnames: dict[str, Path] = {}
    total_bytes = 0

    for candidate in candidates:
        path = candidate.path
        if path in seen_paths:
            continue
        seen_paths.add(path)

        visible = display_path(path, base_dir)
        if path == zip_path:
            continue
        if not path.is_file():
            skipped.append(BundleSkip(display=visible, reason="not a regular file"))
            continue

        if not options.allow_sensitive and is_sensitive_name(path.name):
            skipped.append(BundleSkip(display=visible, reason="looks like a secret file"))
            continue

        reason = user_exclude_reason(visible, path.name, options.excludes)
        if reason is None and not candidate.explicit:
            reason = default_exclude_reason(path, base_dir)
        if reason:
            skipped.append(BundleSkip(display=visible, reason=reason))
            continue

        size = path.stat().st_size
        if size > options.max_file_bytes:
            skipped.append(
                BundleSkip(
                    display=visible,
                    reason=f"{human_size(size)} exceeds the per-file cap of {human_size(options.max_file_bytes)}",
                )
            )
            continue
        if total_bytes + size > options.max_total_bytes:
            skipped.append(
                BundleSkip(
                    display=visible,
                    reason=f"would exceed the total cap of {human_size(options.max_total_bytes)}",
                )
            )
            continue

        arcname = bundle_arcname(path, base_dir, repo_root)
        if used_arcnames.get(arcname, path) != path:
            arcname = PurePosixPath("_conflict", str(len(used_arcnames)), arcname).as_posix()
        used_arcnames[arcname] = path

        entries.append(
            BundleEntry(
                source=path,
                arcname=arcname,
                origin=candidate.origin,
                size=size,
                digest=file_digest(path),
            )
        )
        total_bytes += size

    return BundlePlan(
        zip_path=zip_path,
        archive_root=archive_root,
        entries=tuple(entries),
        skipped=tuple(skipped),
        total_bytes=total_bytes,
    )


def render_bundle_section(plan: BundlePlan, base_dir: Path) -> str:
    lines = [
        "## Code Bundle",
        "",
        f"- Bundle: `{display_path(plan.zip_path, base_dir)}`",
        f"- Files: {len(plan.entries)} ({human_size(plan.total_bytes)} uncompressed)",
        f"- Archive layout: `{plan.archive_root}/HANDOFF.md`, `{plan.archive_root}/MANIFEST.md`, `{plan.archive_root}/files/...`",
        "- Bundled files are complete; the ranges quoted above are the parts that matter.",
    ]

    if plan.entries:
        lines.extend(
            [
                "",
                "| File | Size | Source |",
                "| --- | --- | --- |",
            ]
        )
        lines.extend(
            f"| `{entry.arcname}` | {human_size(entry.size)} | {entry.origin} |"
            for entry in plan.entries
        )

    if plan.skipped:
        lines.extend(["", "### Skipped", ""])
        lines.extend(f"- `{skip.display}` — {skip.reason}" for skip in plan.skipped)

    return "\n".join(lines)


def render_manifest(
    *,
    plan: BundlePlan,
    title: str,
    intent: str,
    base_dir: Path,
    generated_at: datetime,
) -> str:
    repo_root = safe_git_value(base_dir, "rev-parse", "--show-toplevel")
    git_branch = safe_git_value(base_dir, "rev-parse", "--abbrev-ref", "HEAD")
    git_commit = safe_git_value(base_dir, "rev-parse", "--short", "HEAD")

    lines = [
        f"# Manifest — {title}",
        "",
        f"- Generated at: `{generated_at.isoformat(timespec='seconds')}`",
        f"- Intent: `{intent}`",
        f"- Base directory: `{base_dir}`",
    ]
    if repo_root:
        lines.append(f"- Git repo root: `{repo_root}`")
    if git_branch:
        lines.append(f"- Git branch: `{git_branch}`")
    if git_commit:
        lines.append(f"- Git commit: `{git_commit}`")
    lines.extend(
        [
            f"- Files: {len(plan.entries)} ({human_size(plan.total_bytes)} uncompressed)",
            "",
            "## Files",
            "",
        ]
    )

    if plan.entries:
        lines.extend(["| File | Size | Source | SHA-256 |", "| --- | --- | --- | --- |"])
        lines.extend(
            f"| `files/{entry.arcname}` | {human_size(entry.size)} | {entry.origin} | `{entry.digest[:16]}` |"
            for entry in plan.entries
        )
    else:
        lines.append("No files were bundled.")

    if plan.skipped:
        lines.extend(["", "## Skipped", ""])
        lines.extend(f"- `{skip.display}` — {skip.reason}" for skip in plan.skipped)

    return "\n".join(lines).rstrip() + "\n"


def write_bundle(plan: BundlePlan, *, handoff_markdown: str, manifest_markdown: str) -> None:
    plan.zip_path.parent.mkdir(parents=True, exist_ok=True)
    root = plan.archive_root
    with zipfile.ZipFile(plan.zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(f"{root}/HANDOFF.md", handoff_markdown)
        archive.writestr(f"{root}/MANIFEST.md", manifest_markdown)
        for entry in plan.entries:
            archive.write(entry.source, f"{root}/files/{entry.arcname}")


def render_bullet_section(title: str, items: Sequence[str]) -> str | None:
    cleaned = [item.strip() for item in items if item.strip()]
    if not cleaned:
        return None
    lines = [f"## {title}", ""]
    lines.extend(f"- {item}" for item in cleaned)
    return "\n".join(lines)


def render_commands_section(commands: Sequence[CommandCapture]) -> str | None:
    if not commands:
        return None

    chunks = ["## Command Outputs", ""]
    for capture in commands:
        chunks.extend(
            [
                f"### `{capture.command}`",
                f"- Exit code: `{capture.exit_code}`",
                "",
                "#### stdout",
                "",
                "```text",
                capture.stdout or "(empty)",
                "```",
                "",
                "#### stderr",
                "",
                "```text",
                capture.stderr or "(empty)",
                "```",
                "",
            ]
        )
    return "\n".join(chunks).rstrip()


def find_clipboard_command() -> list[str] | None:
    for command in CLIPBOARD_COMMANDS:
        if shutil.which(command[0]):
            return command
    return None


def copy_to_clipboard(text: str) -> str:
    command = find_clipboard_command()
    if command is None:
        raise RuntimeError(
            "No clipboard command found. Install pbcopy, wl-copy, xclip, or xsel, or rerun with --no-clipboard."
        )

    subprocess.run(
        command,
        input=text,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=True,
    )
    return command[0]


def build_handoff_content(
    *,
    title: str,
    summary: str,
    intent: str,
    statuses: Sequence[str],
    next_steps: Sequence[str],
    open_questions: Sequence[str],
    decisions: Sequence[str],
    risks: Sequence[str],
    notes: Sequence[str],
    contexts: Sequence[ContextSpec],
    commands: Sequence[CommandCapture],
    base_dir: Path,
    generated_at: datetime,
    bundle_plan: BundlePlan | None = None,
) -> str:
    repo_root = safe_git_value(base_dir, "rev-parse", "--show-toplevel")
    git_branch = safe_git_value(base_dir, "rev-parse", "--abbrev-ref", "HEAD")

    sections: list[str] = [
        f"# {title}",
        "",
        "## Metadata",
        "",
        f"- Generated at: `{generated_at.isoformat(timespec='seconds')}`",
        f"- Intent: `{intent}`",
        f"- Base directory: `{base_dir}`",
    ]
    if repo_root:
        sections.append(f"- Git repo root: `{repo_root}`")
    if git_branch:
        sections.append(f"- Git branch: `{git_branch}`")
    if bundle_plan is not None:
        sections.append(f"- Code bundle: `{display_path(bundle_plan.zip_path, base_dir)}`")

    sections.extend(
        [
            "",
            "## Summary",
            "",
            summary.strip(),
        ]
    )

    for title_text, items in (
        ("Status", statuses),
        ("Decisions", decisions),
        ("Next Steps", next_steps),
        ("Open Questions", open_questions),
        ("Risks And Assumptions", risks),
        ("Notes", notes),
    ):
        section = render_bullet_section(title_text, items)
        if section:
            sections.extend(["", section])

    if contexts:
        sections.extend(["", "## Context Files", ""])
        for index, spec in enumerate(contexts):
            if index:
                sections.append("")
            sections.append(read_context_block(spec, base_dir))

    commands_section = render_commands_section(commands)
    if commands_section:
        sections.extend(["", commands_section])

    if bundle_plan is not None:
        sections.extend(["", render_bundle_section(bundle_plan, base_dir)])

    return "\n".join(sections).rstrip() + "\n"


def resolve_output_dir(base_dir: Path, out_dir: str) -> Path:
    path = Path(out_dir)
    if not path.is_absolute():
        path = base_dir / path
    return path.resolve()


def resolve_zip_path(base_dir: Path, zip_out: str | None, report_path: Path) -> Path:
    if not zip_out:
        return report_path.with_suffix(".zip")
    path = Path(zip_out)
    if not path.is_absolute():
        path = base_dir / path
    path = path.resolve()
    if path.is_dir():
        return path / report_path.with_suffix(".zip").name
    if path.suffix.lower() != ".zip":
        path = path.with_suffix(".zip")
    return path


def bundle_options_from_args(args: argparse.Namespace) -> BundleOptions:
    git_changed_enabled = args.zip_git_changed is not None
    enabled = bool(
        args.zip
        or args.zip_out
        or args.zip_include
        or git_changed_enabled
    )
    return BundleOptions(
        enabled=enabled,
        zip_out=args.zip_out,
        includes=tuple(args.zip_include),
        git_changed_ref=(args.zip_git_changed or None) if git_changed_enabled else None,
        git_changed_enabled=git_changed_enabled,
        include_contexts=not args.no_zip_context,
        excludes=tuple(args.zip_exclude),
        max_file_bytes=args.zip_max_file_size,
        max_total_bytes=args.zip_max_total_size,
        allow_sensitive=args.zip_allow_sensitive,
    )


def create_handoff(
    *,
    title: str,
    summary: str,
    intent: str,
    statuses: Sequence[str],
    next_steps: Sequence[str],
    open_questions: Sequence[str],
    decisions: Sequence[str],
    risks: Sequence[str],
    notes: Sequence[str],
    context_specs: Sequence[str],
    commands: Sequence[str],
    base_dir: Path,
    out_dir: str,
    slug: str | None = None,
    generated_at: datetime | None = None,
    copy_to_clipboard_enabled: bool = True,
    bundle_options: BundleOptions | None = None,
) -> HandoffResult:
    resolved_base_dir = base_dir.resolve()
    output_dir = resolve_output_dir(resolved_base_dir, out_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = generated_at or datetime.now().astimezone()
    slug_value = slugify(slug or title)
    stem = f"{timestamp.strftime('%Y%m%d-%H%M%S')}-{slug_value}"
    report_path = output_dir / f"{stem}.md"

    parsed_contexts = [parse_context_spec(spec, resolved_base_dir) for spec in context_specs]
    captured_commands = [run_command(command, resolved_base_dir) for command in commands]

    plan: BundlePlan | None = None
    if bundle_options is not None and bundle_options.enabled:
        plan = build_bundle_plan(
            options=bundle_options,
            contexts=parsed_contexts,
            base_dir=resolved_base_dir,
            zip_path=resolve_zip_path(resolved_base_dir, bundle_options.zip_out, report_path),
            archive_root=stem,
        )

    content = build_handoff_content(
        title=title,
        summary=summary,
        intent=intent,
        statuses=statuses,
        next_steps=next_steps,
        open_questions=open_questions,
        decisions=decisions,
        risks=risks,
        notes=notes,
        contexts=parsed_contexts,
        commands=captured_commands,
        base_dir=resolved_base_dir,
        generated_at=timestamp,
        bundle_plan=plan,
    )
    report_path.write_text(content, encoding="utf-8")

    bundle_path: Path | None = None
    if plan is not None:
        manifest = render_manifest(
            plan=plan,
            title=title,
            intent=intent,
            base_dir=resolved_base_dir,
            generated_at=timestamp,
        )
        write_bundle(plan, handoff_markdown=content, manifest_markdown=manifest)
        bundle_path = plan.zip_path
        if not plan.entries:
            print(
                "warning: the code bundle contains no source files; check --context, --zip-include, or --zip-git-changed.",
                file=sys.stderr,
            )

    if copy_to_clipboard_enabled:
        copy_to_clipboard(content)
    return HandoffResult(markdown_path=report_path, bundle_path=bundle_path)


def main() -> int:
    args = parse_args()
    result = create_handoff(
        title=args.title,
        summary=args.summary,
        intent=args.intent,
        statuses=args.status,
        next_steps=args.next_step,
        open_questions=args.open_question,
        decisions=args.decision,
        risks=args.risk,
        notes=args.note,
        context_specs=args.context,
        commands=args.command,
        base_dir=Path(args.base_dir),
        out_dir=args.out_dir,
        slug=args.slug,
        copy_to_clipboard_enabled=not args.no_clipboard,
        bundle_options=bundle_options_from_args(args),
    )
    print(result.markdown_path)
    if result.bundle_path is not None:
        print(result.bundle_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
