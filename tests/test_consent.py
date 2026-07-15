from __future__ import annotations

import json

from google_antigravity_codex import consent_cli, security


def test_local_consent_file_grant_and_revoke(tmp_path, monkeypatch):
    path = tmp_path / "consent.json"
    monkeypatch.setenv("GOOGLE_ANTIGRAVITY_CONSENT_FILE", str(path))
    monkeypatch.delenv("GOOGLE_ANTIGRAVITY_USER_CONSENT", raising=False)
    assert security.user_consent_enabled() is False
    assert consent_cli.grant() == path
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["accepted"] is True
    assert payload["version"] == security.CONSENT_FILE_VERSION
    assert oct(path.stat().st_mode & 0o777) == "0o600"
    assert security.cli_bridge_enabled() is True
    assert security.direct_backend_enabled() is True
    assert security.consent_status()["consent_source"] == "user-consent.json"

    assert consent_cli.revoke() == path
    assert path.exists() is False
    assert security.user_consent_enabled() is False
