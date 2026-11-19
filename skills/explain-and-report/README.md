# Explain & Report · v0.5.1

Create offline visual HTML reports that readers grasp in 5 seconds and can articulate clearly afterward. Pairs technical-magazine pacing with engineering-atlas structure for system explanations, ADRs, architecture convergence proposals, agent traces, and evaluation reports.

By default, reports go to **`<run_dir>/delivery/<topic>.html`** outside code repositories. When you specify an output folder or `.html` path, pass `--output <dir-or-file.html>` (or `--output-dir <dir>`) to write only the final HTML there while keeping figures, QA screenshots, and publish payloads in the external `run_dir`. Markdown is generated only on explicit request, and Feishu publishing runs only with explicit authorization.

## Visual Identity and Navigation

All reports share the **Zish Technical** identity in `assets/report-theme.css`:

- **Theme & canvas:** Charcoal dark mode with a built-in warm-paper light toggle (`[data-theme-toggle]`), wide canvas (`max-width: min(1620px, 96vw)`), comfortable prose measure (`--body: 52rem`), and full-width grids.
- **Explanation blocks:** 5-second executive snapshot cards (`.summary-grid`), right-margin sidenotes (`.with-sidenote` / `.sidenote`), counterexample vs. design contrasts (`.mental-model`), responsive CSS Grid flow maps (`.batch-map`), chronological traces (`.trace-stream` / `.turn-row`), external `.chart-legend` blocks, and `.diff-box` blocks.
- **Zero-clutter reading chrome:** Compact bottom-left floating TOC (`目录` with hover preview, click-to-pin, and progress bar), inline `[C1]` / `[data-tip-title]` popovers, and a bottom-right hover/pin detail drawer (`.explorer-float-drawer`) driven by `assets/report-navigation.js`. Everything essential degrades cleanly without JS.

## Bundled Assets

| File | Purpose |
| --- | --- |
| `assets/report-shell.html` | Minimal offline starter shell with theme toggle, floating TOC, and navigation controller |
| `assets/reference-layout.html` | Complete Explain reference (snapshot, contrast, trace-stream, sidenotes) |
| `assets/reference-report.html` | Complete Report / ADR reference (decision snapshot, comparison table, drawers, citations) |
| `assets/flow-patterns.html` | Static CSS Grid diagrams for fan-out, convergence, branching, and validation |
| `assets/mechanism-walkthrough.html` | Interactive sequence replay paired with static explanation |

## Install

```bash
npx skills add https://github.com/zish-rob-crur/zish-skills --skill explain-and-report --agent codex --global
```

Invoke `$explain-and-report` in Codex, `/explain-and-report` in Claude Code, or reference it by name in Antigravity CLI. Deliverables default to Simplified Chinese unless another language is requested.

## External Run Layout

Artifacts live outside repositories under `${EXPLAIN_REPORT_HOME:-${XDG_STATE_HOME:-$HOME/.local/state}/explain-and-report}`:

```text
runs/<project-name>-<path-hash>/<time>-<topic>-<random>/
  manifest.json
  delivery/<topic>.html      # primary task-named HTML deliverable
  figures/                  # body evidence figures
  qa/review.md
  qa/screenshots/           # layout/visual QA captures (never mixed into body)
  publish/
```

## Scripts and Smoke Check

| Script | Purpose | Dependencies |
| --- | --- | --- |
| `report_workspace.py init/check` | Create external run directory, optionally bind `--output`/`--output-dir`, return `report_path`, guard repo/skill boundaries | Python 3.10+, stdlib; `git` for repo checks |
| `apply_report_theme.py` | Embed `assets/report-theme.css` and refresh inline `report-navigation.js` (supports `--report`) | Python 3.10+, stdlib |
| `check_report.py` | Run static HTML, anchor, contrast-hint, SVG-length, and inline-code checks | Python 3.10+, stdlib |
| `capture_report.py` | Capture desktop/mobile/no-JS views and export tagged figures (supports `--report`) | Existing Playwright Python & Chromium |

Smoke test against a synthetic report:

```bash
SKILL_DIR="$HOME/.agents/skills/explain-and-report"
INIT_JSON="$(python3 -B "$SKILL_DIR/scripts/report_workspace.py" init --workspace "$PWD" --topic style-smoke)" || exit 1
RUN="$(printf '%s' "$INIT_JSON" | python3 -c 'import json,sys; print(json.load(sys.stdin)["run_dir"])')" || exit 1
REPORT="$(printf '%s' "$INIT_JSON" | python3 -c 'import json,sys; print(json.load(sys.stdin)["report_path"])')" || exit 1
cp "$SKILL_DIR/assets/reference-layout.html" "$REPORT"
python3 -B "$SKILL_DIR/scripts/apply_report_theme.py" --run "$RUN"
python3 -B "$SKILL_DIR/scripts/check_report.py" "$REPORT" --require-theme
python3 -B "$SKILL_DIR/scripts/report_workspace.py" check --run "$RUN"
```

Run bundled unit and Node navigation tests:

```bash
python3 -B -m unittest discover -s "$SKILL_DIR/tests" -v
node --test "$SKILL_DIR"/tests/*.cjs
```

## Package Layout

```text
explain-and-report/
├── SKILL.md
├── README.md
├── agents/openai.yaml
├── THIRD_PARTY_NOTICES.md
├── references/   # presentation-rules.md, diagrams-and-interaction.md, storage-policy.md, visual-qa.md, feishu-publish.md, sources.md
├── assets/       # theme CSS, navigation JS, shell, reference HTMLs, publish-plan.example.json
├── scripts/      # report_workspace.py, apply_report_theme.py, check_report.py, capture_report.py
└── tests/        # Python unittest suite, Node .cjs suites, regression-prompts.md
```
