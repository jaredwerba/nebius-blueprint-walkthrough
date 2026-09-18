"""Recipe 02 — Knowledge: local vector index with a Pinecone-shaped interface."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass


def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def bag_vector(text: str, vocab: list[str]) -> list[float]:
    tokens = tokenize(text)
    counts = {t: tokens.count(t) for t in vocab}
    return [float(counts.get(term, 0)) for term in vocab]


def cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


@dataclass
class Chunk:
    chunk_id: str
    text: str
    source: str


class LocalNexus:
    """Stand-in for Pinecone Nexus when PINECONE_API_KEY is not set."""

    def __init__(self) -> None:
        self.chunks: list[Chunk] = []
        self.vocab: list[str] = []

    def upsert(self, chunks: list[Chunk]) -> None:
        self.chunks.extend(chunks)
        terms: set[str] = set()
        for chunk in self.chunks:
            terms.update(tokenize(chunk.text))
        self.vocab = sorted(terms)

    def query(self, text: str, top_k: int = 3) -> list[tuple[float, Chunk]]:
        q = bag_vector(text, self.vocab)
        scored = []
        for chunk in self.chunks:
            score = cosine(q, bag_vector(chunk.text, self.vocab))
            scored.append((score, chunk))
        scored.sort(key=lambda item: item[0], reverse=True)
        return scored[:top_k]


CORPUS = [
    Chunk(
        "c1",
        "Nebius Token Factory serves open models through an OpenAI-compatible API.",
        "docs/token-factory",
    ),
    Chunk(
        "c2",
        "Pinecone stores embeddings so an agent can retrieve source-traceable chunks.",
        "docs/retrieval",
    ),
    Chunk(
        "c3",
        "Tavily supplies live web search so answers are not limited to training data.",
        "docs/grounding",
    ),
]


def answer_from_knowledge(question: str, index: LocalNexus | None = None) -> dict:
    index = index or LocalNexus()
    if not index.chunks:
        index.upsert(CORPUS)
    hits = index.query(question, top_k=2)
    citations = [chunk.source for _, chunk in hits if _ > 0]
    context = "\n".join(chunk.text for score, chunk in hits if score > 0)
    if not context:
        return {"answer": "No matching knowledge.", "citations": []}
    return {
        "answer": f"Retrieved context:\n{context}",
        "citations": citations,
    }


if __name__ == "__main__":
    result = answer_from_knowledge("How do I call open models with an OpenAI API?")
    print(result)
