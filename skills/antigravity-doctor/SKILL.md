---
name: antigravity-doctor
description: "Use to verify, diagnose, install-check, or troubleshoot the native Google Antigravity plugin bundle and local MCP helpers."
---

# Antigravity Doctor

Use this skill for plugin health checks and troubleshooting.

## Checklist

1. Use `google_antigravity_cli_status` to check the official `agy` executable,
   version, live model-list readiness, and native plugin validation. Do not
   treat model-list success as proof of an authenticated request session.
2. Check installed Codex plugin version with `codex plugin list` when Codex is
   the host.
3. Verify MCP stdio `initialize` and `tools/list`.
4. Confirm that direct OAuth and the Codex-to-CLI chat bridge are disabled by
   default. Do not use them as health checks.
5. Use `google_antigravity_list_models` to confirm text and image model
   availability.
6. Run local release-snapshot and path-boundary smoke checks.

## Security

- Never print tokens, refresh tokens, client secrets, authorization headers, or
  raw credential files.
- Never read or copy the official CLI's system-keyring credentials. Use `agy`
  commands and their exit status as the only readiness signal.
- For credential files, report only path, mode, byte count, and whether fields
  are present.
- Do not initiate the legacy OAuth flow or enable a bridge during diagnosis.

## Reporting

Report pass/fail, version, tool count, bundle path, warning names, and
diagnostics keys.
