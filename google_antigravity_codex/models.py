"""Model listing helpers."""

from __future__ import annotations

from typing import Any, Dict, List

from . import auth, client, image, response


def list_models(_: Dict[str, Any] | None = None) -> Dict[str, Any]:
    try:
        access_token = auth.get_valid_access_token()
        payload = client.fetch_available_models(access_token)
        text_ids = payload.get("modelIds") or payload.get("models") or []
        if isinstance(text_ids, dict):
            text_models = [{"id": key, "source": "fetchAvailableModels"} for key in text_ids]
        elif isinstance(text_ids, list):
            text_models = [{"id": str(item), "source": "fetchAvailableModels"} for item in text_ids]
        else:
            text_models = []
        image_models = image.list_models()
        source = "fetchAvailableModels"
    except Exception:
        text_models = client.static_model_catalog()
        image_models = image.list_models()
        source = "static_fallback"
    return {
        "text": f"Listed {len(text_models)} text models and {len(image_models)} image models.",
        "text_models": text_models,
        "image_models": image_models,
        "source": source,
        **response.standard_fields(warnings=[] if source != "static_fallback" else ["model_list_static_fallback"]),
    }
