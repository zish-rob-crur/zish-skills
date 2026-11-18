# Thinking Document Template

Create or resume this Markdown file on Turn 1 once the problem frame and topic map are clear, unless the user requests chat-only mode or the workspace is read-only. Follow user-specified paths or repo conventions first; otherwise write `docs/thinking/YYYY-MM-DD-<topic>.md` in the user's timezone.

Write generated headings, labels, and prose in the user's language (Simplified Chinese by default). Keep the document scannable: fill known context right away, omit blocks that do not apply yet, and never dump blank form fields.

---

# <Topic Title>: Product & Technical Thinking

Status: Active · Created: YYYY-MM-DD · Updated: YYYY-MM-DD · Progress: Decided none | Active T1 | Queued T2, T3

## Problem & Boundary

- **Friction & Outcome:** Who hits what friction, when it happens, and what changes when solved.
- **Constraints, Appetite & Non-Goals:** Time/complexity budget (*appetite*), fixed limits, explicit v1 exclusions, and reversibility for key calls.
- **Evidence Scope:** Inspected repo files/symbols, commit or doc dates, or `No repo access — code facts unverified`.

## Topic Map

Lead with the root Eigenquestion (`T1`); scale down to 1–2 rows for small reversible calls.

| ID | Topic | Depends On / Shapes | Status |
| --- | --- | --- | --- |
| T1 | <Root Eigenquestion (product scope or core tradeoff)> | Resolves or prunes T2, T3 | Active |
| T2 | <Workflow or state-rule question> | Depends on T1 | Queued |
| T3 | <Edge-case or technical-boundary question> | Depends on T1, T2 | Pruned — superseded by T1 |

## Topic Details

### T1 · <Concrete Decision Question>

- **Why it matters & repo facts:** What downstream choice turns on T1; cite `path/to/file::symbol` or mark `Unverified`.
- **Open question:** One focused question without a pre-filled answer.
- **Breadboard (workflow topics, optional):** `Place -> User action -> System outcome` (3–5 lines; skip premature UI specs).
- **User thinking:** Pending user input *(preserve user-authored edits across syncs)*.

<!-- Add only when stress-testing or comparing options -->
- **Stress-test (Tiger / Rabbit Hole):** Single lethal pre-mortem scenario or hidden rabbit hole that could flip the choice (omit harmless paper tigers).
- **Option comparison** *(keep criteria tied to user priorities and repo limits; note when options combine)*:

| Direction | <Priority 1> | <Constraint 2> | Key Cost or Unknown |
| --- | --- | --- | --- |
| <Option A> | <Observed or labeled inference> | <Same> | <Tradeoff or open check> |
| <Option B> | <Same> | <Same> | <Tradeoff or open check> |

- **Agent leaning:** *Shown after objective tradeoffs when helpful — label clearly as Agent judgment and cite the driving priority or constraint.*

<!-- Add once decided, needs verification, or deferred -->
- **Decision:** <Status> · Owner: <User | Agent (delegated)> · Scope: <What is settled>
- **Rationale & accepted tradeoffs:** Only reasons and costs the user accepted; write `Pending` if unstated. Mark extra agent-spotted risks as `Agent note (unconfirmed)`.
- **Assumptions to verify & reopen trigger:** Specific runtime checks needed and what new evidence reverses this call.

## Decision Log & Revisions

- `YYYY-MM-DD · T1 · User · Decided`: <Short statement of choice and scope>. *(On revision: `Old -> New; trigger evidence; retain prior rationale`.)*

## Open Verifications & Parked Ideas

- **Verify:** <Check item and which topic it feeds>.
- **Parked:** <Side idea parked out of scope, plus reopen condition>.
