---
name: antigravity-doctor
description: "Verify and troubleshoot the Google Antigravity plugin, explicit consent, OAuth, MCP, models, quota, grounding, writing, releases, and images."
---

# Antigravity Doctor

1. Check `google_antigravity_consent_status`; report the state without changing it.
2. Check `google_antigravity_cli_status`, plugin version, MCP `initialize`, and
   `tools/list`.
3. For direct workflows, check masked `google_antigravity_auth_status` and then
   model/quota availability.
4. Run only the focused smoke checks requested by the user.
5. Do not treat `agy models` success as proof that a live prompt is authenticated.

Never read or copy the official CLI keyring, and never print OAuth tokens,
refresh tokens, secrets, cookies, or authorization headers. If consent is
absent, provide the local grant command and let the user run it.
