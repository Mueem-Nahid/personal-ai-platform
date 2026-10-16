from __future__ import annotations

import asyncio
import logging
import re
from enum import Enum
from typing import Any

import httpx

from core.config import settings

logger = logging.getLogger(__name__)


class Provider(Enum):
    ollama = "ollama"
    groq = "groq"
    gemini = "gemini"


def _is_gpt_oss(model: str) -> bool:
    """gpt-oss models are reasoning models with Groq-specific knobs."""
    return "gpt-oss" in model.lower()


_HARMONY_MARKERS = ("<|end|>", "<|start|>", "<|return|>", "<|channel|>", "<|message|>")


def _strip_reasoning(text: str) -> str:
    """Defensively remove reasoning leakage from completion content.

    With ``reasoning_format: "parsed"`` Groq returns reasoning in a separate
    field, but a config drift (or non-Groq gateway) could leak Harmony-channel
    markup or <think> blocks into content — which would break repair_json.
    """
    if "<think>" in text and "</think>" in text:
        text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    if "<|message|>" in text:
        # Harmony channels: keep only the final channel's payload
        text = text.split("<|message|>")[-1]
    for marker in _HARMONY_MARKERS:
        text = text.replace(marker, "")
    return text.strip()


async def complete(
    prompt: str,
    *,
    json_mode: bool = True,
    max_tokens: int = 1024,
    temperature: float = 0.1,
) -> str:
    provider = Provider(settings.llm_provider)
    if provider == Provider.groq:
        return await _complete_groq(prompt, json_mode, max_tokens, temperature)
    if provider == Provider.gemini:
        return await _complete_gemini(prompt, json_mode, max_tokens, temperature)
    return await _complete_ollama(prompt, json_mode, max_tokens, temperature)


async def _complete_groq(
    prompt: str, json_mode: bool, max_tokens: int, temperature: float
) -> str:
    if not settings.groq_api_key:
        raise RuntimeError("GROQ_API_KEY not set; cannot use Groq provider")
    body: dict[str, Any] = {
        "model": settings.llm_model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    if json_mode:
        body["response_format"] = {"type": "json_object"}
    if _is_gpt_oss(settings.llm_model):
        # Reasoning models: keep reasoning short and out of `content`.
        # Reasoning tokens count toward max_tokens on Groq.
        body["reasoning_effort"] = "low"
        body["reasoning_format"] = "parsed"
    async with httpx.AsyncClient() as client:
        response = await asyncio.wait_for(
            client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                json=body,
                headers={
                    "Authorization": f"Bearer {settings.groq_api_key}",
                    "Content-Type": "application/json",
                },
            ),
            timeout=settings.llm_timeout_seconds,
        )
    response.raise_for_status()
    data = response.json()
    content = data["choices"][0]["message"]["content"]
    return _strip_reasoning(content)


async def _complete_gemini(
    prompt: str, json_mode: bool, max_tokens: int, temperature: float
) -> str:
    raise NotImplementedError("Gemini provider is not yet implemented")


async def _complete_ollama(
    prompt: str, json_mode: bool, max_tokens: int, temperature: float
) -> str:
    from ollama import AsyncClient

    client = AsyncClient(host=settings.ollama_url)
    options: dict[str, Any] = {"temperature": temperature, "num_predict": max_tokens}
    if json_mode:
        options["format"] = "json"
    try:
        response = await asyncio.wait_for(
            client.generate(
                model=settings.ollama_model,
                prompt=prompt,
                options=options,
            ),
            timeout=settings.llm_timeout_seconds,
        )
    except TimeoutError:
        logger.error(
            "LLM call timed out after %ss (provider=ollama)", settings.llm_timeout_seconds
        )
        raise
    return (response.response or "").strip()
