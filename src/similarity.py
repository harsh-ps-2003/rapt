"""Divergence metrics for comparing LLM outputs."""

from __future__ import annotations

import math
from collections import Counter


def trigram_cosine_similarity(a: str, b: str, n: int = 3) -> float:
    """Character n-gram cosine similarity between two strings.

    Returns a value in [0.0, 1.0].  Zero-dependency port of the JS version.
    """
    va = _ngram_freq(a, n)
    vb = _ngram_freq(b, n)

    if not va or not vb:
        return 0.0

    keys = set(va) | set(vb)
    dot = sum(va.get(k, 0) * vb.get(k, 0) for k in keys)
    norm_a = math.sqrt(sum(v * v for v in va.values()))
    norm_b = math.sqrt(sum(v * v for v in vb.values()))

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return dot / (norm_a * norm_b)


def trigram_divergence(a: str, b: str) -> float:
    """Divergence = 1 - similarity.  Higher = more different."""
    return 1.0 - trigram_cosine_similarity(a, b)


async def embedding_divergence(a: str, b: str) -> float:
    """Placeholder for embedding-based divergence (Phase 2).

    Will use the provider's embedding endpoint to compute cosine distance
    between sentence embeddings, capturing semantic equivalence that
    character trigrams miss (e.g. "fast" vs "quick").
    """
    raise NotImplementedError(
        "Embedding-based divergence is planned for a future release. "
        "Use --metric trigram (default) for now."
    )


def _ngram_freq(text: str, n: int = 3) -> Counter[str]:
    t = text.lower()
    return Counter(t[i : i + n] for i in range(len(t) - n + 1))
