"""Recipe 04 — Orchestration: a small graph (plan -> tool -> answer)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable


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


def answer_node(state: GraphState) -> GraphState:
    state.answer = (
        f"Plan: {state.plan}\nEvidence: {state.evidence}\n"
        "Answer: use the evidence. Do not invent sources."
    )
    return state


def run_graph(question: str, tool: Tool) -> GraphState:
    state = GraphState(question=question)
    state = plan_node(state)
    state = tool_node(state, tool)
    state = answer_node(state)
    return state


if __name__ == "__main__":
    result = run_graph("What is Token Factory?", lambda q: f"fixture evidence for {q}")
    print(result.answer)
