# zish-skills

A collection of reusable skills I use with coding agents and AI workflows.

## Skills

| Skill | Purpose |
| --- | --- |
| `analyze-open-source-repo` | Analyze open source repositories and save structured Obsidian study notes. |
| `handoff` | Create concise Markdown handoffs for Coding Agent work, blockers, reviews, escalations, or context transfers, with an optional zip bundle of the referenced code. |
| `tmux-nvim-review` | Open files changed by Codex in a new tmux pane with nvim for review. |
| `tmux-peer-agent` | Hand a design review or a coding task to Codex or Claude Code in a visible tmux pane and get the result back. |
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
npx skills add https://github.com/zish-rob-crur/zish-skills --skill analyze-open-source-repo --agent codex --global
npx skills add https://github.com/zish-rob-crur/zish-skills --skill handoff --agent codex --global
npx skills add https://github.com/zish-rob-crur/zish-skills --skill tmux-peer-agent --agent codex --global
npx skills add https://github.com/zish-rob-crur/zish-skills --skill tmux-nvim-review --agent codex --global
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
npx skills update analyze-open-source-repo handoff tmux-nvim-review tmux-peer-agent zish-skill-manager --global
```
