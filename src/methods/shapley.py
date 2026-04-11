"""Shapley value approximation via Monte Carlo sampling (Phase 2).

Computes the fair contribution of each phrase by averaging marginal
contributions over sampled permutations.  Captures interaction effects
that leave-one-out misses (e.g. conflicting instructions).

Cost: ~samples x num_phrases API calls.
"""

from __future__ import annotations

from src.methods.base import CallPerturbed, OnTick, SaliencyMethod


class ShapleyValue(SaliencyMethod):
    name = "shapley"

    def __init__(self, samples: int = 100) -> None:
        self._samples = samples

    async def compute(
        self,
        phrases: list[str],
        baseline: str,
        call_perturbed: CallPerturbed,
        on_tick: OnTick,
    ) -> list[float]:
        raise NotImplementedError(
            "Shapley value approximation is planned for Phase 2.  "
            "Use --method perturbation|omission|paraphrase for now."
        )
