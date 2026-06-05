"""Chat request and response translation for Antigravity Code Assist."""

from __future__ import annotations

import json
import os
import time
import uuid
from typing import Any, Dict, List, Optional

from . import auth, client

DEFAULT_MODEL = "gemini-3.5-flash-high"
MIN_REASONING_MODEL_OUTPUT_TOKENS = 256
MIN_OUTPUT_TOKEN_MODEL_MARKERS = (
    "gemini-3.5-flash",
    "gemini-3.1-pro",
    "gemini-3-flash",
    "gemini-pro-agent",
    "gpt-oss",
)
GROUNDING_HINT = (
    "Google Search grounding is enabled for this request. Use grounded search results "
    "for current facts, separate verified facts from inference, and include source URLs "
    "when they materially help verification."
)


def _content_to_text(content: Any) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        pieces: List[str] = []
        for item in content:
            if isinstance(item, str):
                pieces.append(item)
            elif isinstance(item, dict):
                if item.get("type") == "text" and isinstance(item.get("text"), str):
                    pieces.append(item["text"])
                elif isinstance(item.get("text"), str):
                    pieces.append(item["text"])
        return "\n".join(piece for piece in pieces if piece)
    return str(content)


def _build_contents(messages: List[Dict[str, Any]]) -> tuple[List[Dict[str, Any]], Optional[Dict[str, Any]]]:
    contents: List[Dict[str, Any]] = []
    system_parts: List[str] = []
    for message in messages:
        if not isinstance(message, dict):
            continue
        role = str(message.get("role") or "user")
        text = _content_to_text(message.get("content")).strip()
        if role == "system":
            if text:
                system_parts.append(text)
            continue
        if role in {"assistant", "model"}:
            gemini_role = "model"
        else:
            gemini_role = "user"
        if text:
            contents.append({"role": gemini_role, "parts": [{"text": text}]})
    system_instruction = None
    system_text = "\n".join(system_parts).strip()
    if system_text:
        system_instruction = {"parts": [{"text": system_text}]}
    return contents, system_instruction


def _thinking_level_from_model(model: str) -> str:
    normalized = client.normalize_model(model).lower()
    if normalized.endswith("-high"):
        return "high"
    if normalized.endswith("-low"):
        return "low"
    return ""


def _effective_max_tokens(model: str, max_tokens: Optional[int]) -> Optional[int]:
    if not isinstance(max_tokens, int) or max_tokens <= 0:
        return None
    normalized = client.normalize_model(model).lower()
    if any(marker in normalized for marker in MIN_OUTPUT_TOKEN_MODEL_MARKERS):
        return max(int(max_tokens), MIN_REASONING_MODEL_OUTPUT_TOKENS)
    return int(max_tokens)


def build_request(
    *,
    messages: List[Dict[str, Any]],
    model: str = DEFAULT_MODEL,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    top_p: Optional[float] = None,
    grounding: str = "off",
) -> Dict[str, Any]:
    contents, system_instruction = _build_contents(messages)
    body: Dict[str, Any] = {"contents": contents}
    if system_instruction:
        body["systemInstruction"] = system_instruction
    generation: Dict[str, Any] = {}
    if isinstance(temperature, (int, float)):
        generation["temperature"] = float(temperature)
    effective_max_tokens = _effective_max_tokens(model, max_tokens)
    if effective_max_tokens is not None:
        generation["maxOutputTokens"] = effective_max_tokens
    if isinstance(top_p, (int, float)):
        generation["topP"] = float(top_p)
    thinking_level = _thinking_level_from_model(model)
    if thinking_level and "pro" in client.normalize_model(model).lower():
        generation["thinkingConfig"] = {"thinkingLevel": thinking_level}
    if generation:
        body["generationConfig"] = generation
    if grounding in {"always", "auto"}:
        body["tools"] = [{"google_search": {}}]
        existing = body.get("systemInstruction")
        if isinstance(existing, dict) and isinstance(existing.get("parts"), list) and existing["parts"]:
            first = existing["parts"][0]
            if isinstance(first, dict):
                first["text"] = f"{first.get('text', '')}\n\n{GROUNDING_HINT}".strip()
        else:
            body["systemInstruction"] = {"parts": [{"text": GROUNDING_HINT}]}
    body["sessionId"] = "-" + uuid.uuid4().hex
    return body


