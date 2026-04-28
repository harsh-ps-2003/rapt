"""Component classification: tag each phrase with its structural role.

Uses an LLM to classify what each phrase does in a prompt or spec file.
Works for agent prompts (SKILL.md, AGENTS.md, system prompts) as well as
general markdown documents — adapts the category set based on detected
input type.

Large phrase lists are batched to stay within LLM context limits.
"""

from __future__ import annotations

import json
import re
from typing import Awaitable, Callable

from src.methods.base import COMPONENT_LABELS

ClassifyFn = Callable[[str], Awaitable[str]]

_BATCH_SIZE = 60

_AGENT_PROMPT_CLASSIFY = """Classify each numbered phrase from an AI agent prompt or instruction file into exactly ONE category.

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

_DOCUMENT_CLASSIFY = """Classify each numbered phrase from a documentation or specification file into exactly ONE category.

Categories:
- instruction: how-to steps, commands, usage examples, CLI flags
- context: descriptions, explanations, background, overview text
- example: code examples, sample outputs, demo commands
- formatting: table rows, structural markers, headings content
- constraint: requirements, limitations, prerequisites
- guardrail: warnings, caveats, things to avoid
- persona: project identity, tool description, tagline
- dead_weight: filler, redundant, or low-information fragments

Return a JSON array of objects with "index" (int) and "label" (string).
Return ONLY valid JSON, no explanation.

Phrases:
"""

_AGENT_SIGNALS = re.compile(
    r"\b(you (are|must|should|will)|never|always|your role|as an? |"
    r"do not|don't|when (asked|given|the user)|respond|output format|"
    r"system prompt|agent|guardrail|persona)\b",
    re.IGNORECASE,
)


def _detect_prompt_type(phrases: list[str]) -> str:
    """Heuristic: return 'agent' if the text looks like an agent prompt, else 'document'."""
    sample = " ".join(phrases[:40])
    hits = len(_AGENT_SIGNALS.findall(sample))
    return "agent" if hits >= 3 else "document"


async def classify_phrases(
    phrases: list[str],
    classify_fn: ClassifyFn,
) -> list[str]:
    """Classify each phrase and return a label per phrase.

    Batches the phrase list to avoid exceeding LLM context limits.
    """
    prompt_type = _detect_prompt_type(phrases)
    classify_prompt = _AGENT_PROMPT_CLASSIFY if prompt_type == "agent" else _DOCUMENT_CLASSIFY

    labels = ["context"] * len(phrases)

    for batch_start in range(0, len(phrases), _BATCH_SIZE):
        batch = phrases[batch_start : batch_start + _BATCH_SIZE]
        numbered = "\n".join(
            f"{batch_start + i}: {phrase.strip()}" for i, phrase in enumerate(batch)
        )
        try:
            raw = await classify_fn(classify_prompt + numbered)
            batch_labels = _parse_classification(raw, len(phrases))
            for i, label in enumerate(batch_labels):
                global_idx = batch_start + i
                if label != "context" and labels[global_idx] == "context":
                    labels[global_idx] = label
        except Exception:
            pass

    return labels


def _parse_classification(raw: str, count: int) -> list[str]:
    """Parse LLM JSON response into a sparse list of labels (defaults to 'context')."""
    cleaned = raw.strip()
    json_match = re.search(r"\[.*\]", cleaned, re.DOTALL)
    if json_match:
        cleaned = json_match.group(0)

    try:
        items = json.loads(cleaned)
    except json.JSONDecodeError:
        return ["context"] * count

    labels = ["context"] * count
    valid_set = set(COMPONENT_LABELS)

    for item in items:
        if not isinstance(item, dict):
            continue
        idx = item.get("index")
        label = item.get("label", "").lower().strip()
        if isinstance(idx, int) and 0 <= idx < count and label in valid_set:
            labels[idx] = label

    return labels
