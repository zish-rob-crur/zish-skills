# Ponytail Collaboration Rules

Use Ponytail as an input method while keeping judgment, task scope, and output format anchored to `review-with-judgment`. This file documents how the skills work together without duplicating upstream rules.

## Sources and Scope

Baseline reviewed on 2026-11-15 from the public `DietrichGebert/ponytail` repository. Read the active local or explicit project version first when available.

| Skill | Scope | Upstream Source |
| --- | --- | --- |
| `ponytail` | Smallest complete change for designs and plans | [SKILL.md](https://github.com/DietrichGebert/ponytail/blob/main/skills/ponytail/SKILL.md) |
| `ponytail-review` | Code diff, connected callers, scale, and tests | [SKILL.md](https://github.com/DietrichGebert/ponytail/blob/main/skills/ponytail-review/SKILL.md) |
| `ponytail-audit` | Whole package, directory, or repository audit (only on explicit request) | [SKILL.md](https://github.com/DietrichGebert/ponytail/blob/main/skills/ponytail-audit/SKILL.md) |

## Resolution and Fallback

1. Resolve exact installed skill names from the active environment or repo config; read the target `SKILL.md` directly and avoid conflating similarly named skills.
2. If absent locally and network access is allowed, read the upstream raw file from the table above and state that you used the public upstream baseline rather than a local installation.
3. If neither local nor upstream files are readable, note briefly that `ponytail-review` could not be loaded and proceed with `review-with-judgment` alone. Never install, update, or vendor upstream skills just to perform a review.
4. Merge findings that share one root cause instead of emitting two separate review reports.

## Integrating Upstream Guidance with Local Judgment

- Adopt Ponytail's focus on connected callers, concrete failure scenarios, and load assumptions; express unverified gaps in draft specs as open questions or targeted checks rather than confirmed bugs.
- Treat signals such as single-implementation interfaces, extra layers, or `v2` wrappers as investigation prompts, not automatic deletions. Check what contract or failure mode the layer guards and compare total maintenance cost before recommending removal.
- Re-evaluate an accepted shortcut comment (`shortcut:` or `ponytail:`) only when requirements, traffic, or new evidence invalidate its stated limit.
- Follow the user's language and `review-with-judgment` output structure instead of copying upstream English headings, session modes, or mandatory line-count metrics.
- Respect read-only review boundaries: never modify code during a review or expand a single-MR check into a full-repo audit unless asked.
- If the active Ponytail version conflicts with these collaboration rules in a way that affects the verdict, note the difference and state which rule governs.
