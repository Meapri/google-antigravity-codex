"""Minimal MCP stdio server for Google Antigravity Codex."""

from __future__ import annotations

import json
import sys
from typing import Any, Callable, Dict, List

from . import auth, chat, client, grounding, image, models, quota, release, writing

SERVER_NAME = "google-antigravity-codex"
SERVER_VERSION = "0.2.3+codex.20260605075654"


def _schema_auth_empty() -> Dict[str, Any]:
    return {"type": "object", "properties": {}, "additionalProperties": False}


CHAT_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "prompt": {"type": "string"},
        "messages": {"type": "array", "items": {"type": "object"}},
        "system": {"type": "string"},
        "model": {"type": "string", "default": chat.DEFAULT_MODEL},
        "temperature": {"type": "number"},
        "top_p": {"type": "number"},
        "max_tokens": {"type": "integer", "minimum": 1},
        "grounding": {"type": "string", "enum": ["off", "auto", "always"], "default": "off"},
        "timeout_sec": {"type": "integer", "minimum": 20, "maximum": 600},
    },
    "additionalProperties": False,
}

GROUNDING_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "query": {"type": "string"},
        "model": {"type": "string", "default": chat.DEFAULT_MODEL},
        "max_sources": {"type": "integer", "minimum": 1, "maximum": 10, "default": 5},
        "freshness": {"type": "string", "enum": ["auto", "latest", "today", "week", "month", "official"], "default": "auto"},
        "language": {"type": "string", "default": "ko"},
        "resolve_sources": {"type": "boolean", "default": True},
        "timeout_sec": {"type": "integer", "minimum": 20, "maximum": 600},
    },
    "required": ["query"],
    "additionalProperties": False,
}

IMAGE_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "prompt": {"type": "string"},
        "model": {"type": "string", "default": image.DEFAULT_MODEL},
        "aspect_ratio": {"type": "string", "enum": ["landscape", "square", "portrait"], "default": "landscape"},
        "image_size": {"type": "string", "enum": ["512", "1K", "2K", "4K", "1024", "2048", "4096"]},
        "timeout_sec": {"type": "integer", "minimum": 20, "maximum": 600},
    },
    "required": ["prompt"],
    "additionalProperties": False,
}

WRITING_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "task": {
            "type": "string",
            "enum": sorted(writing.TASKS),
            "default": "auto",
        },
        "instruction": {"type": "string"},
        "source_text": {"type": "string"},
        "source_file": {"type": "string"},
        "context": {"type": "string"},
        "profile": {
            "oneOf": [
                {"type": "string"},
                {"type": "array", "items": {"type": "string"}},
            ]
        },
        "tone": {"type": "string"},
        "audience": {"type": "string"},
        "target_language": {"type": "string"},
        "length": {"type": "string"},
        "output_mode": {
            "type": "string",
            "enum": ["final", "alternatives", "edit-with-notes", "diff-summary"],
            "default": "final",
        },
        "project_context": {
            "type": "string",
            "enum": ["off", "auto", "git-summary", "git-diff"],
            "default": "off",
        },
        "project_root": {"type": "string", "default": "."},
        "max_project_context_chars": {"type": "integer", "minimum": 1000, "maximum": 50000},
        "model": {"type": "string", "default": writing.DEFAULT_MODEL},
        "temperature": {"type": "number"},
        "max_tokens": {"type": "integer", "minimum": 1},
        "timeout_sec": {"type": "integer", "minimum": 20, "maximum": 600},
    },
    "additionalProperties": False,
}

RELEASE_SNAPSHOT_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "repo": {"type": "string", "default": "."},
        "base_ref": {"type": "string"},
        "head_ref": {"type": "string", "default": "HEAD"},
        "check_commands": {"type": "array", "items": {"type": "string"}},
        "check_timeout_sec": {"type": "integer", "minimum": 1, "maximum": 3600},
    },
    "additionalProperties": False,
}

RELEASE_DRAFT_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        **RELEASE_SNAPSHOT_SCHEMA["properties"],
        "title": {"type": "string"},
        "version": {"type": "string"},
        "tag": {"type": "string"},
        "polish": {"type": "boolean", "default": False},
        "model": {"type": "string", "default": writing.DEFAULT_MODEL},
        "max_tokens": {"type": "integer", "minimum": 1},
        "timeout_sec": {"type": "integer", "minimum": 20, "maximum": 600},
    },
    "additionalProperties": False,
}

FINISH_LOGIN_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {"code_or_callback_url": {"type": "string"}},
    "required": ["code_or_callback_url"],
    "additionalProperties": False,
}

LOGIN_URL_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {"force": {"type": "boolean", "default": False}},
    "additionalProperties": False,
}


