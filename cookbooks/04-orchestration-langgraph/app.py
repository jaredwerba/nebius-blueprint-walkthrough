"""Recipe 04 — Orchestration: a small graph (plan -> tool -> answer)."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from shared.env import load_env
from shared.token_factory import TokenFactoryClient, TokenFactoryError

load_env()


@dataclass
class GraphState:
    question: str
    plan: str = ""
    evidence: str = ""
    answer: str = ""


Tool = Callable[[str], str]


def plan_node(state: GraphState) -> GraphState:
    state.plan = f"Search for facts about: {state.question}"
    return state


def tool_node(state: GraphState, tool: Tool) -> GraphState:
    state.evidence = tool(state.question)
    return state


def answer_node(state: GraphState, use_llm: bool = False) -> GraphState:
    if not use_llm:
        state.answer = (
            f"Plan: {state.plan}\nEvidence: {state.evidence}\n"
            "Answer: use the evidence. Do not invent sources."
        )
        return state
    try:
        state.answer = TokenFactoryClient().chat(
            [
                {
                    "role": "system",
                    "content": "Use only the evidence. Cite it. Do not invent sources.",
                },
                {
                    "role": "user",
                    "content": f"Plan: {state.plan}\nEvidence:\n{state.evidence}\nQuestion: {state.question}",
                },
            ]
        )
    except TokenFactoryError as exc:
        state.answer = f"LLM skipped: {exc}\nEvidence:\n{state.evidence}"
    return state


def run_graph(question: str, tool: Tool, use_llm: bool = False) -> GraphState:
    state = GraphState(question=question)
    state = plan_node(state)
    state = tool_node(state, tool)
    state = answer_node(state, use_llm=use_llm)
    return state


if __name__ == "__main__":
    import importlib.util

    tavily_path = Path(__file__).resolve().parents[1] / "03-grounding-tavily" / "app.py"
    spec = importlib.util.spec_from_file_location("tavily03", tavily_path)
    tavily = importlib.util.module_from_spec(spec)
    sys.modules["tavily03"] = tavily
    spec.loader.exec_module(tavily)

    def tool(q: str) -> str:
        hits = tavily.TavilyClient().search(q)
        return "\n".join(f"{h.title} | {h.url} | {h.snippet}" for h in hits)

    result = run_graph("What is Nebius Token Factory?", tool, use_llm=True)
    print(result.plan)
    print(result.answer)
