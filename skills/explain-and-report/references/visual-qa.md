# Visual Review: Real Screenshots and Separate Verdicts

## Minimum review workflow

Review the final content's evidence and metric definitions, run static preflight, then open the actual HTML. Follow the user's and project's browser policy. Use an authorized existing browser connection; use the optional bundled Playwright script only where that execution method is permitted and its dependencies already exist. If the host requires a Chrome connection and it fails, do not fall back to another browser, headless automation, or native desktop control. Continue independent checks and report the unavailable browser validation. Do not install browsers/dependencies automatically or use external screenshot services.

```bash
python3 -B <skill-dir>/scripts/apply_report_theme.py --run <run-dir>
python3 -B <skill-dir>/scripts/check_report.py <run-dir>/delivery/report.html --require-theme
python3 -B <skill-dir>/scripts/report_workspace.py check --run <run-dir>
# Only where the host permits this browser route and dependencies already exist:
python3 -B <skill-dir>/scripts/capture_report.py --run <run-dir>
```

The apply command embeds canonical CSS and refreshes an existing standard `report-navigation` script, preserving article content, local styles, and unrelated scripts. It does not add missing navigation markup or migrate arbitrary HTML. `--require-theme` detects a missing or changed CSS block, not navigation compatibility, local overrides, or computed appearance. For an explicitly requested alternate theme, omit the apply command and that flag, keeping the remaining checks. Inspect local CSS and compare actual rendering with the shared reference for the default theme.

The capture script records desktop, narrow-screen, dense-section, ending, and key-figure views, plus no-JS, offline, and print-style checks. Host browser tools may perform the same checks; record which were actually possible. Use `--export-figures` only when body-figure export is needed. Exported figures stay outside repositories.

Default viewports: desktop 1440×1000, narrow screen 390×844. Record browser version, device scale, theme, system fonts, and source HTML SHA-256.
Inspect the first screen, densest passage, key figures, and ending. Long reports require more than a first-screen check. Inspect tables, long code, and complex sequence diagrams separately.
Core text, numbers, and sources must remain visible without JS. Reload with networking blocked instead of merely opening cached content. Check page-level horizontal overflow, broken images, console errors, contents navigation, expand controls, and keyboard focus.
`--load-mode content` is for hosts that explicitly restrict file://. It loads the source HTML and retains offline checks, but does not verify the local file protocol. Do not silently fall back and claim full verification.
Record print-style preview separately from actual printing/PDF inspection. The bundled script only previews print-media styles; it does not produce a PDF.

## Reader check

For substantial skill changes or representative evaluations, use a reader who did not generate the report. First show only the report and neutral questions: what is the question, judgment, decisive evidence, and unresolved matter? For a decision, ask what is recommended and under which conditions. Require evidence locations in the text, figure, or table; repeating the title is insufficient.

Save the reader's first answers before showing source inputs. Then compare them with the inputs, keeping expected answers on the evaluation side. Record rereads, unfamiliar terms, misleading diagrams, and passages removable without losing the reasoning. Mark agent reading as agent evidence, not human/user acceptance. A pass requires the essential meaning, supporting evidence, and material qualifications to be recovered without unsupported claims. If a reader misunderstands, revise the report and recheck the affected question without supplying the answer; retain the initial failure.

Check concision separately. Record representative before/after edits and the conditions retained, or why a repeated point serves preview, local comprehension, or verification. Preserve accessible equivalents. Correct recall alone does not establish concise writing, and fewer words do not establish better comprehension. Claim improvement over an earlier version only after comparable before/after reading checks.

## Skill-change regression

Keep three results separate: **revised existing samples**, **template/script checks**, and **fresh generation with the updated skill**. For the readability regression set, generate architecture, incident, and comparison cases from their original inputs into new external runs. Give generators only the current skill, task inputs, and needed source materials—not old outputs, diagnoses, or answer keys. Add one coherent input variant that changes the decision; keep its expected answer with the evaluator. A case already included in a reference is a known-case regression, not evidence of unseen-task generalization.

Record skill version and file hashes, input, exact generation instruction, and the first output before editing. Keep later revisions and checks distinguishable. For the synthetic cases, use questions such as:

