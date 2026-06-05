---
name: antigravity-image
description: "Use when the user asks to generate an image, visual, concept art, product shot, diagram-like raster image, or inspect image-generation model availability through Google Antigravity."
---

# Antigravity Image

Use this skill for image generation through `google_antigravity_generate_image`.

## Tool Preference

- Use `google_antigravity_route_model` with `task: "image"` when model choice
  matters.
- Use `google_antigravity_generate_image` for the actual generation.
- Use `google_antigravity_list_models` if image model availability is uncertain.
- Use `google_antigravity_quota_status` if quota or plan state matters.

## Tool Shape

Preferred arguments:

```json
{
  "prompt": "A clear visual prompt with no hidden text requirements.",
  "model": "gemini-3.1-flash-image",
  "aspect_ratio": "square",
  "image_size": "512",
  "retry_count": 1,
  "timeout_sec": 180
}
```

## Response Handling

Use `structuredContent.path` or `structuredContent.image` as the generated
local file path. Report `mime_type`, `size_bytes`, model, and warnings. When
showing the image in Codex desktop, use an absolute Markdown image path.

## Boundaries

- Warn that exact text, logos, and typography may be unreliable.
- Do not promise brand-safe or legally cleared output.
- Keep prompts concrete and inspectable.
