# Diagrams and Interactive Mechanisms

Use this guide when readers need to follow a process, understand event order, or see how changing a condition changes the outcome. The goal is understanding, not a quota of diagrams or controls.

## Choose the representation

| Reader question | Representation | What must be visible |
| --- | --- | --- |
| Where does the process branch or fail? | Flowchart | Actor/action nodes, decision condition, labeled outcomes, relevant failure path |
| Who talks to whom, and in what order? | Sequence/swimlane diagram | Stable actor lanes, labeled messages, known ordering, concurrent work where supported |
| What changes after this event? | State diagram or event replay | Before/after state, event, guard/condition, resulting effect |
| Why does another setting produce a different result? | Scenario comparison or parameter control | Same input/baseline, changed assumption, immediate result and explanation |
| Where are the boundaries and dependencies? | Architecture diagram | Ownership/containment, named relationships, evidence for each connection |

Use a static diagram when it fully answers the question. Use a local interactive figure when stepping or changing one condition reveals something that the static view cannot show as clearly. Preserve prose for reasoning, exceptions, and limitations.

## Plan coverage before writing the report

Build a short question-to-figure map in working notes. For each essential relationship, record the reader's question, the figure that answers it, and whether it is observed, inferred, proposed, or illustrative. This can be a few lines, not a separate planning deliverable.

For a diagnosis, start with the actual path and its failure, then show the proposed change if requested. Add a separate overview or implementation view only when it answers another necessary reader question. These are choices, not a required four-figure outline. Put the main mechanism after the answer and limitations; keep code-level detail in an appendix when it is only needed for lookup.

| Relationship in the evidence | Draw it as | Misleading shortcut |
| --- | --- | --- |
| One task contains several work items | Parent with separate outgoing edges or explicit containment | One child after another, implying order |
| Rules and a record are separate inputs to an evaluator | Two labeled paths converging on the evaluator | Rules → record → evaluator |
| A decision has supported alternatives | Condition with separately labeled exits | A chain showing only success |
| Several results feed a final assessment | Incoming result edges plus the aggregate's own criteria | Two unrelated text columns |
| Ownership or scope changes | Named boundary crossed by a labeled data edge | Color alone or a floating “scope” heading |
| Current and proposed behavior differ | Aligned views with stable names and the changed edge/condition marked | Different layouts that obscure what changed |

`assets/flow-patterns.html` is a standalone synthetic example of fan-out, converging inputs, branching, and aggregation boundaries. Copy only the relevant figures and styles into an external run. It is static by design; rich diagrams do not require animation. The existing `mechanism-walkthrough.html` covers sequence replay and state changes.

## Preserve topology and evidence

- Every arrow is a claim. State whether it means containment, data transfer, a decision outcome, or time order. Do not imply concurrency or execution order from a task hierarchy.
- Trace independent inputs separately to their first shared consumer. A required input may be absent; show that absence explicitly instead of drawing an edge implying it was supplied.
- Keep different levels distinct: a task, its execution record, and an evaluator are not interchangeable steps. Use lanes or groups when their ownership matters.
- Mark the failure at the responsible edge or condition. Distinguish a persisted outcome/reason from an inferred cause and a proposed correction. Do not turn a model's saved explanation into a fictional internal execution trace.
- Show both exits of a documented rule. If evidence shows only one outcome and the rule itself is unknown, draw the observed path and label the unknown; do not invent an alternative to fill a diamond.
- Give every figure a short conclusion and nearby evidence/status. Place arrow labels away from lines and node text. Use unique marker IDs when combining SVG figures.

Use prose for why the relationship matters, evidence qualifications, and exceptions. Keep a concise accessible equivalent (SVG description or adjacent prose), but remove a paragraph that merely recites all visible nodes again. Preserve the equivalent in Markdown/Feishu along with static figures where supported.

## Draw the mechanism

Start from one concrete case, not a collection of component names. Write its input, events, state changes, branch condition, and outcome before drawing.

- Give each diagram one question and one takeaway. Split an oversized graph into an overview and focused details.
- Label arrows with actions/data; label decision exits with the actual condition or yes/no meaning. Distinguish rejected, cleared, pending, and accepted states with words.
- Keep the same actors and names across the overview, replay, and comparison. Do not mix components, business phases, and implementation details at one unexplained level.
- Draw SVG edges before nodes; use actual SVG lines/paths and arrow markers. Reserve room for labels. Reflow small diagrams or scroll irreducibly wide sequence diagrams locally; do not shrink labels beyond readability.
- Show real timestamps only when supported. Event rows do not imply equal durations. Label synthetic timing and equality/tie-breaking assumptions explicitly.
- Draw the relevant exception path, not only the success path. If an exception is unknown, label the gap rather than inventing a branch.

## Three reusable patterns

`assets/mechanism-walkthrough.html` is a runnable, dependency-free synthetic example with all three patterns. Copy it into an external run directory before previewing or adapting it. Reuse the relevant figure, CSS, and script parts; do not impose its entire outline or cancellation topic on every report.

### 1. Branching flow

