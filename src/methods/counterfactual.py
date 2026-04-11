"""Counterfactual analysis: negate/intensify/relax phrases and measure divergence (Phase 2).

Instead of removing or masking, generates meaningful alternatives per phrase:
  - Negate:    "Always use JSON" -> "Never use JSON"
  - Intensify: "Be concise"     -> "Be extremely concise, max 10 words"
  - Relax:     "You must use JSON" -> "You may optionally use JSON"

Provides richer signal: tells you *how* a phrase matters, not just *that* it matters.
"""

from __future__ import annotations

from src.methods.base import CallPerturbed, OnTick, SaliencyMethod


class Counterfactual(SaliencyMethod):
    name = "counterfactual"

    def __init__(self, mode: str = "negate") -> None:
        self._mode = mode

    async def compute(
        self,
        phrases: list[str],
        baseline: str,
        call_perturbed: CallPerturbed,
        on_tick: OnTick,
    ) -> list[float]:
        raise NotImplementedError(
            "Counterfactual analysis is planned for Phase 2.  "
            "Use --method perturbation|omission|paraphrase for now."
        )
