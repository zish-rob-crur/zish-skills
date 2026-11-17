---
name: review-with-judgment
description: Review multi-commit MRs/PRs, code changes, ADRs, and agent architectures for correctness, reuse, over-engineering, and long-term maintainability.
---

# Review with Judgment

Define the problem and required behavior before judging the solution. Ask whether existing project capabilities can solve it in a form engineers can read, modify, and debug later. Require every new abstraction, state field, or agent layer to justify its maintenance cost, while checking what simplification would break.

Use this skill for technical proposals, ADRs, implementation plans, multi-commit MRs/PRs, and agent architectures, or when asked to evaluate reuse, cognitive load, and over-engineering. Do not trigger for performance reviews, resume screening, prose editing, or pure implementation tasks without a review step.

Reply in the user's language, defaulting to concise Simplified Chinese when unspecified. English instructions do not imply English review output.

## 1. Frame the Review and Scope

Extract the goal, success criteria, stage, and accepted constraints from the request and source material. Distinguish exploratory spikes from pre-implementation designs and shipped code: spikes test key assumptions, designs settle boundaries and contracts, and code changes answer for real runtime behavior and regressions. Keep settled decisions unless new evidence refutes them.

Inspect the targets the user names: files, branch, MR/PR, or commit range. When no range is specified, inspect uncommitted workspace changes first; if the workspace is clean, inspect the latest commit or current branch against its target base and state the scope used. Ask one focused question only when no target can be identified or a missing fact flips the verdict.

Deliver read-only findings by default. Do not edit code, post MR comments, publish artifacts, or run repo-wide refactors unless explicitly authorized.

## 2. Gather Repo and Multi-Commit MR Evidence

Read applicable `AGENTS.md` files and local conventions first, then trace outward from the primary entry point using targeted search (`rg`) instead of dumping the whole repository.

For multi-commit MRs or feature branches:

- **Inspect both net diff and commit trail.** Run `git diff <base>...HEAD` from the merge-base to judge the net change without being misled by intermediate reverts, and read `git log --oneline <base>..HEAD` to spot self-inflicted churn (early commits adding an abstraction that later commits patch around) or scope creep.
- **Check orphaned code and dual sources of truth.** Verify that new paths clean up or clearly bound legacy paths, and check whether one rule now lives in two places (such as code constants plus prompt prose or config files).
- **Flag mixed mechanical and behavioral churn.** When sweeping renames, formatting, or schema moves bury high-risk logic changes in one MR, recommend landing the mechanical move separately—only when the mix genuinely obscures risk attribution.

| Artifact | Primary Evidence to Verify |
| --- | --- |
| Design / ADR / Agent Spec | Existing code, entry and exit points, ownership of state, cross-layer handoffs, stated assumptions, and proposed checks |
| Multi-commit MR / Code Change | Net diff, commit sequence, all callers and consumers, data/schema contracts, state mutations, side effects, config, and tests |

Trace one main scenario end to end. When a change touches concurrency, async work, cancellation, persistence, or external calls, also trace the failure scenario most likely to break the goal. Judge scale against actual system load rather than imaginary traffic.

Verify reuse claims directly: confirm the target symbol exists, check its exact contract and limits, and note what is covered, what needs an adapter, and what remains unverified. An existing module name or a diagram arrow proves nothing until data and control reach the consumer.

Separate observed code, stated intent, executed test results, and reviewer inference. Cite exact file paths, symbols, line numbers, or commit hashes. Never report a test as passing unless you ran it; note whether verification used mocks, unit checks, or real integration.

## 3. Integrate Ponytail Without Losing Judgment

Read [Ponytail collaboration rules](references/ponytail.md) when reviewing code or suspected bloat.

- Apply `ponytail-review` checks to code changes and their connected callers.
- Apply `ponytail` simplicity and reuse checks to designs, matched to the current stage.
- Apply `ponytail-audit` only when the user asks to audit a whole package or repository.

Merge duplicate findings by root cause and own the final verdict against project contracts and long-term maintenance cost. If upstream Ponytail files are unavailable locally or online, note that briefly and run the independent checks below without installing packages.

## 4. Judge Maintainability, Design Fit, and Agent Anti-Patterns

Apply only the checks relevant to the material.

### Long-Term Maintainability Acid Tests

Run every non-trivial change through five concrete tests:

1. **Change amplification:** Does adding one similar rule or field edit a single place, or force coordinated edits across several files, schemas, and prompts?
2. **Wrong-layer patching and unparsed boundaries:** Does the change parse external inputs into typed schemas at the entry boundary and tighten broken contracts at their source, or pass raw dicts/strings inward and scatter defensive `if/else` checks across callers?
3. **Two-minute failure attribution:** When production or an evaluation breaks at 2 a.m., do logs and persisted state pinpoint the failing layer (input, planner, runtime, external tool), or do silent fallbacks hide the cause?
4. **Subtraction and replacement:** What breaks if we delete this new wrapper, config flag, or intermediate agent and edit the existing module directly? If a new path replaces an old one, check whether the old path still has real callers or remains as uncleaned debt.
5. **Shallow modules and pass-through chains:** Does a new class, wrapper, or prompt template hide substantially more complexity than its signature, config, and required call sequence (`init -> prepare -> run`) impose on callers, or merely forward arguments unchanged across layers?

