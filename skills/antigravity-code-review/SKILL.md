---
name: antigravity-code-review
description: "Use when the user asks for a code review, risk review, bug audit, regression check, security-adjacent implementation review, or review of local diffs using Antigravity as a second reviewer."
---

# Antigravity Code Review

Use this skill when Antigravity should help review code, while Codex keeps the
final review responsibility.

## Workflow

1. Inspect `git status`, local diff, relevant files, and tests in Codex first.
2. Summarize only the relevant diff/context for Antigravity.
3. Use `google_antigravity_route_model` with `task: "code"` for model choice
   when needed.
4. Use `google_antigravity_chat` to ask for bugs, regressions, edge cases,
   missing tests, and behavioral risks.
5. Verify every model finding against the actual files before presenting it.

## Review Prompt Shape

Ask Antigravity for concrete findings:

```json
{
  "model": "gemini-3.1-pro-high",
  "prompt": "Review this diff for bugs, regressions, missing tests, and edge cases. Return only actionable findings with file/line references when possible.",
  "retry_count": 1,
  "timeout_sec": 180
}
```

## Output Rules

Lead with confirmed findings ordered by severity. Include file/line references
from Codex's local inspection, not from unchecked model guesses. If no confirmed
issues remain, say that clearly and mention residual test gaps.

## Boundaries

- Do not send secrets or unrelated private code.
- Do not treat Antigravity output as authoritative.
- Do not include speculative findings that Codex did not verify locally.
