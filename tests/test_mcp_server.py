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
    assert "google_antigravity_consent_status" in names
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
    assert release_tool["title"]
    assert release_tool["annotations"]["readOnlyHint"] is True
    assert release_tool["outputSchema"]["type"] == "object"


def modern_request(request_id, method, params=None, *, version="2026-07-28"):
    request_params = dict(params or {})
    request_params["_meta"] = {
        "io.modelcontextprotocol/protocolVersion": version,
        "io.modelcontextprotocol/clientInfo": {"name": "pytest", "version": "1"},
        "io.modelcontextprotocol/clientCapabilities": {},
    }
    return {"jsonrpc": "2.0", "id": request_id, "method": method, "params": request_params}


def test_rc_discovery_and_stateless_tools_list():
    discovery = mcp_server.handle_request(modern_request(20, "server/discover"))
    tools = mcp_server.handle_request(modern_request(21, "tools/list"))

    assert discovery["result"]["resultType"] == "complete"
    assert "2026-07-28" in discovery["result"]["supportedVersions"]
    assert discovery["result"]["serverInfo"]["version"] == mcp_server.SERVER_VERSION
    assert discovery["result"]["ttlMs"] > 0
    assert discovery["result"]["cacheScope"] == "public"
    assert tools["result"]["resultType"] == "complete"
    assert tools["result"]["ttlMs"] > 0
    assert tools["result"]["cacheScope"] == "public"
    assert [tool["name"] for tool in tools["result"]["tools"]] == [
        tool["name"] for tool in mcp_server.tool_definitions()
    ]


def test_rc_rejects_legacy_session_methods_and_unsupported_version():
    ping = mcp_server.handle_request(modern_request(22, "ping"))
    unsupported = mcp_server.handle_request(
        modern_request(23, "server/discover", version="2027-01-01")
    )

    assert ping["error"]["code"] == -32601
    assert unsupported["error"]["code"] == -32022
    assert unsupported["error"]["data"]["requested"] == "2027-01-01"
    assert "2026-07-28" in unsupported["error"]["data"]["supported"]


def test_rc_tool_call_result_has_result_type():
    response = mcp_server.handle_request(
        modern_request(
            24,
            "tools/call",
            {"name": "google_antigravity_route_model", "arguments": {"task": "writing"}},
        )
    )

    assert response["result"]["resultType"] == "complete"
    assert response["result"]["structuredContent"]["success"] is True


def test_consent_status_is_read_only_and_reports_master_opt_in(monkeypatch):
    monkeypatch.setenv("GOOGLE_ANTIGRAVITY_USER_CONSENT", "1")
    response = mcp_server.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 8,
            "method": "tools/call",
            "params": {"name": "google_antigravity_consent_status", "arguments": {}},
        }
    )
    result = response["result"]["structuredContent"]
    assert result["user_consent"] is True
    assert result["cli_bridge_enabled"] is True
    assert result["direct_backend_enabled"] is True
    assert "set_consent" not in result


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
