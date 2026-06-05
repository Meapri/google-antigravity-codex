---
name: gemini-writing
description: "Use proactively for prose deliverables: draft, rewrite, polish, translate, summarize, email, announcement, blog, product copy, proposal, docs prose, README text, PR description, release notes, commit or issue summary, and Korean/English tone work. This integrated version uses google_antigravity_write directly."
---

# Gemini Writing

Use this skill proactively for explicit prose deliverables. Keep engineering
judgment, implementation, debugging, and factual verification in Codex.

## When To Use

Use `google_antigravity_write` for:

- drafting, rewriting, polishing, shortening, expanding, translating, or summarizing prose
- PR descriptions, release notes, changelog entries, README/docs prose, issue summaries, emails, announcements, blog posts, proposals, and product copy
- Korean or English tone work where wording quality matters

If a request mixes code and prose, implement or review code in Codex, then route
the public-facing prose artifact through `google_antigravity_write`.

Use `google_antigravity_route_model` when prose quality, speed, or fallback
model choice matters before calling `google_antigravity_write`.

## Tool Shape

Preferred MCP arguments:

```json
{
  "task": "auto",
  "profile": ["chanwoo-ko"],
  "instruction": "Make this concise and natural.",
  "tone": "calm, direct, human",
  "audience": "the intended reader",
  "project_context": "auto",
  "output_mode": "final",
  "retry_count": 1,
  "source_text": "Text to improve"
}
```

Useful tasks include `draft`, `rewrite`, `polish`, `summarize`, `translate`,
`email`, `announcement`, `blog`, `pr-description`, `release-notes`, `readme`,
`proposal`, `product-copy`, and `technical-doc`.

Built-in profiles are `chanwoo-ko`, `professional-ko`, `github-release`,
`email-polite`, and `product-copy-clear`.

## Boundaries

- Do not use browser credential import, Chrome extension login, or Keychain access.
- Do not paste Antigravity output blindly.
- Codex must verify versions, dates, commands, tests, issue IDs, links, and release claims before publishing.
