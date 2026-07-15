# Google Antigravity Codex

Codex skills and a local MCP server centered on Google's official Antigravity
CLI (`agy`). The current release is tested with `agy 1.1.2` and requires
`agy >= 1.1.1`.

The plugin supports both the native Antigravity bundle and Codex-facing MCP
integrations. Optional authenticated integrations are available after the user
records explicit consent.

> [!WARNING]
> Direct Code Assist/OAuth uses non-public endpoints. It is opt-in so the user
> can review that boundary and make their own informed choice before use.

> [!CAUTION]
> Google's current Antigravity terms say third-party software using an
> Antigravity login to access the service breaches the agreement and may lead
> to suspension or termination. Therefore the Codex-to-`agy` chat bridge is
> therefore requires explicit consent. Review the
> [Antigravity Terms](https://antigravity.google/terms) and your organization's
> applicable agreement before enabling it; the plugin reports the choice but
> does not override it.

## Features

- `agy models` and `agy plugin validate` diagnostics
- MCP tools for CLI status/chat, guarded writing context, release snapshots,
  model routing, and diagnostics
- Native Antigravity `plugin.json`, `mcp_config.json`, and Agent Skills
- Recursion protection for `agy -> MCP -> agy`
- Allowlisted local paths, sensitive-file blocking, bounded image downloads,
  and private-network URL rejection
- Clean POSIX and Windows plugin bundles

## Install the official CLI

macOS or Linux:

```bash
curl -fsSL https://antigravity.google/cli/install.sh | bash
```

Windows PowerShell:

```powershell
irm https://antigravity.google/cli/install.ps1 | iex
```

See Google's [CLI installation guide](https://antigravity.google/docs/cli-install)
for authentication and enterprise setup.

## Build and install the plugin

Build from an allowlist so `.git`, tests, caches, build output, and local
credentials cannot enter the installed plugin:

```bash
python3 scripts/build_plugin_bundle.py
agy plugin validate dist/antigravity-plugin/google-antigravity-codex
agy plugin install dist/antigravity-plugin/google-antigravity-codex
```

On Windows:

```powershell
py -3 scripts/build_plugin_bundle.py --platform windows
agy plugin validate dist/antigravity-plugin/google-antigravity-codex
agy plugin install dist/antigravity-plugin/google-antigravity-codex
```

Antigravity CLI 1.1.2 stores installed plugins under
`~/.gemini/config/plugins/`. The plugin's two CLI-bridge tools are disabled in
its Antigravity-facing MCP config solely to prevent recursive self-invocation.
The direct chat, grounding, writing, image, model, and quota tools remain
available after consent.

For a local Codex checkout, point your personal Codex marketplace at this
repository or at the generated bundle, then install the plugin by name. Local
repository helpers work without Antigravity authentication.

## Verify

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
.venv/bin/python -m pytest --cov=google_antigravity_codex
.venv/bin/ruff check .
.venv/bin/python -m build
python3 scripts/google_antigravity_doctor.py --json
agy plugin validate dist/antigravity-plugin/google-antigravity-codex
```

`google_antigravity_cli_status` reports the executable, version, model-list
readiness, and plugin validation. It deliberately reports keyring auth as
"not directly inspectable". A short `google_antigravity_cli_chat` call is the
only end-to-end request-readiness check and becomes available after consent.

## Security defaults

- CLI calls default to `--mode plan --sandbox`.
- Optional integrations require explicit user consent.
- `accept-edits` requires `GOOGLE_ANTIGRAVITY_ALLOW_MUTATING_CLI=1`.
- File, repository, and CLI `cwd` parameters may only access the current
  directory or roots listed in `GOOGLE_ANTIGRAVITY_ALLOWED_ROOTS` (separated by
  the platform path separator).
- Common secret paths such as `.env`, `.ssh`, `.aws`, `.netrc`, and credential
  files remain blocked even inside an allowed root.
- MCP release tools never accept arbitrary check commands. Direct library use
  requires `GOOGLE_ANTIGRAVITY_ALLOW_CHECK_COMMANDS=1`, and commands run without
  a shell.
- Image payloads are limited to 10 MiB by default. URL downloads require HTTPS,
  an image MIME type, and globally routable DNS results.
- Prompts passed to `agy --print` are command-line arguments and may be visible
  to same-user process inspection on some operating systems. Do not put secrets
  in prompts.

See [docs/security.md](docs/security.md) and [SECURITY.md](SECURITY.md).

## Explicit user consent

Record durable consent locally:

```bash
python3 scripts/google_antigravity_consent.py grant --i-understand-and-consent
python3 scripts/google_antigravity_consent.py status
```

When installed as a Python package, the equivalent command is
`google-antigravity-consent`.

Revoke it at any time:

```bash
python3 scripts/google_antigravity_consent.py revoke
```

The consent file is written with mode `0600` under
`~/.config/google-antigravity-codex/user-consent.json`. MCP can read its status
through `google_antigravity_consent_status`, but no MCP tool can grant or modify
consent.

For an ephemeral session, enable both optional integrations with:

```bash
export GOOGLE_ANTIGRAVITY_USER_CONSENT=1
```

The feature-specific switches remain available:

```bash
export GOOGLE_ANTIGRAVITY_ENABLE_DIRECT_BACKEND=1
export GOOGLE_ANTIGRAVITY_ENABLE_CLI_BRIDGE=1
```

Restart the host application after changing environment-based consent. Inside
Antigravity itself, nested CLI status/chat tools stay hidden because calling
`agy` from an `agy`-hosted MCP server would recurse. This does not disable the
other consented tools.

## MCP tools

Primary tools:

- `google_antigravity_cli_status`
- `google_antigravity_cli_chat`
- `google_antigravity_consent_status`
- `google_antigravity_auth_status`
- `google_antigravity_login_url`
- `google_antigravity_finish_login`
- `google_antigravity_chat`
- `google_grounded_search`
- `google_antigravity_generate_image`
- `google_antigravity_write`
- `google_antigravity_release_snapshot`
- `google_antigravity_release_draft`
- `google_antigravity_list_models`
- `google_antigravity_route_model`
- `google_antigravity_quota_status`

## Release

Version history is in [CHANGELOG.md](CHANGELOG.md). Pushing a `v*` tag runs the
release workflow, rebuilds the wheel and clean plugin bundle, generates SHA-256
checksums, and creates a GitHub release only after tests pass.

This project is independent and is not affiliated with or endorsed by Google.
Antigravity and Google are trademarks of Google LLC.
