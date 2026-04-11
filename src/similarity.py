"""Divergence metrics for comparing LLM outputs."""

from __future__ import annotations

import math
from collections import Counter

import httpx


def trigram_cosine_similarity(a: str, b: str, n: int = 3) -> float:
    """Character n-gram cosine similarity between two strings.

    Returns a value in [0.0, 1.0].
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


async def embedding_cosine_similarity(
    a: str,
    b: str,
    api_key: str,
    model: str = "text-embedding-3-small",
) -> float:
    """Cosine similarity via OpenAI-compatible embedding endpoint.

    Batches both texts in a single API call.  Returns [0.0, 1.0].
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            "https://api.openai.com/v1/embeddings",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            json={"model": model, "input": [a, b]},
        )
        resp.raise_for_status()
        data = resp.json()["data"]
        vec_a = data[0]["embedding"]
        vec_b = data[1]["embedding"]

    dot = sum(x * y for x, y in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(x * x for x in vec_a))
    norm_b = math.sqrt(sum(y * y for y in vec_b))

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return dot / (norm_a * norm_b)


async def embedding_divergence(
    a: str,
    b: str,
    api_key: str,
    model: str = "text-embedding-3-small",
) -> float:
    """Semantic divergence via embeddings.  Higher = more different."""
    sim = await embedding_cosine_similarity(a, b, api_key, model)
    return 1.0 - sim


def _ngram_freq(text: str, n: int = 3) -> Counter[str]:
    t = text.lower()
    return Counter(t[i : i + n] for i in range(len(t) - n + 1))
