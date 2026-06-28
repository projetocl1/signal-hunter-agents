# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Autonomous market catalyst tracking system for NASDAQ/NYSE swing trading. Three scheduled agents (morning/afternoon/close) run via GitHub Actions, each executing the same shared pipeline. Signals are stored in a dedicated Airtable base; the close scan also commits a daily markdown briefing to `briefings/`.

## Commands

```bash
# Install
pip install -r requirements.txt

# Run tests (offline, no credentials needed)
python -m unittest discover -s tests -v

# Run a single test file
python -m unittest tests.test_durability -v

# Validate credentials + external services before activating schedulers
python -m scripts.validate_setup

# Run an agent manually (requires credentials in env)
python -m agents.morning_scan
python -m agents.afternoon_scan
python -m agents.close_scan
```

No linter or formatter is configured; no build step.

## Architecture

### Pipeline (shared — `agents/__init__.py:run_scan`)

```
get_universe → fetch_news → classify → evaluate → detect_convergence → write_signal
```

Every agent calls `run_scan(focus, expand, max_items)`. The `focus` string drives what the web search agent looks for; `expand=True` (morning only) adds dynamic tickers via a second web search round.

### Module responsibilities

| Module | Role |
|---|---|
| `core/config.py` | Single source of truth for all tuneable constants: scoring thresholds, source allowlist, universe criteria, signal types |
| `core/news_fetcher.py` | Calls Claude API with `web_search_20260209` tool; handles `pause_turn` loop; returns raw candidate dicts |
| `core/classifier.py` | Calls `client.messages.parse()` with a Pydantic schema (`Classification`) for guaranteed-valid JSON output |
| `core/durability_check.py` | Pure function `evaluate(signal, convergence)` → `ScoredSignal`; no I/O |
| `core/airtable_writer.py` | Airtable REST client: `detect_convergence()` (reads), `write_signal()` (writes), `recent_signals()` (for briefing) |
| `core/ticker_universe.py` | Static Nasdaq 100 base + best-effort dynamic expansion via web search |
| `core/briefing.py` | Pure markdown builder; `close_scan` calls `write_briefing()` which commits to `briefings/` |

### Scoring rules (all constants in `core/config.py`)

1. `durability_12h = false` → **always discard**, regardless of score
2. Base score = `catalyst_strength` (1–10, from Claude classifier)
3. `convergence_detected = true` → **+3** (`CONVERGENCE_BONUS`)
4. `final_score >= 8` → high priority (`alerted=True` in Airtable)
5. `final_score 6–7` → monitor
6. `final_score < 6` → discard

**Convergence is authoritative from Airtable, not from the model.** `classifier.py` produces a `convergence_detected` estimate, but `run_scan` always overwrites it with the result of `AirtableClient.detect_convergence()`. Two *different* signal types on the same ticker within 48h (`distinct_types=True`) forces `priority = "high"` regardless of score.

### Claude API usage patterns

- **News fetching** (`news_fetcher.py`): `client.messages.create()` with `web_search_20260209` tool, `allowed_domains` restricted to `config.SOURCE_DOMAINS`. Handles `stop_reason == "pause_turn"` by re-appending the assistant turn and looping (up to `max_turns=6`).
- **Classification** (`classifier.py`): `client.messages.parse()` with `output_format=Classification` (Pydantic). Returns `response.parsed_output`; raises `RuntimeError` if `None`.
- **Universe expansion** (`ticker_universe.py`): same web search pattern as news fetching; failures are caught and swallowed (`best-effort`).

### External dependencies

- **Anthropic API**: classification + web search. Model defaults to `claude-opus-4-8`, overridable via `CLAUDE_MODEL` env var.
- **Airtable REST API** (`https://api.airtable.com/v0`): uses `typecast: true` on writes so single-select values are created automatically. Table name defaults to `catalyst_signals`.
- No database, no broker, no market data feed — all market data comes through Claude's web search.

### GitHub Actions

Three workflows (`morning.yml`, `afternoon.yml`, `close.yml`) all require three secrets: `ANTHROPIC_API_KEY`, `AIRTABLE_TOKEN`, `AIRTABLE_BASE_ID`. All support `workflow_dispatch` for manual runs. `close.yml` has `permissions: contents: write` to commit the daily briefing.

## Key invariants

- This repo shares **zero code and zero Airtable base** with `pharma-intel-agents`. Never reference or import from that repo.
- The `briefings/` directory is committed to git by the `close_scan` GitHub Actions workflow automatically.
- The Nasdaq 100 list in `ticker_universe.py` is a static snapshot and should be refreshed periodically.
- Web search cost: each scan fires up to 10 web search calls (`max_uses=10`). Keep `max_items` and `max_turns` limits in mind when changing fetch behaviour.
