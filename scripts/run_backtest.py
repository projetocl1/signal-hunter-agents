"""
Backtest histórico — corre eventos famosos pelo motor de classificação + scoring.

Uso:
    python -m scripts.run_backtest              # corre todos os eventos seed
    python -m scripts.run_backtest --ticker NVDA  # filtra por ticker
    python -m scripts.run_backtest --limit 5    # corre apenas os primeiros N

Guarda resultados em data/backtest_results.json (acumulativo).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

import anthropic  # noqa: E402

from core.backtest_engine import (  # noqa: E402
    evaluate_event,
    load_results,
    save_results,
)

FAMOUS_EVENTS_PATH = Path("data/famous_events.json")


def _load_events(ticker_filter: str | None = None, limit: int | None = None) -> list[dict]:
    with open(FAMOUS_EVENTS_PATH) as f:
        events = json.load(f)
    if ticker_filter:
        events = [e for e in events if e["ticker"] == ticker_filter.upper()]
    if limit:
        events = events[:limit]
    return events


def main() -> None:
    ticker_filter = None
    limit = None

    args = sys.argv[1:]
    for i, arg in enumerate(args):
        if arg == "--ticker" and i + 1 < len(args):
            ticker_filter = args[i + 1]
        if arg == "--limit" and i + 1 < len(args):
            limit = int(args[i + 1])

    events = _load_events(ticker_filter=ticker_filter, limit=limit)
    print(f"[backtest] {len(events)} eventos a processar...")

    client = anthropic.Anthropic()
    results = []

    for i, event in enumerate(events, 1):
        print(f"\n[{i}/{len(events)}] {event['ticker']} {event['event_date']}")
        print(f"  Headline: {event['headline'][:80]}...")

        result = evaluate_event(client, event)

        if result.error:
            print(f"  ✗ Erro: {result.error}")
        else:
            alert_str = "🔴 ALERTA" if result.would_alert else ("🟡 monitor" if result.would_keep else "⚪ descartado")
            hit_str = "✅ HIT" if result.hit else ("🛑 STOP" if result.stopped else ("❌ miss" if result.hit is not None else "N/A"))
            print(f"  Tipo: {result.signal_type} | Strength: {result.catalyst_strength} | Score: {result.final_score} → {alert_str}")
            print(f"  Durabilidade 12h: {result.durability_12h} | Horizonte: {result.horizon}")
            if result.price_entry:
                print(f"  Preço entrada: ${result.price_entry:.2f}")
                pnl_parts = []
                if result.pnl_3d is not None:
                    pnl_parts.append(f"3d={result.pnl_3d:+.1f}%")
                if result.pnl_10d is not None:
                    pnl_parts.append(f"10d={result.pnl_10d:+.1f}%")
                if result.pnl_30d is not None:
                    pnl_parts.append(f"30d={result.pnl_30d:+.1f}%")
                if result.pnl_90d is not None:
                    pnl_parts.append(f"90d={result.pnl_90d:+.1f}%")
                print(f"  P&L real: {' | '.join(pnl_parts)} → {hit_str}")

        results.append(result)

    save_results(results)
    print(f"\n[backtest] concluído. Resultados guardados em {Path('data/backtest_results.json')}")

    # Resumo
    kept = [r for r in results if r.would_keep and not r.error]
    alerted = [r for r in results if r.would_alert and not r.error]
    hits = [r for r in results if r.hit is True]
    misses = [r for r in results if r.hit is False and not r.stopped]
    stops = [r for r in results if r.stopped]

    print(f"\n{'='*50}")
    print(f"RESUMO BACKTEST ({len(results)} eventos)")
    print(f"{'='*50}")
    print(f"  Sistema teria alertado:    {len(alerted)}/{len(results)} ({len(alerted)/len(results)*100:.0f}%)")
    print(f"  Sistema teria monitorizado:{len(kept)}/{len(results)} ({len(kept)/len(results)*100:.0f}%)")
    print(f"  HITs (no horizonte):       {len(hits)}")
    print(f"  Misses:                    {len(misses)}")
    print(f"  Stops (-7%):               {len(stops)}")
    if hits or misses or stops:
        total_decided = len(hits) + len(misses) + len(stops)
        print(f"  Taxa de acerto real:       {len(hits)/total_decided*100:.0f}% ({len(hits)}/{total_decided})")


if __name__ == "__main__":
    main()
