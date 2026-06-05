# Notice

This plugin includes a small, independent implementation of request and response
shapes used by Google's Antigravity / Code Assist endpoints.

Some translation and quota parsing ideas are adapted from the MIT-licensed
Hermes Agent project and the local Hermes Google Antigravity provider work.
Only the pieces needed for a Codex MCP plugin are reproduced here; Hermes
runtime patching, repair hooks, service restart logic, and installed-tree drift
checks are intentionally excluded.

