"""Model listing helpers."""

from __future__ import annotations

from typing import Any, Dict

from . import auth, cli, client, image, response, security


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
        if security.running_under_agy():
            text_models = client.static_model_catalog()
            source = "static_fallback"
        else:
            try:
                text_models = cli.list_models()
                source = "agy_cli"
            except Exception:
                text_models = client.static_model_catalog()
                source = "static_fallback"
        image_models = image.list_models()
    return {
        "text": f"Listed {len(text_models)} text models and {len(image_models)} image models.",
        "text_models": text_models,
        "image_models": image_models,
        "source": source,
        **response.standard_fields(
            backend="agy-cli" if source == "agy_cli" else "code-assist",
            warnings=[] if source != "static_fallback" else ["model_list_static_fallback"],
        ),
    }
