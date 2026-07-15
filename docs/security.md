# Runtime security boundaries

## Supported trust model

The native `agy` bundle and Codex MCP integrations are both project surfaces.
The optional Codex-to-`agy` bridge never reads the keyring itself and is enabled
only after explicit user consent.

The direct Code Assist/OAuth modules target non-public endpoints. They are
consent-gated so the user controls whether that compatibility path is used.

Consent can be recorded through the local `google_antigravity_consent.py`
script or environment variables. MCP exposes consent status read-only and has
no tool that can grant, revoke, or modify consent.

## Local access

MCP clients are untrusted callers. `source_file`, `project_root`, release
`repo`, and CLI `cwd` are constrained to the current directory plus
`GOOGLE_ANTIGRAVITY_ALLOWED_ROOTS`. Symlinks are resolved before the boundary
check. Known credential and secret paths are denied after resolution.

Source files default to a 1 MiB limit. Git context is redacted and truncated.
Release check commands are absent from MCP schemas; an explicitly opted-in
library caller runs tokenized arguments without a shell.

## CLI recursion and mutation

The child process receives `GOOGLE_ANTIGRAVITY_CLI_BRIDGE_DEPTH=1`. Another
bridge call at that depth is rejected. The Antigravity plugin manifest also
disables the two CLI-bridge tools inside `agy`.

CLI calls default to plan mode and sandboxing. Mutating `accept-edits` mode
requires an explicit local environment opt-in.

## Network and image handling

Generated-image URLs require HTTPS and resolve only to globally routable
addresses. Redirect targets are revalidated, proxy environment variables are
ignored, MIME type is restricted to PNG/JPEG/WebP, and both Content-Length and
streamed bytes are bounded. Inline base64 is validated and bounded before a
cache file is written.

DNS rebinding between validation and connection is reduced but cannot be fully
eliminated with Python's standard URL stack. Keep URL-image handling disabled
in hostile multi-tenant environments.

## Data exposure

Prompts, selected source text, and requested Git metadata are sent to the chosen
model backend. `agy --print` places the prompt in the child process argument
list, which can be visible to same-user process inspection on some systems.
Never submit passwords, API keys, OAuth codes, tokens, cookies, or raw
credential files.
