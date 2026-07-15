"""Shared trust-boundary helpers for local files and experimental backends."""

from __future__ import annotations

import os
import json
from pathlib import Path
from typing import Iterable

SENSITIVE_COMPONENTS = {
    ".aws",
    ".azure",
    ".config/gcloud",
    ".git",
    ".gnupg",
    ".kube",
    ".netrc",
    ".npmrc",
    ".pypirc",
    ".ssh",
    "credentials.json",
    "application_default_credentials.json",
    "id_rsa",
    "id_ed25519",
    "oauth_client.json",
    "service-account.json",
}
SENSITIVE_NAMES = {
    ".env",
    ".env.local",
    ".git-credentials",
    ".netrc",
    ".npmrc",
    ".pypirc",
}
TRUE_VALUES = {"1", "true", "yes", "on"}
CONSENT_FILE_VERSION = 1


def env_flag(name: str, *, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in TRUE_VALUES


def direct_backend_enabled() -> bool:
    return user_consent_enabled() or env_flag("GOOGLE_ANTIGRAVITY_ENABLE_DIRECT_BACKEND")


def cli_bridge_enabled() -> bool:
    return user_consent_enabled() or env_flag("GOOGLE_ANTIGRAVITY_ENABLE_CLI_BRIDGE")


def running_under_agy() -> bool:
    return env_flag("GOOGLE_ANTIGRAVITY_RUNNING_UNDER_AGY")


def user_consent_enabled() -> bool:
    if env_flag("GOOGLE_ANTIGRAVITY_USER_CONSENT"):
        return True
    try:
        data = json.loads(consent_file_path().read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return False
    return bool(
        isinstance(data, dict)
        and data.get("accepted") is True
        and int(data.get("version") or 0) == CONSENT_FILE_VERSION
    )


def consent_file_path() -> Path:
    override = os.getenv("GOOGLE_ANTIGRAVITY_CONSENT_FILE", "").strip()
    if override:
        return Path(override).expanduser()
    config = os.getenv("GOOGLE_ANTIGRAVITY_CONFIG_DIR", "").strip()
    root = Path(config).expanduser() if config else Path.home() / ".config" / "google-antigravity-codex"
    return root / "user-consent.json"


def consent_status() -> dict[str, object]:
    env_consent = env_flag("GOOGLE_ANTIGRAVITY_USER_CONSENT")
    file_consent = user_consent_enabled() and not env_consent
    master = env_consent or file_consent
    cli_specific = env_flag("GOOGLE_ANTIGRAVITY_ENABLE_CLI_BRIDGE")
    direct_specific = env_flag("GOOGLE_ANTIGRAVITY_ENABLE_DIRECT_BACKEND")
    if env_consent:
        source = "GOOGLE_ANTIGRAVITY_USER_CONSENT"
    elif file_consent:
        source = "user-consent.json"
    elif cli_specific or direct_specific:
        source = "feature_specific_environment"
    else:
        source = "none"
    return {
        "user_consent": master,
        "consent_source": source,
        "consent_file": str(consent_file_path()),
        "consent_file_active": file_consent,
        "cli_bridge_enabled": master or cli_specific,
        "direct_backend_enabled": master or direct_specific,
        "running_under_agy": running_under_agy(),
        "configuration": {
            "grant_command": (
                "python3 scripts/google_antigravity_consent.py grant "
                "--i-understand-and-consent"
            ),
            "revoke_command": "python3 scripts/google_antigravity_consent.py revoke",
            "enable_all": "GOOGLE_ANTIGRAVITY_USER_CONSENT=1",
            "enable_cli_bridge_only": "GOOGLE_ANTIGRAVITY_ENABLE_CLI_BRIDGE=1",
            "enable_direct_backend_only": "GOOGLE_ANTIGRAVITY_ENABLE_DIRECT_BACKEND=1",
        },
    }


def allowed_roots() -> list[Path]:
    roots = [Path.cwd().resolve()]
    for item in os.getenv("GOOGLE_ANTIGRAVITY_ALLOWED_ROOTS", "").split(os.pathsep):
        if item.strip():
            roots.append(Path(item).expanduser().resolve())
    return list(dict.fromkeys(roots))


def _is_within(path: Path, roots: Iterable[Path]) -> bool:
    for root in roots:
        try:
            path.relative_to(root)
            return True
        except ValueError:
            continue
    return False


def is_sensitive_path(path: Path) -> bool:
    lowered = [part.lower() for part in path.parts]
    name = path.name.lower()
    if name in SENSITIVE_NAMES or name.startswith(".env"):
        return True
    if name.endswith((".p12", ".pfx")) or (
        name.endswith((".key", ".pem")) and "public" not in name
    ):
        return True
    joined = "/".join(lowered)
    return any(
        marker in lowered or "/" + marker + "/" in "/" + joined + "/"
        for marker in SENSITIVE_COMPONENTS
    )


def resolve_allowed_path(
    value: str | Path,
    *,
    purpose: str,
    must_exist: bool = True,
    directory: bool | None = None,
    allow_sensitive: bool = False,
) -> Path:
    path = Path(value).expanduser().resolve()
    if not _is_within(path, allowed_roots()):
        roots = ", ".join(str(root) for root in allowed_roots())
        raise ValueError(f"{purpose} is outside allowed roots ({roots}): {path}")
    if not allow_sensitive and is_sensitive_path(path):
        raise ValueError(f"{purpose} points to a sensitive path and is blocked: {path}")
    if must_exist and not path.exists():
        raise ValueError(f"{purpose} does not exist: {path}")
    if directory is True and path.exists() and not path.is_dir():
        raise ValueError(f"{purpose} is not a directory: {path}")
    if directory is False and path.exists() and not path.is_file():
        raise ValueError(f"{purpose} is not a file: {path}")
    return path


def bounded_int_env(name: str, default: int, *, minimum: int, maximum: int) -> int:
    try:
        value = int(os.getenv(name, str(default)))
    except ValueError:
        value = default
    return max(minimum, min(value, maximum))
