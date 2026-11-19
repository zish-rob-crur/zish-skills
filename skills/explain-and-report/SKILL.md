---
name: explain-and-report
description: Create visual HTML reports that explain complex systems, workflows, or evaluations.
metadata:
  version: "0.5.1"
---

# Explain & Report

Build technical reports readers understand in 5 seconds and can articulate clearly afterward. Pair a 5-second executive judgment with intuitive mental-model contrasts, domain-first diagrams, and traceable evidence. Write strictly about the subject; never leak UI instructions or production notes into report prose.

## Scope, Deliverable, and Boundaries

| Mode | Reader's question | Reading flow |
| --- | --- | --- |
| Explain | What happens, and how does it work? | 5-second snapshot (`.summary-grid`) → contrast (`.mental-model`) → concrete walkthrough & mechanism → boundaries |
| Report / ADR | What is decided/assessed, why, and what reverses it? | 5-second decision snapshot (`.summary-grid`) → decisive evidence → tradeoffs & baseline → change conditions |

- **Task-named HTML deliverable:** Deliver one offline HTML file named after the task slug, **`<run_dir>/delivery/<task-slug>.html`** (e.g., `delivery/sync-file-loss-adr.html`, never generic `report.html`), or write directly to the user's requested `--output` directory or `.html` path. Add `<task-slug>.md` only when requested. Default to Simplified Chinese (`lang="zh-CN"`) unless the request uses or asks for another language.
- **External QA & workspace:** Keep default deliverables, figures, QA screenshots, and publish payloads outside repositories (`references/storage-policy.md`). When the user specifies a custom output path (even inside a repo `docs/` folder), send only the final self-contained HTML there while keeping `run_dir` outside all repositories, and never write inside the skill source directory.
- **Separate verdicts and strict authorization:** Verify factual correctness, reader comprehension, visual quality, and user approval independently. Publish or redact strictly within explicit user authorization.

## 1. Frame the Question and External Workspace

Infer audience, central question, evidence, and open unknowns from context; ask only what changes the outcome. Before writing files, initialize an external run directory with a concise English `--topic` slug (passing `--output <dir-or-file.html>` or `--output-dir <dir>` when the user specifies an output location):

```bash
python3 -B <skill-dir>/scripts/report_workspace.py init \
  --workspace "$PWD" --topic <task-slug> [--output <dir-or-file.html>]
```

Write the final HTML to the returned `report_path` and keep all intermediates, figures, and QA artifacts under `run_dir`. If no authorized directory is writable, answer in chat and note the limitation.

## 2. Structure Prose and Visuals for Comprehension

Read `references/presentation-rules.md` and `references/diagrams-and-interaction.md`.

- **5-second Executive Snapshot (`.summary-grid`):** Place four concise cards directly under `.lead`: (1) **核心判断 / 决策**, (2) **决定性依据 / 机制发现**, (3) **适用边界 / 样本口径**, and (4) **核心归因 / 机制要旨** (a 1–2 sentence takeaway the reader can immediately repeat).
- **Zero UI or build leaks:** Keep words like `"悬浮目录"`, `"一句话怎么讲"`, `"鼠标悬停即可弹出预览"`, or `"点击切换查看"` out of all headings, prose, labels, and captions.
- **Decision-driven `<h2>` assertions and distinct roles:** Organize around 3–5 reader decision questions rather than mirroring PR file lists. Write short bottom-left TOC labels (`4–8 字`), write body `<h2>` headings as full assertion sentences, jump straight into causal reasoning after `.lead` without repeating it, and reserve `<figcaption>` for denominators, source IDs, and excluded cases.
- **Natural Chinese prose + concrete grounding:** Keep pre-verbal `的` modifiers `<= 2` layers, replace `对…进行了合并` with `合并`, and cut `不是简单的 X，而是 Y` filler. Follow every 1–2 sentences of abstract mechanism with a named case walkthrough (`J-104`, `E1→E5`, `Round 4`).
- **Contrast before mechanics (`.mental-model`):** Open complex mechanisms with a Counterexample vs. Design block showing what fails without the rule.
- **Low code density & telegraphic tables:** Explain domain meaning before code symbols. Keep inline `<code>` tags `< 6` per paragraph or `<td>`, cap `<strong>` in prose at 1–2 deciding phrases per paragraph, keep comparison rows to 4–6 dimensions, and structure each `<td>` as `[.badge] + <strong>≤8 字结论</strong> + concise sentence (≤40 chars) + [.jump-pill / cite-ref]`. Move paths, signatures, schemas, and diffs into `<details>`, `.sidenote`, `.diff-box`, or `#evidence`.
- **Margin caveats:** Place statistical caveats, unverified assumptions, and scope bounds in `.with-sidenote` / `.sidenote` or `.caveat-box` instead of derailing main prose.
- **Evidence-bound diagrams:** Use responsive CSS Grid diagrams (`.batch-map`, `.guard-map`) for containment or branching, `.trace-stream` / `.turn-row` for sequential traces, and external `.chart-legend` / `.milestone-strip` blocks for multi-clause SVG legends. Add interaction only when toggling parameters or inspecting events exposes behavior; keep one complete default state visible without JS.

