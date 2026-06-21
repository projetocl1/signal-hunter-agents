"""
insider_scan — 07:30 UTC (diário, dias de mercado).

Foco: compras de insiders (Form 4) de openinsider.com com valor >= $500K.
Filtra: option exercises automáticos (10b5-1), vendas e heranças.
"""

from __future__ import annotations

from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

from agents import run_scan  # noqa: E402

# Apenas as fontes relevantes para insider buying
INSIDER_DOMAINS = ["openinsider.com", "sec.gov"]

FOCUS = (
    "Pesquisa em openinsider.com (secção 'latest purchases') as compras de "
    "insiders confirmadas nas últimas 24 horas. Foca-te APENAS em:\n"
    "- Open-market purchases (tipo P na coluna Transaction)\n"
    "- Valor >= $500,000\n"
    "- Título do insider: CEO, CFO, President, COO, Founder, Director\n\n"
    "EXCLUI obrigatoriamente:\n"
    "- Option exercises (A, M, S)\n"
    "- Planned 10b5-1 transactions\n"
    "- Vendas (S)\n"
    "- Compras < $500,000\n\n"
    "Para cada compra qualificada, o headline deve incluir: nome do insider, "
    "título, valor em USD e ticker. Exemplo: "
    "'CEO John Smith compra $1.2M NVDA — open market purchase Form 4'. "
    "O summary deve indicar: número de acções, preço médio, % das acções totais "
    "do insider e se existem outras compras recentes do mesmo insider (cluster). "
    "Inclui o link directo para o Form 4 no SEC EDGAR quando disponível."
)


def main() -> None:
    print("=== insider_scan (07:30 UTC) ===")
    run_scan(FOCUS, expand=False, max_items=15, source_domains=INSIDER_DOMAINS)


if __name__ == "__main__":
    main()
