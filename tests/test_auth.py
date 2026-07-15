from __future__ import annotations

import json
import os
from unittest.mock import patch

import pytest

from google_antigravity_codex import auth


def test_save_load_credentials_uses_private_file(tmp_path):
    path = tmp_path / "credentials.json"
    with patch.dict(os.environ, {"GOOGLE_ANTIGRAVITY_CREDENTIALS_FILE": str(path)}):
        creds = auth.Credentials(
            access_token="access",
            refresh_token="refresh",
            expires_at_ms=9999999999999,
            email="user@example.com",
        )
        auth.save_credentials(creds)
        loaded = auth.load_credentials()

    assert loaded is not None
    assert loaded.access_token == "access"
    assert loaded.refresh_token == "refresh"
    assert oct(path.stat().st_mode & 0o777) == "0o600"


def test_oauth_client_loads_from_env():
    with patch.dict(
        os.environ,
        {"GOOGLE_ANTIGRAVITY_CLIENT_ID": "cid", "GOOGLE_ANTIGRAVITY_CLIENT_SECRET": "secret"},
    ):
        client = auth.require_oauth_client()

    assert client.client_id == "cid"
    assert client.client_secret == "secret"
    assert client.source == "env"


def test_extract_authorization_code_validates_state():
    url = "https://antigravity.google/oauth-callback?code=abc&state=expected"

    assert auth.extract_authorization_code(url, expected_state="expected") == "abc"


def test_auth_status_never_returns_token_values(tmp_path):
    with patch.dict(os.environ, {"GOOGLE_ANTIGRAVITY_CREDENTIALS_FILE": str(tmp_path / "credentials.json")}):
        auth.save_credentials(
            auth.Credentials("access-secret", "refresh-secret", 9999999999999, email="user@example.com")
        )
        status = auth.auth_status()
    serialized = json.dumps(status)

    assert status["access_token_present"] is True
    assert status["refresh_token_present"] is True
    assert status["email_present"] is True
    assert status["email"] == "us***r@example.com"
    assert "access-secret" not in serialized
    assert "refresh-secret" not in serialized
    assert "user@example.com" not in serialized


def test_login_url_existing_session_masks_email(tmp_path):
    with patch.dict(
        os.environ,
        {
            "GOOGLE_ANTIGRAVITY_CREDENTIALS_FILE": str(tmp_path / "credentials.json"),
            "GOOGLE_ANTIGRAVITY_ENABLE_DIRECT_BACKEND": "1",
        },
    ):
        auth.save_credentials(
            auth.Credentials(
                access_token="access",
                refresh_token="refresh",
                expires_at_ms=9999999999999,
                email="person@example.com",
            )
        )
        result = auth.build_login_url(force=False)
    serialized = json.dumps(result)

    assert result["already_logged_in"] is True
    assert result["email"] == "pe***n@example.com"
    assert result["email_present"] is True
    assert "person@example.com" not in serialized


def test_direct_oauth_is_disabled_without_explicit_opt_in(monkeypatch):
    monkeypatch.delenv("GOOGLE_ANTIGRAVITY_ENABLE_DIRECT_BACKEND", raising=False)
    with pytest.raises(auth.AuthError) as error:
        auth.build_login_url()
    assert error.value.code == "direct_backend_disabled"


def test_credentials_parse_packed_refresh_project_ids():
    creds = auth.Credentials.from_dict(
        {
            "access": "access",
            "refresh": "refresh|project|managed",
            "expires": 123,
            "email": "user@example.com",
        }
    )

    assert creds.refresh_token == "refresh"
    assert creds.project_id == "project"
    assert creds.managed_project_id == "managed"
