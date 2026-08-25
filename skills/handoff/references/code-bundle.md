# Code Bundle Reference

The bundle is the optional second half of a handoff: the Markdown explains the work, the zip carries the code behind it. It exists for receivers who cannot clone the repo, work outside it, or need to run the code exactly as it stands.

## When To Bundle

Bundle when at least one is true:

- The receiver has no access to the repository or the branch.
- The work is unpushed, and the diff alone does not reproduce the state.
- The receiver has to run or debug the code, not just read it.
- The handoff travels through a channel that loses repo context, such as email or a ticket.

Skip the bundle when the receiver shares the repo and branch. A path plus a line range is smaller, easier to review, and never goes stale.

## Archive Layout

```
20260825-150340-auth-callback-refactor.zip
└── 20260825-150340-auth-callback-refactor/
    ├── HANDOFF.md        # identical to the generated Markdown handoff
    ├── MANIFEST.md       # bundled files, sizes, sources, SHA-256 prefixes, skipped entries
    └── files/
        ├── src/routes/auth/callback.ts
        └── tests/auth-callback.test.ts
```

- The single top-level directory keeps unzipping from splattering into the receiver's cwd.
- Paths under `files/` stay relative to `--base-dir`, or to the Git repo root for files outside it, so the tree still reads like the project.
- Files outside both anchors land under `files/_external/`.
- `MANIFEST.md` records where each file came from: `context`, `include`, or `git`.

## Source Selection

| Flag | Bundles |
| --- | --- |
| `--zip` | the full files behind every `--context` |
| `--zip-include PATH_OR_GLOB` | an extra file, a directory tree, or a glob |
| `--zip-git-changed` | files changed in the working tree, including untracked ones |
| `--zip-git-changed REF` | files changed against `REF`, for example `main` |
| `--no-zip-context` | nothing from `--context`; use with explicit includes |

Duplicates are collapsed, and the first source that contributed a file wins in the manifest.

## Default Exclusions

Skipped entries are never silent: each one is listed with a reason in the handoff's `Code Bundle` section and in `MANIFEST.md`.

- Secret-looking names: `.env*`, `*.pem`, `*.key`, `*.p12`, `*.pfx`, `*.keystore`, `id_rsa*`, `id_ed25519*`, `.npmrc`, `.netrc`, `.pypirc`, and anything matching `*credentials*`, `*secret*`, or `*service-account*.json`.
- Dependency and build directories: `.git`, `node_modules`, `vendor`, `dist`, `build`, `target`, `coverage`, `.venv`, `venv`, `__pycache__`, `.next`, `.turbo`, `.terraform`, and similar caches.
- Binary and generated files: `*.pyc`, `*.so`, `*.dylib`, `*.dll`, `*.exe`, `*.jar`, `*.class`, `*.zip`, `*.tar.gz`, `*.log`, `*.sqlite`, `.DS_Store`.
- Files over `--zip-max-file-size`, defaulting to `1MB`, and anything past `--zip-max-total-size`, defaulting to `20MB`.

Two overrides exist, and they behave differently:

- A file named exactly by `--context` or `--zip-include` bypasses the directory and pattern exclusions, because naming it is a deliberate choice. Size caps and the secret check still apply.
- `--zip-allow-sensitive` is the only way past the secret check. Use it only after confirming the file holds no real credential, for example a committed `.env.example`.

## Review Checklist

Before sharing the zip:

1. Read the `Skipped` list. A file skipped as a secret is a signal, not noise.
2. Confirm the entry count and total size match what the handoff claims to be about. A bundle of hundreds of files usually means an over-broad `--zip-include`.
3. Open `MANIFEST.md` and check that every `git`-sourced file belongs in the handoff; working-tree noise gets picked up too.
4. Confirm nothing in `files/` carries tokens, customer data, or production configuration.
5. Tell the receiver that `HANDOFF.md` inside the archive is the entry point.
