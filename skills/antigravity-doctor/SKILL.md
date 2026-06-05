---
name: antigravity-doctor
description: "Use when the user asks to verify, diagnose, install-check, smoke-test, or troubleshoot the Google Antigravity Codex plugin, OAuth, MCP server, models, quota, grounded search, writing, release, or image generation."
---

# Antigravity Doctor

Use this skill for plugin health checks and troubleshooting.

## Checklist

1. Check installed plugin version with `codex plugin list`.
2. Verify MCP stdio `initialize` and `tools/list`.
3. Use `google_antigravity_auth_status` and report only masked account state.
4. Use `google_antigravity_list_models` to confirm text and image model
   availability.
5. Use `google_antigravity_quota_status` to confirm project, paid tier, and
   quota buckets when credentials are present.
6. Run focused smoke checks only when credentials are present:
   - `google_antigravity_chat`
   - `google_grounded_search`
   - `google_antigravity_write`
   - `google_antigravity_generate_image`
   - `google_antigravity_release_snapshot`

## Security

- Never print tokens, refresh tokens, client secrets, authorization headers, or
  raw credential files.
- For credential files, report only path, mode, byte count, and whether fields
  are present.
- If auth is missing, use `google_antigravity_login_url` and
  `google_antigravity_finish_login` with user-mediated OAuth.

## Reporting

Report pass/fail, version, tool count, masked email presence, project id
presence, paid tier name, warning names, diagnostics keys, and generated image
path when applicable.
