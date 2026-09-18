# Nebius Agents Blueprint walkthrough

This repository records work on the Nebius Agents Blueprint recipes.

Source of the recipes: https://dev.nebius.com/blueprints
Official code: https://github.com/nebius/nebius-partner-cookbook

This is not a fork of the official repository. This is a personal implementation of the same sequence.

The text below follows ASD-STE100 (Simplified Technical English). Sentences are short. Verbs are direct.

## What you built

You built ten recipe modules plus one shared Token Factory client.

| ID | Recipe | What the module does |
| --- | --- | --- |
| 01 | Foundation | Sends a chat request to Nebius Token Factory through an OpenAI-compatible HTTP client. |
| 02 | Knowledge | Stores document chunks and retrieves the nearest chunks with a cosine score. This is a local stand-in for Pinecone Nexus. |
| 03 | Grounding | Calls Tavily when `TAVILY_API_KEY` is set. Uses a fixture result when the key is empty. |
| 04 | Orchestration | Runs a three-node graph: plan, tool, answer. This is the LangGraph pattern without a vendor lock. |
| 05 | Thread memory | Keeps short-term messages for one session and drops old turns. |
| 06 | User memory | Stores long-term facts in SQLite with a Postgres-shaped put/get API. |
| 07 | Observability | Writes a JSON trace with spans. This is a local stand-in for LangSmith. |
| 08 | Guardrails | Rejects blocked input. Redacts SSN patterns in output. |
| 09 | Actions | Registers MCP-shaped tools. Includes a Stripe PaymentIntent stub in test mode. |
| 10 | Simulation | Runs a labeled conversation suite before production. This is a local stand-in for Snowglobe. |

Shared code is in `shared/token_factory.py`.

## Why you built it

You followed the Blueprint sequence from Foundation to Simulation.

The official page states that agent failures are system problems, not only model problems.

You built the system layers so that you can:

- Call an open model on Token Factory.
- Retrieve domain knowledge with source citations.
- Ground answers in live search.
- Orchestrate multi-step work.
- Keep thread memory and user memory.
- Record traces.
- Apply guardrails.
- Call tools (including payments).
- Test the agent with synthetic cases.

You published the work so that other engineers can run the same sequence.

## What it does

1. Offline tests run with no network and no paid keys.
2. Live Token Factory inference runs only when `NEBIUS_API_KEY` is set.
3. Each recipe is a small Python module. You can run it with `python cookbooks/<name>/app.py`.

## How you run the tests

```
cd /path/to/nebius-blueprint-walkthrough
uv sync --group dev
uv run pytest -q
```

If `uv` is not available, use:

```
python3 -m venv .venv
.venv/bin/pip install httpx pytest
.venv/bin/pytest -q
```

## How you run a live agent (recipe 01)

1. Copy `.env.example` to `.env`.
2. Set `NEBIUS_API_KEY`.
3. Export the variables.
4. Run:

```
python cookbooks/01-first-agent/app.py "Explain Token Factory in one paragraph."
```

If the key is empty, the process prints an error and exits with code 2.

## Lessons learned

1. The Blueprint page is a catalog. The runnable recipes live in `nebius/nebius-partner-cookbook`.
2. Official recipes require Python 3.12, `uv`, FastAPI, Prometheus, and several partner keys. This walkthrough keeps the same ideas with a smaller surface so that tests run on a laptop with Python 3.14.
3. You cannot complete live partner integrations without keys. You must record that gap. See `ERRORS.md`.
4. A local vector index is enough to learn retrieval. Pinecone is required only when you need a hosted index.
5. Guardrails must run on input and on output. Input filters stop jailbreaks. Output filters stop leaked identifiers.
6. Simulation tests catch policy failures before you spend inference budget.
7. Do not commit API keys. The official `.env.example` in the partner cookbook shows a truncated key shape. Do not copy real secrets into git.

## Errors

See `ERRORS.md` for the list of failures, the cause, and the fix.

## License

The original Nebius partner cookbook has its own license. This repository contains original code written for the walkthrough.
