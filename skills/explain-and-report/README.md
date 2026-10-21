# Explain & Report · v0.4.1

Explain complex content clearly, then choose diagrams, tables, sequences, or prose to express it. Use for technical explanations, system analysis, business workflows, agent traces, and evaluation reports. This is not a general-purpose web design framework.

The default deliverable is `report.html` only. A Markdown version is generated only on explicit request.
Relevant available evidence images, including error screenshots, are embedded in the HTML by default with short captions. Screenshots of the report's own layout checks stay in QA storage.

**Keep skill source in the repository, reports and review images outside it, and publish to Feishu only with explicit authorization.**

## Included capabilities

Skill instructions, evidence rules, design intent, optional HTML examples, external-workspace scripts, static preflight, an optional screenshot script, and a publishing workflow that reuses existing Feishu skills.

The model chooses the report's visual identity and composition for its subject and audience. The bundled templates are references, not a prescribed style. Review focuses on clarity, evidence, and usability.

This is not a standalone Feishu synchronization client and does not bundle credentials or external skills. The agent uses document tools actually installed and authorized in your environment. Local reports work without Feishu.

## Installation

The extracted top-level directory must be named `explain-and-report` and contain `SKILL.md`.

Use `~/.agents/skills/` for Codex personal skills and `~/.claude/skills/` for Claude Code personal skills. See [installation sources](references/sources.md).

For a repository checkout, link its canonical skill directory into both discovery directories:

```bash
# Run from the root of this zish-skills checkout.
SKILL_SOURCE="$PWD/skills/explain-and-report"
for SKILL_DEST in "$HOME/.agents/skills" "$HOME/.claude/skills"; do
  mkdir -p "$SKILL_DEST"
  if [ -e "$SKILL_DEST/explain-and-report" ] || [ -L "$SKILL_DEST/explain-and-report" ]; then
    printf 'Existing entry: %s; inspect it before replacing.\n' "$SKILL_DEST/explain-and-report"
  else
    ln -s "$SKILL_SOURCE" "$SKILL_DEST/explain-and-report"
  fi
done
```

For a ZIP distribution, run the following from the download directory. Back up and move an existing version before replacing it; the command refuses to overwrite to avoid mixing versions.

```bash
# Codex; for Claude Code use "$HOME/.claude/skills".
DEST="$HOME/.agents/skills"
if [ -e "$DEST/explain-and-report" ] || [ -L "$DEST/explain-and-report" ]; then
  printf '%s\n' 'A skill with this name exists. Back up and move the old version before installing.'
else
  mkdir -p "$DEST"
  unzip explain-and-report-v0.4.1.zip -d "$DEST"
fi
```

Confirm the installed path is `<DEST>/explain-and-report/SKILL.md`, without an extra version directory. Do not keep multiple versions of the same name in discovery directories. If the host has not refreshed, start a new session and recheck its skill list.

Teams may version **this source package**. It contains no PNG/JPEG files, run screenshots, or actual business reports. `assets/reference-layout.html` is a synthetic design-test source that can be rendered as a reference, not QA evidence from a report run.

## Static flow patterns (0.4)

`assets/flow-patterns.html` demonstrates task fan-out, independent inputs converging on a validator, labeled decision branches, and results crossing into aggregate acceptance. It is synthetic, static, and dependency-free. Copy it to an external run before previewing.

Plan essential relationships before drafting long prose, and check topology and coverage separately from layout. More figures are useful when they answer distinct questions; a fixed figure quota or a decorative chain does not establish clarity. See `references/diagrams-and-interaction.md`.

## Mechanism walkthrough (0.3)

The new `assets/mechanism-walkthrough.html` combines a branching flowchart, a step-by-step sequence replay, and a parameter/policy comparison in one synthetic cancellation example. It runs offline without dependencies. Copy it to an external run directory before previewing; do not generate screenshots in the skill repository.

Read `references/diagrams-and-interaction.md` to reuse only the relevant pieces. Change the old-result arrival time around the interruption boundary, toggle the generation guard, and watch the sequence, queue, and explanations update together. The sample includes the equality case and states its concurrency assumptions.

The instructions remain English; the sample uses Chinese to demonstrate the default report language. Upstream revisions and MIT notices are in `THIRD_PARTY_NOTICES.md`, with notices also embedded in the standalone sample.

## Everyday use

Invoke `$explain-and-report` in Codex, or `/explain-and-report` in Claude Code; you can also ask the agent to use the skill by name. See [sources](references/sources.md).

Instructions and UI metadata are in English. Deliverables follow the user's requested language or the language of their request, defaulting to Simplified Chinese when neither is clear. Bundled HTML templates retain Chinese sample content for that default; adapt labels and HTML `lang` for other languages.

### Explain complex content

```text
Use explain-and-report to clarify the system mechanism we just discussed.
Start with a direct answer, then use necessary diagrams to explain key relationships and boundaries.
Produce HTML; do not turn every paragraph into a card.
```

### System evaluation report

```text
Use explain-and-report to create a report from these evaluation results.
Include conclusions, metric definitions, failure cases, and uncertainties.
Produce HTML and review real browser screenshots.
```

### Publish to Feishu

