"""Component classification: tag each phrase with its structural role.

Uses an LLM to classify what each phrase does in an agent prompt:
persona, constraint, guardrail, formatting, example, context,
instruction, or dead_weight.  Overlaid on saliency scores to produce
actionable editing advice ("this is a guardrail with 0.9 saliency").
"""

from __future__ import annotations

import json
import re
from typing import Awaitable, Callable

from src.methods.base import COMPONENT_LABELS

ClassifyFn = Callable[[str], Awaitable[str]]

_CLASSIFY_PROMPT = """Classify each numbered phrase from an AI agent prompt into exactly ONE category.

Categories:
- persona: defines who the agent is, voice, identity, role
- constraint: limits on behavior, scope restrictions, boundaries  
- guardrail: safety rules, things to never do, error prevention
- formatting: output format requirements (JSON, markdown, structure)
- example: demonstrations, few-shot examples, sample inputs/outputs
- context: background information, definitions, domain knowledge
- instruction: direct task directives, action steps, workflow rules
- dead_weight: filler, redundant, or meaningless phrases

Return a JSON array of objects with "index" (int) and "label" (string).
Return ONLY valid JSON, no explanation.

Phrases:
"""


async def classify_phrases(
    phrases: list[str],
    classify_fn: ClassifyFn,
) -> list[str]:
    """Classify each phrase and return a label per phrase."""
    numbered = "\n".join(
        f"{i}: {phrase.strip()}" for i, phrase in enumerate(phrases)
    )

    try:
        raw = await classify_fn(_CLASSIFY_PROMPT + numbered)
        labels = _parse_classification(raw, len(phrases))
    except Exception:
        labels = ["instruction"] * len(phrases)

    return labels


def _parse_classification(raw: str, count: int) -> list[str]:
    """Parse LLM JSON response into a list of labels."""
    cleaned = raw.strip()
    json_match = re.search(r"\[.*\]", cleaned, re.DOTALL)
    if json_match:
        cleaned = json_match.group(0)

    try:
        items = json.loads(cleaned)
    except json.JSONDecodeError:
        return ["instruction"] * count

    labels = ["instruction"] * count
    valid_set = set(COMPONENT_LABELS)

    for item in items:
        if not isinstance(item, dict):
            continue
        idx = item.get("index")
        label = item.get("label", "").lower().strip()
        if isinstance(idx, int) and 0 <= idx < count and label in valid_set:
            labels[idx] = label

    return labels
