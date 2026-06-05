"""Direct Antigravity Code Assist client primitives."""

from __future__ import annotations

from dataclasses import dataclass, field
import json
import os
import re
import time
import urllib.error
import urllib.request
import uuid
from typing import Any, Dict, Iterable, List, Optional, Tuple

from . import auth

ANTIGRAVITY_ENDPOINT_PROD = "https://cloudcode-pa.googleapis.com"
ANTIGRAVITY_ENDPOINT_FALLBACKS = (ANTIGRAVITY_ENDPOINT_PROD,)
ANTIGRAVITY_VERSION_FALLBACK = "2.0.1"
ANTIGRAVITY_VERSION_URL = "https://antigravity-auto-updater-974169037036.us-central1.run.app"
ANTIGRAVITY_VERSION_CACHE_TTL_SECONDS = 6 * 60 * 60
GOOGLE_ONE_AI_CREDIT_TYPE = "GOOGLE_ONE_AI"
FREE_TIER_ID = "free-tier"
STANDARD_TIER_ID = "standard-tier"

_VERSION_CACHE: Dict[str, Any] = {"version": ANTIGRAVITY_VERSION_FALLBACK, "fetched_at": 0.0}


class AntigravityError(RuntimeError):
    def __init__(
        self,
        message: str,
        *,
        code: str = "antigravity_error",
        status_code: Optional[int] = None,
        retry_after: Optional[float] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.status_code = status_code
        self.retry_after = retry_after
        self.details = details or {}


@dataclass
class ProjectContext:
    project_id: str = ""
    managed_project_id: str = ""
    tier_id: str = ""
    tier_name: str = ""
    paid_tier_id: str = ""
    paid_tier_name: str = ""
    has_google_one_ai_credits: bool = False
    source: str = ""
    raw: Dict[str, Any] = field(default_factory=dict)


@dataclass
class QuotaBucket:
    model_id: str
    token_type: str = ""
    remaining_fraction: float = 0.0
    reset_time_iso: str = ""
    raw: Dict[str, Any] = field(default_factory=dict)


MODEL_FALLBACKS: Dict[str, List[str]] = {
    "gemini-3.5-flash-high": ["gemini-3-flash-agent"],
    "gemini-3.5-flash-medium": ["gemini-3-flash"],
    "gemini-3.5-flash-low": ["gemini-3-flash"],
    "gemini-3.5-flash": ["gemini-3-flash-agent"],
    "gemini-3-flash-high": ["gemini-3-flash"],
    "gemini-3-flash-medium": ["gemini-3-flash"],
    "gemini-3-flash-low": ["gemini-3-flash"],
    "gemini-3.1-pro-high": ["gemini-3.1-pro-low"],
    "gemini-3.1-pro-medium": ["gemini-3.1-pro-low"],
    "gemini-3.1-pro": ["gemini-3.1-pro-low"],
    "claude-sonnet-4-6-thinking": ["claude-sonnet-4-6"],
    "claude-sonnet-4.6-thinking": ["claude-sonnet-4-6"],
    "claude-sonnet-4.6": ["claude-sonnet-4-6"],
    "claude-opus-4.6-thinking": ["claude-opus-4-6-thinking"],
    "claude-opus-4.6": ["claude-opus-4-6-thinking"],
    "claude-opus-4-6": ["claude-opus-4-6-thinking"],
    "gpt-oss-120b": ["gpt-oss-120b-medium"],
    "openai/gpt-oss-120b": ["gpt-oss-120b-medium"],
}


def normalize_model(model: Any) -> str:
    value = str(model or "").strip()
    if not value:
        return "gemini-3.5-flash-high"
    vendor, sep, bare = value.partition("/")
    if sep and vendor.lower() in {"google", "gemini", "anthropic", "openai"}:
        return bare.strip() or value
    return value


def model_candidates(model: str) -> List[str]:
    normalized = normalize_model(model).lower()
    return MODEL_FALLBACKS.get(normalized, [normalized])


def _parse_antigravity_version(text: str) -> Optional[str]:
    match = re.search(r"\b(\d+\.\d+\.\d+)\b", text or "")
    return match.group(1) if match else None


def resolve_antigravity_version(*, refresh: bool = False) -> str:
    override = os.getenv("GOOGLE_ANTIGRAVITY_VERSION", "").strip()
    if override:
        return override
    now = time.time()
    if not refresh and now - float(_VERSION_CACHE.get("fetched_at") or 0.0) < ANTIGRAVITY_VERSION_CACHE_TTL_SECONDS:
        return str(_VERSION_CACHE.get("version") or ANTIGRAVITY_VERSION_FALLBACK)
    try:
        with urllib.request.urlopen(ANTIGRAVITY_VERSION_URL, timeout=5.0) as response:
            text = response.read().decode("utf-8", errors="replace")
        version = _parse_antigravity_version(text) or ANTIGRAVITY_VERSION_FALLBACK
    except Exception:
        version = ANTIGRAVITY_VERSION_FALLBACK
    _VERSION_CACHE.update({"version": version, "fetched_at": now})
    return version


def antigravity_headers(*, access_token: str = "", refresh_version: bool = False) -> Dict[str, str]:
    version = resolve_antigravity_version(refresh=refresh_version)
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": f"Antigravity/{version} Chrome/138.0.0.0 Electron/37.0.0",
        "X-Goog-Api-Client": f"antigravity-cli/{version}",
    }
    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"
    return headers


