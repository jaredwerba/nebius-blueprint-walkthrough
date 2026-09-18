# Errors during the Blueprint walkthrough

Record of what you tried, what failed, and how you fixed it.

## E01 — Blueprint page has no cloneable recipe tree

Tried: Open https://dev.nebius.com/blueprints and extract every recipe from the HTML.

Result: The page describes architecture (Token Factory, Deep Agents, LangSmith, Pinecone, Tavily, Snowglobe). It does not list the ten cookbook directories.

Fix: Use the GitHub repository that the page links: https://github.com/nebius/nebius-partner-cookbook. The recipes are `cookbooks/01` through `cookbooks/10`.

## E02 — Firecrawl extract of GitHub returned HTTP 403

Tried: Fetch https://github.com/nebius/nebius-partner-cookbook with a scrape API.

Result: `403 Forbidden`.

Fix: Clone the repository with git. Git clone succeeded.

## E03 — No NEBIUS_API_KEY on this machine

Tried: Read `/home/jkw/.hermes/.env` for `NEBIUS_API_KEY`, `TAVILY_API_KEY`, `PINECONE_API_KEY`, `LANGSMITH_API_KEY`, Stripe keys.

Result: All missing.

Impact: Live Token Factory chat, live Tavily search, live Pinecone upsert, live LangSmith traces, and live Stripe charges cannot run.

Fix: Implement a Token Factory client that fails with a clear error when the key is empty. Add offline tests with a fake client. Document the gap here. Do not invent a successful live run.

## E04 — Official recipes pin Python 3.12; host has 3.14.7

Tried: Follow the official `requires-python = ">=3.12"` stack with FastAPI, prometheus, redis, langchain.

Result: Host Python is 3.14.7. Installing the full official dependency tree is slow and not required for a walkthrough of the ideas.

Fix: Write a smaller original implementation. Keep `requires-python = ">=3.12"`. Run tests on 3.14.

## E05 — Official cookbook is large and not your work

Tried: Publish a copy of `nebius/nebius-partner-cookbook`.

Result: That would republish Nebius code as if you wrote it.

Fix: Write original modules that implement the same sequence. Link the official repo. Do not copy their FastAPI trees.

## E06 — Recipe 01 live run without a key

Tried: `python cookbooks/01-first-agent/app.py`

Expected: A paragraph about Token Factory.

Result: `TokenFactoryError: NEBIUS_API_KEY is empty`.

Fix: Catch `TokenFactoryError` in `main()`, print the fix, exit 2. Tests inject a fake client and do not call the network.

## E07 — Pinecone and Tavily without keys

Tried: Call partner APIs for recipes 02 and 03.

Result: No keys.

Fix: Local bag-of-words index for knowledge. Fixture search hits for Tavily when the key is empty. If a key is present, recipe 03 posts to `https://api.tavily.com/search`.

## E08 — Stripe live mode risk

Tried: Use a real Stripe secret if present.

Result: No key. Also, a walkthrough must not create live charges.

Fix: Tool handler returns `livemode: False` and id `pi_test_local`. Do not send HTTP to Stripe in tests.

## E09 — pytest import path

Tried: `from cookbooks.01-first-agent.app import run_agent`

Result: Invalid Python package name because of hyphens.

Fix: Load modules with `importlib.util.spec_from_file_location` in tests.

## E10 — dataclass + importlib without sys.modules

Tried: Load recipe modules with `importlib.util.spec_from_file_location` and `exec_module`.

Result: Python 3.13 dataclasses raised `AttributeError: 'NoneType' object has no attribute '__dict__'` because the module was not in `sys.modules`.

Fix: Register the module in `sys.modules` before `exec_module`.

## E11 — Host python has no httpx

Tried: `python cookbooks/01-first-agent/app.py` with system Python 3.14.

Result: `ModuleNotFoundError: No module named 'httpx'`.

Fix: Run with `uv run python`. Tests use the uv environment.

## E12 — Keys were on disk, not in Hermes env

Tried: Look in `/home/jkw/.hermes/.env` for live keys.

Result: `NEBIUS_API_KEY` is commented as a placeholder. Hermes env did not have Tavily.

Fix: The keys from the earlier session are in gitignored files under `/home/jkw/Projects/ai-agents-nv-notebooks/.env`. Copied into this repo's gitignored `.env`. Do not commit that file.

Live rerun (keys present):

- Recipe 01: Token Factory returned two sentences. The default model did not describe Token Factory as a product. The HTTP call succeeded.
- Recipe 03: Tavily returned five live hits. Note field: `Live Tavily used`.

## Open items
- Replace SQLite in recipe 06 with Postgres when a database is available.
- Point recipe 07 at LangSmith when `LANGSMITH_API_KEY` is set.
