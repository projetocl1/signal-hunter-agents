"""
close_scan — 21:00 UTC.

Foco: after-hours earnings (EPS beats, guidance raises) + gera o briefing diário.

Depois do scan, lê do Airtable todos os sinais do dia (últimas 24h, score >= 6)
e escreve o briefing markdown no repositório.
"""

from __future__ import annotations

from agents import run_scan
from core import briefing
from core.airtable_writer import AirtableClient

FOCUS = (
    "Earnings after-hours: EPS beats >= 20% vs estimativa e guidance raises "
    "acima de consenso, em GlobeNewswire, PR Newswire e Benzinga. Inclui "
    "também novos produtos com revenue guidance e deals >= $100M anunciados "
    "hoje. Foco em 'earnings' e 'product'."
)


def main() -> None:
    print("=== close_scan (21:00 UTC) ===")
    run_scan(FOCUS, expand=False)

    # Briefing diário: lê os sinais do dia do Airtable (fonte de verdade).
    at = AirtableClient()
    signals = at.recent_signals(hours=24, min_score=6)
    print(f"[briefing] {len(signals)} sinais nas últimas 24h (score >= 6)")

    markdown = briefing.build_briefing(signals)
    path = briefing.write_briefing(markdown)
    print(f"[briefing] escrito em {path}")


if __name__ == "__main__":
    main()
