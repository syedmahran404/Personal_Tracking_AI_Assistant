"""LLM provider abstraction.

The rest of the system depends only on `LLMProvider` — swap providers by
flipping the env var. Adding a new provider = one new class implementing
the protocol.
"""
from __future__ import annotations

import json
from typing import Any, Protocol

import httpx

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class LLMProvider(Protocol):
    async def complete(
        self,
        system: str,
        messages: list[dict[str, Any]],
        *,
        temperature: float = 0.4,
        max_tokens: int = 800,
    ) -> str: ...


class MockProvider:
    """Deterministic fake provider — used in dev and tests.

    Generates plausible answers grounded in the supplied context so the
    full pipeline (chat, insights, weekly summary) can be exercised
    without an API key.
    """

    async def complete(
        self,
        system: str,
        messages: list[dict[str, Any]],
        *,
        temperature: float = 0.4,
        max_tokens: int = 800,
    ) -> str:
        last_user = next(
            (m["content"] for m in reversed(messages) if m.get("role") == "user"),
            "",
        )
        if "weekly" in last_user.lower() or "week" in last_user.lower():
            return (
                "Here's your week at a glance: focus held strong through midweek, "
                "with the deepest blocks on Tuesday and Wednesday afternoons. "
                "Distractions clustered around late evenings — consider a hard cutoff at 9pm. "
                "Your top language was the one you spent the most time in; keep momentum."
            )
        if "distract" in last_user.lower():
            return (
                "Your biggest distraction patterns appear in the late afternoon. "
                "Try a 25-minute focus block followed by a 5-minute break (Pomodoro)."
            )
        if "code" in last_user.lower() or "coding" in last_user.lower():
            return (
                "Coding-wise you're trending up. Most active in your main project, "
                "with shorter context-switching sessions toward the end of the day."
            )
        return (
            "Based on the data I can see, you've had a balanced day. "
            "I'd recommend protecting one 90-minute deep-work block tomorrow morning."
        )


class OpenAIProvider:
    """Minimal OpenAI Chat Completions client (no SDK dep)."""

    def __init__(self, api_key: str, model: str) -> None:
        self.api_key = api_key
        self.model = model
        self.base_url = "https://api.openai.com/v1"

    async def complete(
        self,
        system: str,
        messages: list[dict[str, Any]],
        *,
        temperature: float = 0.4,
        max_tokens: int = 800,
    ) -> str:
        payload = {
            "model": self.model,
            "messages": [{"role": "system", "content": system}, *messages],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json=payload,
            )
            r.raise_for_status()
            data = r.json()
            return data["choices"][0]["message"]["content"]


class AnthropicProvider:
    """Minimal Anthropic Messages client."""

    def __init__(self, api_key: str, model: str) -> None:
        self.api_key = api_key
        self.model = model
        self.base_url = "https://api.anthropic.com/v1"

    async def complete(
        self,
        system: str,
        messages: list[dict[str, Any]],
        *,
        temperature: float = 0.4,
        max_tokens: int = 800,
    ) -> str:
        payload = {
            "model": self.model,
            "system": system,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(
                f"{self.base_url}/messages",
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json=payload,
            )
            r.raise_for_status()
            data = r.json()
            return data["content"][0]["text"]


def get_provider() -> LLMProvider:
    """Resolve provider from settings.

    Defaults to MockProvider if a real provider is requested but the API
    key is missing — this prevents broken deployments while keeping
    intent visible in logs.
    """
    p = settings.AI_PROVIDER
    if p == "openai" and settings.OPENAI_API_KEY:
        return OpenAIProvider(settings.OPENAI_API_KEY, settings.AI_MODEL)
    if p == "anthropic" and settings.ANTHROPIC_API_KEY:
        return AnthropicProvider(settings.ANTHROPIC_API_KEY, settings.AI_MODEL)
    if p != "mock":
        logger.warning("ai.provider.fallback_to_mock", requested=p)
    return MockProvider()


def safe_json_dumps(obj: Any) -> str:
    """JSON dump that survives non-serializable objects (datetimes etc)."""
    return json.dumps(obj, default=str, separators=(",", ":"))
