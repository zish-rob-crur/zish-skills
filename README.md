# zish-skills

A collection of reusable skills I use with coding agents and AI workflows.

## Skills

| Skill | Purpose |
| --- | --- |
| `handoff` | Create concise Markdown handoffs for Coding Agent work, blockers, reviews, escalations, or context transfers. |
| `zish-skill-manager` | Manage personal, public, private, company, and customer-specific Codex skills without leaking private material into this public repo. |

## Install From Remote With `npx skills`

The repo follows the standard skills layout under `skills/`, so the `skills` CLI can discover and install them directly from the remote GitHub URL.

List the available skills:

```bash
npx skills add https://github.com/zish-rob-crur/zish-skills --list
```

Install all skills for Codex globally:

```bash
npx skills add https://github.com/zish-rob-crur/zish-skills --skill '*' --agent codex --global
```

Install a single skill for Codex globally:

```bash
npx skills add https://github.com/zish-rob-crur/zish-skills --skill handoff --agent codex --global
npx skills add https://github.com/zish-rob-crur/zish-skills --skill zish-skill-manager --agent codex --global
```

Install into the current project instead of the global agent directory by omitting `--global`:

```bash
npx skills add https://github.com/zish-rob-crur/zish-skills --skill handoff --agent codex
```

The GitHub shorthand form is equivalent:

```bash
npx skills add zish-rob-crur/zish-skills --skill handoff --agent codex --global
```

Update installed skills later:

```bash
npx skills update handoff zish-skill-manager --global
```
