---
name: antigravity-image
description: "Legacy image-generation compatibility guidance; direct Antigravity image access is disabled and must not be enabled automatically."
---

# Antigravity Image

The bundled `google_antigravity_generate_image` tool uses the unsupported
direct backend and is disabled by default. Prefer the host's supported image
generation capability or a separately configured official API.

Do not enable the legacy backend automatically. If the user is maintaining the
compatibility code itself, keep URL downloads HTTPS-only, reject non-global
network targets, enforce MIME and byte limits, and use synthetic test data.
