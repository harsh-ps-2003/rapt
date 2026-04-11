"""Paraphrase saliency: rewrite each phrase to be vague, then measure divergence.

Costs 2x API calls per phrase -- one to generate the neutral rewrite, one to
measure the effect of the substitution.
"""

from __future__ import annotations

from typing import Awaitable, Callable

from src.methods.base import CallPerturbed, OnTick, SaliencyMethod
from src.similarity import trigram_divergence

GenerateParaphrase = Callable[[str], Awaitable[str]]

PARAPHRASE_INSTRUCTION = (
    "Rewrite the following phrase to remove all specific information, "
    "making it maximally vague and uninformative. "
    "Keep roughly the same character length. "
    "Return ONLY the rewritten phrase — no explanation, no quotes:\n"
)


class Paraphrase(SaliencyMethod):
    name = "paraphrase"

    def __init__(self, paraphrase_fn: GenerateParaphrase | None = None) -> None:
        self._paraphrase_fn = paraphrase_fn

    async def compute(
        self,
        phrases: list[str],
        baseline: str,
        call_perturbed: CallPerturbed,
        on_tick: OnTick,
    ) -> list[float]:
        scores: list[float] = []
        for i in range(len(phrases)):
            neutral = "[something]"
            if self._paraphrase_fn:
                try:
                    neutral = await self._paraphrase_fn(
                        PARAPHRASE_INSTRUCTION + phrases[i]
                    )
                except Exception:
                    pass

            perturbed = "".join(
                neutral if j == i else p for j, p in enumerate(phrases)
            )
            try:
                output = await call_perturbed(perturbed)
                scores.append(trigram_divergence(baseline, output))
            except Exception:
                scores.append(0.0)
            on_tick(i + 1, len(phrases))
        return scores
