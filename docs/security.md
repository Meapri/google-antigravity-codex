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
`repo`, and CLI `cwd` are constrained to configured roots. The stateless MCP
tools can carry a visible, explicit workspace/repository root; server operators
can additionally set `GOOGLE_ANTIGRAVITY_ALLOWED_ROOTS`. Explicit filesystem
roots, the user's whole home directory, path escapes, and known credential or
secret paths are rejected after symlink resolution.

Source files default to a 1 MiB limit. Git context is redacted and truncated.
Release check commands are absent from MCP schemas; an explicitly opted-in
library caller runs tokenized arguments without a shell.

## CLI recursion and mutation

The child process receives `GOOGLE_ANTIGRAVITY_CLI_BRIDGE_DEPTH=1`. Another
bridge call at that depth is rejected. The Antigravity plugin manifest also
disables the two CLI-bridge tools inside `agy`.

Codex MCP startup marks its host explicitly. The read-only CLI status tool
does not run nested `agy models` in that context because agy may load plugins
and block under the host sandbox. The local doctor script performs the live
model probe outside that nested path. An explicit environment override is
available for diagnostic testing.

CLI calls default to plan mode and sandboxing. Plan mode rejects a workspace
`cwd` and runs in a disposable directory that is deleted after the call.
Mutating `accept-edits` mode requires both an explicit local environment opt-in
and a visible workspace `cwd`. Unsandboxed plan mode is always rejected.
Before starting `agy`, the bridge removes ambient environment variables whose
names identify tokens, secrets, passwords, API/private/access keys, credentials,
SSH/GPG agent sockets, or `CODEX_`/`MCP_` host state. This applies to version,
model-list, plugin-validation, and prompt calls. Ordinary runtime variables such
as `PATH`, `HOME`, locale, and explicit consent remain available.

MCP tool annotations describe likely side effects for compatible hosts, but
they are hints rather than the security boundary. Every sensitive behavior is
also checked deterministically by the server.

Credential status reads do not create files. Credential writes remain atomic
and serialized with a private sidecar lock.

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
