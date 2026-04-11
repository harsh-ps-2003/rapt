"""Base class and result type for saliency methods."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Awaitable, Callable

CallPerturbed = Callable[[str], Awaitable[str]]
OnTick = Callable[[int, int], None]

COMPONENT_LABELS = [
    "persona",
    "constraint",
    "guardrail",
    "formatting",
    "example",
    "context",
    "instruction",
    "dead_weight",
]


@dataclass
class SaliencyResult:
    phrases: list[str]
    raw_scores: list[float]
    norm_scores: list[float]
    baseline_output: str
    method: str
    provider: str
    model: str
    api_calls: int
    stats: dict[str, object] = field(default_factory=dict)
    component_labels: list[str] = field(default_factory=list)
    section_scores: list[tuple[str, float]] = field(default_factory=list)


class SaliencyMethod(ABC):
    """Interface that every saliency method must implement."""

    name: str

    @abstractmethod
    async def compute(
        self,
        phrases: list[str],
        baseline: str,
        call_perturbed: CallPerturbed,
        on_tick: OnTick,
    ) -> list[float]:
        """Return a raw divergence score per phrase."""
        ...
