"""
options_scan — 14:30 UTC e 18:00 UTC (dias de mercado).

Foco: fluxo de opções incomum — sweeps agressivos, blocos OTM com premium
elevado, rácio volume/OI anómalo. Fontes: barchart.com e unusualwhales.com.
"""

from __future__ import annotations

from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

from agents import run_scan  # noqa: E402

OPTIONS_DOMAINS = ["barchart.com", "unusualwhales.com"]

FOCUS = (
    "Pesquisa em barchart.com (secção 'options unusual activity' ou 'options "
    "flow') e unusualwhales.com as opções com actividade incomum das últimas "
    "4 horas. Foca-te APENAS em:\n"
    "- CALLS (bullish) com premium total >= $500,000\n"
    "- OTM (out-of-the-money): strike acima do preço actual\n"
    "- Volume/OI ratio >= 3x (volume muito superior ao open interest)\n"
    "- Sweeps: execução agressiva em múltiplas exchanges\n"
    "- Expiry < 6 semanas (urgência/convicção)\n\n"
    "EXCLUI obrigatoriamente:\n"
    "- PUTS (bearish) — excepto se volume/OI > 20x e premium > $2M (short squeeze signal)\n"
    "- ETFs broad-market: SPY, QQQ, IWM, DIA, XLF\n"
    "- Calls deep ITM (cobertura/hedge)\n"
    "- Premium < $200,000\n"
    "- Volume/OI < 2x\n\n"
    "Para cada fluxo qualificado, o headline deve incluir: ticker, tipo (CALL/PUT), "
    "premium total, strike vs preço actual (OTM %), data de expiry. Exemplo: "
    "'NVDA CALL $1.5M sweep — strike $145 (+8% OTM) expiry Jul 18'. "
    "O summary deve incluir: exchange(s) onde ocorreu, volume vs OI, "
    "se houve outras opções recentes no mesmo ticker (cluster de smart money) "
    "e qualquer notícia ou catalisador associado visível. "
    "Prioriza os maiores premiums e os sweeps cruzados (multi-exchange)."
)


def main() -> None:
    print("=== options_scan (14:30 / 18:00 UTC) ===")
    run_scan(FOCUS, expand=False, max_items=20, source_domains=OPTIONS_DOMAINS)


if __name__ == "__main__":
    main()
