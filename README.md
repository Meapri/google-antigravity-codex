# Google Antigravity Codex

Codex skills and a local MCP server centered on Google's official Antigravity
CLI (`agy`). The current release is tested with `agy 1.1.2` and requires
`agy >= 1.1.1`.

The primary supported artifact is a native Antigravity plugin bundle. It adds
skills and guarded local MCP helpers without importing Antigravity credentials.

> [!WARNING]
> The repository retains an older direct Code Assist/OAuth implementation for
> compatibility research. It uses non-public endpoints, is unsupported, and is
> disabled by default. Do not enable it for normal use or distribution.

> [!CAUTION]
> Google's current Antigravity terms say third-party software using an
> Antigravity login to access the service breaches the agreement and may lead
> to suspension or termination. Therefore the Codex-to-`agy` chat bridge is
> also disabled by default. Review the
> [Antigravity Terms](https://antigravity.google/terms) and your organization's
> applicable agreement before enabling it.

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
its Antigravity-facing MCP config to prevent recursive self-invocation.

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
only end-to-end request-readiness check, but it is unavailable unless the
bridge is explicitly enabled after reviewing the applicable terms.

## Security defaults

- CLI calls default to `--mode plan --sandbox`.
- Codex-to-`agy` chat requires `GOOGLE_ANTIGRAVITY_ENABLE_CLI_BRIDGE=1`.
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

## Experimental direct backend

The legacy tools (`google_antigravity_login_url`, direct chat, grounding,
image, quota) fail with `direct_backend_disabled` unless this is set:

```bash
export GOOGLE_ANTIGRAVITY_ENABLE_DIRECT_BACKEND=1
```

This switch is intentionally not present in the distributed MCP config. It is
for isolated compatibility tests only and does not make the non-public API a
supported integration.

The Codex-to-CLI bridge has a separate opt-in:

```bash
export GOOGLE_ANTIGRAVITY_ENABLE_CLI_BRIDGE=1
```

Only use it if your applicable Google agreement permits that integration.

## MCP tools

Primary tools:

- `google_antigravity_cli_status`
- `google_antigravity_cli_chat`
- `google_antigravity_write`
- `google_antigravity_release_snapshot`
- `google_antigravity_release_draft`
- `google_antigravity_list_models`
- `google_antigravity_route_model`

Legacy experimental tools remain discoverable with explicit descriptions so
existing clients receive a clear disabled error instead of silently falling
back to unsupported behavior.

## Release

Version history is in [CHANGELOG.md](CHANGELOG.md). Pushing a `v*` tag runs the
release workflow, rebuilds the wheel and clean plugin bundle, generates SHA-256
checksums, and creates a GitHub release only after tests pass.

This project is independent and is not affiliated with or endorsed by Google.
Antigravity and Google are trademarks of Google LLC.
