"""Legacy experimental Google Antigravity OAuth compatibility code.

The default flow is intentionally user-mediated:

1. `google_antigravity_login_url` creates a PKCE verifier and login URL.
2. The user completes Google OAuth in a browser.
3. `google_antigravity_finish_login` exchanges the pasted callback URL or code.

This unsupported path is disabled by default. No browser cookie or Keychain
access is used by this module.
"""

from __future__ import annotations

import base64
import contextlib
from dataclasses import dataclass
import hashlib
import json
import os
import secrets
import stat
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, Iterator, Optional

from . import paths, security

PROVIDER_ID = "google-antigravity"
AUTH_ENDPOINT = "https://accounts.google.com/o/oauth2/auth"
TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
USERINFO_ENDPOINT = "https://www.googleapis.com/oauth2/v1/userinfo"
REDIRECT_URI = "https://antigravity.google/oauth-callback"
OAUTH_SCOPES = (
    "https://www.googleapis.com/auth/cloud-platform "
    "https://www.googleapis.com/auth/userinfo.email "
    "https://www.googleapis.com/auth/userinfo.profile "
    "https://www.googleapis.com/auth/cclog "
    "https://www.googleapis.com/auth/experimentsandconfigs "
    "openid"
)
REFRESH_SKEW_SECONDS = 60
TOKEN_TIMEOUT_SECONDS = 20.0
PENDING_MAX_AGE_SECONDS = 20 * 60


class AuthError(RuntimeError):
    """Authentication or credential storage failure."""

    def __init__(self, message: str, *, code: str = "auth_error") -> None:
        super().__init__(message)
        self.code = code


@dataclass
class OAuthClient:
    client_id: str
    client_secret: str
    source: str = ""


@dataclass
class Credentials:
    access_token: str
    refresh_token: str
    expires_at_ms: int
    email: str = ""
    project_id: str = ""
    managed_project_id: str = ""

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Credentials":
        refresh = str(data.get("refresh_token") or data.get("refresh") or "")
        project_id = str(data.get("project_id") or "")
        managed_project_id = str(data.get("managed_project_id") or "")
        if refresh and "|" in refresh:
            refresh_parts = refresh.split("|", 2)
            refresh = refresh_parts[0]
            if len(refresh_parts) > 1 and not project_id:
                project_id = refresh_parts[1]
            if len(refresh_parts) > 2 and not managed_project_id:
                managed_project_id = refresh_parts[2]
        return cls(
            access_token=str(data.get("access_token") or data.get("access") or ""),
            refresh_token=refresh,
            expires_at_ms=int(data.get("expires_at_ms") or data.get("expires") or 0),
            email=str(data.get("email") or ""),
            project_id=project_id,
            managed_project_id=managed_project_id,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "expires_at_ms": int(self.expires_at_ms),
            "email": self.email,
            "project_id": self.project_id,
            "managed_project_id": self.managed_project_id,
        }

    def is_expired(self, skew_seconds: int = REFRESH_SKEW_SECONDS) -> bool:
        if not self.access_token or self.expires_at_ms <= 0:
            return True
        return (time.time() + max(0, skew_seconds)) * 1000 >= self.expires_at_ms


_lock_state = threading.local()


@contextlib.contextmanager
def _file_lock(path: Path) -> Iterator[None]:
    lock_path = path.with_suffix(path.suffix + ".lock")
    paths.ensure_private_parent(lock_path)
    fd = os.open(str(lock_path), os.O_CREAT | os.O_RDWR, 0o600)
    try:
        try:
            import fcntl

            fcntl.flock(fd, fcntl.LOCK_EX)
        except ImportError:
            pass
        yield
    finally:
        try:
            import fcntl

            fcntl.flock(fd, fcntl.LOCK_UN)
        except ImportError:
            pass
        os.close(fd)


def _atomic_write_json(path: Path, payload: Dict[str, Any]) -> None:
    paths.ensure_private_parent(path)
    tmp = path.with_suffix(f"{path.suffix}.tmp.{os.getpid()}.{secrets.token_hex(4)}")
    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    try:
        fd = os.open(
            str(tmp),
            os.O_WRONLY | os.O_CREAT | os.O_EXCL,
            stat.S_IRUSR | stat.S_IWUSR,
        )
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(text)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)
    finally:
        try:
            if tmp.exists():
                tmp.unlink()
        except OSError:
            pass


