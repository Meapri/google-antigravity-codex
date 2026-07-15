---
name: google-antigravity
description: "Use for native Antigravity plugin diagnostics, model routing, and guarded local helpers; third-party login bridges remain disabled by default."
---

# Google Antigravity

Use this skill for the native Antigravity plugin and its local MCP helpers.

## Boundaries

- Do not read browser cookies, macOS Keychain entries, or unrelated credential
  stores.
- Never print OAuth tokens, refresh tokens, client secrets, authorization
  headers, or raw credential files.

## Tool Preference

- Use `google_antigravity_cli_status` when the user asks about the installed
  official CLI, its version, native plugin validation, or model-list readiness.
  It cannot prove authentication because `agy` has no non-interactive auth
  status command.
- Do not call `google_antigravity_cli_chat` from inside Antigravity. In Codex it
  remains disabled unless the user has confirmed their applicable agreement and
  explicitly configured the bridge.
- Use `google_antigravity_route_model` when the task type is clear but the best
  model/tool choice is not.
- Treat direct OAuth, chat, grounding, image, and quota tools as unsupported
  legacy surfaces. Do not enable or invoke them automatically.
- Use `google_antigravity_release_snapshot` and
  `google_antigravity_release_draft` for release planning, PR descriptions,
  changelog entries, release notes, and local git release context.
- Use `google_antigravity_list_models` before assuming a model id is available
  or when comparing Gemini, Claude, GPT-OSS, and image model availability.

## Response Handling

Prefer `structuredContent.text` for natural-language output, `sources` and
`evidence` for grounded answers, and `path` for generated images. Treat
`warnings` and `diagnostics` as operational signals. If `retry_count` is
available on a long request, keep it low unless the user explicitly wants a
longer wait.

When a tool returns `isError: true`, report the specific error without enabling
an experimental backend as a workaround.
