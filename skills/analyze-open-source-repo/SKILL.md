---
name: analyze-open-source-repo
description: Analyze open source repos and save structured Obsidian study notes.
---

# Analyze Open Source Repo

## Output Contract

Produce a structured Obsidian note that helps the user quickly understand a repository's purpose, core logic, architecture, learning value, and next reading path.

Default all narrative output, note headings, and generated diagram labels to Simplified Chinese unless the user explicitly specifies another language.

Read `references/obsidian-note-template.md` when composing the final note.

## Inputs

Accept:

- A local repo path, or a public repo URL.
- Optional focus areas such as architecture design, agent runtime, workflow, plugin system, engineering practices, performance optimization, or test design.

If the input is a URL, shallow-clone it into a temporary working directory. Do not modify the analyzed repo. If authentication is required, report that the URL is not publicly accessible; do not ask for tokens.

## Workflow

1. Resolve the repo.
   - For a local path, verify it exists and identify whether it is a Git repo.
   - For a URL, run a shallow clone into a temp directory.
   - Record repo name, source, commit SHA when available, and analysis date.

2. Identify basic project information.
   - Read README, docs, examples, package manifests, lockfiles, build files, Dockerfiles, CI configs, and top-level scripts.
   - Identify purpose, main language, stack, runtime, package manager, startup command, build command, test command, and directory overview.
   - Use `rg --files`, `git ls-files`, and manifest files before broad recursive scans.

3. Find the core execution path.
   - Locate entry files and entry modules: CLI commands, server bootstrap, app main, package exports, framework routes, worker startup, plugin registration, or library public API.
   - Trace the main call chain from entry point to core orchestration.
   - Use README, examples, tests, and integration tests to infer intended usage.
   - For large repos, focus on the shortest representative path that explains the product's main behavior.

4. Explain core logic.
   - Summarize key module responsibilities.
   - Explain primary data flow and control flow.
   - Name important interfaces, state objects, configuration objects, dependency injection boundaries, queues, registries, or lifecycle hooks.
   - Separate confirmed facts from reasoned inferences.

5. Extract architecture and design.
   - Describe module boundaries, core abstractions, extension or plugin mechanisms, configuration management, state management, dependency management, error handling, and boundary handling.
   - Explain why the design likely exists, using evidence from code, docs, tests, issues in the repo, or examples.

6. Extract learning value.
   - Identify design ideas worth learning.
   - Identify implementation patterns worth borrowing.
   - Identify code or module patterns suitable for reuse in the user's own projects.
   - Call out complex areas that are probably historical compatibility, scale-specific, ecosystem-specific, or special-case product constraints.

7. Produce diagrams with `$imagegen`.
   - Use the `imagegen` skill, if available, to generate:
     - One overall architecture diagram.
     - One main workflow flowchart.
     - One key subsystem data-flow or sequence diagram when it would materially improve understanding.
   - Keep diagram text short, large, and readable. Use the same output language as the note, and include concise text legends in the note so understanding does not depend only on image text.
   - Save final diagram images into the Obsidian vault attachment location and embed them in the note with Obsidian image embeds.
   - If image generation is unavailable or fails, include Mermaid diagrams as a fallback and record the limitation under "疑问 / 待验证点".

8. Save the note to Obsidian.
   - Use the `obsidian-markdown` skill, if available, for Obsidian-specific Markdown syntax.
   - If the user provides an Obsidian vault or note path, use it.
   - Otherwise discover candidate vaults by looking for `.obsidian` directories in common user locations and current workspace parents.
   - If exactly one vault is found, save under a repo-analysis or open-source-study folder.
   - If multiple plausible vaults exist and no default can be inferred, ask one concise vault-selection question before writing because saving to the wrong Obsidian vault is a real ambiguity.
   - If no vault can be found, create the note in the current workspace, state that no Obsidian vault was discoverable, and keep the output ready to move.
   - Use Obsidian-compatible Markdown, wikilinks only when the target exists or is intentionally created, and relative embeds for generated images.

## Investigation Heuristics

Start with these files when present:

- `README*`, `docs/**`, `examples/**`, `demo/**`
- `package.json`, `pnpm-workspace.yaml`, `Cargo.toml`, `pyproject.toml`, `go.mod`, `pom.xml`, `build.gradle`, `Makefile`, `justfile`, `Taskfile.yml`
- `Dockerfile`, `docker-compose*.yml`, `.github/workflows/**`
- `src/**`, `cmd/**`, `bin/**`, `cli/**`, `app/**`, `server/**`, `packages/**`
- `test/**`, `tests/**`, `spec/**`, `__tests__/**`, integration or e2e tests

Prefer structural evidence over guessing:

- Manifests reveal commands and package boundaries.
- Public APIs and exports reveal intended module boundaries.
- Examples reveal happy-path usage.
- Tests reveal supported behavior and edge cases.
- CI reveals the commands maintainers actually rely on.

## Verification

Run lightweight verification when feasible:

- Parse manifest commands instead of running expensive full builds by default.
- Run targeted tests or dry-run commands only when they are quick and safe.
- Do not install dependencies globally. Use the repo's existing package manager and lockfile if dependency installation is necessary.
- Record whether startup, build, or tests were only identified from configuration or actually run.

## Final Response

After saving the note, report:

- The note path.
- Diagram paths or fallback diagram status.
- What was verified by reading, what was verified by running commands, and what remains inferred.
- Any tradeoffs caused by repo size, missing dependencies, unavailable network, or ambiguous Obsidian vault location.
