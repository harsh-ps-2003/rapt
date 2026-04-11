"""Hierarchical ablation: section-level then phrase-level analysis (Phase 2).

Auto-detects markdown sections (headers, paragraph breaks), ablates at
section granularity first (cheap), then drills into high-saliency sections
at phrase level.  Best for long agent prompts (AGENTS.md, system prompts).
"""

from __future__ import annotations

from src.methods.base import CallPerturbed, OnTick, SaliencyMethod


class HierarchicalAblation(SaliencyMethod):
    name = "hierarchical"

    def __init__(self, section_threshold: float = 0.4) -> None:
        self._threshold = section_threshold

    async def compute(
        self,
        phrases: list[str],
        baseline: str,
        call_perturbed: CallPerturbed,
        on_tick: OnTick,
    ) -> list[float]:
        raise NotImplementedError(
            "Hierarchical ablation is planned for Phase 2.  "
            "Use --method perturbation|omission|paraphrase for now."
        )
