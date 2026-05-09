---
name: zish-skill-manager
description: Manage Zish's personal, public, private, company, and customer-specific Codex skills. Use when creating, updating, migrating, validating, linking, or organizing user-level skills; when deciding whether a skill belongs in the public personal GitHub repo or must remain private; or when maintaining symlinks under ~/.agents/skills.
---

# Zish Skill Manager

## Purpose

Use this skill to manage user-level Codex skills without leaking private or company material into a personal GitHub repo.

Keep the canonical skill source in the right place, validate the skill, and expose it to agents through `~/.agents/skills` symlinks.

## Path Resolution

Do not hard-code the user's absolute home path. Resolve paths at the start of each task:

```bash
eval "$(python3 "$HOME/.agents/skills/zish-skill-manager/scripts/resolve_paths.py" --format shell)"
```

The resolver sets:

- `PUBLIC_SKILLS_REPO`: public personal `zish-skills` repo root
- `PUBLIC_SKILLS_ROOT`: public personal skill source root
- `PRIVATE_SKILLS_ROOT`: private local fallback root
- `AGENT_SKILLS_ROOT`: agent discovery root
- `SKILL_TOOLS_PYTHON`: Python interpreter for skill tooling
- `INIT_SKILL`: `skill-creator` initializer script
- `VALIDATE_SKILL`: `skill-creator` validator script

Resolution order for `PUBLIC_SKILLS_REPO`:

1. `$ZISH_SKILLS_REPO`, when set
2. A parent `zish-skills` repo from the current working directory
3. A `zish-skills` repo under `$GITHUB_REPOS_ROOT`
4. A `zish-skills` repo under `$HOME/Githubrepos`, `$HOME/GitHubRepos`, `$HOME/githubrepos`, or `$HOME/github-repos`

Use `$ZISH_PRIVATE_SKILLS_ROOT`, `$AGENT_SKILLS_ROOT`, or `$ZISH_SKILL_TOOLS_PYTHON` to override the private source root, discovery root, or tools Python.

If `SKILL_TOOLS_PYTHON` does not exist, create it without modifying system Python:

```bash
python3 -m venv "$HOME/.agents/skill-tools-venv"
"$HOME/.agents/skill-tools-venv/bin/python" -m pip install PyYAML
```

## Classification

Classify the skill before choosing its source directory.

Treat a skill as **public personal** only when it is generic, reusable, owned by the user personally, and safe to commit to the user's personal GitHub repo.

Treat a skill as **private** when it contains or depends on any of these signals:

- Company, customer, or client context
- Internal systems, private workflows, proprietary code, schemas, non-public URLs, internal docs, or account/permission details
- Secrets, credentials, tokens, billing details, or clues about sensitive infrastructure
- Anything whose public status is unclear

When uncertain, default to private. Do not move private material into the public personal repo unless the user explicitly says it is safe to publish there.

## Language

Write skill contents in English by default, including:

- `SKILL.md`
- YAML frontmatter
- `agents/openai.yaml`
- `references/` documents
- Script comments
- Agent-facing prompts and examples

Preserve commands, paths, API names, product names, and proper nouns exactly when needed.

## Create Or Update A Public Personal Skill

1. Normalize the skill name to lowercase hyphen-case. Use the same name for the folder.
2. Create or update the canonical source at:
   `$PUBLIC_SKILLS_ROOT/<skill-name>`
3. For new skills, initialize with:
   ```bash
   "$SKILL_TOOLS_PYTHON" "$INIT_SKILL" <skill-name> --path "$PUBLIC_SKILLS_ROOT"
   ```
4. Keep the skill concise and follow the `skill-creator` structure: required `SKILL.md`, optional `agents/`, `scripts/`, `references/`, and `assets/`.
5. Validate with:
   ```bash
   "$SKILL_TOOLS_PYTHON" "$VALIDATE_SKILL" "$PUBLIC_SKILLS_ROOT/<skill-name>"
   ```
6. Expose it through a safe symlink:
   ```bash
   ln -sfn "$PUBLIC_SKILLS_ROOT/<skill-name>" "$AGENT_SKILLS_ROOT/<skill-name>"
   ```

## Create Or Update A Private Skill

1. Keep the canonical source in a company private repo, a company-specified directory, or the local private fallback root:
   `$PRIVATE_SKILLS_ROOT/<skill-name>`
2. Never copy, migrate, commit, or push private skill contents to:
   `$PUBLIC_SKILLS_REPO`
3. If no private destination is specified, use the local private fallback root instead of asking, unless that would conflict with an existing file or directory.
4. Create `~/.agents/skills/<skill-name>` as a symlink to the private source directory after validating that doing so will not overwrite an existing real directory.
5. Validate with `"$SKILL_TOOLS_PYTHON" "$VALIDATE_SKILL" <private-skill-folder>` whenever the private skill follows the standard skill structure.

## Safe Symlink Rules

Before creating or replacing `$AGENT_SKILLS_ROOT/<skill-name>`:

1. Check whether the path already exists.
2. If it is already a symlink to the intended source, leave it alone.
3. If it is a symlink to another source, inspect the target and preserve it unless the migration is clearly part of the current task.
4. If it is a real directory or file, do not overwrite it with `ln -sfn`. Migrate only after preserving the original contents.
5. Never delete user skill contents as part of routine linking.

## Migration Rules

When an existing skill only lives under `$AGENT_SKILLS_ROOT/<skill-name>`:

1. Inspect whether the entry is a real directory or a symlink.
2. Classify the contents as public personal or private.
3. Move or copy public personal contents into the public personal repo root only when the contents are safe for personal GitHub.
4. Move or copy private contents into the private destination or leave them in place and link to them.
5. Validate the resulting skill and update the discovery symlink.

## Manager Self-Link

If the discovery link for this skill is missing or stale, locate the canonical `zish-skill-manager` directory under `$ZISH_SKILLS_REPO`, `$HOME/Githubrepos`, or `$HOME/GitHubRepos`, then recreate:

```bash
ln -sfn "<path-to-zish-skills>/skills/zish-skill-manager" "$HOME/.agents/skills/zish-skill-manager"
```

Symlinks are literal filesystem entries; they do not expand `$HOME` or other environment variables after creation.

## Git Safety

Do not commit, push, publish, or deploy skill changes unless the user explicitly asks.

It is fine to report `git status` for the public skill repo and name which files are ready to review.
