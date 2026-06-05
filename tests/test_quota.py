from __future__ import annotations

from google_antigravity_codex import client, quota


def test_quota_status_formats_rest_buckets(monkeypatch):
    monkeypatch.setattr(quota.auth, "get_valid_access_token", lambda: "token")
    monkeypatch.setattr(
        quota.client,
        "ensure_project_context",
        lambda *args, **kwargs: client.ProjectContext(
            project_id="project",
            tier_id="standard-tier",
            paid_tier_id="g1-ultra-tier",
            paid_tier_name="Google AI Ultra",
            raw={"upgradeSubscriptionUri": "https://example.test/?Email=full@example.com"},
        ),
    )
    monkeypatch.setattr(
        quota.client,
        "retrieve_user_quota",
        lambda *args, **kwargs: [
            client.QuotaBucket(
                model_id="gemini-3-flash-agent",
                token_type="REQUESTS",
                remaining_fraction=0.42,
                reset_time_iso="2026-06-04T12:00:00Z",
            )
        ],
    )

    result = quota.quota_status({})

    assert "paidTier: g1-ultra-tier" in result["text"]
    assert "gemini-3-flash-agent" in result["text"]
    assert "42%" in result["text"]
    assert result["buckets"][0]["remaining_fraction"] == 0.42
    assert "raw" not in result["project_context"]
    assert "raw" not in result["buckets"][0]
    assert "full@example.com" not in str(result)
