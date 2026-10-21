# External Artifact and Image Storage

## Keep source and run artifacts separate

**Versionable skill source:** SKILL.md, rules, scripts, HTML/CSS templates, and text fixtures containing only synthetic inputs.
**Run artifacts that must stay outside code repositories:** report HTML/Markdown, exported SVG/PNG, browser screenshots, PDFs, recordings, log excerpts, raw data copies, publication payloads, Feishu responses, and review results.
Source templates are not business reports. SVG, Base64, and images embedded in Markdown remain report artifacts; being text does not exempt them from the storage rule.
If the user explicitly requests a report index in the repository, write only authorized plain-text titles, versions, and controlled document links. Do not copy images or local absolute paths. Leave the repository unchanged by default.

## Default paths

```text
${EXPLAIN_REPORT_HOME:-${XDG_STATE_HOME:-$HOME/.local/state}/explain-and-report}/
├── runs/
│   └── <project-name>-<path-hash>/
│       └── <UTC-time>-<topic>-<random>/
│           ├── manifest.json
│           ├── delivery/             # report.html; report.md only on explicit request
│           ├── figures/              # Body figures, not QA screenshots
│           ├── qa/
│           │   ├── review.md
│           │   └── screenshots/<capture-id>/
│           │       ├── desktop-first.png
│           │       ├── mobile-first.png
│           │       └── capture.json
│           └── publish/              # Minimal payloads, receipts, recovery state
└── style-library/                    # Optional authorized long-term references/baselines
    └── <style-id>/
        ├── reference.png
        └── reference.json
```

`init` creates only the directories needed for this run under `runs`; it does not create baselines or approval records.
Use non-sensitive English run names with random suffixes. Keep customer names, phone numbers, and business secrets out of filenames. Do not upload the manifest's local project path by default.
The root must be absolute, writable, and outside source directories, the skill, and every Git worktree. Checks consider both lexical paths and realpaths, rejecting worktrees, submodule `.git` files, and symlink detours.
`XDG_STATE_HOME` is an optional configuration input. On macOS, the unset default is also `~/.local/state/...`; this is a skill convention, not a mandatory macOS standard.

```bash
# The user may choose an already authorized location outside all repositories.
export EXPLAIN_REPORT_HOME="$HOME/Library/Application Support/explain-and-report"
```

The script does not scan the whole machine or perform global Git operations. Source directories outside Git are protected too; Git projects use the repository root as the protected boundary.

## Two layers against accidental commits

First, physical separation: create an external directory before generation, pass external destinations explicitly to every tool, and launch third-party tools from the external run directory.
Second, final checks: recheck external paths, reject symlinks within the run directory, and report repository image candidates that changed during the run.

Image-candidate checks prevent mistakes; they are not repository-wide DLP, malicious-script isolation, or a concurrency-safe sandbox. They do not fully detect Base64 in arbitrary text or prevent other programs from copying artifacts into the repository.
If repository images change, do not assume the current run caused every change. Pause commits/publication, report the paths, and preserve user edits. Never automatically run `git reset`, delete files, or change the index.
Do not add blanket `*.png` / `*.svg` ignores that hide legitimate source assets. Do not store run artifacts in an installed skill directory.

## Four image roles

| Role | Local location | Default Feishu behavior |
| --- | --- | --- |
| Body diagrams, charts, and evidence images (including failure screenshots) | `figures/` | Insert allowlisted images into the body when report publication is authorized |
| Report-layout QA screenshots | `qa/screenshots/` | Do not upload; send to a designated review destination only when explicitly requested |
| User design references | External `style-library/` or this run's `qa/reference/` | Do not automatically upload or redistribute |
| Fixed regression baselines | External `style-library/.../baselines/` | May be stored in a restricted review document/folder with authorization |

Feishu is an optional sharing destination, not a local temporary filesystem. Uploading body figures does not back up local QA evidence.
`file://` and `/Users/...` paths are not team-accessible image links. Temporary Feishu download URLs are not permanent image hosting.
Inline necessary images in offline HTML. For Feishu, actually upload and insert images rather than pasting local paths.

## Privacy, retention, and cleanup

Retain minimal data by default; do not copy entire raw logs. Screenshots may contain names, phone numbers, prompts, or paths. Inspect each before publishing; collapsed content may still exist in HTML source.
On POSIX systems, scripts create run directories with mode 0700 and files with mode 0600. This is not encryption or a replacement for disk/account management.
Do not clean up automatically. Before cleanup, list specific run IDs, paths, sizes, and whether remote copies have been verified. Limit deletion to confirmed objects within this skill's storage root and obtain authorization. Do not follow symlinks, delete shared source, or remove the only deliverable.
CI may use controlled artifact storage with explicit permissions, retention, and link expiry. Never publish sensitive screenshots as public CI artifacts.
Containers may use authorized external paths such as `/mnt/data/...`. Downloadable attachments and code commits are distinct; do not describe temporary session storage as permanent archival storage.
