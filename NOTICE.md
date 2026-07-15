# Notice

This plugin includes an independent implementation of request and response
shapes used by Google's Antigravity / Code Assist endpoints. That direct path
requires explicit user consent; the official `agy` CLI remains available as a
separate integration.

Architecture and quota-parsing ideas were informed by the MIT-licensed
[NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent) and
the upstream `Meapri/google-antigravity-codex` history. No Hermes source tree,
runtime patch, repair hook, service restart logic, or installed-tree drift
checker is vendored in the release bundle.
