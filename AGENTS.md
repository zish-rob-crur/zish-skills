# AGENTS.md

## Skill Authoring Rules

- Keep the `description` in `SKILL.md` frontmatter short: one clear trigger sentence.
- Do not put full workflows, long scenario lists, or output structures in `description`.
- Put detailed workflows in the `SKILL.md` body; put longer templates, examples, and reference material in `references/`.

## Public Repo Boundaries & Workflow

- Keep company, customer, internal URL/schema, or credential material out of this public repo; store private skills in a private repo or `~/.agents/private-skills-src`.
- Write public skill files (`SKILL.md`, `references/`, `agents/openai.yaml`) in English by default.
- Validate updated skills with `quick_validate.py` when available, and do not commit or push unless explicitly requested.
