"""
premarket_scan — 12:00 UTC (08:00 ET, antes da abertura de bolsa).

A janela de maior valor do dia: analistas publicam upgrades e initiations
antes da abertura, earnings pre-market chegam, e o fluxo institucional
posiciona-se. O operador tem 1.5h antes do sino para avaliar e decidir.
"""

from __future__ import annotations

from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

from agents import run_scan  # noqa: E402

FOCUS = (
    "Janela pré-mercado americano (07:00–09:30 ET). Procura em:\n"
    "- Benzinga e TipRanks: analyst upgrades, initiations e price target raises "
    "publicados esta manhã antes da abertura de bolsa. Prioriza raises >= 20% "
    "e initiations com target acima do preço actual.\n"
    "- SEC EDGAR (8-K e S-1 pré-mercado): Material Definitive Agreement, "
    "guidance updates, FDA outcomes.\n"
    "- GlobeNewswire e PRNewswire: earnings pré-mercado com EPS beat >= 20% "
    "vs estimativa e/ou guidance raise.\n\n"
    "PRIORIDADE MÁXIMA neste scan: catalisadores que criam momentum logo na "
    "abertura (09:30 ET). O operador pode entrar posição antes do sino ou "
    "nos primeiros 30 minutos de mercado. Rejeitar tudo o que não tenha "
    "números concretos ou seja marketing sem substância."
)


def main() -> None:
    print("=== premarket_scan (12:00 UTC / 08:00 ET) ===")
    run_scan(FOCUS, expand=True, max_items=20)


if __name__ == "__main__":
    main()
