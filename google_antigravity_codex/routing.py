"""Task-aware model routing helpers."""

from __future__ import annotations

from typing import Any, Dict, List

from . import chat, image, response


ROUTES: Dict[str, Dict[str, Any]] = {
    "chat": {
        "model": chat.DEFAULT_MODEL,
        "candidates": ["gemini-3.5-flash-high", "gemini-3.5-flash-medium", "gemini-3.1-pro-high"],
        "tool": "google_antigravity_chat",
        "reason": "Balanced default for general Codex chat.",
    },
    "code": {
        "model": "gemini-3.1-pro-high",
        "candidates": ["gemini-3.1-pro-high", "gemini-3.5-flash-high", "claude-sonnet-4-6-thinking"],
        "tool": "google_antigravity_chat",
        "reason": "Higher reasoning budget for code, architecture, and debugging.",
    },
    "fast": {
        "model": "gemini-3.5-flash-high",
        "candidates": ["gemini-3.5-flash-high", "gemini-3.5-flash-medium", "gemini-3.1-flash-lite"],
        "tool": "google_antigravity_chat",
        "reason": "Fast response path for lightweight tasks.",
    },
    "grounded-search": {
        "model": "gemini-3.5-flash-high",
        "candidates": ["gemini-3.5-flash-high", "gemini-3.1-pro-high"],
        "tool": "google_grounded_search",
        "reason": "Grounding-capable model for current facts and source checks.",
    },
    "writing": {
        "model": "gemini-3.1-pro-high",
        "candidates": ["gemini-3.1-pro-high", "gemini-3.5-flash-high", "claude-sonnet-4-6"],
        "tool": "google_antigravity_write",
        "reason": "Best default for polished prose and Korean/English tone work.",
    },
    "release": {
        "model": "gemini-3.1-pro-high",
        "candidates": ["gemini-3.1-pro-high", "gemini-3.5-flash-high"],
        "tool": "google_antigravity_release_draft",
        "reason": "Release prose benefits from stronger synthesis after deterministic snapshotting.",
    },
    "image": {
        "model": image.DEFAULT_MODEL,
        "candidates": [image.DEFAULT_MODEL],
        "tool": "google_antigravity_generate_image",
        "reason": "Only image-capable Antigravity model currently exposed by this plugin.",
    },
}


ALIASES = {
    "search": "grounded-search",
    "grounding": "grounded-search",
    "current": "grounded-search",
    "docs": "writing",
    "prose": "writing",
    "pr": "release",
    "release-notes": "release",
    "picture": "image",
    "generate-image": "image",
}


def normalize_task(value: Any) -> str:
    text = str(value or "chat").strip().lower().replace("_", "-")
    return ALIASES.get(text, text if text in ROUTES else "chat")


def route_model(arguments: Dict[str, Any]) -> Dict[str, Any]:
    task = normalize_task(arguments.get("task") or arguments.get("intent"))
    if arguments.get("image") is True:
        task = "image"
    if str(arguments.get("grounding") or "").lower() in {"always", "required"}:
        task = "grounded-search"
    if str(arguments.get("speed") or "").lower() in {"fast", "low-latency"} and task == "chat":
        task = "fast"
    route = ROUTES[task]
    candidates: List[str] = list(route["candidates"])
    preferred = str(arguments.get("preferred_model") or "").strip()
    if preferred:
        candidates = [preferred, *[item for item in candidates if item != preferred]]
    model = candidates[0]
    return {
        "text": f"Recommended {model} via {route['tool']} for task '{task}'.",
        "task": task,
        "recommended_model": model,
        "model": model,
        "candidates": candidates,
        "tool": route["tool"],
        "reason": route["reason"],
        "arguments_template": {
            "model": model,
            **({"grounding": "always"} if task == "grounded-search" else {}),
        },
        **response.standard_fields(model=model),
    }
