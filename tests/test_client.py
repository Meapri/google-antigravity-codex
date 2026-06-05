from __future__ import annotations

import os
from unittest.mock import patch

from google_antigravity_codex import client


def test_model_aliases_match_antigravity_backend_ids():
    assert client.model_candidates("gemini-3.5-flash-high") == ["gemini-3-flash-agent"]
    assert client.model_candidates("google/gemini-3.1-pro-high") == ["gemini-3.1-pro-low"]
    assert client.model_candidates("anthropic/claude-sonnet-4.6-thinking") == ["claude-sonnet-4-6"]
    assert client.model_candidates("openai/gpt-oss-120b") == ["gpt-oss-120b-medium"]


def test_wrap_request_uses_antigravity_agent_shape():
    wrapped = client.wrap_request(
        project_id="project",
        model="gemini-3-flash-agent",
        request={"contents": []},
        use_google_one_ai_credits=True,
    )

    assert wrapped["project"] == "project"
    assert wrapped["model"] == "gemini-3-flash-agent"
    assert wrapped["requestType"] == "agent"
    assert wrapped["userAgent"] == "antigravity"
    assert wrapped["enabledCreditTypes"] == ["GOOGLE_ONE_AI"]
    assert wrapped["request"] == {"contents": []}


def test_antigravity_headers_can_be_version_overridden():
    with patch.dict(os.environ, {"GOOGLE_ANTIGRAVITY_VERSION": "2.0.9"}):
        headers = client.antigravity_headers()

    assert "Antigravity/2.0.9" in headers["User-Agent"]
    assert headers["X-Goog-Api-Client"] == "antigravity-cli/2.0.9"


def test_load_code_assist_uses_google_code_assist_metadata():
    seen = {}

    def fake_post_json(url, body, headers, *, timeout):
        seen.update({"url": url, "body": body, "headers": headers, "timeout": timeout})
        return {"cloudaicompanionProject": "project", "currentTier": {"id": "standard-tier"}}

    with patch.object(client, "post_json", fake_post_json), patch.object(
        client.auth, "update_project_ids", lambda **kwargs: None
    ):
        ctx = client.load_code_assist("token")

    assert ctx.project_id == "project"
    assert seen["body"]["metadata"]["pluginType"] == "GEMINI"
    assert seen["body"]["metadata"]["duetProject"] == ""
    assert "cloudaicompanionProject" not in seen["body"]


def test_error_from_response_parses_retry_info():
    body = (
        '{"error":{"status":"RESOURCE_EXHAUSTED","message":"capacity",'
        '"details":[{"@type":"type.googleapis.com/google.rpc.RetryInfo","retryDelay":"3.5s"}]}}'
    )

    error = client.error_from_response(429, body, {})

    assert error.status_code == 429
    assert error.retry_after == 3.5
    assert error.code == "antigravity_rate_limited"
