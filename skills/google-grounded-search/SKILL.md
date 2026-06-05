---
name: google-grounded-search
description: "Default-first Google grounded search route for modern products, companies, models, releases, current facts, source-backed answers, verification, prices, schedules, official-source checks, or anything likely to have changed. Uses this plugin's Antigravity OAuth and MCP server."
---

# Google Grounded Search

Use this skill when the user asks for current, source-backed, or verification-heavy information.
When in doubt, use it before answering.

## When To Use

Use `google_grounded_search` for:

- latest or current information
- modern named products, chips, GPUs, phones, laptops, apps, services, companies, models, releases, or newly announced technologies
- source URLs, citations, official-source checks, fact checking, and claim verification
- prices, schedules, versions, policies, and anything likely to change
- Korean requests that mention `검색`, `최신`, `출처`, `근거`, `확인`, or `팩트체크`

Do not use it for pure coding, local file work, stable background knowledge,
creative writing, personal preference questions, or requests that explicitly say
not to search.

## Tool Preference

Prefer the `google_grounded_search` MCP tool from `google-antigravity-codex`
when available. It uses this plugin's OAuth credentials and Gemini native Google
Search grounding directly.

Do not fall back to generic web search as the primary route when this tool is
available and the user expects Google-grounded source checks.

## Answer Handling

Treat the tool output as evidence, not text to copy blindly. Codex remains
responsible for uncertainty, synthesis, source choice, and final wording. Prefer
`structuredContent.sources[].resolved_url` over raw redirect URLs when citing.
If `quality_signals.needs_manual_source_check` is true, say the evidence is thin
instead of overstating confidence.
