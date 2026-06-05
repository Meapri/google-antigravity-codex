"""Google Search grounding helper for Antigravity Gemini requests."""

from __future__ import annotations

import os
import re
import urllib.parse
import urllib.request
from typing import Any, Dict, List

from . import chat

URL_RE = re.compile(r"https?://[^\s)>\]}\"']+")
TRAILING_URL_CHARS = ".,;:*!?_~`"
CLAIM_RE = re.compile(
    r"(?<![\w])(?:\d{1,3}(?:,\d{3})+|\d+(?:\.\d+)?)\s*"
    r"(?:GB|TB|MB|GHz|MHz|nm|W|Wh|fps|FPS|core|cores|tokens?|%|년|월|일|Q[1-4])",
    re.IGNORECASE,
)
DEFAULT_OFFICIAL_DOMAINS = (
    "google.com",
    "blog.google",
    "deepmind.google",
    "ai.google.dev",
    "developers.googleblog.com",
    "nvidia.com",
    "microsoft.com",
    "github.com",
    "openai.com",
)


def _clean_url(url: str) -> str:
    return (url or "").rstrip(TRAILING_URL_CHARS)


def _official_domains() -> tuple[str, ...]:
    extras = [
        item.strip().lower().removeprefix("www.")
        for item in os.getenv("GOOGLE_ANTIGRAVITY_OFFICIAL_DOMAINS", "").split(",")
        if item.strip()
    ]
    return tuple(dict.fromkeys([*DEFAULT_OFFICIAL_DOMAINS, *extras]))


def extract_urls(text: str) -> List[str]:
    seen = set()
    urls: List[str] = []
    for match in URL_RE.finditer(text or ""):
        url = _clean_url(match.group(0))
        if url not in seen:
            seen.add(url)
            urls.append(url)
    return urls


def classify_source(url: str) -> str:
    domain = urllib.parse.urlparse(url).netloc.lower()
    if domain.startswith("www."):
        domain = domain[4:]
    if domain == "vertexaisearch.cloud.google.com":
        return "grounding_redirect"
    academic = ("arxiv.org", "nature.com", "science.org", "acm.org", "ieee.org")
    community = ("reddit.com", "x.com", "twitter.com", "news.ycombinator.com")
    if any(domain == item or domain.endswith("." + item) for item in _official_domains()):
        return "official"
    if any(domain == item or domain.endswith("." + item) for item in academic):
        return "academic"
    if any(domain == item or domain.endswith("." + item) for item in community):
        return "community"
    return "media_or_web" if domain else "unknown"


def resolve_url(url: str, *, timeout_sec: int = 8) -> Dict[str, Any]:
    parsed = urllib.parse.urlparse(url)
    source = {
        "url": url,
        "resolved_url": url,
        "domain": parsed.netloc.lower(),
        "source_type": classify_source(url),
        "redirect_resolved": False,
        "resolution_error": "",
    }
    if "vertexaisearch.cloud.google.com" not in parsed.netloc.lower():
        return source
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "google-antigravity-codex/0.1.0"})
        with urllib.request.urlopen(request, timeout=max(1, timeout_sec)) as response:
            final_url = response.geturl()
    except Exception as exc:
        source["resolution_error"] = str(exc)
        return source
    final = urllib.parse.urlparse(final_url)
    source.update(
        {
            "resolved_url": final_url,
            "domain": final.netloc.lower(),
            "source_type": classify_source(final_url),
            "redirect_resolved": final_url != url,
            "resolution_error": "",
        }
    )
    return source


def extract_numeric_claims(text: str) -> List[str]:
    seen = set()
    claims: List[str] = []
    for match in CLAIM_RE.finditer(text or ""):
        claim = match.group(0).strip()
        if claim not in seen:
            seen.add(claim)
            claims.append(claim)
    return claims[:40]


def build_prompt(arguments: Dict[str, Any]) -> str:
    query = str(arguments.get("query") or "").strip()
    if not query:
        raise ValueError("query is required")
    max_sources = max(1, min(int(arguments.get("max_sources") or 5), 10))
    freshness = str(arguments.get("freshness") or "auto").strip() or "auto"
    language = str(arguments.get("language") or "ko").strip() or "ko"
    return (
        "Use native Google Search grounding. Answer in "
        f"{language}. Freshness preference: {freshness}. Include up to {max_sources} "
        "direct source URLs when available. Separate verified facts from inference. "
        "If grounding does not find enough evidence, say that clearly. End with a "
        "Sources section whose lines include full https:// URLs.\n\n"
        f"Question: {query}"
    )


def run_grounded_search(arguments: Dict[str, Any]) -> Dict[str, Any]:
    model = str(arguments.get("model") or chat.DEFAULT_MODEL).strip() or chat.DEFAULT_MODEL
    prompt = build_prompt(arguments)
    response = chat.run_chat(
        {
            "prompt": prompt,
            "model": model,
            "grounding": "always",
            "timeout_sec": arguments.get("timeout_sec") or 180,
        }
    )
    answer = response.get("text", "")
    resolve_sources = bool(arguments.get("resolve_sources", True))
    sources = [
        resolve_url(url) if resolve_sources else {
            "url": url,
            "resolved_url": url,
            "domain": urllib.parse.urlparse(url).netloc.lower(),
            "source_type": classify_source(url),
            "redirect_resolved": False,
            "resolution_error": "",
        }
        for url in extract_urls(answer)
    ]
    official_count = sum(1 for item in sources if item.get("source_type") == "official")
    unresolved_redirect_count = sum(1 for item in sources if item.get("source_type") == "grounding_redirect")
    return {
        "answer": answer,
        "sources": sources,
        "numeric_claims": extract_numeric_claims(answer),
        "quality_signals": {
            "source_count": len(sources),
            "official_source_count": official_count,
            "unresolved_redirect_count": unresolved_redirect_count,
            "needs_manual_source_check": unresolved_redirect_count > 0 or official_count == 0,
        },
        "provider": "google-antigravity",
        "model": model,
        "grounding": "native_google_search",
        "usage": response.get("usage", {}),
    }
