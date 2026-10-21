# Feishu Publishing: Reuse Installed Skills

## Scope and defaults

This is an agent publishing workflow, not a persistent synchronization service. Default to a **one-way local → Feishu snapshot**, without automatic bidirectional sync, watchers, or scheduled execution.
This skill owns content, design, figures, and review. The Feishu skill owns platform formats, authentication, uploads, writes, and readback. Prefer the user's installed tools without depending on a nonstandard skill name.
Publishing is off by default. “Support Feishu later” or “add sync rules to the skill” authorizes adding a capability, not uploading the current materials.
Perform writes when the user explicitly requests the document/folder destination and the content scope is clear. Do not ask again for already explicit low-risk authorization. If creation location, update scope, or permission boundaries are unclear, clarify only the missing details while continuing local production.

## Discover capabilities

Find installed Feishu/Lark document skills, MCP tools, or connectors and read their current instructions. Check supported URLs, document reading, creation/updates, local images, attachments, readback, and permissions.
If capabilities are missing, you may identify official or user-designated integrations, but do not install them, acquire credentials, or change permissions on your own. Deliver local materials and record `blocked_missing_capability`.
One official option is `lark-doc` in `larksuite/cli`. Route authentication to `lark-shared` and drive/permission/file-level operations to `lark-drive`. This is a documented adapter option, not an assumption that the host has it installed. [1][2]
Follow the actual skill's staged reference loading during execution; do not load all Feishu documentation at once. Conceptual names in this document are not real tool function names.

## Local publication materials

Prepare the following under `<run-dir>/publish/<publish-id>/`, entirely outside repositories:

```text
content.md or content.xml        # Editable body; the Feishu skill determines platform format
assets/                         # Explicitly allowlisted images, not the entire qa directory
plan.json                       # Destination, method, allowlist, source hashes
state.json                      # Document IDs, block mappings, completed steps, failures, readback status
```

`assets/publish-plan.example.json` is a structural example. Fill it with real values; it is not authorization evidence. Do not change `authorized=false` to true without citing the current user instruction or the scope of existing valid authorization.
The allowlist must include at least `local_path`, `sha256`, `role`, `figure_id`, and `caption`. Body images use role=`content`; role=`qa` requires explicit authorization and normally a separate review destination.
Do not copy `qa/`, manifests, raw logs, or the entire run directory. Copy only inspected, explicitly listed figures whose paths exist within the run directory and contain no symlinks.
Bind publication objects to both their local paths and content hashes; recheck before publishing, not just by filename.

## Map HTML information into Feishu

| Local form | Feishu form |
| --- | --- |
| Body text, headings, explanations, sources | Editable paragraphs/headings/quotes |
| Short comparison tables and key data | Native tables or supported equivalents |
| Code and log excerpts | Editable code blocks, redacted with necessary context |
| SVG/HTML diagrams and statistical charts | Actual uploaded image blocks beside editable captions and explanations |
| Evidence images, including failure screenshots | Include selected, inspected images as content blocks beside editable captions within the authorized report scope |
| Interactive traces and filtered charts | Static key states, key values/tables, and explanations; not just the empty default state |
| Full-page styling and JS | Do not migrate; attach HTML or an approved hosted link when authorized and needed |
| QA screenshots | Excluded by default; include only in the specified review document when explicitly requested |

Do not screenshot an entire long report into one image and call it a synchronized document. Do not promise to preserve HTML layout and interactions in Feishu.
Local Markdown image paths, `file://`, data URIs, and short-lived signed URLs are not Feishu images. Use the current skill's upload and insertion capabilities, then read back. [3]

## Publication states

`not_requested → prepared → publishing → verified`
Branches: `blocked_missing_capability`, `blocked_permission`, `conflict`, `partial`, `failed`.
`verified` requires evidence of successful writes and readback. Without readback, use `partial` / `unverified`; a zero command exit code is not proof of complete synchronization.

