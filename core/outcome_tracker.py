"""
Actualiza o desfecho dos sinais abertos no Airtable.

Para cada sinal com outcome='open', busca o preço actual via yfinance
e determina o desfecho com base no horizon e na variação face ao entry_price:

  - hit      : pnl_pct >= limiar de sucesso do horizon
  - stopped  : pnl_pct <= -7%
  - expired  : horizon expirado sem hit nem stop
  - open     : dentro do prazo, sem condição de saída atingida

Limiares de 'hit' por horizon:
  3d → +5%  |  10d → +8%  |  30d → +15%  |  90d → +25%
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import NamedTuple

import requests
import yfinance as yf

from . import config
from .airtable_writer import AirtableClient

STOP_PCT = -7.0

HORIZON_DAYS = {"3d": 3, "10d": 10, "30d": 30, "90d": 90}
HIT_PCT = {"3d": 5.0, "10d": 8.0, "30d": 15.0, "90d": 25.0}


class OutcomeResult(NamedTuple):
    ticker: str
    outcome: str
    pnl_pct: float
    price_now: float


def _price(ticker: str) -> float | None:
    try:
        return yf.Ticker(ticker).fast_info.last_price
    except Exception:
        return None


def _days_since(date_str: str) -> float:
    try:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return (datetime.now(timezone.utc) - dt).total_seconds() / 86400
    except Exception:
        return 0.0


def evaluate_outcome(rec: dict) -> OutcomeResult | None:
    ticker = rec.get("ticker", "")
    entry = rec.get("entry_price")
    horizon = rec.get("horizon", "30d")
    date_str = rec.get("date", "")

    if not ticker or not entry:
        return None

    price_now = _price(ticker)
    if price_now is None:
        return None

    pnl_pct = round((price_now - entry) / entry * 100, 2)
    days_elapsed = _days_since(date_str)
    horizon_days = HORIZON_DAYS.get(horizon, 30)
    hit_threshold = HIT_PCT.get(horizon, 15.0)

    if pnl_pct >= hit_threshold:
        outcome = "hit"
    elif pnl_pct <= STOP_PCT:
        outcome = "stopped"
    elif days_elapsed >= horizon_days:
        outcome = "expired"
    else:
        outcome = "open"

    return OutcomeResult(ticker=ticker, outcome=outcome, pnl_pct=pnl_pct, price_now=round(price_now, 2))


def run_update(dry_run: bool = False) -> list[dict]:
    at = AirtableClient()

    # Todos os sinais ainda abertos.
    records = at._list({"filterByFormula": "{outcome}='open'", "pageSize": 100})
    print(f"[outcome_tracker] {len(records)} sinais abertos a verificar")

    updated = []
    for rec in records:
        fields = rec.get("fields", {})
        rec_id = rec["id"]
        result = evaluate_outcome(fields)
        if result is None:
            continue

        patch = {
            "price_now": result.price_now,
            "pnl_pct": result.pnl_pct,
            "outcome": result.outcome,
        }

        status = f"{result.ticker}: {result.outcome} | pnl={result.pnl_pct:+.1f}% | now={result.price_now}"
        print(f"[outcome_tracker] {status}")

        if not dry_run:
            url = f"{at._url}/{rec_id}"
            resp = requests.patch(
                url,
                headers=at._headers,
                json={"fields": patch, "typecast": True},
                timeout=30,
            )
            resp.raise_for_status()

        updated.append({"id": rec_id, **patch})

    print(f"[outcome_tracker] concluído: {len(updated)} actualizados.")
    return updated