def _retry_after_from_headers(headers: Any) -> Optional[float]:
    try:
        raw = headers.get("Retry-After") or headers.get("retry-after")
    except Exception:
        raw = None
    if not raw:
        return None
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None


def error_from_response(status: int, body_text: str, headers: Any = None) -> AntigravityError:
    parsed: Dict[str, Any] = {}
    try:
        maybe = json.loads(body_text) if body_text else {}
        if isinstance(maybe, dict):
            parsed = maybe
    except (TypeError, ValueError):
        parsed = {}
    error = parsed.get("error") if isinstance(parsed.get("error"), dict) else {}
    details = error.get("details") if isinstance(error.get("details"), list) else []
    reason = ""
    retry_after = _retry_after_from_headers(headers)
    metadata: Dict[str, Any] = {}
    for detail in details:
        if not isinstance(detail, dict):
            continue
        type_url = str(detail.get("@type") or "")
        if not reason and type_url.endswith("/google.rpc.ErrorInfo"):
            reason = str(detail.get("reason") or "")
            md = detail.get("metadata")
            if isinstance(md, dict):
                metadata = md
        if retry_after is None and type_url.endswith("/google.rpc.RetryInfo"):
            delay = detail.get("retryDelay")
            if isinstance(delay, str) and delay.endswith("s"):
                try:
                    retry_after = float(delay[:-1])
                except ValueError:
                    pass
    status_text = str(error.get("status") or "")
    message = str(error.get("message") or "").strip()
    code = f"antigravity_http_{status}"
    if status == 401:
        code = "antigravity_unauthorized"
    elif status == 429:
        code = "antigravity_rate_limited"
        if reason == "MODEL_CAPACITY_EXHAUSTED":
            code = "antigravity_capacity_exhausted"
    if not message:
        message = body_text[:500] or "empty error response"
    return AntigravityError(
        f"Antigravity HTTP {status} ({status_text or 'error'}): {message}",
        code=code,
        status_code=status,
        retry_after=retry_after,
        details={"reason": reason, "metadata": metadata, "raw": parsed},
    )