### Modern AI and Coding-Agent Anti-Patterns

Watch for seven failure modes common in agent-authored MRs and LLM workflows:

- **Premature agent loops and multi-agent sprawl:** Running an open-ended tool-calling loop when call order or routing is known up front and a deterministic workflow or single structured LLM call suffices, or splitting one coherent decision across sequential sub-agents (`Planner -> Router -> Validator -> Summarizer`) and overlapping prompt slots. Multi-agent separation earns its cost only for isolated generator–verifier checks, parallel read-only exploration feeding single-threaded writes (never uncoordinated concurrent writers on shared state or files), or strict permission/tool boundaries.
- **Thin CRUD tool tax and context pollution:** Exposing fragmented 1:1 REST or database wrappers that return bare IDs, dump raw stack traces, or force multi-turn joins instead of coarse-grained workflow tools with actionable error hints; appending unbounded logs, raw JSON payloads, or failed retry noise into conversation history without filtering or compaction.
- **Boundary inversion (prompt vs. code):** Putting deterministic invariants (state transitions, permissions, quotas, idempotency, schema constraints) into natural-language prompts instead of code—or writing brittle regex and keyword hacks in code to guess semantic intent instead of structured outputs.
- **Prompt patch-stacking:** Appending `IMPORTANT: NEVER do X when Y unless Z` overrides to prompts or skills for individual test cases instead of merging rules and resolving contradictions.
- **Repo idiom drift and phantom guards:** Introducing generic textbook patterns or duplicate libraries where the codebase already follows a local convention; adding branches for states upstream types already rule out, or leaving `# Step 1: ...` self-narration comments that restate the code.
- **Add-only parallel paths and fallback soup:** Leaving old code untouched beside new `v2` wrappers, unused flags, or internal compatibility shims; wrapping calls in broad `try/except` blocks or chained `or` defaults that convert upstream contract errors into silent corrupt data.
- **Harness leakage and test theater:** Embedding test/playground flags inside production reasoning paths, or writing heavy mock tests that mirror mock expectations while leaving real caller contracts untested.

### Reuse, Necessary Complexity, and Cognitive Gain

Check existing project owners and conventions before recommending new shared utilities; keep distinct semantics separate rather than forcing unrelated callers behind one parameterized wrapper. Retain complexity that enforces a real contract, centralizes volatile rules, or protects error and concurrency boundaries.

For exploratory spikes, judge cognitive gain: what uncertainty the experiment resolves, which choice it informs, and what result flips the next step. Do not demand spike rituals for routine bug fixes.

## 5. Turn Observations into Defensible Findings

Every major finding connects four links: **evidence or location -> trigger scenario -> impact on correctness or maintenance -> smallest fix or check**. Simplification advice still needs a concrete maintenance cost; never invent runtime crashes to argue that dead code looks messy.

Check counter-evidence before reporting:

- Confirm whether dynamic dispatch, reflection, external webhooks, or CLI entry points call the code.
- Check whether an upstream layer already guarantees the invariant or an inline `shortcut:` comment documents the accepted limit.
- Separate regressions introduced by this MR from pre-existing bugs; note pre-existing risk without mislabeling it a regression.
- Verify that your proposed simplification preserves all required behavior and adds no new framework.

Group findings sharing one root cause. When no material bug or simplification debt exists, state clearly that nothing blocks merging; never pad reviews with style nitpicks or filler praise. Consult [judgment examples](references/judgment-examples.md) when weighing borderline retention or blocking calls; treat those scenarios as synthetic calibration cases, not facts about the repo under review.

## 6. Deliver a Decision-Ready Review

Keep review length proportional to risk and change size. Follow any format the user or host requires; otherwise use this structure and omit empty sections:

1. **Verdict & Scope:** State the clear call (`Ship`, `Ship after fixing F1`, or `Rework design before merging`), the stage or commit range inspected, and the deciding reason.
2. **Key Findings (`F1`, `F2`, ...):** Number continuously across tiers (**Must Fix**, **Simplify / Reduce Debt**, **Verify**) so the author can respond with *"Fix F1 and F3"*. For each item, give the location, trigger scenario, concrete impact, and smallest fix (`Current -> Simpler alternative`).
3. **Worth Keeping** *(only when decision-relevant)*: Note necessary complexity or reuse worth preserving so it is not stripped accidentally.
4. **Checked & Unverified:** List what you read or executed and any unverified boundary that could alter the verdict.

Stop once the verdict is defensible and remaining questions either do not change the decision or await one concrete verification step.