The example separates interruption actions from result admission: interruption advances a generation number and clears the existing queue; each returning result is checked against the current generation before admission. The yes/no branches make the exact intervention point visible.

For another process, replace actors, guards, and effects together. A row of three cards is sufficient only when the process really is linear.

### 2. Event replay

Each step represents one event, not one paragraph revealed. Keep the full sequence visible and emphasize the selected event. Show its timestamp/order, changed state, and the reason for the transition next to it.

The example opens at the final snapshot so the result is visible immediately. Readers can step backward/forward, scrub, return to the start, or play/pause. Playback uses a fixed reading cadence, explicitly unrelated to simulated elapsed time. Nothing autoplays.

Use recorded events for real trace replay. For an illustrative simulation, label it as such and state simplifications. Do not animate inferred events as if they were observed.

### 3. Parameter and policy comparison

Change only a meaningful input or assumption: arrival order, retry limit, queue capacity, cache lifetime, or a policy switch. Keep the compared cases otherwise identical.

The example varies old-result arrival time around a fixed interruption time and compares generation checking on/off. Before interruption, the old result can enter and then be cleared; after interruption, the guard determines whether it re-enters. At equal timestamps, the model explicitly processes interruption first.

One pure `simulate(settings)` returns event snapshots. The selected snapshot drives the sequence highlight, queue, generation value, event list, and caption. The comparison runs the same model with each policy. Avoid separate hard-coded prose or chart calculations that disagree after an input changes.

## Implementation scope

Keep this version small: inline SVG, semantic HTML, a pure model, and a local controller. Use ordinary labeled buttons and ranges, readable text, textual status, and pause/reset. No dependency, reusable component framework, formal accessibility audit, autoplay, or ornamental animation is needed.

Keep a complete static explanation and default case outside optional `data-interactive` regions. Initially hide controls, render successfully, then reveal them. No-JS and print readers must still understand the conclusion and mechanism. Do not hide the entire article in a dynamic mount.

Never put untrusted source text into executable JavaScript or HTML strings. Use safe serialization for embedded data and `textContent` for labels. The demo uses only authored synthetic values.

Changing an input or manually choosing a step pauses playback. Starting again at the final event begins a fresh replay. Stop timers at the end, when the page is hidden, and before print. A reset must say what it resets: the example's “Back to start” resets the event index while preserving the current scenario.

## Adaptation and verification

1. Specify the reader question and the condition the figure will make visible.
2. Replace the synthetic scenario with supported behavior, or clearly label the new model as illustrative.
3. Keep all representations driven by the same state. State concurrency assumptions; for example, the demo treats generation-check-plus-enqueue as indivisible and does not model audio consumption.
4. Check both outcomes, equality boundaries, first/last steps, reset, replay, pause, and changes during playback. Model tests do not prove the browser controls or layout work.
5. Inspect the final browser rendering at desktop and narrow widths. Record the selected scenario and event with screenshots. Respect the host's browser restrictions; a failed Chrome connection is not permission to use another browser or native desktop control.
6. For Markdown/Feishu, include the static diagram and representative labeled states plus the conclusion. Never pass a moving diagram off as a single unexplained screenshot.

Before screenshot review, trace the arrows as a reader: where does each input originate, which condition changes the route, what leaves each responsibility boundary, and where does the observed failure occur? Compare this with the question-to-figure map. Fix missing relationships and misleading edges; a diagram that repeats prose without exposing structure does not close a coverage gap.

The bundled model tests run with `node --test <skill-dir>/tests/test_mechanism.cjs`; they read the exact inline model and controller from the HTML. Controller tests use small DOM/timer doubles; they do not prove layout or real-browser interaction.

## Upstream sources

Patterns selectively adapted from these pinned MIT sources:

- `nicobailon/visual-explainer`, commit `69cd7395cee2979aa7301ebe51bb4c2ba5f5ef9e`: [diagram rules](https://github.com/nicobailon/visual-explainer/blob/69cd7395cee2979aa7301ebe51bb4c2ba5f5ef9e/plugins/visual-explainer/references/diagrams.md), [page template](https://github.com/nicobailon/visual-explainer/blob/69cd7395cee2979aa7301ebe51bb4c2ba5f5ef9e/plugins/visual-explainer/templates/page.html). Retained branch labeling, complete-overview-first replay, and a shared model for live figures. Omitted its mandatory figure-heavy writing, CDN resources, decorative motion, and broader presentation system.
- `joshuadavidthomas/agent-skills`, commit `516dee7a422b90937b2958d11c03694154ab9c09`: [component contracts](https://github.com/joshuadavidthomas/agent-skills/blob/516dee7a422b90937b2958d11c03694154ab9c09/html-artifacts/references/component-contracts.md). Retained the question → action → visible-answer test, full process visibility, and synchronized state updates. Omitted its shared CSS/component system and geometric compliance requirements.

See `../THIRD_PARTY_NOTICES.md`. The example embeds the license notices so a copied standalone file retains attribution. Keep those notices when redistributing adapted code; do not automatically install or update the upstream skills.
