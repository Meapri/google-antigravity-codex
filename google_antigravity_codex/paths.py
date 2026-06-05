"""Filesystem paths for Google Antigravity Codex.

All credentials and cache files live under this plugin's own config/cache roots
unless the user overrides a path through environment variables.
"""

from __future__ import annotations

import os
from pathlib import Path

APP_NAME = "google-antigravity-codex"


def config_dir() -> Path:
    override = os.getenv("GOOGLE_ANTIGRAVITY_CONFIG_DIR", "").strip()
    if override:
        return Path(override).expanduser()
    return Path.home() / ".config" / APP_NAME


def cache_dir() -> Path:
    override = os.getenv("GOOGLE_ANTIGRAVITY_CACHE_DIR", "").strip()
    if override:
        return Path(override).expanduser()
    return Path.home() / ".cache" / APP_NAME


def credentials_path() -> Path:
    override = os.getenv("GOOGLE_ANTIGRAVITY_CREDENTIALS_FILE", "").strip()
    if override:
        return Path(override).expanduser()
    return config_dir() / "credentials.json"


def oauth_client_path() -> Path:
    override = os.getenv("GOOGLE_ANTIGRAVITY_OAUTH_CLIENT_FILE", "").strip()
    if override:
        return Path(override).expanduser()
    return config_dir() / "oauth_client.json"


def pending_oauth_path() -> Path:
    return config_dir() / "oauth_pending.json"


def images_dir() -> Path:
    return cache_dir() / "images"


def ensure_private_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        path.parent.chmod(0o700)
    except OSError:
        pass