def redact_secret(value: Any) -> str:
    text = str(value or "")
    if not text:
        return ""
    if len(text) <= 8:
        return f"<redacted:{len(text)}>"
    return f"{text[:4]}...<redacted:{len(text)}>"


def mask_email(value: str) -> str:
    text = str(value or "").strip()
    if "@" not in text:
        return ""
    local, domain = text.split("@", 1)
    if not local or not domain:
        return ""
    if len(local) <= 2:
        masked_local = local[:1] + "*"
    else:
        masked_local = local[:2] + "***" + local[-1:]
    return f"{masked_local}@{domain}"


def load_oauth_client() -> Optional[OAuthClient]:
    env_id = os.getenv("GOOGLE_ANTIGRAVITY_CLIENT_ID", "").strip()
    env_secret = os.getenv("GOOGLE_ANTIGRAVITY_CLIENT_SECRET", "").strip()
    if env_id and env_secret:
        return OAuthClient(client_id=env_id, client_secret=env_secret, source="env")

    path = paths.oauth_client_path()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    client_id = str(data.get("client_id") or "").strip()
    client_secret = str(data.get("client_secret") or "").strip()
    if not client_id or not client_secret:
        return None
    return OAuthClient(client_id=client_id, client_secret=client_secret, source=str(path))


def require_oauth_client() -> OAuthClient:
    client = load_oauth_client()
    if client is None:
        raise AuthError(
            "Google Antigravity OAuth client is not configured. Set "
            "GOOGLE_ANTIGRAVITY_CLIENT_ID and GOOGLE_ANTIGRAVITY_CLIENT_SECRET, "
            f"or write {paths.oauth_client_path()} with client_id/client_secret.",
            code="oauth_client_missing",
        )
    return client


def load_credentials() -> Optional[Credentials]:
    path = paths.credentials_path()
    try:
        with _file_lock(path):
            data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    creds = Credentials.from_dict(data)
    if not creds.refresh_token and not creds.access_token:
        return None
    return creds


def save_credentials(creds: Credentials) -> None:
    path = paths.credentials_path()
    with _file_lock(path):
        _atomic_write_json(path, creds.to_dict())


def clear_credentials() -> None:
    path = paths.credentials_path()
    with _file_lock(path):
        try:
            path.unlink()
        except FileNotFoundError:
            pass


def update_project_ids(project_id: str = "", managed_project_id: str = "") -> None:
    creds = load_credentials()
    if creds is None:
        return
    if project_id:
        creds.project_id = project_id
    if managed_project_id:
        creds.managed_project_id = managed_project_id
    save_credentials(creds)


def _generate_pkce_pair() -> tuple[str, str]:
    verifier = secrets.token_urlsafe(64)
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
    return verifier, challenge


def _post_form(url: str, data: Dict[str, str], timeout: float = TOKEN_TIMEOUT_SECONDS) -> Dict[str, Any]:
    body = urllib.parse.urlencode(data).encode("ascii")
    request = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8", errors="replace")
            parsed = json.loads(raw) if raw else {}
            return parsed if isinstance(parsed, dict) else {}
    except urllib.error.HTTPError as exc:
        detail = ""
        try:
            detail = exc.read().decode("utf-8", errors="replace")
        except Exception:
            pass
        code = "oauth_http_error"
        if "invalid_grant" in detail.lower():
            code = "oauth_invalid_grant"
        raise AuthError(
            f"Google OAuth token endpoint returned HTTP {exc.code}: {detail or exc.reason}",
            code=code,
        ) from exc
    except urllib.error.URLError as exc:
        raise AuthError(f"Google OAuth token request failed: {exc}", code="oauth_network_error") from exc


