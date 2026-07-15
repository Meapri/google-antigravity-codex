# Changelog

All notable changes are documented in this file.

## 0.6.0 - 2026-07-15

### Added

- Dual-era MCP support for legacy sessions and the stateless `2026-07-28`
  release-candidate protocol.
- Tool titles, annotations, output schemas, deterministic discovery metadata,
  and explicit stateless workspace roots.
- macOS runtime coverage for private credential and consent permissions,
  disposable CLI directories, and bundled MCP startup from paths with spaces.

### Security

- Plan-mode CLI prompts now run in disposable directories and cannot receive a
  repository working directory.
- The agy child process no longer inherits unrelated token, secret, password,
  API-key, private-key, credential, SSH/GPG-agent, or Codex/MCP host environment
  values. The boundary applies to all official CLI subprocesses.
- Codex-hosted status avoids the nested `agy models` path that can stall under
  a read-only MCP sandbox; the standalone doctor remains the live model check.
- Read-only authentication status no longer creates a credential lock file.
- Tests isolate consent, credentials, cache, and opt-in environment state.

## 0.5.0 - 2026-07-15

### Added

- Official `agy` 1.1.2 CLI bridge, diagnostics, and native plugin manifest.
- Allowlisted release bundles with POSIX and Windows launcher variants.
- Local path, command-execution, recursion, download-size, and SSRF guards.
- CI, compatibility validation, release packaging, and security policy.

### Changed

- The official CLI is the primary runtime path.
- Direct Code Assist, OAuth, and CLI-bridge behavior is available after
  explicit user consent, with a durable local grant/revoke workflow.
