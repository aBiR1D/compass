"""LLM abstraction layer — supports Anthropic and OpenAI backends."""

from __future__ import annotations

import json
import os
from typing import Any

from dotenv import load_dotenv

load_dotenv()

_PROVIDER: str = os.getenv("COMPASS_LLM_PROVIDER", "anthropic").lower()
_ANTHROPIC_MODEL: str = os.getenv("COMPASS_ANTHROPIC_MODEL", "claude-sonnet-4-20250514")
_OPENAI_MODEL: str = os.getenv("COMPASS_OPENAI_MODEL", "gpt-4o")


async def chat(
    system: str,
    messages: list[dict[str, str]],
    *,
    temperature: float = 0.7,
    max_tokens: int = 2048,
    response_format: str | None = None,
) -> str:
    """Send a chat completion and return the assistant's text.

    Parameters
    ----------
    system:
        System prompt.
    messages:
        List of ``{"role": ..., "content": ...}`` dicts.
    temperature:
        Sampling temperature.
    max_tokens:
        Maximum tokens in the response.
    response_format:
        If ``"json"``, instruct the model to return valid JSON.
    """
    if _PROVIDER == "openai":
        return await _openai_chat(system, messages, temperature, max_tokens, response_format)
    return await _anthropic_chat(system, messages, temperature, max_tokens)


async def _anthropic_chat(
    system: str,
    messages: list[dict[str, str]],
    temperature: float,
    max_tokens: int,
) -> str:
    import anthropic

    client = anthropic.AsyncAnthropic()
    resp = await client.messages.create(
        model=_ANTHROPIC_MODEL,
        max_tokens=max_tokens,
        temperature=temperature,
        system=system,
        messages=messages,
    )
    return resp.content[0].text


async def _openai_chat(
    system: str,
    messages: list[dict[str, str]],
    temperature: float,
    max_tokens: int,
    response_format: str | None,
) -> str:
    import openai

    client = openai.AsyncOpenAI()
    full_messages = [{"role": "system", "content": system}] + messages
    kwargs: dict[str, Any] = dict(
        model=_OPENAI_MODEL,
        messages=full_messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    if response_format == "json":
        kwargs["response_format"] = {"type": "json_object"}
    resp = await client.chat.completions.create(**kwargs)
    return resp.choices[0].message.content or ""


def parse_json_response(text: str) -> dict:
    """Best-effort extraction of JSON from an LLM response."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = lines[1:]  # drop opening fence
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines)
    return json.loads(text)
