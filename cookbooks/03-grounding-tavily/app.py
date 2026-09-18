"""Recipe 03 — Grounding: Tavily search with a mock fallback."""

from __future__ import annotations

import os
from dataclasses import dataclass


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


def grounded_answer(question: str, client: TavilyClient | None = None) -> dict:
    client = client or TavilyClient()
    hits = client.search(question)
    return {
        "question": question,
        "sources": [hit.__dict__ for hit in hits],
        "note": "Live Tavily was not used" if not client.api_key else "Live Tavily used",
    }


if __name__ == "__main__":
    print(grounded_answer("What is Nebius Token Factory?"))
