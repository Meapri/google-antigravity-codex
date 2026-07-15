"""Antigravity image generation support."""

from __future__ import annotations

import base64
import datetime
import os
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple
import urllib.request
import uuid

from . import auth, client, network, paths, response

DEFAULT_MODEL = "gemini-3.1-flash-image"
DEFAULT_ASPECT_RATIO = "landscape"

MODELS: Dict[str, Dict[str, Any]] = {
    "gemini-3.1-flash-image": {
        "display": "Nano Banana (Gemini 3.1 Flash Image)",
        "speed": "~8-20s",
        "strengths": "Legacy experimental direct image generation",
    },
    "gemini-2.5-flash-image": {
        "display": "Gemini 2.5 Flash Image",
        "speed": "~8-20s",
        "strengths": "Compatibility image model",
    },
}
MODEL_ALIASES = {
    "nano-banana": "gemini-3.1-flash-image",
    "nano-banana-pro": "gemini-3-pro-image",
    "gemini-3.1-pro-image": "gemini-3-pro-image",
    "gemini-3-pro-image-preview": "gemini-3-pro-image",
}
ASPECT_RATIOS = {"landscape": "16:9", "square": "1:1", "portrait": "9:16"}
IMAGE_SIZES = {"512", "1K", "2K", "4K"}
IMAGE_SIZE_ALIASES = {"1024": "1K", "2048": "2K", "4096": "4K", "512PX": "512", "2048PX": "2K", "4096PX": "4K"}
MIME_EXTENSIONS = {"image/png": "png", "image/jpeg": "jpg", "image/jpg": "jpg", "image/webp": "webp"}


