"""Deep research — compact stand-in for a Tavily + Token Factory research agent.

Official cookbook uses deepagents + langchain-tavily.
This module plans sub-questions, searches (live Tavily or fixtures), and cites sources.
"""

from __future__ import annotations

import importlib.util
import sys
from dataclasses import asdict, dataclass
from pathlib import Path


def _load_tavily():
    path = Path(__file__).resolve().parents[2] / "cookbooks/03-grounding-tavily/app.py"
    spec = importlib.util.spec_from_file_location("g03_research", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["g03_research"] = mod
    spec.loader.exec_module(mod)
    return mod


@dataclass
class Report:
    question: str
    subquestions: list[str]
    sources: list[dict]
    answer: str
    note: str


def plan(question: str) -> list[str]:
    q = question.strip() or "What is Nebius Token Factory?"
    return [
        q,
        f"Who operates {q[:80]}",
        f"What sources describe {q[:80]}",
    ]


def research(question: str, live: bool = False) -> Report:
    tavily = _load_tavily()
    client = tavily.TavilyClient() if live else tavily.TavilyClient(api_key="")
    subs = plan(question)
    sources: list[dict] = []
    notes = []
    for sub in subs:
        result = tavily.grounded_answer(sub, client=client)
        sources.extend(result.get("sources") or [])
        notes.append(result.get("note", ""))
    unique = []
    seen = set()
    for src in sources:
        url = src.get("url", "")
        if url and url not in seen:
            seen.add(url)
            unique.append(src)
    cited = "; ".join(s.get("url", "") for s in unique[:5]) or "no sources"
    answer = (
        f"Research question: {question}. "
        f"I used {len(subs)} sub-questions and {len(unique)} sources. "
        f"Citations: {cited}."
    )
    note = notes[0] if notes else "offline fixture"
    return Report(question, subs, unique, answer, note)


if __name__ == "__main__":
    q = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "What is Nebius Token Factory?"
    print(asdict(research(q, live=False)))
