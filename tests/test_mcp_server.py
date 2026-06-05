from __future__ import annotations

import os
from unittest.mock import patch

from google_antigravity_codex import mcp_server


def test_initialize_and_tools_list():
    init = mcp_server.handle_request({"jsonrpc": "2.0", "id": 1, "method": "initialize"})
    tools = mcp_server.handle_request({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})

    assert init["result"]["serverInfo"]["name"] == "google-antigravity-codex"
    names = {tool["name"] for tool in tools["result"]["tools"]}
    assert "google_antigravity_chat" in names
    assert "google_grounded_search" in names
    assert "google_antigravity_generate_image" in names
    assert "google_antigravity_write" in names
    assert "google_antigravity_release_snapshot" in names
    assert "google_antigravity_release_draft" in names
    assert "google_antigravity_route_model" in names


def test_route_model_tool_schema_and_result():
    response = mcp_server.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {"name": "google_antigravity_route_model", "arguments": {"task": "writing"}},
        }
    )

    result = response["result"]["structuredContent"]
    assert result["success"] is True
    assert result["recommended_model"] == "gemini-3.1-pro-high"
    assert result["tool"] == "google_antigravity_write"


def test_auth_missing_returns_tool_error(tmp_path):
    with patch.dict(os.environ, {"GOOGLE_ANTIGRAVITY_CREDENTIALS_FILE": str(tmp_path / "missing.json")}):
        response = mcp_server.handle_request(
            {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {"name": "google_antigravity_chat", "arguments": {"prompt": "hi"}},
            }
        )

    result = response["result"]
    assert result["isError"] is True
    assert result["structuredContent"]["error_type"] == "not_logged_in"
