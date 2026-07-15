---
name: google-antigravity
description: "Use Google Antigravity for consent-gated CLI chat, direct OAuth/chat, grounded search, images, writing, models, quota, and local release helpers."
---

# Google Antigravity

Use the `google-antigravity-codex` MCP tools for Antigravity workflows.

## Consent

Check `google_antigravity_consent_status` before an authenticated integration.
If consent is absent, tell the user to run this themselves:

```bash
python3 scripts/google_antigravity_consent.py grant --i-understand-and-consent
```

Never grant or modify consent through MCP. The user may revoke it with the same
script's `revoke` command.

## Tools

- Use `google_antigravity_cli_status` for official CLI version and plugin health.
- Use `google_antigravity_cli_chat` from Codex when consented. Never invoke it
  from inside Antigravity because that would recursively launch `agy`.
- Use `google_antigravity_auth_status`, `google_antigravity_login_url`, and
  `google_antigravity_finish_login` for the separate direct OAuth flow.
- Use `google_antigravity_chat`, `google_grounded_search`,
  `google_antigravity_generate_image`, and `google_antigravity_write` for their
  named consented workflows.
- Use `google_antigravity_list_models`, `google_antigravity_route_model`, and
  `google_antigravity_quota_status` for discovery and diagnostics.
- Use the release snapshot/draft tools for guarded local Git context.

Never print tokens, client secrets, authorization headers, cookies, or raw
credential files. Treat tool warnings and diagnostics as operational signals.
