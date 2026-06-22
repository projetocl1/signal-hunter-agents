"""
midsession_scan — 16:30 UTC (12:30 ET, meio de sessão).

Entrega dados frescos 30 minutos antes do check das 17:00 UTC (18:00 PT).
O mercado americano tem ainda 3.5h abertas — sinais aqui são accionáveis
na mesma sessão. Foco em desenvolvimentos de meio de sessão: anúncios
de FDA ao almoço, upgrades tardios, blocos institucionais e momentum plays.
"""

from __future__ import annotations

from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

from agents import run_scan  # noqa: E402

FOCUS = (
    "Meio de sessão americano (11:00–12:30 ET). Procura desenvolvimentos "
    "das últimas 3 horas que ainda não foram capturados:\n"
    "- Anúncios FDA frequentemente publicados entre 10:00 e 12:00 ET: "
    "PDUFA outcomes, Complete Response Letters, Advisory Committee votes.\n"
    "- Analyst notes tardias: upgrades publicados após a abertura por "
    "bancos que actualizaram após ver os primeiros dados de mercado.\n"
    "- Deals e supply agreements anunciados mid-morning.\n"
    "- Earnings surprises de empresas que reportaram antes do almoço ET.\n"
    "- Blocos de opções incomuns das últimas 2 horas (barchart.com, "
    "unusualwhales.com): sweeps de mid-session são frequentemente de "
    "informação que ainda não chegou ao mercado.\n\n"
    "O operador verifica este scan às 17:00 UTC (18:00 PT) e pode entrar "
    "posição com 3h de mercado pela frente. Prioriza sinais accionáveis "
    "HOJE — evitar eventos futuros distantes sem catalisador imediato."
)


def main() -> None:
    print("=== midsession_scan (16:30 UTC / 12:30 ET) ===")
    run_scan(FOCUS, expand=False, max_items=20)


if __name__ == "__main__":
    main()
