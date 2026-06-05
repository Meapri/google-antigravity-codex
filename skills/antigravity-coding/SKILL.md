---
name: antigravity-coding
description: "Use when the user asks for coding help, architecture analysis, debugging strategy, refactoring options, implementation planning, or code explanation where Antigravity model assistance can complement Codex's local repo work."
---

# Antigravity Coding

Use this skill for engineering tasks where Codex should combine local repo
inspection with Antigravity model reasoning.

## Workflow

1. Inspect the local files, errors, tests, and git state in Codex first.
2. Use `google_antigravity_route_model` with `task: "code"` when model choice
   matters or the task is complex.
3. Use `google_antigravity_chat` for code reasoning, architecture tradeoffs,
   bug hypotheses, refactor plans, or alternative implementation sketches.
4. Apply edits in Codex only after validating the model output against the
   actual codebase.
5. Run local tests or focused verification before reporting completion.

## Tool Shape

Preferred `google_antigravity_chat` arguments:

```json
{
  "model": "gemini-3.1-pro-high",
  "prompt": "Analyze this code context and suggest the root-cause fix.",
  "retry_count": 1,
  "timeout_sec": 180
}
```

Use `google_antigravity_list_models` when the user requests Claude, GPT-OSS, or
another specific model and availability is uncertain.

## Boundaries

- Do not send secrets, credential files, tokens, private keys, or raw `.env`
  contents to Antigravity.
- Do not paste large unrelated files. Summarize local context and include only
  the relevant snippets.
- Codex remains responsible for final code edits, tests, and user-facing
  conclusions.
