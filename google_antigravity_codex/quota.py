"""Quota and status helpers."""

from __future__ import annotations

from typing import Any, Dict, List

from . import auth, client, response


def _bar(fraction: float, width: int = 20) -> str:
    pct = max(0.0, min(1.0, float(fraction or 0.0)))
    filled = int(round(pct * width))
    return "#" * filled + "-" * (width - filled)


def _pct(fraction: float) -> str:
    pct = max(0.0, min(1.0, float(fraction or 0.0)))
    return f"{int(round(pct * 100)):3d}%"


def quota_status(_: Dict[str, Any] | None = None) -> Dict[str, Any]:
    access_token = auth.get_valid_access_token()
    ctx = client.ensure_project_context(access_token, model="gemini-3.5-flash-high")
    buckets = client.retrieve_user_quota(access_token, project_id=ctx.project_id)
    lines: List[str] = []
    lines.append("Google Antigravity quota/status")
    lines.append(f"  currentTier: {ctx.tier_id or '(unknown)'}")
    lines.append(f"  paidTier: {ctx.paid_tier_id or '(none)'}")
    if ctx.paid_tier_name:
        lines.append(f"  paidTierName: {ctx.paid_tier_name}")
    lines.append(f"  project: {ctx.project_id or '(unknown)'}")
    lines.append("")
    if not buckets:
        lines.append("Base request quota: no buckets reported")
    else:
        lines.append("Base request quota (REST retrieveUserQuota):")
        for bucket in sorted(buckets, key=lambda b: (b.model_id, b.token_type)):
            suffix = f" reset {bucket.reset_time_iso}" if bucket.reset_time_iso else ""
            lines.append(
                f"  {bucket.model_id:34s} [{bucket.token_type or 'REQUESTS':8s}] "
                f"{_bar(bucket.remaining_fraction)} {_pct(bucket.remaining_fraction)}{suffix}"
            )
    return {
        "text": "\n".join(lines),
        "project_context": {
            "project_id": ctx.project_id,
            "managed_project_id": ctx.managed_project_id,
            "tier_id": ctx.tier_id,
            "tier_name": ctx.tier_name,
            "paid_tier_id": ctx.paid_tier_id,
            "paid_tier_name": ctx.paid_tier_name,
            "has_google_one_ai_credits": ctx.has_google_one_ai_credits,
            "source": ctx.source,
        },
        "buckets": [
            {
                "model_id": bucket.model_id,
                "token_type": bucket.token_type,
                "remaining_fraction": bucket.remaining_fraction,
                "reset_time_iso": bucket.reset_time_iso,
            }
            for bucket in buckets
        ],
        **response.standard_fields(warnings=[] if buckets else ["quota_buckets_empty"]),
    }
