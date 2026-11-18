# zish-skills

A collection of reusable skills I use with coding agents and AI workflows.

## Skills

| Skill | Purpose |
| --- | --- |
| `analyze-open-source-repo` | Analyze open source repositories and save structured Obsidian study notes. |
| `explain-and-report` | Explain complex systems with diagrams, interactive walkthroughs, and HTML reports, with optional Feishu publishing. |
| `handoff` | Create concise Markdown handoffs for Coding Agent work, blockers, reviews, escalations, or context transfers, with an optional zip bundle of the referenced code. |
| `review-with-judgment` | Review multi-commit MRs/PRs, code changes, ADRs, and agent architectures for correctness, reuse, over-engineering, and long-term maintainability. |
| `think-with-me` | Clarify product and technical problems into ordered topics, discuss and decide one topic at a time, and sync a live decision document. |
| `tmux-peer-agent` | Hand a design review or a coding task to Codex, Claude Code, or Antigravity CLI in a visible tmux pane and get the result back. |

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
npx skills add https://github.com/zish-rob-crur/zish-skills --skill explain-and-report --agent codex --global
npx skills add https://github.com/zish-rob-crur/zish-skills --skill handoff --agent codex --global
npx skills add https://github.com/zish-rob-crur/zish-skills --skill review-with-judgment --agent codex --global
npx skills add https://github.com/zish-rob-crur/zish-skills --skill think-with-me --agent codex --global
npx skills add https://github.com/zish-rob-crur/zish-skills --skill tmux-peer-agent --agent codex --global
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
npx skills update analyze-open-source-repo explain-and-report handoff review-with-judgment think-with-me tmux-peer-agent --global
```
