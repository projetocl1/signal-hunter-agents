"""
morning_scan — 06:30 UTC.

Foco: analyst upgrades overnight + SEC 8-K das últimas 8h.
"""

from __future__ import annotations

from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

from agents import run_scan

FOCUS = (
    "Analyst upgrades, initiations e price target raises publicados durante a "
    "noite (overnight) em Benzinga e TipRanks. Adicionalmente, SEC 8-K filings "
    "materiais publicados no EDGAR nas últimas 8 horas. Prioriza catalisadores "
    "com números concretos (target raises >= 20%, deals >= $100M, guidance)."
)


def main() -> None:
    print("=== morning_scan (06:30 UTC) ===")
    # Expande o universo de manhã: upgrades recentes alteram a watchlist.
    run_scan(FOCUS, expand=True)


if __name__ == "__main__":
    main()
