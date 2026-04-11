"""Hierarchical ablation: section-level then phrase-level analysis.

Auto-detects markdown sections (headers, paragraph breaks), ablates at
section granularity first (cheap), then drills into high-saliency sections
at phrase level.  Best for long agent prompts (AGENTS.md, system prompts).
"""

from __future__ import annotations

import re

from src.methods.base import CallPerturbed, OnTick, SaliencyMethod
from src.similarity import trigram_divergence

_MD_HEADER_RE = re.compile(r"^(#{1,6}\s.+)$", re.MULTILINE)


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
        sections = _group_into_sections(phrases)
        total_steps = len(sections) + len(phrases)
        done = 0

        section_scores: list[float] = []
        for sec_phrases in sections:
            sec_text = "".join(sec_phrases)
            all_text = "".join(phrases)
            perturbed = all_text.replace(sec_text, "[...]", 1)
            try:
                output = await call_perturbed(perturbed)
                section_scores.append(trigram_divergence(baseline, output))
            except Exception:
                section_scores.append(0.0)
            done += 1
            on_tick(done, total_steps)

        max_sec = max(section_scores) if section_scores else 1.0
        norm_sec = [s / max_sec if max_sec > 0 else 0.5 for s in section_scores]

        hot_sections = {
            i for i, s in enumerate(norm_sec) if s >= self._threshold
        }

        phrase_to_section = _map_phrases_to_sections(phrases, sections)
        scores: list[float] = []

        for i, phrase in enumerate(phrases):
            sec_idx = phrase_to_section[i]
            if sec_idx not in hot_sections:
                scores.append(section_scores[sec_idx] if sec_idx < len(section_scores) else 0.0)
            else:
                perturbed = "".join(
                    "[...]" if j == i else p for j, p in enumerate(phrases)
                )
                try:
                    output = await call_perturbed(perturbed)
                    scores.append(trigram_divergence(baseline, output))
                except Exception:
                    scores.append(0.0)
            done += 1
            on_tick(done, total_steps)

        return scores


def _group_into_sections(phrases: list[str]) -> list[list[str]]:
    """Group phrases into sections by markdown headers.

    Each header starts a new section.  Phrases before any header
    form the first section.
    """
    sections: list[list[str]] = []
    current: list[str] = []

    for phrase in phrases:
        if _MD_HEADER_RE.match(phrase.strip()):
            if current:
                sections.append(current)
            current = [phrase]
        else:
            current.append(phrase)

    if current:
        sections.append(current)

    return sections if sections else [phrases]


def _map_phrases_to_sections(
    phrases: list[str],
    sections: list[list[str]],
) -> dict[int, int]:
    """Map each phrase index to its section index."""
    mapping: dict[int, int] = {}
    phrase_idx = 0
    for sec_idx, sec_phrases in enumerate(sections):
        for _ in sec_phrases:
            if phrase_idx < len(phrases):
                mapping[phrase_idx] = sec_idx
                phrase_idx += 1
    for i in range(phrase_idx, len(phrases)):
        mapping[i] = len(sections) - 1
    return mapping