## 3. Apply the Theme and Wide Layout

Default to **Zish Technical** (`assets/report-theme.css`) with `assets/report-shell.html` (`assets/reference-layout.html` for Explain; `assets/reference-report.html` for Report/ADR). The theme pairs charcoal dark mode and a warm-paper `[data-theme-toggle]` light mode with a wide canvas (`--page-max: 1620px; --wide: min(var(--page-max), 96vw)`), `--body: 52rem` prose measure, and `100%` container width for grids and side notes.

Embed `assets/report-theme.css` unchanged via `apply_report_theme.py`. Keep local CSS scoped to report diagrams without overriding global palette or typography; if the user asks for a different style, document the override in `qa/review.md`.

## 4. Build Offline HTML

Use semantic HTML and inline CSS/SVG; forbid external CDNs, fonts, analytics, or remote scripts. Keep all judgments, evidence, and default figures readable offline without JS; collapse only bulky raw specs or logs inside `<details>`.

Keep the shell's `<aside class="reading-rail">`, `[data-theme-toggle]`, and inline `assets/report-navigation.js`:
- **Bottom-left floating TOC (`目录`):** Hover-to-preview, click-to-pin, reading progress bar (mark appendix links `.nav-sub`; degrades cleanly inline without JS).
- **Popovers & detail drawer:** `[C1]` citation links (`<dt id="C1">` + `<dd>`) and `[data-tip-title]` elements render popovers automatically; `.jump-pill[data-drawer-target]` triggers the bottom-right hover-to-preview / click-to-pin drawer (`.explorer-float-drawer`).

Embed relevant error or evidence screenshots with source captions; give exportable figures unique `<figure data-figure-id="...">` slugs; HTML-escape external data and redact sensitive text before sharing.

## 5. Verify Content, Checks, and Visuals

Follow `references/visual-qa.md`. Before browser checks, read the rendered copy once for information gain, run the editorial deletion pass in `references/presentation-rules.md`, and verify zero UI meta-commentary leaked. Then run static validation, workspace checks, and browser inspection (desktop `1440x1000`, narrow `390x844`, no-JS, key figures, and ending):

```bash
python3 -B <skill-dir>/scripts/apply_report_theme.py --run <run-dir>
python3 -B <skill-dir>/scripts/check_report.py <report-path> --require-theme
python3 -B <skill-dir>/scripts/report_workspace.py check --run <run-dir>
```

Record static checks, visual inspection, content review, and user approval separately in external `qa/review.md`; recapture screenshots after any HTML edit.

## 6. Publish and Deliver

Publish to Feishu only when requested (`references/feishu-publish.md`), inserting external figures with readback verification while preserving human edits. Deliver `<report-path>`, the core conclusion, checks actually executed, and open unknowns without repeating the report. Never commit, stage, or clean up artifacts inside repositories without permission.
