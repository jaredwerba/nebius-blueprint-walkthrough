"""Recipe 03 — Grounding: Tavily search with a mock fallback."""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from shared.env import load_env
from shared.token_factory import TokenFactoryClient, TokenFactoryError

load_env()


@dataclass
class SearchHit:
    title: str
    url: str
    snippet: str


class TavilyClient:
    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key if api_key is not None else os.getenv("TAVILY_API_KEY", "")

    def search(self, query: str) -> list[SearchHit]:
        if not self.api_key:
            return [
                SearchHit(
                    title="Offline fixture: Token Factory docs",
                    url="https://docs.tokenfactory.nebius.com",
                    snippet="OpenAI-compatible inference API for open models.",
                )
            ]
        import httpx

        response = httpx.post(
            "https://api.tavily.com/search",
            json={"api_key": self.api_key, "query": query, "max_results": 5},
            timeout=30.0,
        )
        response.raise_for_status()
        data = response.json()
        hits = []
        for item in data.get("results", []):
            hits.append(
                SearchHit(
                    title=item.get("title", ""),
                    url=item.get("url", ""),
                    snippet=item.get("content", "")[:280],
                )
            )
        return hits


def grounded_answer(
    question: str,
    client: TavilyClient | None = None,
    synthesize: bool = False,
) -> dict:
    client = client or TavilyClient()
    hits = client.search(question)
    payload = {
        "question": question,
        "sources": [hit.__dict__ for hit in hits],
        "note": "Live Tavily was not used" if not client.api_key else "Live Tavily used",
        "answer": "",
    }
    if not synthesize:
        return payload
    lines = [f"- {h.title} ({h.url}): {h.snippet}" for h in hits]
    prompt = (
        "Answer using only these sources. Cite URLs. If sources are insufficient, say so.\n"
        f"Question: {question}\nSources:\n" + "\n".join(lines)
    )
    try:
        payload["answer"] = TokenFactoryClient().chat(
            [
                {"role": "system", "content": "You ground answers in the provided sources only."},
                {"role": "user", "content": prompt},
            ]
        )
    except TokenFactoryError as exc:
        payload["answer"] = f"Synthesis skipped: {exc}"
    return payload


if __name__ == "__main__":
    result = grounded_answer("What is Nebius Token Factory?", synthesize=True)
    print(result["note"])
    print(result["answer"])
    for src in result["sources"]:
        print(src["url"])
