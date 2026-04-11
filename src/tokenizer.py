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

# Matches http(s) URLs, bare doi: links, and complete markdown link syntax ([text](url))
_URL_RE = re.compile(
    r"\[(?:[^\[\]]*)\]\([^\s\)]+\)"  # full markdown link: [text](url)
    r"|https?://[^\s\)\]\"'`>]+"     # bare https?:// URL
    r"|doi:[^\s\)\]\"'`>]+",         # bare doi: reference
    re.IGNORECASE,
)

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
    """Split text at sentence-ending punctuation, then sub-split long sentences.

    URLs are masked before splitting so their internal dots and slashes
    don't create spurious phrase boundaries, then restored afterwards.
    """
    text, url_map = _mask_urls(text)
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
                        sentences.append(_restore_urls(acc, url_map))
                    acc = ""
            if acc.strip():
                sentences.append(_restore_urls(acc, url_map))
        else:
            sentences.append(_restore_urls(s, url_map))

    return sentences


def _mask_urls(text: str) -> tuple[str, dict[str, str]]:
    """Replace URLs with placeholder tokens that contain no sentence-ending chars."""
    url_map: dict[str, str] = {}
    counter = [0]

    def replace(m: re.Match) -> str:
        url = m.group(0)
        placeholder = f"__URL{counter[0]}__"
        url_map[placeholder] = url
        counter[0] += 1
        return placeholder

    masked = _URL_RE.sub(replace, text)
    return masked, url_map


def _restore_urls(text: str, url_map: dict[str, str]) -> str:
    """Swap placeholder tokens back to original URLs."""
    for placeholder, url in url_map.items():
        text = text.replace(placeholder, url)
    return text