| Case | Neutral reading questions |
| --- | --- |
| Architecture | What does “saved” confirm? Where do searches read? What happens when versions 12, 11, and 12 arrive? What does the atomic operation protect? What timing, if any, is promised? |
| Incident | What can have happened remotely after a timeout? What does the final local receipt establish? What conditions limit deduplication? What is the repair's verification status? |
| Comparison | What is recommended, and which evidence decides it? What do 29 seconds and 62 seconds each measure, and what comparison do they support? What statistic is 1.3 seconds? What would change the choice? |
| Variant | What is this report's judgment, under which conditions, and where is its supporting evidence? |

The variant reader sees only that report. The evaluator compares its answer with the variant input and baseline afterward; do not ask a blind reader what changed from an unseen baseline.

Run affected script tests, static/theme checks, and the relevant tasks in `tests/regression-prompts.md`, including the deletion task when changing editorial guidance. Update only statuses backed by actual execution. First-generation failure and post-edit success are different results. Keep the record in external QA; do not grow a testing platform or use word/figure quotas as acceptance.

## Visual coverage for a skill revision

Create a file-by-check matrix in external QA. Copy fixed sources into external runs before previewing. Each row identifies the final HTML hash; each check is passed, failed, or not run, with evidence or a reason. Apply the following coverage to the readability regression set; ordinary report delivery needs only its own row.

| Files | Specific focus, in addition to the shared checks below |
| --- | --- |
| `assets/reference-layout.html` (Explain) | Mechanism, default case, boundaries, and ending |
| `assets/reference-report.html` (Report) | Recommendation, decisive evidence, tradeoffs, methods, and change conditions |
| `assets/flow-patterns.html` | Containment, input merge, decision branches, aggregate evidence/unknown state |
| `assets/mechanism-walkthrough.html` | Atomic boundary, fixed default case, current scenario, sequence and controls |
| Three revised sample reports | Every changed figure or passage, including narrow version decisions and comparison thresholds |
| Three freshly generated reports plus the input variant | Each report's own layout and final content; previous sample captures do not cover them |

For **each final report**, run the minimum review workflow above at 1440×1000 and 390×844: opening, key figures, dense passages, and ending, plus no-JS, offline reload, and print preview. Simple diagrams must associate inputs, condition, and outcome without repeated sideways scanning. Record actual print/PDF inspection separately from print-media styling.

The shared navigation controller's behavior may be regression-tested once per unchanged implementation, but verify each report's anchors, deep links, outline placement, and interaction with its figures. Use the navigation checks below; script tests do not replace browser evidence.

When the user explicitly defers visual acceptance, leave these checks **not run—deferred by request** and retain the matrix for later acceptance. An unavailable permitted browser is a different reason. Neither permits claiming visual acceptance from source inspection, DOM checks, or old screenshots.

## Mechanism and interaction checks

For reports with the shared outline, also check reading navigation:

- At the start, middle, and end of `main`, verify progress and the current-section marker against the visible content. Progress reaches 100% when the article's end is visible; footer space does not extend it. Opening the floating directory must not change progress or the active section. Check an article that fits in one viewport too.
- Open a section deep link, follow outline links, and resize across the sidebar breakpoint. Headings must remain visible with the same top inset whether the floating directory is open or closed. Check collapse after a link or outside tap, and keyboard focus including Escape.
- On narrow screens, check the compact entry near the bottom safe area and the panel opening above it. The panel must scroll to its last link without page overflow; final article text and links must scroll clear of the entry. The percentage must not intercept the directory button's pointer input.
- Disable JS: static outline links and the entire article remain usable, without a false progress value. Check layout changes after figures load or details expand. Inspect the rail alongside the densest figure so navigation does not reduce labels below readable size.

`node --test <skill-dir>/tests/test_navigation.cjs` checks navigation calculations and controller behavior with DOM doubles. It does not establish real scrolling, focus, sticky layout, or visual acceptance.

For diagrams and replay, read `diagrams-and-interaction.md`. Check the reader's actual question: can they locate the decision, identify the state that changed, and explain why a different condition changes the result?

- Exercise all controls, including previous/next boundaries, reset, pause, replay, and parameter changes during playback. Changing settings must not leave a stale timer advancing another scenario.
- Check a case on each side of a decision boundary and the equality case. Check diagram labels, selected event, queue/state values, and explanatory text together.
- Record which scenario and event each screenshot shows. The generic capture script captures the currently rendered state; it does not validate custom controls or enumerate scenarios.
- `data-interactive` marks optional dynamic regions excluded from the script's no-JS core-text comparison. Keep the conclusion, mechanism, and complete default example outside those regions. Do not mark the entire report interactive to bypass validation.
- Keep labels readable, controls named, states distinguishable with text, and playback pausable. No separate accessibility framework or formal compliance audit is required.

