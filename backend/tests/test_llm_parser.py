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
        mock_settings.llm_model = "llama-3.1-8b-instant"
        mock_settings.groq_api_key = "test-key"
        mock_settings.llm_timeout_seconds = 10.0

        with patch(
            "parsers.llm_provider.asyncio.wait_for", AsyncMock(return_value=mock_response)
        ):
            result = await complete("Parse this job", json_mode=True)
            assert "title" in result


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
