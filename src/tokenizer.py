"""Phrase tokenization for prompt saliency analysis.

Splits prompts into analysable phrases at sentence/clause boundaries,
with markdown-aware splitting for agent prompt files.
"""

from __future__ import annotations

import re

_SENTENCE_RE = re.compile(r"([^.!?\n]+[.!?\n]+)|([^.!?\n]+$)")
_CLAUSE_SPLIT_RE = re.compile(r"(?<=[,;])")
_MD_HEADER_RE = re.compile(r"^(#{1,6}\s.+)$", re.MULTILINE)
_MD_FENCE_RE = re.compile(r"^```", re.MULTILINE)

MIN_PHRASE_LEN = 35
MAX_UNSPLIT_LEN = 60


def tokenize_phrases(text: str, *, markdown_aware: bool = True) -> list[str]:
    """Split text into phrases suitable for perturbation analysis.

    When ``markdown_aware`` is True (default), the text is first split at
    markdown structural boundaries (headers, blank-line paragraphs, code
    fences, list items) before sentence/clause splitting is applied
    within each block.
    """
    if not text or not text.strip():
        return [text] if text else [""]

    if markdown_aware:
        blocks = _split_markdown_blocks(text)
    else:
        blocks = [text]

    phrases: list[str] = []
    for block in blocks:
        phrases.extend(_split_sentences_and_clauses(block))

    return phrases if phrases else [text]


def _split_markdown_blocks(text: str) -> list[str]:
    """Split at markdown headers and double-newline paragraph breaks."""
    lines = text.split("\n")
    blocks: list[str] = []
    current: list[str] = []
    in_fence = False

    for line in lines:
        if _MD_FENCE_RE.match(line):
            in_fence = not in_fence
            current.append(line)
            if not in_fence:
                blocks.append("\n".join(current))
                current = []
            continue

        if in_fence:
            current.append(line)
            continue

        is_header = bool(_MD_HEADER_RE.match(line))
        is_blank = not line.strip()

        if is_header or (is_blank and current and any(l.strip() for l in current)):
            if current:
                joined = "\n".join(current)
                if joined.strip():
                    blocks.append(joined)
                current = []

        if is_header:
            blocks.append(line)
        elif not is_blank or current:
            current.append(line)

    if current:
        joined = "\n".join(current)
        if joined.strip():
            blocks.append(joined)

    return blocks if blocks else [text]


def _split_sentences_and_clauses(text: str) -> list[str]:
    """Split text at sentence-ending punctuation, then sub-split long sentences."""
    sentences: list[str] = []

    for match in _SENTENCE_RE.finditer(text):
        s = match.group(0)
        if not s.strip():
            continue

        if len(s) > MAX_UNSPLIT_LEN:
            parts = _CLAUSE_SPLIT_RE.split(s)
            acc = ""
            for i, part in enumerate(parts):
                acc += part
                is_last = i == len(parts) - 1
                if len(acc.strip()) >= MIN_PHRASE_LEN or is_last:
                    if acc.strip():
                        sentences.append(acc)
                    acc = ""
            if acc.strip():
                sentences.append(acc)
        else:
            sentences.append(s)

    return sentences
