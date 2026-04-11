"""Counterfactual analysis: negate/intensify/relax phrases and measure divergence.

Instead of removing or masking, generates meaningful alternatives per phrase:
  - negate:    "Always use JSON" -> "Never use JSON"
  - intensify: "Be concise"     -> "Be extremely concise, max 10 words"
  - relax:     "You must use JSON" -> "You may optionally use JSON"

Provides richer signal: tells you *how* a phrase matters, not just *that* it matters.
A phrase that scores low on omission but high on negation is a silent guardrail.
"""

from __future__ import annotations

from typing import Awaitable, Callable

from src.methods.base import CallPerturbed, OnTick, SaliencyMethod
from src.similarity import trigram_divergence

GenerateCounterfactual = Callable[[str], Awaitable[str]]

_MODE_INSTRUCTIONS: dict[str, str] = {
    "negate": (
        "Rewrite the following instruction to mean the EXACT OPPOSITE. "
        "Flip every constraint, requirement, or directive. "
        "Examples: 'always'->'never', 'must'->'must not', 'include'->'exclude'. "
        "Return ONLY the rewritten phrase, nothing else:\n"
    ),
    "intensify": (
        "Rewrite the following instruction to be MUCH MORE EXTREME and absolute. "
        "Add superlatives, hard numeric limits, and urgency. "
        "Examples: 'be concise'->'use maximum 10 words, never exceed this', "
        "'prefer X'->'you MUST always use X without exception'. "
        "Return ONLY the rewritten phrase, nothing else:\n"
    ),
    "relax": (
        "Rewrite the following instruction to be as WEAK and OPTIONAL as possible. "
        "Remove all obligation, urgency, and specificity. "
        "Examples: 'must use JSON'->'could optionally consider JSON', "
        "'always check'->'might sometimes look at'. "
        "Return ONLY the rewritten phrase, nothing else:\n"
    ),
}

VALID_MODES = list(_MODE_INSTRUCTIONS.keys())


class Counterfactual(SaliencyMethod):
    name = "counterfactual"

    def __init__(
        self,
        mode: str = "negate",
        counterfactual_fn: GenerateCounterfactual | None = None,
    ) -> None:
        if mode not in _MODE_INSTRUCTIONS:
            raise ValueError(f"Unknown counterfactual mode '{mode}'. Choose from: {VALID_MODES}")
        self._mode = mode
        self._counterfactual_fn = counterfactual_fn
        self._instruction = _MODE_INSTRUCTIONS[mode]

    async def compute(
        self,
        phrases: list[str],
        baseline: str,
        call_perturbed: CallPerturbed,
        on_tick: OnTick,
    ) -> list[float]:
        scores: list[float] = []
        for i, phrase in enumerate(phrases):
            counterfactual = _fallback_negate(phrase)
            if self._counterfactual_fn:
                try:
                    counterfactual = await self._counterfactual_fn(
                        self._instruction + phrase
                    )
                except Exception:
                    pass

            perturbed = "".join(
                counterfactual if j == i else p for j, p in enumerate(phrases)
            )
            try:
                output = await call_perturbed(perturbed)
                scores.append(trigram_divergence(baseline, output))
            except Exception:
                scores.append(0.0)
            on_tick(i + 1, len(phrases))
        return scores


_NEGATE_PAIRS = [
    ("always", "never"),
    ("never", "always"),
    ("must", "must not"),
    ("must not", "must"),
    ("should", "should not"),
    ("should not", "should"),
    ("do not", "do"),
    ("don't", "do"),
    ("include", "exclude"),
    ("exclude", "include"),
    ("enable", "disable"),
    ("disable", "enable"),
    ("allow", "disallow"),
    ("disallow", "allow"),
    ("require", "forbid"),
    ("forbid", "require"),
    ("prefer", "avoid"),
    ("avoid", "prefer"),
]


def _fallback_negate(phrase: str) -> str:
    """Simple rule-based negation as fallback when no LLM is available."""
    lower = phrase.lower()
    for orig, repl in _NEGATE_PAIRS:
        if orig in lower:
            idx = lower.index(orig)
            return phrase[:idx] + repl + phrase[idx + len(orig) :]
    return "Do the opposite of: " + phrase
