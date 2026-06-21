"""
Configuração central do signal-hunter-agents.

Tudo o que é "afinável" vive aqui: fontes a navegar, critérios de
qualificação do universo de tickers, tipos de catalisador e — sobretudo —
as regras de scoring. Manter num único módulo evita números mágicos
espalhados pelos agentes.
"""

from __future__ import annotations

import os

# ── Claude ───────────────────────────────────────────────────────────────
CLAUDE_MODEL = os.environ.get("CLAUDE_MODEL", "claude-opus-4-8")

# ── Airtable ─────────────────────────────────────────────────────────────
AIRTABLE_TABLE = os.environ.get("AIRTABLE_TABLE", "catalyst_signals")

# ── Fontes a monitorizar ──────────────────────────────────────────────────
# O agente navega directamente estes domínios através da ferramenta de
# web search da Claude API. Cada entrada tem o tipo de sinal que costuma
# produzir, para orientar o foco de cada scan.
SOURCES = {
    "benzinga.com": "analyst upgrades e initiations",
    "tipranks.com": "price target changes",
    "sec.gov": "8-K filings (EDGAR)",
    "globenewswire.com": "product announcements / PR",
    "prnewswire.com": "product announcements / PR",
    "marketwatch.com": "macro e geopolítico",
    "slickcharts.com": "sector performance e rotation",
    # Novos coletores
    "openinsider.com": "insider buying — compras de insiders com $500K+",
    "barchart.com": "unusual options activity — sweeps e volume anómalo",
    "unusualwhales.com": "fluxo de opções incomum — smart money flow",
}

# Domínios passados à web search da Claude (allowlist).
SOURCE_DOMAINS = list(SOURCES.keys())

# ── Universo de tickers ────────────────────────────────────────────────────
# Critérios de qualificação. A base é o Nasdaq 100; a expansão dinâmica
# (upgrades recentes + laggards sectoriais) é resolvida em ticker_universe.py.
UNIVERSE_CRITERIA = {
    "min_market_cap_usd": 500_000_000,      # > $500M
    "min_avg_daily_volume": 500_000,        # > 500K shares/dia
    "min_move_90d_pct": 15.0,               # >= 1 movimento >= 15% em 90 dias
    "min_price_usd": 5.0,                    # preço > $5
}

# Expansão dinâmica do universo.
EXPANSION = {
    "analyst_upgrade_lookback_days": 30,     # upgrades nos últimos 30 dias
    "sector_leader_move_pct": 15.0,          # líder moveu >= 15% → puxa o sector
}

# ── Tipos de catalisador ───────────────────────────────────────────────────
SIGNAL_TYPES = ("analyst", "earnings", "product", "macro", "rotation", "insider", "options")
HORIZONS = ("3d", "10d", "30d", "90d")

# Catalisadores que PASSAM o filtro (orientação para o classificador).
CATALYSTS_PASS = [
    # --- analyst / earnings / product ---
    "Analyst initiation (novo banco a cobrir)",
    "Price target raise >= 20% numa única revisão",
    "Earnings EPS beat >= 20% vs estimativa",
    "Guidance raise acima de consenso",
    "FDA approval ou PDUFA outcome positivo",
    "Deal ou supply agreement >= $100M",
    "New product com revenue guidance associado",
    "Sector leader subiu >= 10% → detectar laggards",
    "Competitor capacity expansion announcement",
    # --- insider buying ---
    "Cluster buy: 2+ insiders compraram no mesmo mês",
    "CEO/CFO/Founder open-market purchase >= $500K",
    "Director purchase >= $1M (open market, não option exercise)",
    "Compra em dias de queda do mercado >= 3% (contra-corrente)",
    "Compra representa >= 1% das acções totais do insider",
    # --- unusual options ---
    "OTM call sweep >= $1M premium, expiry < 3 semanas",
    "Volume/OI ratio > 10x na mesma strike (call OTM)",
    "Sweep cruzado em múltiplas exchanges (agressivo)",
    "Bloco de calls > $500K sem notícias públicas visíveis",
    "Put/call ratio invertido abaixo de 0.3 em contexto de queda",
]

# Catalisadores que NÃO passam o filtro.
CATALYSTS_REJECT = [
    "Dividendo regular",
    "Insider sale rotineira",
    "Insider option exercise automático (10b5-1 plan)",
    "Rating mantido sem mudança de target",
    "Press release de marketing sem números",
    "Earnings in-line sem surpresa",
    "Rumor não confirmado por fonte primária",
    "Options volume < 2x OI sem sweeps",
    "Calls deep ITM de cobertura (hedge known)",
    "Options em ETFs broad-market (SPY, QQQ, IWM)",
]

# ── Thresholds específicos por tipo ──────────────────────────────────────────
INSIDER_MIN_USD = 500_000        # compra mínima para qualificar insider
INSIDER_CLUSTER_MIN = 2          # mínimo de insiders para cluster buy
OPTIONS_MIN_PREMIUM = 500_000    # premium mínimo para qualificar options flow
OPTIONS_VOL_OI_MIN = 3.0         # rácio volume/OI mínimo

# ── Regras de scoring ──────────────────────────────────────────────────────
# durability_12h = false  → descarta sempre (tratado em durability_check)
# convergence_detected    → +3 ao score
# score >= 8              → alta prioridade
# score 6-7              → monitorização
# score < 6              → descarta
CONVERGENCE_BONUS = 3
SCORE_HIGH_PRIORITY = 8          # >= 8
SCORE_MONITOR_MIN = 6            # 6-7 (inclusive)
CONVERGENCE_WINDOW_HOURS = 48    # janela para detecção de convergência
DURABILITY_HOURS = 12            # sinal tem de continuar válido 12h após detecção
