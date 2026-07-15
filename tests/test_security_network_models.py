from __future__ import annotations

from io import BytesIO
import socket
from unittest.mock import patch

import pytest

from google_antigravity_codex import models, network, security


class Response:
    def __init__(self, data: bytes, headers=None):
        self._body = BytesIO(data)
        self.headers = headers or {}

    def read(self, size=-1):
        return self._body.read(size)


def public_dns(*args, **kwargs):
    return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("8.8.8.8", 443))]


def test_public_url_validation_and_rejections(monkeypatch):
    monkeypatch.setattr(socket, "getaddrinfo", public_dns)
    assert network.validate_public_url("https://example.com/image.png").startswith("https://")
    with pytest.raises(ValueError, match="HTTPS"):
        network.validate_public_url("http://example.com/image.png")
    with pytest.raises(ValueError, match="embedded credentials"):
        network.validate_public_url("https://user:pass@example.com/image.png")


def test_public_url_rejects_dns_failures_and_empty_results(monkeypatch):
    monkeypatch.setattr(socket, "getaddrinfo", lambda *args, **kwargs: [])
    with pytest.raises(ValueError, match="no addresses"):
        network.validate_public_url("https://example.test/image.png")

    def fail(*args, **kwargs):
        raise socket.gaierror("nope")

    monkeypatch.setattr(socket, "getaddrinfo", fail)
    with pytest.raises(ValueError, match="could not be resolved"):
        network.validate_public_url("https://example.test/image.png")


def test_bounded_download_reader():
    assert network.read_limited(Response(b"image"), 5) == b"image"
    with pytest.raises(ValueError, match="size limit"):
        network.read_limited(Response(b"toolarge"), 4)
    with pytest.raises(ValueError, match="size limit"):
        network.read_limited(Response(b"x", {"Content-Length": "99"}), 4)


def test_security_path_shape_and_bounded_env(tmp_path, monkeypatch):
    monkeypatch.setenv("GOOGLE_ANTIGRAVITY_ALLOWED_ROOTS", str(tmp_path))
    file_path = tmp_path / "file.txt"
    file_path.write_text("ok", encoding="utf-8")
    assert security.resolve_allowed_path(file_path, purpose="test", directory=False) == file_path
    with pytest.raises(ValueError, match="not a directory"):
        security.resolve_allowed_path(file_path, purpose="test", directory=True)
    with pytest.raises(ValueError, match="does not exist"):
        security.resolve_allowed_path(tmp_path / "missing", purpose="test")
    monkeypatch.setenv("LIMIT", "invalid")
    assert security.bounded_int_env("LIMIT", 5, minimum=1, maximum=10) == 5
    monkeypatch.setenv("LIMIT", "999")
    assert security.bounded_int_env("LIMIT", 5, minimum=1, maximum=10) == 10


def test_models_prefers_direct_then_cli_then_static():
    with patch.object(models.auth, "get_valid_access_token", return_value="token"), patch.object(
        models.client, "fetch_available_models", return_value={"modelIds": ["one", "two"]}
    ), patch.object(models.image, "list_models", return_value=[]):
        direct = models.list_models()
    assert direct["source"] == "fetchAvailableModels"
    assert [item["id"] for item in direct["text_models"]] == ["one", "two"]

    with patch.object(models.auth, "get_valid_access_token", side_effect=RuntimeError), patch.object(
        models.cli, "list_models", return_value=[{"id": "cli-model"}]
    ), patch.object(models.image, "list_models", return_value=[]):
        cli_result = models.list_models()
    assert cli_result["source"] == "agy_cli"

    with patch.object(models.auth, "get_valid_access_token", side_effect=RuntimeError), patch.object(
        models.cli, "list_models", side_effect=RuntimeError
    ), patch.object(models.client, "static_model_catalog", return_value=[{"id": "fallback"}]), patch.object(
        models.image, "list_models", return_value=[]
    ):
        fallback = models.list_models()
    assert fallback["source"] == "static_fallback"
    assert fallback["warnings"] == ["model_list_static_fallback"]


def test_models_never_spawn_nested_agy_when_running_as_an_agy_plugin(monkeypatch):
    monkeypatch.setenv("GOOGLE_ANTIGRAVITY_RUNNING_UNDER_AGY", "1")
    with patch.object(models.auth, "get_valid_access_token", side_effect=RuntimeError), patch.object(
        models.cli, "list_models"
    ) as cli_list, patch.object(
        models.client, "static_model_catalog", return_value=[{"id": "fallback"}]
    ), patch.object(models.image, "list_models", return_value=[]):
        result = models.list_models()
    assert result["source"] == "static_fallback"
    cli_list.assert_not_called()
