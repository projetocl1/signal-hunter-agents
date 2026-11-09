"""
Agentes de scan. O pipeline é partilhado entre morning/afternoon/close;
cada agente apenas define o seu `focus` e, no caso do close, gera o briefing.
"""

from __future__ import annotations

import anthropic

from core import airtable_writer, classifier, news_fetcher, ticker_universe
from core.durability_check import evaluate


def run_scan(focus: str, expand: bool = False, max_items: int = 25) -> list[dict]:
    """
    Executa um scan completo:
      navegar fontes → classificar → durabilidade → convergência → scoring →
      escrever no Airtable (score >= 6).

    Devolve a lista de resultados processados (para logging do agente).
    """
    client = anthropic.Anthropic()
    at = airtable_writer.AirtableClient()

    universe = ticker_universe.get_universe(client, expand=expand)
    print(f"[scan] universo: {len(universe)} tickers (expand={expand})")

    items = news_fetcher.fetch_news(client, focus, universe, max_items=max_items)
    print(f"[scan] candidatos recolhidos: {len(items)}")

    results: list[dict] = []
    for item in items:
        headline = item.get("headline", "")
        source = item.get("source", "")
        if not headline:
            continue

        try:
            cls = classifier.classify(
                client,
                headline=headline,
                source=source,
                context=item.get("summary", ""),
                ticker_hint=item.get("ticker", ""),
            )
        except Exception as exc:  # noqa: BLE001 — não deixar 1 item partir o scan
            print(f"[scan] classificação falhou para {headline!r}: {exc}")
            continue

        signal = cls.model_dump()
        signal["headline"] = headline

        # Convergência autoritativa vem do Airtable, não do modelo.
        conv = at.detect_convergence(signal["ticker"], signal["signal_type"])
        scored = evaluate(signal, convergence=conv.detected)

        # Dois tipos DIFERENTES no mesmo ticker = prioridade máxima.
        if scored.kept and conv.distinct_types:
            scored.priority = "high"

        status = f"{signal['ticker']} {signal['signal_type']} " \
                 f"strength={scored.raw_score} final={scored.final_score} " \
                 f"→ {scored.priority}"
        print(f"[scan] {status} | {scored.reason}")

        if scored.kept:
            record = airtable_writer.build_record(
                signal, scored, convergence=conv.detected, source=source
            )
            try:
                rec_id = at.write_signal(record)
                print(f"[scan]   ✓ Airtable {rec_id}")
            except Exception as exc:  # noqa: BLE001
                print(f"[scan]   ✗ falha a escrever no Airtable: {exc}")

        results.append({"signal": signal, "scored": scored, "convergence": conv})

    kept = [r for r in results if r["scored"].kept]
    print(f"[scan] concluído: {len(kept)}/{len(results)} sinais registados.")
    return results
