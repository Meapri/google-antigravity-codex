"""Shared trust-boundary helpers for local files and experimental backends."""

from __future__ import annotations

import os
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


def env_flag(name: str, *, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in TRUE_VALUES


def direct_backend_enabled() -> bool:
    return env_flag("GOOGLE_ANTIGRAVITY_ENABLE_DIRECT_BACKEND")


def cli_bridge_enabled() -> bool:
    return env_flag("GOOGLE_ANTIGRAVITY_ENABLE_CLI_BRIDGE")


def running_under_agy() -> bool:
    return env_flag("GOOGLE_ANTIGRAVITY_RUNNING_UNDER_AGY")


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
