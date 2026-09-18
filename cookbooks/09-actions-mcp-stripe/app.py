"""Recipe 09 — Actions: MCP-shaped tools plus a Stripe test-mode stub."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


@dataclass
class ToolSpec:
    name: str
    description: str
    handler: Callable[[dict], dict]


class McpRegistry:
    def __init__(self) -> None:
        self.tools: dict[str, ToolSpec] = {}

    def register(self, spec: ToolSpec) -> None:
        self.tools[spec.name] = spec

    def call(self, name: str, arguments: dict) -> dict:
        if name not in self.tools:
            raise KeyError(f"Unknown tool: {name}")
        return self.tools[name].handler(arguments)


def stripe_create_payment_intent(arguments: dict) -> dict:
    amount = int(arguments["amount_cents"])
    if amount <= 0:
        raise ValueError("amount_cents must be positive")
    return {
        "id": "pi_test_local",
        "amount": amount,
        "currency": arguments.get("currency", "usd"),
        "status": "requires_payment_method",
        "livemode": False,
    }


def build_default_registry() -> McpRegistry:
    registry = McpRegistry()
    registry.register(
        ToolSpec(
            "stripe.create_payment_intent",
            "Create a Stripe PaymentIntent in test mode.",
            stripe_create_payment_intent,
        )
    )
    return registry


if __name__ == "__main__":
    print(build_default_registry().call("stripe.create_payment_intent", {"amount_cents": 500}))
