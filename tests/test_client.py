from __future__ import annotations

from unittest.mock import patch

import pytest

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


def test_direct_headers_identify_this_plugin_instead_of_impersonating_cli():
    headers = client.antigravity_headers()

    assert headers["User-Agent"].startswith("google-antigravity-codex/")
    assert headers["X-Goog-Api-Client"].startswith("google-antigravity-codex/")


def test_post_json_blocks_direct_backend_without_opt_in(monkeypatch):
    monkeypatch.delenv("GOOGLE_ANTIGRAVITY_ENABLE_DIRECT_BACKEND", raising=False)
    with pytest.raises(client.AntigravityError) as error:
        client.post_json("https://example.test", {}, {})
    assert error.value.code == "direct_backend_disabled"


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


def test_submit_generate_content_records_retry_diagnostics():
    calls = {"count": 0}

    def fake_post_json(url, body, headers, *, timeout):
        calls["count"] += 1
        if calls["count"] == 1:
            raise client.AntigravityError(
                "capacity",
                code="antigravity_capacity_exhausted",
                status_code=429,
                retry_after=0,
            )
        return {"response": {"candidates": [{"content": {"parts": [{"text": "ok"}]}}]}}

    with patch.object(client.auth, "load_credentials", lambda: None), patch.object(
        client, "ensure_project_context", lambda access_token, model="": client.ProjectContext(project_id="project")
    ), patch.object(client, "post_json", fake_post_json):
        payload = client.submit_generate_content(
            access_token="token",
            model="gemini-3.5-flash-high",
            request={"contents": []},
            max_retries=1,
            retry_sleep_cap_seconds=0,
        )

    diagnostics = payload["_antigravity_diagnostics"]
    assert calls["count"] == 2
    assert diagnostics["selected_model"] == "gemini-3-flash-agent"
    assert diagnostics["retry_count"] == 1
    assert diagnostics["attempts"][0]["retried"] is True
