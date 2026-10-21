# Visual Review: Real Screenshots and Separate Verdicts

## Minimum review workflow

Review the final content's evidence and metric definitions, run static preflight, then open the actual HTML. Use existing browser tools or the optional bundled Playwright script. Do not automatically install browsers/dependencies or use external screenshot services.

Default viewports: desktop 1440×1000, narrow screen 390×844. Record browser version, device scale, theme, system fonts, and source HTML SHA-256.
Inspect the first screen, densest passage, key figures, and ending. Long reports require more than a first-screen check. Inspect tables, long code, and complex sequence diagrams separately.
Core text, numbers, and sources must remain visible without JS. Reload with networking blocked instead of merely opening cached content. Check page-level horizontal overflow, broken images, console errors, contents navigation, expand controls, and keyboard focus.
`--load-mode content` is for hosts that explicitly restrict file://. It loads the source HTML and retains offline checks, but does not verify the local file protocol. Do not silently fall back and claim full verification.
Record print-style preview separately from actual printing/PDF inspection. The bundled script only previews print-media styles; it does not produce a PDF.

## Mechanism and interaction checks

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
- Diagram coverage and topology: passed / issues / not applicable; questions answered, missing relationships, and evidence status
- Static preflight: passed / issues / not run
- Browser machine checks: passed / issues / not run
- Visual review: passed / issues / not reviewed; identify agent or human reviewer
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
2. **Reading quality:** typography and composition suit the content and language; dense passages, tables, and code remain readable. Judge the result rather than its resemblance to a bundled template. Check actual contrast, targeting at least 4.5:1 for body text and 3:1 for large text and essential non-text graphics; see `sources.md`.
3. **Diagram quality:** trace each essential relationship against the evidence. Inputs, decisions, ownership, and aggregation retain their meaning. A reader can locate the failure and distinguish observed from proposed behavior. Check arrow routing and readable labels; boxes, SVG counts, and decorative arrows alone do not pass.
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
