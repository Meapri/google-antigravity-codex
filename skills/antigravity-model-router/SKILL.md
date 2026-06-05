---
name: antigravity-model-router
description: "Use when the user asks which Antigravity model or tool should handle a task, when model availability is uncertain, or when fallback candidates are needed for code, writing, search, release, image, or fast chat workflows."
---

# Antigravity Model Router

Use this skill before an Antigravity call when model/tool fit matters.

## Tool Preference

- Use `google_antigravity_route_model` for task routing across `chat`, `code`,
  `fast`, `grounded-search`, `writing`, `release`, and `image`.
- Use `google_antigravity_list_models` when availability is uncertain or the
  user asks about Gemini, Claude, GPT-OSS, or image model options.
- Use `google_antigravity_quota_status` when quota, paid tier, or capacity
  routing matters.

## Response Handling

Use the returned `recommended_model`, `candidates`, `tool`, `reason`, and
`arguments_template` to choose the next MCP call. If a live call fails with
capacity or rate-limit diagnostics, retry only with a listed fallback model and
keep retries low unless the user agrees to wait.

## Boundaries

- Do not assume a model exists without either route output, list output, or a
  recent successful call.
- Do not turn routing into a long discussion unless the user asks for model
  comparison.