When exporting to Markdown, print, or Feishu, retain the static explanation and label representative before/after states with their settings. A screenshot of one selected event cannot stand in for the entire mechanism.

## Files and statuses

Each capture gets a separate `qa/screenshots/<source-hash>-<capture-id>/`; do not overwrite earlier evidence.
The script generates `capture.json`, retaining `visual_review: not_reviewed` and `content_review: not_reviewed` even when machine checks pass.
After an agent or reviewer actually inspects the images, write a separate `qa/review.md`:

```markdown
# Review for This Run
- Source HTML SHA-256: actual value
- Capture batch: actual relative path
- Content and evidence: passed / issues / not reviewed; explanation
- Reader understanding: passed / issues / not checked; record recovered meaning and any material misunderstanding
- Editorial deletion pass: passed / issues / not checked; note removed repetition or the purpose of retained repeats
- Diagram coverage and topology: passed / issues / not applicable; questions answered, missing relationships, and evidence status
- Generation evidence: revised sample / template-script regression / fresh generation; input, instruction, skill hashes, first output, and revision paths
- Static preflight: passed / issues / not run
- Browser machine checks: passed / issues / not run
- Visual review: passed / issues / not reviewed; identify agent or human reviewer
- Visual identity: shared theme / explicit user override; note the request for any override and inspect local CSS for unintended restyling
- User style approval: not requested / candidate / approved; cite actual approval evidence
- Feishu readback: not requested / verified / partial / unverified

## Findings and Fixes
Record specific locations, problems, changes, and recheck results. State review scope even if no issues were found.

## Not Covered
For example: Safari not tested, actual printing not verified, or no real business evaluation performed.
```

Recapture after changing source HTML; an old hash cannot represent the new artifact. Do not edit capture.json to fabricate passing checks.

## Judge visual quality, not only overflow

1. **Information hierarchy:** the opening makes the question, answer, and material limitations easy to find. Each section advances the explanation. Remove repeated conclusions across prose, diagrams, and captions; keep supporting identifiers and methods from interrupting the main thread. Concision passes only when the causal chain, evidence, and qualifications survive.
2. **Reading quality and identity:** retain the shared palette, type hierarchy, borders, captions, and status meanings across reports, unless the user requested a different style. Compare with the relevant Explain or Report reference; the content layout need not match. Check local CSS and SVG colors for overrides even when `--require-theme` passes. Dense passages, tables, and code must remain readable. Check actual contrast, targeting at least 4.5:1 for body text and 3:1 for large text and essential non-text graphics; see `sources.md`.
3. **Diagram quality:** trace each essential relationship against the evidence. Inputs, decisions, ownership, and aggregation retain their meaning. A reader can locate the failure and distinguish observed from proposed behavior. Check arrow routing and readable labels at the actual rendered scale. SVG font-size alone is insufficient when a wide viewBox is scaled down. Reflow simple diagrams; preserve readable labels and use local scrolling for irreducibly wide sequences. Boxes, SVG counts, and decorative arrows alone do not pass.
4. **Complete presentation:** desktop and narrow-screen layouts work, disabling JS loses no information, and key content is not hidden behind interaction.

Fix missing essential text, occlusion, incorrect labels, and evidence available only on hover. A “visual score of 95” cannot replace actual findings.

## Distinguish body figures from review screenshots

Body figures explain or document the subject: diagrams, charts, and inspected evidence images such as failure screenshots. Report-layout QA screenshots show how the current report renders and stay out of its body by default. Check that evidence images are legible, captions identify the relevant case, and the visible content supports the nearby claim. See `presentation-rules.md` for image treatment.
`--export-figures` exports only regions with `data-figure-id`, still outside the repository. A region may include its caption, but retain an editable caption and explanation in Feishu as well.
Review evidence must come from real browser screenshots, not ImageGen concepts, manually assembled images, or DOM-based guesses.
A design reference may be an authorized mockup, but that does not prove the current HTML achieves the same effect.

## Fixed-baseline regression (optional)

Fixed inputs and HTML test source may be versioned. Keep baseline PNGs in an external style-library or an authorized restricted remote location.
New results are candidates by default and must not automatically overwrite approved baselines. Before comparison, align viewport, browser, fonts, scale, and dynamic fields.
Without approved baselines, review clarity, evidence, and usability; do not fabricate pixel regression. Do not require pixel equality across different content.