def _fetch_user_email(access_token: str) -> str:
    request = urllib.request.Request(
        USERINFO_ENDPOINT + "?alt=json",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    try:
        with urllib.request.urlopen(request, timeout=TOKEN_TIMEOUT_SECONDS) as response:
            raw = response.read().decode("utf-8", errors="replace")
        data = json.loads(raw)
        return str(data.get("email") or "") if isinstance(data, dict) else ""
    except Exception:
        return ""


def _save_pending_login(payload: Dict[str, Any]) -> None:
    _atomic_write_json(paths.pending_oauth_path(), payload)


def _load_pending_login() -> Dict[str, Any]:
    path = paths.pending_oauth_path()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AuthError("No pending Antigravity OAuth login. Call login_url first.", code="oauth_pending_missing") from exc
    if not isinstance(data, dict):
        raise AuthError("Pending Antigravity OAuth login is invalid.", code="oauth_pending_invalid")
    created_at = float(data.get("created_at") or 0.0)
    if created_at and time.time() - created_at > PENDING_MAX_AGE_SECONDS:
        raise AuthError("Pending Antigravity OAuth login expired. Call login_url again.", code="oauth_pending_expired")
    return data


def build_login_url(*, force: bool = False) -> Dict[str, Any]:
    if not security.direct_backend_enabled():
        raise AuthError(
            "Direct Antigravity OAuth is disabled. Use the official agy CLI, or set "
            "GOOGLE_ANTIGRAVITY_ENABLE_DIRECT_BACKEND=1 only for isolated compatibility testing.",
            code="direct_backend_disabled",
        )
    if not force:
        existing = load_credentials()
        if existing and existing.access_token and not existing.is_expired():
            return {
                "already_logged_in": True,
                "auth_url": "",
                "credential_path": str(paths.credentials_path()),
                "email": mask_email(existing.email),
                "email_present": bool(existing.email),
            }

    client = require_oauth_client()
    verifier, challenge = _generate_pkce_pair()
    state = secrets.token_urlsafe(16)
    params = [
        ("access_type", "offline"),
        ("client_id", client.client_id),
        ("code_challenge", challenge),
        ("code_challenge_method", "S256"),
        ("prompt", "consent"),
        ("redirect_uri", REDIRECT_URI),
        ("response_type", "code"),
        ("scope", OAUTH_SCOPES),
        ("state", state),
    ]
    auth_url = AUTH_ENDPOINT + "?" + urllib.parse.urlencode(params)
    _save_pending_login(
        {
            "state": state,
            "verifier": verifier,
            "redirect_uri": REDIRECT_URI,
            "created_at": time.time(),
            "client_source": client.source,
        }
    )
    return {
        "already_logged_in": False,
        "auth_url": auth_url,
        "state": state,
        "redirect_uri": REDIRECT_URI,
        "credential_path": str(paths.credentials_path()),
        "client_source": client.source,
    }


def extract_authorization_code(raw: str, *, expected_state: str = "") -> str:
    text = (raw or "").strip()
    if not text:
        return ""
    params: Dict[str, list[str]] = {}
    if text.startswith(("http://", "https://")):
        parsed = urllib.parse.urlparse(text)
        params = urllib.parse.parse_qs(parsed.query)
        for key, value in urllib.parse.parse_qs(parsed.fragment).items():
            params.setdefault(key, value)
    elif text.startswith("?"):
        params = urllib.parse.parse_qs(text[1:])
    elif "code=" in text or "error=" in text:
        params = urllib.parse.parse_qs(text.lstrip("?"))
    if params:
        error = (params.get("error") or [""])[0]
        if error:
            raise AuthError(f"Authorization failed: {error}", code="oauth_authorization_failed")
        state = (params.get("state") or [""])[0]
        if expected_state and state and state != expected_state:
            raise AuthError("Authorization failed: state mismatch.", code="oauth_state_mismatch")
        return (params.get("code") or [""])[0].strip()
    return text


def finish_login(code_or_callback_url: str) -> Credentials:
    if not security.direct_backend_enabled():
        raise AuthError("Direct Antigravity OAuth is disabled.", code="direct_backend_disabled")
    pending = _load_pending_login()
    client = require_oauth_client()
    code = extract_authorization_code(code_or_callback_url, expected_state=str(pending.get("state") or ""))
    if not code:
        raise AuthError("No authorization code provided.", code="oauth_code_missing")
    token_resp = _post_form(
        TOKEN_ENDPOINT,
        {
            "grant_type": "authorization_code",
            "code": code,
            "code_verifier": str(pending.get("verifier") or ""),
            "client_id": client.client_id,
            "client_secret": client.client_secret,
            "redirect_uri": str(pending.get("redirect_uri") or REDIRECT_URI),
        },
    )
    access = str(token_resp.get("access_token") or "").strip()
    refresh = str(token_resp.get("refresh_token") or "").strip()
    if not access or not refresh:
        raise AuthError("OAuth exchange did not return access_token and refresh_token.", code="oauth_empty_token")
    expires_in = int(token_resp.get("expires_in") or 3600)
    creds = Credentials(
        access_token=access,
        refresh_token=refresh,
        expires_at_ms=int((time.time() + max(60, expires_in)) * 1000),
        email=_fetch_user_email(access),
    )
    save_credentials(creds)
    try:
        paths.pending_oauth_path().unlink()
    except OSError:
        pass
    return creds


_refresh_inflight: Dict[str, threading.Event] = {}
_refresh_lock = threading.Lock()


def refresh_credentials(creds: Credentials) -> Credentials:
    if not creds.refresh_token:
        raise AuthError("Cannot refresh because refresh_token is missing.", code="refresh_token_missing")
    client = require_oauth_client()
    resp = _post_form(
        TOKEN_ENDPOINT,
        {
            "grant_type": "refresh_token",
            "refresh_token": creds.refresh_token,
            "client_id": client.client_id,
            "client_secret": client.client_secret,
        },
    )
    access = str(resp.get("access_token") or "").strip()
    if not access:
        raise AuthError("Refresh response did not include access_token.", code="refresh_empty_token")
    refresh = str(resp.get("refresh_token") or "").strip() or creds.refresh_token
    expires_in = int(resp.get("expires_in") or 3600)
    creds.access_token = access
    creds.refresh_token = refresh
    creds.expires_at_ms = int((time.time() + max(60, expires_in)) * 1000)
    save_credentials(creds)
    return creds


def get_valid_access_token(*, force_refresh: bool = False) -> str:
    if not security.direct_backend_enabled():
        raise AuthError(
            "Direct Antigravity backend is disabled; use google_antigravity_cli_chat.",
            code="direct_backend_disabled",
        )
    creds = load_credentials()
    if creds is None:
        raise AuthError("No Google Antigravity credentials found. Run google_antigravity_login_url first.", code="not_logged_in")
    if not force_refresh and not creds.is_expired():
        return creds.access_token

    key = creds.refresh_token or "<no-refresh>"
    with _refresh_lock:
        event = _refresh_inflight.get(key)
        if event is None:
            event = threading.Event()
            _refresh_inflight[key] = event
            owner = True
        else:
            owner = False
    if not owner:
        event.wait(timeout=30.0)
        fresh = load_credentials()
        if fresh and not fresh.is_expired():
            return fresh.access_token

    try:
        fresh = refresh_credentials(creds)
        return fresh.access_token
    finally:
        if owner:
            with _refresh_lock:
                _refresh_inflight.pop(key, None)
            event.set()


def auth_status() -> Dict[str, Any]:
    client = load_oauth_client()
    creds = load_credentials()
    logged_in = bool(creds and creds.access_token and (creds.refresh_token or not creds.is_expired()))
    return {
        "provider": PROVIDER_ID,
        "direct_backend_enabled": security.direct_backend_enabled(),
        "experimental": True,
        "logged_in": logged_in,
        "client_configured": client is not None,
        "client_source": client.source if client else "",
        "credentials_present": creds is not None,
        "credential_path": str(paths.credentials_path()),
        "oauth_client_path": str(paths.oauth_client_path()),
        "email": mask_email(creds.email) if creds else "",
        "email_present": bool(creds and creds.email),
        "project_id": creds.project_id if creds else "",
        "managed_project_id": creds.managed_project_id if creds else "",
        "expires_at_ms": creds.expires_at_ms if creds else None,
        "access_token_present": bool(creds and creds.access_token),
        "refresh_token_present": bool(creds and creds.refresh_token),
    }
