# Implementation and Integration Sources

Reference review date: 2026-10-15. External directory layout, publication states, and image classifications are conventions of this skill, not requirements imposed by these platforms.
External documentation and commands may change. Use the actual installed version and current tool schemas at execution time.

## Agent Skills structure and hosts

- Agent Skills format, progressive disclosure, scripts/references/assets: https://agentskills.io/specification
- Script design: https://agentskills.io/skill-creation/using-scripts
- Codex local skill directories and explicit invocation: https://developers.openai.com/codex/skills/ (redirect recorded at reference review: https://learn.chatgpt.com/docs/build-skills)
- Claude Code personal skill directories and invocation: https://code.claude.com/docs/en/skills

## Optional Feishu integration

- Official larksuite CLI and skills: https://github.com/larksuite/cli
- lark-doc entry point: https://github.com/larksuite/cli/blob/main/skills/lark-doc/SKILL.md
- Creation/import formats and readback: https://github.com/larksuite/cli/blob/main/skills/lark-doc/references/lark-doc-create.md
- Local media insertion, append position, and Docx IDs: https://github.com/larksuite/cli/blob/main/skills/lark-doc/references/lark-doc-media-insert.md
- Readback formats and block IDs: https://github.com/larksuite/cli/blob/main/skills/lark-doc/references/lark-doc-fetch.md
- Identity, relative paths, safety, and success responses: https://github.com/larksuite/cli/blob/main/skills/lark-shared/SKILL.md

This package does not copy or bundle external Feishu skills and contains no credentials. Reviewing documentation does not substitute for actual remote publication tests.

## Readability and browser checks

- Text contrast: https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html
- Non-text contrast: https://www.w3.org/WAI/WCAG22/Understanding/non-text-contrast.html
- Playwright Python screenshots: https://playwright.dev/python/docs/screenshots
- Screenshot regression and environment differences: https://playwright.dev/docs/test-snapshots

Scripts perform basic checks only; they do not establish full WCAG compliance. This package includes neither baseline PNGs nor an automated image-diff service.

## Diagram and interaction adaptations (0.3)

See [diagrams-and-interaction.md](diagrams-and-interaction.md#upstream-sources) for pinned upstream revisions, adapted patterns, and intentionally omitted machinery. License notices are in `../THIRD_PARTY_NOTICES.md`. These sources inform presentation, not the factual validity of generated reports.
