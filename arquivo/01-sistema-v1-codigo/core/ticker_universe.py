"""
Universo de tickers — dinâmico.

Base: Nasdaq 100 (lista estática abaixo; refrescar periodicamente).
Expansão automática (best-effort, via web search da Claude):
  - tickers mencionados em analyst upgrades nos últimos 30 dias;
  - laggards no mesmo sector de um líder que moveu >= 15%.

Critérios de qualificação (market cap, volume, histórico de movimento, preço)
estão em config.UNIVERSE_CRITERIA e são aplicados na expansão por filtragem
do próprio modelo — não temos um feed de mercado próprio neste repositório,
por isso a qualificação é pedida explicitamente ao modelo na expansão.
"""

from __future__ import annotations

import json
import re

import anthropic

from . import config

# Nasdaq 100 — base estática (subconjunto representativo e estável).
# Deve ser refrescada periodicamente; a expansão dinâmica cobre o resto.
NASDAQ_100_BASE = [
    "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "GOOG", "META", "AVGO", "TSLA",
    "COST", "NFLX", "AMD", "PEP", "ADBE", "CSCO", "TMUS", "INTC", "QCOM",
    "INTU", "TXN", "AMGN", "AMAT", "HON", "ISRG", "BKNG", "VRTX", "ADP",
    "REGN", "MU", "LRCX", "PANW", "SBUX", "GILD", "MDLZ", "ADI", "KLAC",
    "SNPS", "CDNS", "MELI", "PYPL", "MAR", "CRWD", "ABNB", "ORLY", "CTAS",
    "MRVL", "FTNT", "DASH", "ADSK", "WDAY", "NXPI", "ROP", "PCAR", "CPRT",
    "MNST", "AEP", "PAYX", "ODFL", "FAST", "ROST", "KDP", "EA", "DDOG",
    "VRSK", "EXC", "CTSH", "GEHC", "KHC", "LULU", "CCEP", "BKR", "XEL",
    "IDXX", "TTD", "CSGP", "ON", "ANSS", "ZS", "DXCM", "BIIB", "CDW",
    "MCHP", "TEAM", "GFS", "WBD", "ILMN", "MDB", "ARM", "SMCI", "PDD",
]


def base_universe() -> list[str]:
    """Devolve a base estática (Nasdaq 100)."""
    return list(dict.fromkeys(NASDAQ_100_BASE))


def _extract_symbols(text: str) -> list[str]:
    text = re.sub(r"```(?:json)?", "", text or "").strip()
    start, end = text.find("["), text.rfind("]")
    if start == -1 or end == -1:
        return []
    try:
        data = json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return []
    out = []
    for item in data if isinstance(data, list) else []:
        if isinstance(item, str):
            out.append(item.strip().upper())
        elif isinstance(item, dict) and "ticker" in item:
            out.append(str(item["ticker"]).strip().upper())
    return [s for s in out if s.isalpha() and 1 <= len(s) <= 5]


def expand_universe(client: anthropic.Anthropic, max_extra: int = 40) -> list[str]:
    """
    Expansão dinâmica (best-effort) via web search.
    Devolve tickers extra que cumprem os critérios de qualificação.
    """
    c = config.UNIVERSE_CRITERIA
    e = config.EXPANSION
    user = f"""Identifica tickers NASDAQ/NYSE a ADICIONAR a uma watchlist de swing trading.

Inclui tickers que satisfaçam AMBOS:
1. Pelo menos uma destas condições de expansão:
   - mencionados em analyst upgrades nos últimos {e['analyst_upgrade_lookback_days']} dias;
   - laggards no mesmo sector de um líder que subiu >= {e['sector_leader_move_pct']:.0f}% recentemente.
2. TODOS os critérios de qualificação:
   - market cap > ${c['min_market_cap_usd']:,};
   - volume médio diário > {c['min_avg_daily_volume']:,} shares;
   - pelo menos um movimento >= {c['min_move_90d_pct']:.0f}% em 90 dias;
   - preço > ${c['min_price_usd']:.0f}.

Pesquisa fontes (Benzinga, TipRanks, Slickcharts) e devolve APENAS um array
JSON de símbolos (strings), no máximo {max_extra}. Sem texto à volta."""

    messages = [{"role": "user", "content": user}]
    final_text = ""
    for _ in range(6):
        response = client.messages.create(
            model=config.CLAUDE_MODEL,
            max_tokens=4000,
            tools=[
                {
                    "type": "web_search_20260209",
                    "name": "web_search",
                    "allowed_domains": config.SOURCE_DOMAINS,
                    "max_uses": 8,
                }
            ],
            messages=messages,
        )
        final_text = "".join(
            b.text for b in response.content if getattr(b, "type", "") == "text"
        )
        if response.stop_reason == "pause_turn":
            messages.append({"role": "assistant", "content": response.content})
            continue
        break
    return _extract_symbols(final_text)[:max_extra]


def get_universe(
    client: anthropic.Anthropic | None = None, expand: bool = False
) -> list[str]:
    """
    Universo completo. Se `expand` e houver client, junta a expansão dinâmica.
    Falhas na expansão não quebram o pipeline — devolve pelo menos a base.
    """
    universe = base_universe()
    if expand and client is not None:
        try:
            extra = expand_universe(client)
            universe = list(dict.fromkeys(universe + extra))
        except Exception as exc:  # noqa: BLE001 — expansão é best-effort
            print(f"[ticker_universe] expansão falhou, uso só a base: {exc}")
    return universe
