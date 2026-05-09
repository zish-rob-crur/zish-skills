#!/usr/bin/env python3
"""Resolve local paths for Zish skill management."""

from __future__ import annotations

import argparse
import json
import os
import shlex
import sys
from pathlib import Path


def expand_path(value: str, *, follow_symlinks: bool = True) -> Path:
    path = Path(os.path.expandvars(os.path.expanduser(value)))
    if follow_symlinks:
        return path.resolve()
    return path.absolute()


def existing_dirs(paths: list[Path]) -> list[Path]:
    seen: set[Path] = set()
    result: list[Path] = []
    for path in paths:
        try:
            resolved = path.resolve()
        except OSError:
            resolved = path
        if resolved in seen or not resolved.is_dir():
            continue
        seen.add(resolved)
        result.append(resolved)
    return result


def find_from_parents(start: Path) -> list[Path]:
    candidates: list[Path] = []
    for parent in [start, *start.parents]:
        if parent.name == "zish-skills":
            candidates.append(parent)
        nested = parent / "zish-skills"
        if nested.is_dir():
            candidates.append(nested)
    return existing_dirs(candidates)


def github_roots(home: Path) -> list[Path]:
    values: list[str] = []
    if os.environ.get("GITHUB_REPOS_ROOT"):
        values.extend(os.environ["GITHUB_REPOS_ROOT"].split(os.pathsep))
    values.extend(
        [
            str(home / "Githubrepos"),
            str(home / "GitHubRepos"),
            str(home / "githubrepos"),
            str(home / "github-repos"),
        ]
    )
    return existing_dirs([expand_path(value) for value in values if value])


def find_under_roots(roots: list[Path]) -> list[Path]:
    candidates: list[Path] = []
    for root in roots:
        candidates.append(root / "zish-skills")
        candidates.extend(root.glob("*/zish-skills"))
        candidates.extend(root.glob("*/*/zish-skills"))
    return existing_dirs(candidates)


def resolve_public_repo() -> Path:
    explicit = os.environ.get("ZISH_SKILLS_REPO")
    if explicit:
        path = expand_path(explicit)
        if path.is_dir():
            return path
        raise SystemExit(f"ZISH_SKILLS_REPO does not exist or is not a directory: {path}")

    home = Path.home().resolve()
    cwd = Path.cwd().resolve()
    candidates = find_from_parents(cwd)
    candidates.extend(find_under_roots(github_roots(home)))

    for candidate in existing_dirs(candidates):
        if (candidate / ".git").exists() or (candidate / "README.md").exists():
            return candidate

    raise SystemExit(
        "Could not locate zish-skills. Set ZISH_SKILLS_REPO to the repo root, "
        "or place the repo under ~/Githubrepos or ~/GitHubRepos."
    )


def resolved_paths() -> dict[str, str]:
    home = Path.home().resolve()
    repo = resolve_public_repo()
    private_root = expand_path(
        os.environ.get("ZISH_PRIVATE_SKILLS_ROOT", str(home / ".agents/private-skills-src")),
        follow_symlinks=False,
    )
    agent_root = expand_path(
        os.environ.get("AGENT_SKILLS_ROOT", str(home / ".agents/skills")),
        follow_symlinks=False,
    )
    tools_python = expand_path(
        os.environ.get("ZISH_SKILL_TOOLS_PYTHON", str(home / ".agents/skill-tools-venv/bin/python")),
        follow_symlinks=False,
    )

    return {
        "PUBLIC_SKILLS_REPO": str(repo),
        "PUBLIC_SKILLS_ROOT": str(repo / "skills"),
        "PRIVATE_SKILLS_ROOT": str(private_root),
        "AGENT_SKILLS_ROOT": str(agent_root),
        "SKILL_TOOLS_PYTHON": str(tools_python),
        "INIT_SKILL": str(home / ".codex/skills/.system/skill-creator/scripts/init_skill.py"),
        "VALIDATE_SKILL": str(home / ".codex/skills/.system/skill-creator/scripts/quick_validate.py"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Resolve local paths for Zish skill management.")
    parser.add_argument("--format", choices=["shell", "json"], default="shell")
    args = parser.parse_args()

    paths = resolved_paths()
    if args.format == "json":
        print(json.dumps(paths, indent=2, sort_keys=True))
        return 0

    for key, value in paths.items():
        print(f"{key}={shlex.quote(value)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
