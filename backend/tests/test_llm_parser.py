from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from parsers.llm_provider import Provider, complete
from utils.json_repair import repair_json

_EXPECTED_FIELDS = frozenset({"title", "company"})


def test_repair_json_valid():
    result = repair_json('{"title": "Engineer", "company": "Acme"}')
    assert result["title"] == "Engineer"
    assert result["company"] == "Acme"


def test_repair_json_with_fence():
    result = repair_json('```json\n{"title": "Engineer"}\n```')
    assert result["title"] == "Engineer"


def test_repair_json_extracts_braces():
    result = repair_json('Some leading text {"title": "Engineer", "company": "A"} trailing')
    assert result["title"] == "Engineer"


def test_repair_json_raises_on_invalid():
    with pytest.raises(ValueError):
        repair_json("not json at all")


def test_repair_json_raises_on_no_expected_fields():
    with pytest.raises(ValueError, match="missing all expected fields"):
        repair_json('{"foo": 1, "bar": 2}', expected_fields=_EXPECTED_FIELDS)


@pytest.mark.asyncio
async def test_complete_groq():
    mock_choice = {"message": {"content": '{"title":"Test","company":"Corp"}'}}
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {"choices": [mock_choice]}

    with patch("parsers.llm_provider.settings") as mock_settings:
        mock_settings.llm_provider = "groq"
        mock_settings.llm_model = "qwen/qwen3.6-27b"
        mock_settings.groq_api_key = "test-key"
        mock_settings.llm_timeout_seconds = 10.0

        with patch(
            "parsers.llm_provider.asyncio.wait_for", AsyncMock(return_value=mock_response)
        ):
            result = await complete("Parse this job", json_mode=True)
            assert "title" in result


@pytest.mark.asyncio
async def test_complete_groq_gpt_oss_sends_reasoning_params():
    """gpt-oss models must request low effort + parsed reasoning (clean content)."""
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        "choices": [{"message": {"content": '{"title":"Test"}'}}]
    }
    captured: dict = {}

    class FakeClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

        async def post(self, url, json=None, headers=None):
            captured.update(json or {})
            return mock_response

    with patch("parsers.llm_provider.settings") as mock_settings:
        mock_settings.llm_provider = "groq"
        mock_settings.llm_model = "openai/gpt-oss-120b"
        mock_settings.groq_api_key = "test-key"
        mock_settings.llm_timeout_seconds = 10.0

        with patch("parsers.llm_provider.httpx.AsyncClient", return_value=FakeClient()):
            result = await complete("Parse this job", json_mode=True)
            assert "title" in result

    assert captured["model"] == "openai/gpt-oss-120b"
    assert captured["reasoning_effort"] == "low"
    assert captured["reasoning_format"] == "parsed"
    assert captured["response_format"] == {"type": "json_object"}


@pytest.mark.asyncio
async def test_complete_groq_non_gpt_oss_no_reasoning_params():
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        "choices": [{"message": {"content": '{"title":"Test"}'}}]
    }
    captured: dict = {}

    class FakeClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

        async def post(self, url, json=None, headers=None):
            captured.update(json or {})
            return mock_response

    with patch("parsers.llm_provider.settings") as mock_settings:
        mock_settings.llm_provider = "groq"
        mock_settings.llm_model = "qwen/qwen3.6-27b"
        mock_settings.groq_api_key = "test-key"
        mock_settings.llm_timeout_seconds = 10.0

        with patch("parsers.llm_provider.httpx.AsyncClient", return_value=FakeClient()):
            await complete("Parse this job", json_mode=True)

    assert "reasoning_effort" not in captured
    assert "reasoning_format" not in captured


def test_strip_reasoning_harmony_channels():
    from parsers.llm_provider import _strip_reasoning

    leaky = (
        "<|channel|>analysis<|message|>thinking about it<|end|>"
        "<|start|>assistant<|channel|>final<|message|>{\"ok\": true}"
    )
    assert _strip_reasoning(leaky) == '{"ok": true}'


def test_strip_reasoning_think_block():
    from parsers.llm_provider import _strip_reasoning

    assert _strip_reasoning('<think>internal</think>\n{"ok":1}') == '{"ok":1}'


def test_strip_reasoning_passthrough_clean_json():
    from parsers.llm_provider import _strip_reasoning

    clean = '{"title": "Engineer", "company": "Acme"}'
    assert _strip_reasoning(clean) == clean


@pytest.mark.asyncio
async def test_complete_ollama():
    mock_resp = MagicMock()
    mock_resp.response = MagicMock()
    mock_resp.response.strip.return_value = '{"title":"Test"}'

    with patch("parsers.llm_provider.settings") as mock_settings:
        mock_settings.llm_provider = "ollama"
        mock_settings.ollama_url = "http://localhost:11434"
        mock_settings.ollama_model = "qwen3:8b"
        mock_settings.llm_timeout_seconds = 10.0

        with patch(
            "parsers.llm_provider.asyncio.wait_for", AsyncMock(return_value=mock_resp)
        ):
            result = await complete("Parse this job", json_mode=True)
            assert "title" in result


def test_provider_enum():
    assert Provider.ollama.value == "ollama"
    assert Provider.groq.value == "groq"
    assert Provider.gemini.value == "gemini"
    assert Provider("groq") == Provider.groq
