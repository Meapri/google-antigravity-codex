from __future__ import annotations

import base64
import os
from unittest.mock import patch

from google_antigravity_codex import chat, grounding, image


PNG_HEX = (
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4"
    "890000000d49444154789c6300010000000500010d0a2db40000000049454e44"
    "ae426082"
)


def b64_png() -> str:
    return base64.b64encode(bytes.fromhex(PNG_HEX)).decode()


def test_chat_request_adds_google_search_grounding():
    request = chat.build_request(
        messages=[{"role": "user", "content": "latest news with sources"}],
        grounding="always",
    )

    assert {"google_search": {}} in request["tools"]
    assert "toolConfig" not in request
    assert "Google Search grounding" in request["systemInstruction"]["parts"][0]["text"]


def test_chat_floors_small_generation_limits_for_reasoning_models():
    request = chat.build_request(
        messages=[{"role": "user", "content": "short answer"}],
        model="gemini-3.5-flash-high",
        max_tokens=16,
    )

    assert request["generationConfig"]["maxOutputTokens"] == 256


def test_chat_floors_small_generation_limits_for_gemini_pro_agent():
    request = chat.build_request(
        messages=[{"role": "user", "content": "short answer"}],
        model="gemini-pro-agent",
        max_tokens=16,
    )

    assert request["generationConfig"]["maxOutputTokens"] == 256


def test_chat_uses_grounding_env_default():
    seen = {}

    def fake_submit_generate_content(**kwargs):
        seen.update(kwargs)
        return {"response": {"candidates": [{"content": {"parts": [{"text": "ok"}]}}]}}

    with patch.dict(os.environ, {"GOOGLE_ANTIGRAVITY_GROUNDING": "always"}), patch.object(
        chat.auth, "get_valid_access_token", lambda: "token"
    ), patch.object(chat.client, "submit_generate_content", fake_submit_generate_content):
        result = chat.run_chat({"prompt": "latest"})

    assert result["text"] == "ok"
    assert {"google_search": {}} in seen["request"]["tools"]


def test_chat_extracts_text_and_usage():
    payload = {
        "response": {
            "candidates": [{"content": {"parts": [{"text": "hello"}]}, "finishReason": "STOP"}],
            "usageMetadata": {"promptTokenCount": 1, "candidatesTokenCount": 2, "totalTokenCount": 3},
        }
    }

    result = chat.extract_response_text(payload)

    assert result["text"] == "hello"
    assert result["usage"]["total_tokens"] == 3


def test_grounding_extracts_sources_and_claims():
    text = "A device has 16 GB memory. Sources: **https://blog.google/example**"

    urls = grounding.extract_urls(text)
    claims = grounding.extract_numeric_claims(text)
    source_type = grounding.classify_source(urls[0])

    assert urls == ["https://blog.google/example"]
    assert claims == ["16 GB"]
    assert source_type == "official"


def test_grounding_official_domains_can_be_extended():
    with patch.dict(os.environ, {"GOOGLE_ANTIGRAVITY_OFFICIAL_DOMAINS": "example.com"}):
        assert grounding.classify_source("https://docs.example.com/page") == "official"


def test_image_request_shape_and_extraction():
    request = image.build_image_request(prompt="draw", aspect_ratio="portrait", image_size="2K")
    payload = {"candidates": [{"content": {"parts": [{"inlineData": {"mimeType": "image/png", "data": b64_png()}}]}}]}

    data, kind, extension = image.extract_image_result(payload)

    assert request["generationConfig"]["responseModalities"] == ["TEXT", "IMAGE"]
    assert request["generationConfig"]["imageConfig"] == {"aspectRatio": "9:16", "imageSize": "2K"}
    assert data == b64_png()
    assert kind == "b64"
    assert extension == "png"


def test_image_model_normalization():
    assert image.normalize_model("google/gemini-3-1-flash-image") == "gemini-3.1-flash-image"
    assert image.normalize_model("nano-banana") == "gemini-3.1-flash-image"
    assert image.resolve_image_size("2048") == "2K"
