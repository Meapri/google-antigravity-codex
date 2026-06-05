---
name: google-antigravity
description: "Use when the user asks Codex to use Google Antigravity directly for OAuth status, chat, native Google-grounded search, image generation, model listing, or quota checks. This plugin is independent of Hermes and agy."
---

# Google Antigravity

Use this skill when a task should use Google Antigravity through this Codex
plugin. Prefer the MCP tools from `google-antigravity-codex` when they are
available.

## Boundaries

- Do not call Hermes.
- Do not call `agy --print`.
- Do not use Gemini API keys as a fallback.
- Do not read browser cookies, macOS Keychain entries, or unrelated credential
  stores.
- Never print OAuth tokens, refresh tokens, client secrets, authorization
  headers, or raw credential files.

## Tool Preference

- Use `google_antigravity_auth_status` before assuming auth is ready.
- Use `google_antigravity_login_url` and `google_antigravity_finish_login` for
  user-mediated OAuth setup.
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
- Use `google_antigravity_quota_status` when quota, plan, or paid-tier routing
  matters.

When a tool returns `isError: true`, report the specific auth or provider error
without inventing a workaround.