```text
Use explain-and-report to generate a report, then use the installed Feishu document skill
to publish to the document I specify, updating only the “Current Experiment Results” section.
Keep the body editable, insert necessary figures, and retain sources and limitations.
Do not upload QA screenshots, change sharing permissions, or overwrite other people's edits.
```

Provide the target document link with the request. For new documents, specify the destination folder. If the target is missing, the agent completes local materials and clarifies the missing publication details.
For remote QA archiving, explicitly specify a separate restricted review document/folder and content scope. Sync support does not authorize automatic upload of future reports.

## Artifact locations

Default:

```text
~/.local/state/explain-and-report/
  runs/<project-name>-<path-hash>/<time>-<topic>-<random>/
    manifest.json
    delivery/report.html
    figures/
    qa/screenshots/
    qa/review.md
    publish/
```

Set `EXPLAIN_REPORT_HOME` to another **absolute path outside repositories**. If unset, an existing `XDG_STATE_HOME` overrides the default state root. On macOS, you may choose:

```bash
export EXPLAIN_REPORT_HOME="$HOME/Library/Application Support/explain-and-report"
```

Do not use `./reports`, ignored repository directories, installed skill directories, or Git LFS. To satisfy Feishu relative-path requirements, launch tools from the external publish directory instead of copying assets into the repository.
Keep body figures separate from review screenshots. Authorized report publication may include body figures; QA screenshots remain local by default. Files are not automatically deleted or uploaded to public image hosts.

## Scripts and dependencies

| Script | Purpose | Dependencies |
| --- | --- | --- |
| `report_workspace.py init/check` | Create external run directories, check paths, report repository image changes | Python 3.10+; git for Git-project checks |
| `check_report.py` | Preflight common HTML structure, external resources, and references | Python 3.10+, standard library |
| `capture_report.py` | Capture desktop/narrow-screen/diagram views, run basic browser checks, export body figures | Existing Playwright Python and Chromium |

Scripts do not install dependencies automatically. Without Playwright, use available host browser tools. Without image viewing, do not claim visual review.

From your source working directory, run a local smoke test using the synthetic design reference:

```bash
SKILL_DIR="$HOME/.agents/skills/explain-and-report"
# For Claude Code, use "$HOME/.claude/skills/explain-and-report".
INIT_JSON="$(python3 -B "$SKILL_DIR/scripts/report_workspace.py" init \
  --workspace "$PWD" --topic style-smoke)" || exit 1
RUN="$(printf '%s' "$INIT_JSON" | python3 -c 'import json,sys; print(json.load(sys.stdin)["run_dir"])')" || exit 1
cp "$SKILL_DIR/assets/reference-layout.html" "$RUN/delivery/report.html"
python3 -B "$SKILL_DIR/scripts/check_report.py" "$RUN/delivery/report.html"
python3 -B "$SKILL_DIR/scripts/report_workspace.py" check --run "$RUN"
# Run the next step only when browser dependencies are already installed.
python3 -B "$SKILL_DIR/scripts/capture_report.py" --run "$RUN" --export-figures
printf 'Run directory: %s\n' "$RUN"
```

HTML opens through `file://` by default. If the host prohibits this but permits loading HTML content, **explicitly** add `--load-mode content`. That mode records `file_protocol_verified=false`; it does not establish that double-clicking the local file works.
To select a browser, use `--browser /absolute/path/to/chromium`. Do not automatically download one or disable system security policies.

Captures record `source_html_sha256`; recapture after HTML changes. Passing machine checks still leave `visual_review=not_reviewed`. After viewing screenshots, the agent writes `qa/review.md` separately.

### Tests

```bash
python3 -B -m unittest discover -s "$SKILL_DIR/tests" -v
# Optional Node.js check of the exact inline mechanism model (no npm dependencies):
node --test "$SKILL_DIR/tests/test_mechanism.cjs"
```

Tests use temporary directories and temporary Git repositories, leaving the user's repository index untouched. `tests/regression-prompts.md` contains separate agent regression tasks; it does not claim those actual generation tasks have been executed.

## Package layout

```text
explain-and-report/
├── SKILL.md
├── README.md
├── agents/openai.yaml
├── THIRD_PARTY_NOTICES.md
├── references/
│   ├── diagrams-and-interaction.md
│   ├── presentation-rules.md
│   ├── storage-policy.md
│   ├── visual-qa.md
│   ├── feishu-publish.md
│   └── sources.md
├── assets/
│   ├── flow-patterns.html
│   ├── mechanism-walkthrough.html
│   ├── report-shell.html
│   ├── reference-layout.html
│   └── publish-plan.example.json
├── scripts/
│   ├── report_workspace.py
│   ├── check_report.py
│   └── capture_report.py
└── tests/
    ├── test_mechanism.cjs
    ├── test_workspace.py
    ├── test_html.py
    └── regression-prompts.md
```

## Main changes from v0.1

Content-led design with optional examples; all run artifacts stored outside repositories by default; separate roles for body figures, QA screenshots, and long-term references; screenshots bound to source hashes; and optional publishing through existing Feishu skills with image allowlists, readback, and protection for human edits.

This package does not implement persistent sync, a cross-platform pixel-regression service, repository-wide DLP, or a complete security sandbox. Path guards prevent mistakes; they cannot constrain another malicious process or replace access control.