def tool_definitions() -> List[Dict[str, Any]]:
    return [
        {
            "name": "google_antigravity_auth_status",
            "description": "Check Google Antigravity Codex OAuth status without returning tokens.",
            "inputSchema": _schema_auth_empty(),
        },
        {
            "name": "google_antigravity_login_url",
            "description": "Create a user-mediated Google Antigravity OAuth login URL.",
            "inputSchema": LOGIN_URL_SCHEMA,
        },
        {
            "name": "google_antigravity_finish_login",
            "description": "Finish OAuth by exchanging a pasted authorization code or callback URL.",
            "inputSchema": FINISH_LOGIN_SCHEMA,
        },
        {
            "name": "google_antigravity_chat",
            "description": "Send a chat request through Google Antigravity Code Assist.",
            "inputSchema": CHAT_SCHEMA,
        },
        {
            "name": "google_grounded_search",
            "description": "Answer a current/source-backed question through Gemini native Google Search grounding.",
            "inputSchema": GROUNDING_SCHEMA,
        },
        {
            "name": "google_antigravity_generate_image",
            "description": "Generate an image through Google Antigravity image models and cache it locally.",
            "inputSchema": IMAGE_SCHEMA,
        },
        {
            "name": "google_antigravity_write",
            "description": "Draft, rewrite, polish, translate, summarize, or prepare public prose through Antigravity chat.",
            "inputSchema": WRITING_SCHEMA,
        },
        {
            "name": "google_antigravity_release_snapshot",
            "description": "Collect a local git release snapshot: branch, diff, commits, versions, tools, checks, and bump suggestion.",
            "inputSchema": RELEASE_SNAPSHOT_SCHEMA,
        },
        {
            "name": "google_antigravity_release_draft",
            "description": "Draft PR descriptions, release notes, and changelog entries from a local git release snapshot.",
            "inputSchema": RELEASE_DRAFT_SCHEMA,
        },
        {
            "name": "google_antigravity_list_models",
            "description": "List text and image models visible to Google Antigravity.",
            "inputSchema": _schema_auth_empty(),
        },
        {
            "name": "google_antigravity_quota_status",
            "description": "Fetch Google Antigravity quota/status using REST quota APIs.",
            "inputSchema": _schema_auth_empty(),
        },
    ]


def _text_result(text: str, structured: Dict[str, Any], *, is_error: bool = False) -> Dict[str, Any]:
    return {
        "content": [{"type": "text", "text": text}],
        "structuredContent": structured,
        "isError": is_error,
    }


def _safe_call(func: Callable[[Dict[str, Any]], Dict[str, Any]], arguments: Dict[str, Any]) -> Dict[str, Any]:
    try:
        data = func(arguments)
        text = data.get("text") or data.get("answer") or json.dumps(data, ensure_ascii=False, indent=2)
        return _text_result(str(text), data)
    except auth.AuthError as exc:
        return _text_result(
            str(exc),
            {"error_type": exc.code, "provider": "google-antigravity", "auth_status": auth.auth_status()},
            is_error=True,
        )
    except client.AntigravityError as exc:
        return _text_result(
            str(exc),
            {
                "error_type": exc.code,
                "status_code": exc.status_code,
                "retry_after": exc.retry_after,
                "details": exc.details,
                "provider": "google-antigravity",
            },
            is_error=True,
        )
    except Exception as exc:
        return _text_result(str(exc), {"error_type": type(exc).__name__, "provider": "google-antigravity"}, is_error=True)


def _login_url(arguments: Dict[str, Any]) -> Dict[str, Any]:
    data = auth.build_login_url(force=bool(arguments.get("force")))
    text = "Already logged in." if data.get("already_logged_in") else data.get("auth_url", "")
    return {"text": text, **data}


def _finish_login(arguments: Dict[str, Any]) -> Dict[str, Any]:
    creds = auth.finish_login(str(arguments.get("code_or_callback_url") or ""))
    masked_email = auth.mask_email(creds.email)
    return {
        "text": f"Logged in to Google Antigravity as {masked_email or '(email unavailable)'}",
        "email": masked_email,
        "email_present": bool(creds.email),
        "credential_path": str(auth.paths.credentials_path()),
        "expires_at_ms": creds.expires_at_ms,
        "project_id": creds.project_id,
    }


def dispatch_tool(name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    table: Dict[str, Callable[[Dict[str, Any]], Dict[str, Any]]] = {
        "google_antigravity_auth_status": lambda args: {"text": json.dumps(auth.auth_status(), indent=2), **auth.auth_status()},
        "google_antigravity_login_url": _login_url,
        "google_antigravity_finish_login": _finish_login,
        "google_antigravity_chat": chat.run_chat,
        "google_grounded_search": grounding.run_grounded_search,
        "google_antigravity_generate_image": image.generate_image,
        "google_antigravity_write": writing.run_writing,
        "google_antigravity_release_snapshot": release.release_snapshot,
        "google_antigravity_release_draft": release.release_draft,
        "google_antigravity_list_models": models.list_models,
        "google_antigravity_quota_status": quota.quota_status,
    }
    if name not in table:
        raise ValueError(f"unknown tool: {name}")
    return _safe_call(table[name], arguments)


def handle_request(message: Dict[str, Any]) -> Dict[str, Any] | None:
    request_id = message.get("id")
    if request_id is None:
        return None
    method = message.get("method")
    try:
        if method == "initialize":
            result = {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
            }
        elif method == "tools/list":
            result = {"tools": tool_definitions()}
        elif method == "tools/call":
            params = message.get("params") or {}
            name = str(params.get("name") or "")
            arguments = params.get("arguments") or {}
            if not isinstance(arguments, dict):
                raise ValueError("tool arguments must be an object")
            result = dispatch_tool(name, arguments)
        else:
            raise ValueError(f"unsupported method: {method}")
        return {"jsonrpc": "2.0", "id": request_id, "result": result}
    except Exception as exc:
        return {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32000, "message": str(exc)}}


def serve() -> int:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            message = json.loads(line)
        except json.JSONDecodeError as exc:
            response = {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": str(exc)}}
        else:
            response = handle_request(message)
        if response is not None:
            print(json.dumps(response, ensure_ascii=False), flush=True)
    return 0