def normalize_model(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return DEFAULT_MODEL
    vendor, sep, bare = text.partition("/")
    if sep and vendor.lower() in {"google", "gemini"}:
        text = bare.strip() or text
    text = text.replace("gemini-2-5-", "gemini-2.5-").replace("gemini-3-1-", "gemini-3.1-")
    return MODEL_ALIASES.get(text, text)


def resolve_aspect_ratio(value: Any) -> str:
    text = str(value or DEFAULT_ASPECT_RATIO).strip().lower()
    return text if text in ASPECT_RATIOS else DEFAULT_ASPECT_RATIO


def resolve_image_size(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    upper = text.upper()
    return IMAGE_SIZE_ALIASES.get(upper, upper if upper in IMAGE_SIZES else "")


def build_image_request(*, prompt: str, aspect_ratio: str, image_size: str = "") -> Dict[str, Any]:
    image_config = {"aspectRatio": ASPECT_RATIOS[resolve_aspect_ratio(aspect_ratio)]}
    if image_size:
        image_config["imageSize"] = image_size
    return {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseModalities": ["TEXT", "IMAGE"],
            "imageConfig": image_config,
        },
    }


def _model_catalog_from_payload(payload: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    ids = payload.get("imageGenerationModelIds") or payload.get("image_generation_model_ids") or []
    if not isinstance(ids, list):
        ids = []
    catalog: Dict[str, Dict[str, Any]] = {}
    details = payload.get("models") if isinstance(payload.get("models"), dict) else {}
    for raw in ids:
        model_id = normalize_model(raw)
        known = MODELS.get(model_id, {})
        detail = details.get(model_id) if isinstance(details.get(model_id), dict) else {}
        quota = detail.get("quotaInfo") if isinstance(detail.get("quotaInfo"), dict) else {}
        catalog[model_id] = {
            "display": str(detail.get("displayName") or known.get("display") or model_id),
            "speed": known.get("speed", "~8-30s"),
            "strengths": known.get("strengths", "Antigravity image generation model"),
            "quotaInfo": quota,
        }
    return catalog


def available_model_catalog(access_token: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
    if not access_token:
        try:
            access_token = auth.get_valid_access_token()
        except Exception:
            return dict(MODELS)
    try:
        payload = client.fetch_available_models(access_token)
    except Exception:
        return dict(MODELS)
    return _model_catalog_from_payload(payload) or dict(MODELS)


def iter_values(value: Any) -> Iterable[Any]:
    yield value
    if isinstance(value, dict):
        for child in value.values():
            yield from iter_values(child)
    elif isinstance(value, list):
        for child in value:
            yield from iter_values(child)


def image_extension_from_b64(value: str) -> str:
    text = value.strip()
    if text.startswith("data:image/"):
        header, _, text = text.partition(",")
        mime = header.split(";", 1)[0].removeprefix("data:").lower()
        return MIME_EXTENSIONS.get(mime, "png")
    try:
        raw = base64.b64decode(text[:256] + "==", validate=False)
    except Exception:
        return ""
    if raw.startswith(b"\x89PNG"):
        return "png"
    if raw.startswith(b"\xff\xd8\xff"):
        return "jpg"
    if raw.startswith(b"RIFF") and b"WEBP" in raw[:16]:
        return "webp"
    return ""


def looks_like_base64_image(value: str) -> bool:
    text = value.strip()
    if len(text) < 32:
        return False
    if text.startswith("data:image/"):
        return True
    try:
        raw = base64.b64decode(text[:128] + "==", validate=False)
    except Exception:
        return False
    return raw.startswith((b"\x89PNG", b"\xff\xd8\xff", b"RIFF"))


def extract_image_result(payload: Any) -> Tuple[Optional[str], str, str]:
    for item in iter_values(payload):
        if not isinstance(item, dict):
            continue
        inline = item.get("inlineData") or item.get("inline_data")
        if isinstance(inline, dict):
            data = inline.get("data") or inline.get("b64Json") or inline.get("b64_json")
            if isinstance(data, str) and data.strip():
                mime = str(inline.get("mimeType") or inline.get("mime_type") or "").lower()
                return data.strip(), "b64", MIME_EXTENSIONS.get(mime) or image_extension_from_b64(data) or "png"
        for key in ("imageUrl", "image_url", "url", "uri"):
            value = item.get(key)
            if isinstance(value, str) and value.startswith(("http://", "https://")):
                return value, "url", "png"
        for key in ("imageBase64", "image_b64", "b64Json", "b64_json", "base64", "data", "result"):
            value = item.get(key)
            if isinstance(value, str) and looks_like_base64_image(value):
                return value.strip(), "b64", image_extension_from_b64(value) or "png"
    return None, "", "png"


def _cache_file(prefix: str, extension: str) -> Path:
    directory = paths.images_dir()
    directory.mkdir(parents=True, exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    return directory / f"{prefix}_{ts}_{uuid.uuid4().hex[:8]}.{extension}"


def strip_data_url(value: str) -> Tuple[str, str]:
    text = value.strip()
    if not text.startswith("data:image/"):
        return text, image_extension_from_b64(text) or "png"
    header, _, data = text.partition(",")
    mime = header.split(";", 1)[0].removeprefix("data:").lower()
    return data.strip(), MIME_EXTENSIONS.get(mime, "png")


def save_b64_image(value: str, *, prefix: str, extension: str) -> Path:
    data, ext = strip_data_url(value)
    limit = network.max_download_bytes()
    if len(data) > ((limit + 2) // 3) * 4 + 4:
        raise ValueError(f"image exceeds the {limit}-byte size limit")
    try:
        decoded = base64.b64decode(data, validate=True)
    except ValueError as exc:
        raise ValueError("image payload is not valid base64") from exc
    if len(decoded) > limit:
        raise ValueError(f"image exceeds the {limit}-byte size limit")
    path = _cache_file(prefix, ext or extension or "png")
    path.write_bytes(decoded)
    return path


def save_url_image(url: str, *, prefix: str) -> Path:
    network.validate_public_url(url)
    request = urllib.request.Request(url, headers={"User-Agent": "google-antigravity-codex"})
    with network.public_url_opener().open(request, timeout=60.0) as response:
        network.validate_public_url(response.geturl())
        content_type = (response.headers.get("Content-Type") or "").split(";", 1)[0].lower()
        if content_type not in MIME_EXTENSIONS:
            raise ValueError(f"downloaded content type is not a supported image: {content_type or 'missing'}")
        data = network.read_limited(response, network.max_download_bytes())
    ext = MIME_EXTENSIONS[content_type]
    path = _cache_file(prefix, ext)
    path.write_bytes(data)
    return path


def list_models() -> List[Dict[str, Any]]:
    catalog = available_model_catalog()
    return [
        {
            "id": model_id,
            "display": meta["display"],
            "speed": meta["speed"],
            "strengths": meta["strengths"],
            "price": "Antigravity plan quota",
            **({"quota": meta["quotaInfo"]} if meta.get("quotaInfo") else {}),
        }
        for model_id, meta in catalog.items()
    ]


def generate_image(arguments: Dict[str, Any]) -> Dict[str, Any]:
    prompt = str(arguments.get("prompt") or "").strip()
    if not prompt:
        raise ValueError("prompt is required")
    access_token = auth.get_valid_access_token()
    requested = normalize_model(arguments.get("model") or os.getenv("GOOGLE_ANTIGRAVITY_IMAGE_MODEL") or DEFAULT_MODEL)
    catalog = available_model_catalog(access_token)
    if requested not in catalog:
        raise ValueError(
            f"Unsupported Google Antigravity image model '{requested}'. "
            f"Available image models: {', '.join(catalog) or 'none'}."
        )
    image_size = resolve_image_size(arguments.get("image_size") or arguments.get("resolution") or "")
    aspect = resolve_aspect_ratio(arguments.get("aspect_ratio") or DEFAULT_ASPECT_RATIO)
    request = build_image_request(prompt=prompt, aspect_ratio=aspect, image_size=image_size)
    payload = client.submit_generate_content(
        access_token=access_token,
        model=requested,
        request=request,
        use_model_aliases=False,
        timeout=float(arguments.get("timeout_sec") or 180.0),
        max_retries=int(arguments.get("retry_count") if arguments.get("retry_count") is not None else 1),
        retry_sleep_cap_seconds=float(arguments.get("retry_sleep_cap_sec") or 8.0),
    )
    data, kind, extension = extract_image_result(payload)
    if not data:
        raise ValueError("Antigravity response contained no image bytes or image URL.")
    if kind == "url":
        saved = save_url_image(data, prefix=f"google_antigravity_{requested}")
    else:
        saved = save_b64_image(data, prefix=f"google_antigravity_{requested}", extension=extension)
    mime_type = next((mime for mime, ext in MIME_EXTENSIONS.items() if ext == saved.suffix.removeprefix(".").lower()), "")
    return {
        "success": True,
        "text": f"Generated image: {saved}",
        "image": str(saved),
        "path": str(saved),
        "size_bytes": saved.stat().st_size,
        "mime_type": mime_type or "application/octet-stream",
        "model": requested,
        "prompt": prompt,
        "aspect_ratio": aspect,
        **response.standard_fields(
            model=requested,
            diagnostics=payload.get("_antigravity_diagnostics") if isinstance(payload.get("_antigravity_diagnostics"), dict) else {},
        ),
        **({"image_size": image_size} if image_size else {}),
    }