1. **Confirm the destination.** Resolve the exact Docx / Wiki / folder target supplied by the user. For existing documents, read the title, relevant blocks, and version first. Do not turn “update this document” into “create another copy.”
2. **Confirm the content.** Use the same source content, retaining evidence, limitations, and simulation labels. Verify allowlisted files, hashes, and permission scope. Do not make the destination publicly readable.
3. **Update safely.** Create a new document only when requested. Update only explicitly authorized, identifiable sections/blocks. Use version preconditions supported by the current API. Without CAS, reread immediately before writing and disclose the remaining concurrency window. Merge human edits or flag conflicts; do not claim atomic updates.
4. **Write body and images.** Follow the actual tool's create/import/edit workflow. Record real document_id, block_id, and file_token values; never guess IDs. Place figures beside their explanations and keep captions editable.
5. **Handle partial failure.** Immediately record successful documents/blocks. After a network timeout, read back and retry only after confirming the insertion did not occur. Do not blindly recreate content. Without stable matching information, report partial completion rather than claiming exactly-once behavior.
6. **Verify by readback.** Compare titles, sections, key numbers, conclusions and limitations, source links, and image block counts/positions. If preview is available, check that images are not blank. Token existence alone is insufficient. Check destination access boundaries and disclose when intended-reader access cannot be confirmed.
7. **Deliver a receipt.** Provide the real link, publication status, conversion losses, and failed items. Keep source hashes and remote versions in local state for recovery, but never store access tokens there.

## Details for the official lark-doc route

Reference review date: 2026-10-15. Use parameters supported by the installed version at execution time.

- `lark-doc` provides content reading, creation, updates, and media entry points. Follow its current routing for business reads/writes and authentication. [1]
- Creation supports XML and Markdown; do not assume XML, Markdown, and raw HTML are interchangeable. For the prepared Markdown, follow the skill's import branch and format references. Follow its authoring workflow when recreating or substantially restructuring content. [2]
- Local file parameters require paths relative to the current working directory. First `cd` to external `publish/<publish-id>/`, then pass `@./content.md` or `./assets/figure.png`. Never copy images back into the repository to satisfy relative-path requirements. [1][4]
- `docs +media-insert` **appends to the document**, rather than inserting at arbitrary anchors. For exact body placement, use the current `+update` / block-edit workflow. If unsupported, explicitly present a figure appendix or mark the operation incomplete; do not claim in-place insertion. [3]
- Media insertion support for `/wiki/...` URLs does not imply read-command support. Prefer the actual Docx document_id from resolution/creation responses; do not assume URL compatibility across commands. [3]
- Even with `ok=true`, inspect creation warnings and read back the document. Success envelopes depend on each connector's schema; do not universally assume `code==0`. [2][4]
- Do not automatically switch user/bot identity, expand authorization domains, or bypass confirmation gates. Request only the capabilities needed for the current task. [4]

The following illustrates call shape after content preparation. Read the actual skill and current help before execution:

```bash
# CWD must be this run's publish/<publish-id>/; destination and permission authorization are not included here.
lark-cli docs +create --doc-format markdown --content '@./content.md' --as user
# Read back using the actual returned ID.
lark-cli docs +fetch --doc '<returned-document-id>' --detail with-ids --as user
```

This package does not bundle external skills or credentials, and its tests do not perform real Feishu writes.

## Sources

[1] https://github.com/larksuite/cli/blob/main/skills/lark-doc/SKILL.md
[2] https://github.com/larksuite/cli/blob/main/skills/lark-doc/references/lark-doc-create.md
[3] https://github.com/larksuite/cli/blob/main/skills/lark-doc/references/lark-doc-media-insert.md
[4] https://github.com/larksuite/cli/blob/main/skills/lark-shared/SKILL.md
[5] https://github.com/larksuite/cli/blob/main/skills/lark-doc/references/lark-doc-fetch.md
