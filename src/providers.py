"""Unified async LLM interface for OpenAI, Anthropic, and Google AI Studio."""

from __future__ import annotations

import os
from dataclasses import dataclass
from enum import Enum
import httpx


class Provider(Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"


@dataclass(frozen=True)
class ProviderConfig:
    name: str
    model: str
    env_key: str
    endpoint: str


PROVIDER_CONFIGS: dict[Provider, ProviderConfig] = {
    Provider.OPENAI: ProviderConfig(
        name="OpenAI",
        model="gpt-4o-mini",
        env_key="OPENAI_API_KEY",
        endpoint="https://api.openai.com/v1/chat/completions",
    ),
    Provider.ANTHROPIC: ProviderConfig(
        name="Anthropic",
        model="claude-sonnet-4-20250514",
        env_key="ANTHROPIC_API_KEY",
        endpoint="https://api.anthropic.com/v1/messages",
    ),
    Provider.GOOGLE: ProviderConfig(
        name="Google AI Studio",
        model="gemini-2.0-flash",
        env_key="GOOGLE_API_KEY",
        endpoint="https://generativelanguage.googleapis.com/v1beta/models",
    ),
}


def resolve_provider(name: str) -> Provider:
    try:
        return Provider(name.lower())
    except ValueError:
        valid = ", ".join(p.value for p in Provider)
        raise ValueError(f"Unknown provider '{name}'. Choose from: {valid}")


def resolve_api_key(provider: Provider, cli_key: str | None = None) -> str:
    if cli_key:
        return cli_key
    cfg = PROVIDER_CONFIGS[provider]
    key = os.environ.get(cfg.env_key, "")
    if not key:
        raise EnvironmentError(
            f"No API key found. Set {cfg.env_key} or pass --api-key."
        )
    return key


async def call_llm(
    provider: Provider,
    api_key: str,
    user_msg: str,
    system_msg: str = "",
    max_tokens: int = 500,
    temperature: float = 0.0,
    model_override: str | None = None,
) -> str:
    """Send a chat completion request and return the assistant's text."""
    cfg = PROVIDER_CONFIGS[provider]
    model = model_override or cfg.model

    match provider:
        case Provider.OPENAI:
            return await _call_openai(cfg, api_key, model, user_msg, system_msg, max_tokens, temperature)
        case Provider.ANTHROPIC:
            return await _call_anthropic(cfg, api_key, model, user_msg, system_msg, max_tokens, temperature)
        case Provider.GOOGLE:
            return await _call_google(cfg, api_key, model, user_msg, system_msg, max_tokens, temperature)


async def _call_openai(
    cfg: ProviderConfig,
    api_key: str,
    model: str,
    user_msg: str,
    system_msg: str,
    max_tokens: int,
    temperature: float,
) -> str:
    messages: list[dict] = []
    if system_msg:
        messages.append({"role": "system", "content": system_msg})
    messages.append({"role": "user", "content": user_msg})

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            cfg.endpoint,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            json={
                "model": model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
            },
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]


async def _call_anthropic(
    cfg: ProviderConfig,
    api_key: str,
    model: str,
    user_msg: str,
    system_msg: str,
    max_tokens: int,
    temperature: float,
) -> str:
    body: dict = {
        "model": model,
        "messages": [{"role": "user", "content": user_msg}],
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    if system_msg:
        body["system"] = system_msg

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            cfg.endpoint,
            headers={
                "Content-Type": "application/json",
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
            },
            json=body,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["content"][0]["text"]


async def _call_google(
    cfg: ProviderConfig,
    api_key: str,
    model: str,
    user_msg: str,
    system_msg: str,
    max_tokens: int,
    temperature: float,
) -> str:
    url = f"{cfg.endpoint}/{model}:generateContent?key={api_key}"

    contents: list[dict] = []
    if system_msg:
        contents.append({"role": "user", "parts": [{"text": system_msg}]})
        contents.append({"role": "model", "parts": [{"text": "Understood."}]})
    contents.append({"role": "user", "parts": [{"text": user_msg}]})

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            url,
            headers={"Content-Type": "application/json"},
            json={
                "contents": contents,
                "generationConfig": {
                    "maxOutputTokens": max_tokens,
                    "temperature": temperature,
                },
            },
        )
        resp.raise_for_status()
        data = resp.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]
