# Interaction Examples

All cases below are synthetic calibration scenarios. Apply the workflow to fresh evidence in each session; never cite these examples as facts about the current repository.

## 1. Frame the Problem With Appetite and an Eigenquestion (Turn 1)

**Scenario:** The user opens with "I want to add an approval workflow toggle to our agent runner."

**Response:** Inspect existing runner and permission code (`src/runner/execute.ts`, `src/policy/rules.ts`) first, skip sycophantic praise, and establish appetite, baseline, and the root Eigenquestion before designing toggles:

- Reframe problem and appetite: verify what operator incident triggered the ask, establish how much budget it merits (e.g., 1-week v1 appetite), and note a low-cost baseline (existing per-tool allowlists in `src/policy/rules.ts` already block unapproved external calls without building a queue).
- Lead `docs/thinking/2026-11-17-approval-flow.md` with the root Eigenquestion (`T1`): "Must v1 halt before an action runs, or only audit actions afterward?" Explain that pre-run halting drives `T2` (approver routing and timeouts) and `T3` (entry flow), whereas post-hoc audit eliminates `T2`.
- Show `Decided: none | Current: T1 | Queued: T2, T3` and ask one open question on `T1` without pushing a toggle design.

## 2. Run a Tiger Check, Prune Topics, and Breadboard Next Flow

**Scenario:** On `T1`, the user confirms the 1-week appetite and says "v1 only needs post-hoc audit; operators shouldn't block mid-run."

**Response:** Check the repo (`src/events/audit.ts` already records tool calls) and run a pre-mortem separating real **Tigers / Rabbit Holes** from harmless **Paper Tigers**:

- **Tiger / Rabbit Hole:** External webhooks in `src/tools/notify.ts` cannot be rolled back once sent—if a bad rule fires twice, post-hoc audit spots it after customer impact. Ignore harmless paper tigers such as 50ms async log lag. Ask if webhook allowlists cover this risk for v1.
- **Outcome:** User confirms allowlists guard webhooks and locks `T1` (`Decided`, User). Prune `T2` (`Pruned — post-hoc audit removes approver routing and timeout queue`), sync `docs/thinking/2026-11-17-approval-flow.md`, and open `T3` with a 3-line text **breadboard**: `Runner Config -> Enable audit flag -> Audit Log Page shows tool + caller`.

## 3. Compare Options With Shared Criteria and Transparent Agent Leaning

**Scenario:** On `T3` (export delivery), `src/exports/api.ts::createExport` cancels work when the HTTP connection drops (`tests/exports/disconnect.test.ts`), and the user asks what options exist while prioritizing reliability over fewer client requests.

**Response:** Compare distinct directions against the user's priority (`survives disconnect`) and simplicity preference (`single client path in v1`):

| Direction | Survives Disconnect | Single Client Path | Key Cost or Unknown |
| --- | --- | --- | --- |
| Persist job + unified status polling | Yes (detached from request) | Yes (one polling flow) | Client adds polling loop |
| Sync wait + fallback status check | Yes (via fallback) | No (two client code paths) | Extra client branching |

- **Agent leaning:** Given your preference for reliability over request count and a single v1 retrieval path, unified polling fits better and avoids maintaining two client read paths. Whether `src/workers/jobs.ts` recovers jobs across worker restarts remains unverified.
- **Record cleanly:** When the user accepts polling, log `Decided` under User with the stated rationale and accepted client polling cost, plus a separate open check on worker restart recovery. Never fold unaccepted caveats into user rationale.

## 4. Revise a Settled Topic Without Losing History

**Scenario:** A benchmark reveals exports run 4 minutes, invalidating an earlier preference for synchronous HTTP responses.

**Response:** Update the active decision to async job polling, record `Sync HTTP -> Persist job + polling; triggered by 4-minute runtime benchmark; user accepts extra poll step` in `Decision Log & Revisions` while keeping the original rationale visible, and re-check downstream error-handling topics that assumed synchronous HTTP status codes.

## 5. Work Without Target Repo Access

**Scenario:** The user asks to structure and think through a product outline when no workspace or repo is attached.

**Response:** Create the portable thinking document locally (or in chat if read-only), mark `Evidence Scope: No repo access — code facts unverified`, track concrete codebase checks under `Open Verifications`, and continue the topic-by-topic loop without inventing file paths or symbol contracts.