def extract_response_text(payload: Dict[str, Any]) -> Dict[str, Any]:
    inner = payload.get("response") if isinstance(payload.get("response"), dict) else payload
    candidates = inner.get("candidates") if isinstance(inner, dict) else []
    if not isinstance(candidates, list) or not candidates:
        return {"text": "", "reasoning": "", "finish_reason": "stop", "raw": inner}
    candidate = candidates[0] if isinstance(candidates[0], dict) else {}
    content = candidate.get("content") if isinstance(candidate.get("content"), dict) else {}
    parts = content.get("parts") if isinstance(content.get("parts"), list) else []
    text_parts: List[str] = []
    reasoning_parts: List[str] = []
    tool_calls: List[Dict[str, Any]] = []
    for part in parts:
        if not isinstance(part, dict):
            continue
        if part.get("thought") is True and isinstance(part.get("text"), str):
            reasoning_parts.append(part["text"])
        elif isinstance(part.get("text"), str):
            text_parts.append(part["text"])
        elif isinstance(part.get("functionCall"), dict):
            fn = part["functionCall"]
            tool_calls.append({"name": fn.get("name", ""), "args": fn.get("args") or {}})
    usage = inner.get("usageMetadata") if isinstance(inner.get("usageMetadata"), dict) else {}
    return {
        "text": "".join(text_parts),
        "reasoning": "".join(reasoning_parts),
        "tool_calls": tool_calls,
        "finish_reason": str(candidate.get("finishReason") or "STOP").lower(),
        "usage": {
            "prompt_tokens": int(usage.get("promptTokenCount") or 0),
            "completion_tokens": int(usage.get("candidatesTokenCount") or 0),
            "total_tokens": int(usage.get("totalTokenCount") or 0),
        },
        "raw": inner,
    }


def run_chat(arguments: Dict[str, Any]) -> Dict[str, Any]:
    model = str(arguments.get("model") or DEFAULT_MODEL).strip() or DEFAULT_MODEL
    messages = arguments.get("messages")
    if not isinstance(messages, list):
        prompt = str(arguments.get("prompt") or "").strip()
        if not prompt:
            raise ValueError("prompt or messages is required")
        messages = []
        system = str(arguments.get("system") or "").strip()
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
    grounding = str(arguments.get("grounding") or os.getenv("GOOGLE_ANTIGRAVITY_GROUNDING") or "off").strip().lower()
    if grounding not in {"off", "auto", "always"}:
        grounding = "off"
    request = build_request(
        messages=messages,
        model=model,
        temperature=arguments.get("temperature"),
        max_tokens=arguments.get("max_tokens"),
        top_p=arguments.get("top_p"),
        grounding=grounding,
    )
    access_token = auth.get_valid_access_token()
    payload = client.submit_generate_content(
        access_token=access_token,
        model=model,
        request=request,
        use_model_aliases=True,
        timeout=float(arguments.get("timeout_sec") or 180.0),
    )
    extracted = extract_response_text(payload)
    return {
        "text": extracted["text"],
        "model": model,
        "provider": "google-antigravity",
        "created": int(time.time()),
        "finish_reason": extracted["finish_reason"],
        "usage": extracted.get("usage", {}),
        "reasoning": extracted.get("reasoning", ""),
        "tool_calls": extracted.get("tool_calls", []),
    }


def to_jsonable(value: Any) -> Any:
    try:
        json.dumps(value)
        return value
    except TypeError:
        return str(value)
