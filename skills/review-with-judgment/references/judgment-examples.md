# Judgment Examples

All cases below are synthetic calibration examples. Apply the underlying decision tests to fresh evidence in each review; never treat these examples as facts about the current repository.

## 1. Narrow a Speculative Extension

**Material:** The product requires one fixed notification channel. Although the codebase already has a sender helper, the proposal adds a plugin registry, a routing DSL, and dynamic module loading in case future channels arrive.

**Judgment:** Check the existing sender contract first. When direct integration meets current requirements without locking callers into a breaking public API, implement the local call now and defer the registry and DSL.

**How to state it:** Specify the maintenance burden avoided (registry lifecycle, DSL parser, dynamic load errors), what the local call still supports, and the concrete trigger for revisiting plugins later. Avoid dismissing it with a bare "over-engineered" label.

## 2. Verify Wiring Behind a Reuse Claim

**Material:** One component produces real interaction transcripts and another generates reports from fixture data. The proposal claims the pipeline already evaluates real user runs end to end.

**Judgment:** Verify both components separately, then inspect the seam between them: how transcripts convert, where runtime evidence originates, and what schema the report reads.

**How to state it:** Keep the existing reuse plan, list the unverified seam as an open blocker, and propose one end-to-end trace check. Do not demand a new event bus to bridge the seam, and do not report missing draft wiring as a production regression.

## 3. Keep Necessary Boundary Complexity

**Material:** Users can cancel a background import, yet an external worker may finish after cancellation arrives. The receiver checks the task ID and current state before committing results.

**Judgment:** Check whether cancel guarantees immediate worker termination and who consumes late results. When cancellation cannot stop in-flight work, preserve the admission check and reuse existing state storage.

**How to state it:** Explain the race condition this guard blocks and where ownership lives. Shorter code does not justify removing a safety check, nor does the check justify building a distributed coordinator.

## 4. Retain a Single-Implementation Adapter That Owns a Contract

**Material:** The project integrates one storage provider, yet keeps a thin adapter that normalizes error codes, enforces timeouts, and logs audit fields behind a domain interface.

**Judgment:** Inspect what happens if callers invoke the vendor SDK directly. Implementation count alone never decides whether an interface belongs.

**How to state it:** Recommend keeping the boundary when it isolates real contract guarantees. Only merge wrappers that pass calls through unchanged without translating errors, validating inputs, or hiding vendor churn.

## 5. Approve Code That Is Already Good Enough

**Material:** A small bug fix reuses an existing helper, stays scoped to one module, includes a regression test for the failing input, and adds no new state or dependencies.

**Judgment:** Verify callers and edge cases, then stop. Do not invent extra interfaces, file splits, benchmarks, or unrelated coverage targets.

**How to state it:** State that no blocking issues were found, summarize the paths checked, and note any unverified area only if it affects risk.

## 6. Value Cognitive Gain in Exploratory Work

**Material:** An experiment compares two context-injection strategies before production rollout to separate missing context, ignored instructions, and downstream execution errors.

**Judgment:** Check whether the experiment isolates the deciding variable and informs a real choice. Temporary probe code is acceptable when scoped and labeled.

**How to state it:** Name the single experiment that settles the design decision and distinguish spike results from production readiness. Do not ask ordinary bug fixes to justify learning outcomes.

## 7. Fix Boundary Inversion Between Prompts and Code

**Material:** An agent workflow tries to prevent duplicate billing and enforce a three-step state machine purely through a 150-line system prompt, while a Python parser uses brittle keyword regexes to guess user intent from free-form text.

**Judgment:** Both responsibilities sit in the wrong layer. Models handle semantic classification well through structured tool schemas, whereas deterministic state machines, quotas, and idempotency require code guards.

**How to state it:** Move state validation and idempotency keys into deterministic code, and replace regex guessing with a structured enum output schema. Explain why prompt-only rules still fail silently under load or paraphrasing.

## 8. Collapse Multi-Agent and Prompt-Slot Sprawl

**Material:** A single classification and reply task passes through four sequential agents (`Planner -> Router -> Guard -> Responder`) and splits instructions across twelve overlapping prompt slots, duplicating context across handoffs.

**Judgment:** Count how many handoffs actually introduce independent data, tools, or isolation boundaries. When stages share the same model and context window, splitting them loses detail, doubles latency, and breaks failure attribution.

**How to state it:** Show the concrete collapse path (e.g., merge into one single-pass agent with structured output plus deterministic post-checks) and name the eliminated failure modes (context drift and multi-hop debugging).

## 9. Reject Add-Only `v2` Shims and Silent Fallback Soup

**Material:** An agent-authored MR leaves an existing internal helper untouched, adds `process_order_v2` behind a default-off boolean flag, and wraps downstream field reads in `try/except Exception: return {}`.

**Judgment:** For internal callers under the same repo, parallel `v2` paths double maintenance and orphan tests. Broad fallbacks turn schema bugs into silent data corruption that surfaces hours later.

**How to state it:** Require updating the few internal callers in place, deleting the old helper and flag, and failing fast on malformed required fields at the contract boundary.

## 10. Separate Eval Harnesses and Cut Mock Test Theater

**Material:** A PR injects `if provider == "playground_dry_run"` branches into the production planner to make an eval pass, and adds 300 lines of tests that patch every collaborator to verify mocked call counts.

**Judgment:** Production code should remain unaware of test doubles; harness translation belongs at the boundary adapter. Mock-heavy tests lock in private call structure while missing real schema mismatches.

**How to state it:** Move the test-double translation into the dialer/adapter boundary while retaining provenance metadata separately, and replace mock-echo tests with one focused contract test exercising real input-to-output invariants.

## 11. Downgrade an Autonomous Loop to a Workflow (and Bound Multi-Agent Splits)

**Material:** A refund handler runs an open-ended ReAct loop that decides at runtime when to look up the order, check eligibility, and refund payment, while two sub-agents write concurrently to the same case ledger.

**Judgment:** The step sequence and eligibility rules are fixed at design time, so a deterministic workflow or single structured LLM call removes unpredictable tool loops. Meanwhile, concurrent write agents corrupt shared state; split agents only for isolated generator–verifier checks, parallel read-only exploration feeding single-threaded writes, or strict permission boundaries.

**How to state it:** Replace the autonomous loop with a deterministic workflow wrapping one bounded structured call, serialize ledger writes through a single owner, and keep a second agent only if independent verification is needed.

## 12. Consolidate Thin CRUD Tools and Stop Context Pollution

**Material:** An agent integration exposes 18 thin REST wrappers (`get_ticket_id`, `get_ticket_body`, `list_comments`) returning bare UUIDs and raw 500 stack traces, and appends multi-megabyte raw logs directly into conversation history.

**Judgment:** Thin CRUD wrappers tax context with unused tool schemas and force multi-turn ID joins, while raw tracebacks and unfiltered logs crowd out instructions and fuel retry loops.

**How to state it:** Merge the 1:1 wrappers into coarse-grained workflow tools that return readable summaries beside IDs and actionable validation hints, and replace raw log dumps with bounded search or summary tools plus history compaction.
