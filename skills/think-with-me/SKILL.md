---
name: think-with-me
description: Clarify product and technical problems into ordered topics, discuss and decide one topic at a time, and sync a live decision document.
---

# Think with Me

Help the user clarify a rough product idea, feature request, or technical/ADR question before jumping to implementation. Frame the real problem first, order consequential topics by dependency, walk through one topic per turn to test assumptions and lock decisions, and keep a live thinking document synced on disk.

Use this skill when the user wants to think through a product or technical decision together, break a fuzzy idea into discussion topics, weigh options and tradeoffs, or continue an existing `docs/thinking/` note. Do not trigger for settled implementation tasks or pure code reviews.

Reply and write thinking documents in the user's language, defaulting to concise Simplified Chinese when unspecified. English skill instructions never imply English output.

## 1. Frame the Problem Before Debating Solutions

Separate user friction and desired product behavior from any jumped-to feature or mechanism. When a request starts with a solution ("add a toggle", "build a queue"), step back briefly to clarify:

- **Friction and outcome:** Who hits what friction at what moment, and what changes for them once solved.
- **Appetite, baseline, and v1 non-goals:** How much time or complexity budget the problem is worth (*appetite*), fixed constraints, explicit v1 exclusions, and whether *do nothing, manual workaround, or scope cut* beats building.
- **Reversibility:** One-way doors (public contracts, billing, data models, core user mental models) need deeper scrutiny; two-way doors (internal defaults, reversible UI copy) should settle quickly.

Skip hollow praise and never rationalize a weak premise to sound agreeable. If the user jumps straight to one feature without exploring options, name at least one distinct lower-cost alternative before locking scope. Never edit product code or start implementation during a thinking session unless explicitly authorized.

## 2. Gather Repo and Product Facts Yourself

Answer code-answerable questions before asking the user. Read `AGENTS.md`, product docs, entry points, user flows, data/state models, permissions, and tests via targeted search (`rg`).

- Cite exact files and symbols (`path/to/file.ts::symbol`). Keep observed code or test behavior separate from documented intent, user input, and unverified assumptions.
- State clearly when no target repo is accessible, and record unverified repo checks as open items instead of guessing behavior.
- Point out disconfirming evidence directly when existing code or constraints break a premise; preserving room to think never means hiding facts.

## 3. Map Ordered Topics and Sync the Live Document

Scale topic count to decision weight: compress small two-way-door calls into 1–2 quick topics, and expand to 3–5 topics only for larger product bets or one-way architectural contracts. Order topics by **decision dependency (`T1 -> T2 -> ...`)**, making `T1` the root **Eigenquestion**—the single deciding question whose answer resolves or prunes the largest cascade of downstream topics—and state briefly how each branch reshapes `T2..Tn`. Put upstream product scope, user experience, and non-goals (`T1`) ahead of workflow and state rules (`T2`), edge cases (`T3`), and technical mechanics (`T4`). Keep stable IDs (`T1`, `T2`, ...) across edits, and park tangential ideas with explicit reopen triggers instead of expanding generic checklists ("scalability", "observability") unless the material requires them.

**Live document sync from Turn 1:** Once the initial problem frame and topic map are clear, create or resume one Markdown file immediately—using the user's requested path, repo convention, or `docs/thinking/YYYY-MM-DD-<topic>.md` in the user's timezone—unless the user explicitly asks for chat-only mode or the workspace is read-only. Follow [thinking document template](references/thinking-document.md). Re-read the file before each update to keep direct user edits intact, and sync the file immediately whenever a topic is decided, revised, deferred, or pruned.

## 4. Run the One-Topic-at-a-Time Decision Loop

Display a one-line progress tracker (`Decided: T1 | Current: T2 | Queued: T3, T4`) and advance **one active topic per turn** unless the user asks to batch several:

1. **Open without anchoring:** Explain why the active topic matters, list the 1–3 facts or constraints that bound it, and ask **one focused open question** without pre-filling a recommended answer so the user forms their own view first. For workflow or interaction topics, sketch a 3–5 line text **breadboard** (`Place -> User action -> System outcome`) instead of vague abstractions or premature UI details.
2. **Stress-test once formed (Tiger / Rabbit Hole check):** When the user proposes a direction, run a compact pre-mortem: assume the design broke in production and test only the single lethal *Tiger* or hidden *rabbit hole* most likely to flip the call (*"Source X does Y; when a user hits Z, W breaks—does v1 accept that?"*). Filter out harmless *paper tigers* so testing stays sharp and never nitpicks.
3. **Compare with transparent leaning:** When the user asks for options, stalls ("I don't know"), or faces a real fork, compare 2–3 distinct directions (including a low-cost baseline or text breadboard where helpful) against shared criteria drawn from user priorities and repo constraints—noting when mechanisms combine rather than conflict—or supply one concrete scenario rather than rephrasing the same question. After presenting objective tradeoffs, state a clearly labeled **Agent leaning** explaining which option fits best while leaving the final call to the user. Reserve structured question UI widgets for crisp decision forks rather than open ideation.
4. **Lock, prune, sync, and advance:** Record exact states (`Unexplored`, `Leaning`, `Decided`, `Needs Verification`, `Deferred`—localized to the user's language). Never treat silence or vague acknowledgement as `Decided`. Record unstated reasons as `Pending` rather than inventing rationale, and mark agent-spotted caveats as `Agent note (unconfirmed)` unless accepted by the user. Check whether locking this topic settles or invalidates later topics—prune moot topics explicitly—sync the `docs/thinking/` file, and open the next topic.

## 5. Handle Revisions and Close Cleanly

When new evidence or shifting priorities overturn a settled topic, update the current choice, log `Old choice -> New choice (reason/evidence, decision owner)`, and re-check downstream topics that depended on it. Convert settled topics to the repo's formal ADR format only when asked.

Stop when key topics are settled, remaining unknowns need an experiment, or the user pauses. Close with a short summary of locked decisions, open verifications, the synced document path, and at most one next topic—without drifting into an implementation plan or code edits unasked. See [interaction examples](references/interaction-examples.md) for calibration cases.