def post_json(url: str, body: Dict[str, Any], headers: Dict[str, str], *, timeout: float = 120.0) -> Dict[str, Any]:
    data = json.dumps(body).encode("utf-8")
    request = urllib.request.Request(url, data=data, method="POST", headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8", errors="replace")
            parsed = json.loads(raw) if raw else {}
            return parsed if isinstance(parsed, dict) else {}
    except urllib.error.HTTPError as exc:
        body_text = ""
        try:
            body_text = exc.read().decode("utf-8", errors="replace")
        except Exception:
            pass
        raise error_from_response(exc.code, body_text, exc.headers) from exc
    except urllib.error.URLError as exc:
        raise AntigravityError(f"Antigravity network error: {exc}", code="antigravity_network_error") from exc


def _paid_tier(raw: Dict[str, Any]) -> Tuple[str, str]:
    paid = raw.get("paidTier") or raw.get("paid_tier")
    if not isinstance(paid, dict):
        return "", ""
    return str(paid.get("id") or paid.get("tierId") or ""), str(paid.get("name") or paid.get("displayName") or "")


def _has_google_one_entitlement(paid_id: str, paid_name: str, tier_id: str = "") -> bool:
    text = f"{paid_id} {paid_name} {tier_id}".lower()
    return any(marker in text for marker in ("google ai plus", "google ai pro", "google ai ultra", "g1-plus", "g1-pro", "g1-ultra"))


def configured_project_id() -> str:
    for name in ("GOOGLE_ANTIGRAVITY_PROJECT_ID", "GOOGLE_CLOUD_PROJECT", "GOOGLE_CLOUD_PROJECT_ID"):
        value = os.getenv(name, "").strip()
        if value:
            return value
    creds = auth.load_credentials()
    return creds.project_id if creds else ""


def load_code_assist(access_token: str, *, project_id: str = "", model: str = "") -> ProjectContext:
    body: Dict[str, Any] = {
        "metadata": {
            "duetProject": project_id,
            "ideType": "IDE_UNSPECIFIED",
            "platform": "PLATFORM_UNSPECIFIED",
            "pluginType": "GEMINI",
        }
    }
    if project_id:
        body["cloudaicompanionProject"] = project_id
    payload = post_json(
        f"{ANTIGRAVITY_ENDPOINT_PROD}/v1internal:loadCodeAssist",
        body,
        antigravity_headers(access_token=access_token, refresh_version=True),
        timeout=30.0,
    )
    current = payload.get("currentTier") if isinstance(payload.get("currentTier"), dict) else {}
    tier_id = str(current.get("id") or "")
    tier_name = str(current.get("name") or current.get("displayName") or "")
    paid_id, paid_name = _paid_tier(payload)
    project = str(payload.get("cloudaicompanionProject") or project_id or "")
    ctx = ProjectContext(
        project_id=project,
        managed_project_id=project if tier_id == FREE_TIER_ID else "",
        tier_id=tier_id,
        tier_name=tier_name,
        paid_tier_id=paid_id,
        paid_tier_name=paid_name,
        has_google_one_ai_credits=_has_google_one_entitlement(paid_id, paid_name, tier_id),
        source="discovered" if project else "loadCodeAssist",
        raw=payload,
    )
    if project:
        auth.update_project_ids(project_id=project, managed_project_id=ctx.managed_project_id)
    return ctx


def ensure_project_context(access_token: str, *, model: str = "") -> ProjectContext:
    project = configured_project_id()
    try:
        return load_code_assist(access_token, project_id=project, model=model)
    except AntigravityError:
        if project:
            return ProjectContext(project_id=project, tier_id=STANDARD_TIER_ID, source="configured")
        raise


def credit_attempts(ctx: ProjectContext) -> List[bool]:
    return [True] if ctx.has_google_one_ai_credits else [False]


def wrap_request(*, project_id: str, model: str, request: Dict[str, Any], use_google_one_ai_credits: bool = False) -> Dict[str, Any]:
    body = {
        "project": project_id,
        "model": model,
        "request": request,
        "requestType": "agent",
        "userAgent": "antigravity",
        "requestId": "agent-" + str(uuid.uuid4()),
    }
    if use_google_one_ai_credits:
        body["enabledCreditTypes"] = [GOOGLE_ONE_AI_CREDIT_TYPE]
    return body


def submit_generate_content(
    *,
    access_token: str,
    model: str,
    request: Dict[str, Any],
    use_model_aliases: bool = True,
    timeout: float = 180.0,
) -> Dict[str, Any]:
    ctx = ensure_project_context(access_token, model=model)
    if not ctx.project_id:
        raise AntigravityError("Could not resolve Google Antigravity project id.", code="project_id_missing")
    candidates = model_candidates(model) if use_model_aliases else [normalize_model(model)]
    headers = antigravity_headers(access_token=access_token, refresh_version=True)
    last_error: Optional[AntigravityError] = None
    retry_statuses = {400, 404, 429, 500, 502, 503, 504}
    for candidate in candidates:
        for use_credits in credit_attempts(ctx):
            body = wrap_request(
                project_id=ctx.project_id,
                model=candidate,
                request=request,
                use_google_one_ai_credits=use_credits,
            )
            try:
                return post_json(
                    f"{ANTIGRAVITY_ENDPOINT_PROD}/v1internal:generateContent",
                    body,
                    headers,
                    timeout=timeout,
                )
            except AntigravityError as exc:
                last_error = exc
                if exc.status_code not in retry_statuses:
                    raise
    raise last_error or AntigravityError("Antigravity request failed.", code="request_failed")


def fetch_available_models(access_token: str) -> Dict[str, Any]:
    ctx = ensure_project_context(access_token, model="gemini-3.5-flash-high")
    body = {"project": ctx.project_id, "requestId": "agent-" + str(uuid.uuid4())}
    return post_json(
        f"{ANTIGRAVITY_ENDPOINT_PROD}/v1internal:fetchAvailableModels",
        body,
        antigravity_headers(access_token=access_token, refresh_version=True),
        timeout=60.0,
    )


def retrieve_user_quota(access_token: str, *, project_id: str = "") -> List[QuotaBucket]:
    body: Dict[str, Any] = {}
    if project_id:
        body["project"] = project_id
    payload = post_json(
        f"{ANTIGRAVITY_ENDPOINT_PROD}/v1internal:retrieveUserQuota",
        body,
        antigravity_headers(access_token=access_token, refresh_version=True),
        timeout=60.0,
    )
    buckets: List[QuotaBucket] = []
    raw_buckets = payload.get("buckets") or []
    if not isinstance(raw_buckets, list):
        return buckets
    for item in raw_buckets:
        if not isinstance(item, dict):
            continue
        buckets.append(
            QuotaBucket(
                model_id=str(item.get("modelId") or ""),
                token_type=str(item.get("tokenType") or "REQUESTS"),
                remaining_fraction=float(item.get("remainingFraction") or 0.0),
                reset_time_iso=str(item.get("resetTime") or ""),
                raw=item,
            )
        )
    return buckets


def static_model_catalog() -> List[Dict[str, Any]]:
    ids = [
        "gemini-3.5-flash-high",
        "gemini-3.5-flash-medium",
        "gemini-3.1-pro-high",
        "gemini-3.1-pro-low",
        "claude-sonnet-4-6-thinking",
        "claude-opus-4-6-thinking",
        "gpt-oss-120b-medium",
        "gemini-3.1-flash-image",
        "gemini-2.5-flash-image",
    ]
    return [{"id": item, "source": "static"} for item in ids]
