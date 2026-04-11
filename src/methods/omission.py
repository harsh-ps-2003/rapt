"""Leave-one-out saliency: remove each phrase entirely and measure divergence."""

from __future__ import annotations

from src.methods.base import CallPerturbed, OnTick, SaliencyMethod
from src.similarity import trigram_divergence


class Omission(SaliencyMethod):
    name = "omission"

    async def compute(
        self,
        phrases: list[str],
        baseline: str,
        call_perturbed: CallPerturbed,
        on_tick: OnTick,
    ) -> list[float]:
        scores: list[float] = []
        for i in range(len(phrases)):
            omitted = "".join(p for j, p in enumerate(phrases) if j != i) or " "
            try:
                output = await call_perturbed(omitted)
                scores.append(trigram_divergence(baseline, output))
            except Exception:
                scores.append(0.0)
            on_tick(i + 1, len(phrases))
        return scores
