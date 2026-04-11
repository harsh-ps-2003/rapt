"""Perturbation saliency: replace each phrase with [...] and measure divergence."""

from __future__ import annotations

from src.methods.base import CallPerturbed, OnTick, SaliencyMethod
from src.similarity import trigram_divergence


class Perturbation(SaliencyMethod):
    name = "perturbation"

    async def compute(
        self,
        phrases: list[str],
        baseline: str,
        call_perturbed: CallPerturbed,
        on_tick: OnTick,
    ) -> list[float]:
        scores: list[float] = []
        for i in range(len(phrases)):
            perturbed = "".join(
                "[...]" if j == i else p for j, p in enumerate(phrases)
            )
            try:
                output = await call_perturbed(perturbed)
                scores.append(trigram_divergence(baseline, output))
            except Exception:
                scores.append(0.0)
            on_tick(i + 1, len(phrases))
        return scores
