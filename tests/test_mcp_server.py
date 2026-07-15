from __future__ import annotations

import os
from unittest.mock import patch

from google_antigravity_codex import mcp_server


def test_initialize_and_tools_list():
    init = mcp_server.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {"protocolVersion": "2025-06-18"},
        }
    )
    tools = mcp_server.handle_request({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})

    assert init["result"]["serverInfo"]["name"] == "google-antigravity-codex"
    assert init["result"]["protocolVersion"] == "2025-06-18"
    names = {tool["name"] for tool in tools["result"]["tools"]}
    assert "google_antigravity_cli_status" in names
    assert "google_antigravity_cli_chat" in names
    assert "google_antigravity_chat" in names
    assert "google_grounded_search" in names
    assert "google_antigravity_generate_image" in names
    assert "google_antigravity_write" in names
    assert "google_antigravity_release_snapshot" in names
    assert "google_antigravity_release_draft" in names
    assert "google_antigravity_route_model" in names
    release_tool = next(
        tool for tool in tools["result"]["tools"] if tool["name"] == "google_antigravity_release_snapshot"
    )
    assert "check_commands" not in release_tool["inputSchema"]["properties"]


def test_cli_error_returns_secret_safe_tool_error():
    with patch.object(
        mcp_server.cli,
        "run_prompt",
        side_effect=mcp_server.cli.CliError(
            "request failed", code="agy_cli_request_failed", returncode=1, stderr="private"
        ),
    ):
        response = mcp_server.handle_request(
            {
                "jsonrpc": "2.0",
                "id": 5,
                "method": "tools/call",
                "params": {
                    "name": "google_antigravity_cli_chat",
                    "arguments": {"prompt": "hi"},
                },
            }
        )

    result = response["result"]
    serialized = str(result)
    assert result["isError"] is True
    assert result["structuredContent"]["error_type"] == "agy_cli_request_failed"
    assert "private" not in serialized


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
    with patch.dict(
        os.environ,
        {
            "GOOGLE_ANTIGRAVITY_CREDENTIALS_FILE": str(tmp_path / "missing.json"),
            "GOOGLE_ANTIGRAVITY_ENABLE_DIRECT_BACKEND": "1",
        },
    ):
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
