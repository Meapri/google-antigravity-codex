---
name: google-antigravity
description: "Use when the user asks Codex to use Google Antigravity directly for OAuth status, chat, native Google-grounded search, image generation, model listing, or quota checks."
---

# Google Antigravity

Use this skill when a task should use Google Antigravity through this Codex
plugin. Prefer the MCP tools from `google-antigravity-codex` when they are
available.

## Boundaries

- Do not use Gemini API keys as a fallback.
- Do not read browser cookies, macOS Keychain entries, or unrelated credential
  stores.
- Never print OAuth tokens, refresh tokens, client secrets, authorization
  headers, or raw credential files.

## Tool Preference

- Use `google_antigravity_auth_status` before assuming auth is ready.
- Use `google_antigravity_login_url` and `google_antigravity_finish_login` for
  user-mediated OAuth setup.
- Use `google_antigravity_route_model` when the task type is clear but the best
  model/tool choice is not.
- Use `google_antigravity_chat` for direct Antigravity model calls, coding
  questions, planning, summarization, and non-grounded reasoning tasks.
- Use `google_grounded_search` for current facts, latest information, source
  checks, or verification-heavy questions.
- Use `google_antigravity_generate_image` for image requests that should stay
  inside the Antigravity OAuth path.
- Use `google_antigravity_write` for prose drafting, rewriting, polishing,
  translation, summaries, PR descriptions, release notes, README prose, and
  public-facing wording.
- Use `google_antigravity_release_snapshot` and
  `google_antigravity_release_draft` for release planning, PR descriptions,
  changelog entries, release notes, and local git release context.
- Use `google_antigravity_list_models` before assuming a model id is available
  or when comparing Gemini, Claude, GPT-OSS, and image model availability.
- Use `google_antigravity_quota_status` when quota, plan, or paid-tier routing
  matters.

## Response Handling

Prefer `structuredContent.text` for natural-language output, `sources` and
`evidence` for grounded answers, and `path` for generated images. Treat
`warnings` and `diagnostics` as operational signals. If `retry_count` is
available on a long request, keep it low unless the user explicitly wants a
longer wait.

When a tool returns `isError: true`, report the specific auth or provider error
without inventing a workaround.
