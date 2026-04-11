"""Orchestrates the full saliency analysis pipeline.

Tokenize -> baseline -> run saliency method -> normalize -> return result.
"""

from __future__ import annotations

from typing import Callable

from src.methods.base import SaliencyMethod, SaliencyResult, OnTick
from src.providers import PROVIDER_CONFIGS, Provider, call_llm
from src.tokenizer import tokenize_phrases


def normalize(scores: list[float]) -> list[float]:
    lo = min(scores)
    hi = max(scores)
    if hi == lo:
        return [0.5] * len(scores)
    return [(s - lo) / (hi - lo) for s in scores]


async def analyze(
    prompt_text: str,
    context_text: str,
    method: SaliencyMethod,
    provider: Provider,
    api_key: str,
    model: str | None = None,
    max_tokens: int = 500,
    analyze_as_system: bool = False,
    on_status: Callable[[str], None] | None = None,
    on_tick: OnTick | None = None,
) -> SaliencyResult:
    """Run a full saliency analysis and return the result."""

    def _status(msg: str) -> None:
        if on_status:
            on_status(msg)

    def _tick(done: int, total: int) -> None:
        if on_tick:
            on_tick(done, total)

    _status("Tokenizing prompt...")
    phrases = tokenize_phrases(prompt_text)

    _status(f"Getting baseline response ({len(phrases)} phrases found)...")

    async def _call(user_msg: str, system_msg: str = "") -> str:
        return await call_llm(
            provider, api_key, user_msg, system_msg,
            max_tokens=max_tokens, model_override=model,
        )

    if analyze_as_system:
        baseline = await _call(context_text, prompt_text)
    else:
        baseline = await _call(prompt_text, context_text)

    _status(f"Running {method.name} saliency...")

    async def call_perturbed(perturbed_text: str) -> str:
        if analyze_as_system:
            return await _call(context_text, perturbed_text)
        return await _call(perturbed_text, context_text)

    raw_scores = await method.compute(phrases, baseline, call_perturbed, _tick)

    _status("Normalizing scores...")
    norm_scores = normalize(raw_scores)

    resolved_model = model or PROVIDER_CONFIGS[provider].model
    api_calls = 1 + len(phrases)
    if method.name == "paraphrase":
        api_calls += len(phrases)

    low_count = sum(1 for s in norm_scores if s < 0.25)
    top_idx = norm_scores.index(max(norm_scores))

    return SaliencyResult(
        phrases=phrases,
        raw_scores=raw_scores,
        norm_scores=norm_scores,
        baseline_output=baseline,
        method=method.name,
        provider=provider.value,
        model=resolved_model,
        api_calls=api_calls,
        stats={
            "phrase_count": len(phrases),
            "top_phrase": phrases[top_idx].strip(),
            "top_score": round(norm_scores[top_idx] * 100),
            "dead_weight_pct": round((low_count / len(phrases)) * 100) if phrases else 0,
        },
    )
