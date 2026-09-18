"""Recipe 07 — Observability: structured traces without LangSmith when no key."""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import asdict, dataclass, field


@dataclass
class Span:
    name: str
    started_at: float
    ended_at: float = 0.0
    attributes: dict = field(default_factory=dict)

    @property
    def duration_ms(self) -> float:
        return (self.ended_at - self.started_at) * 1000


@dataclass
class Trace:
    trace_id: str
    spans: list[Span] = field(default_factory=list)

    def to_json(self) -> str:
        payload = {
            "trace_id": self.trace_id,
            "spans": [
                {**asdict(span), "duration_ms": span.duration_ms} for span in self.spans
            ],
        }
        return json.dumps(payload, indent=2)


class Tracer:
    def start_trace(self) -> Trace:
        return Trace(trace_id=str(uuid.uuid4()))

    def span(self, trace: Trace, name: str, **attributes) -> Span:
        span = Span(name=name, started_at=time.time(), attributes=attributes)
        trace.spans.append(span)
        return span

    def end(self, span: Span) -> None:
        span.ended_at = time.time()


def run_traced_agent(question: str) -> tuple[str, Trace]:
    tracer = Tracer()
    trace = tracer.start_trace()
    plan = tracer.span(trace, "plan", question=question)
    tracer.end(plan)
    llm = tracer.span(trace, "llm", model="MiniMaxAI/MiniMax-M3")
    answer = f"Traced reply for: {question}"
    tracer.end(llm)
    return answer, trace


if __name__ == "__main__":
    answer, trace = run_traced_agent("ping")
    print(answer)
    print(trace.to_json())
