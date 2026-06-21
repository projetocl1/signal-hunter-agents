"""
Escrita e leitura no Airtable (base DEDICADA a catalisadores).

Tabela: catalyst_signals
Campos: date | ticker | signal_type | catalyst_strength | horizon |
        durability_12h | convergence | headline | source | raw_score | alerted

Também implementa a detecção de convergência: mesmo ticker com outro sinal
nas últimas 48h. Dois tipos DIFERENTES de sinal no mesmo ticker = prioridade
máxima (flag distinct_types).

IMPORTANTE: usa SEMPRE a base dedicada (AIRTABLE_BASE_ID). Nunca a base do
pharma-intel-agents.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime, timezone

import requests

from . import config


def _fetch_price(ticker: str) -> float | None:
    if not ticker:
        return None
    try:
        import yfinance as yf
        return yf.Ticker(ticker).fast_info.last_price
    except Exception:
        return None

API_BASE = "https://api.airtable.com/v0"


@dataclass
class Convergence:
    detected: bool                       # há outro sinal no mesmo ticker em 48h?
    distinct_types: bool                 # há um TIPO diferente → prioridade máxima
    prior_types: list[str] = field(default_factory=list)


class AirtableClient:
    """Cliente fino sobre a REST API do Airtable."""

    def __init__(
        self,
        token: str | None = None,
        base_id: str | None = None,
        table: str | None = None,
    ):
        self.token = token or os.environ["AIRTABLE_TOKEN"]
        self.base_id = base_id or os.environ["AIRTABLE_BASE_ID"]
        self.table = table or config.AIRTABLE_TABLE
        self._headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    @property
    def _url(self) -> str:
        return f"{API_BASE}/{self.base_id}/{self.table}"

    # ── Leitura ────────────────────────────────────────────────────────────

    def _list(self, params: dict) -> list[dict]:
        """Lista registos com paginação automática."""
        records: list[dict] = []
        offset = None
        while True:
            q = dict(params)
            if offset:
                q["offset"] = offset
            resp = requests.get(self._url, headers=self._headers, params=q, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            records.extend(data.get("records", []))
            offset = data.get("offset")
            if not offset:
                break
        return records

    def detect_convergence(self, ticker: str, signal_type: str) -> Convergence:
        """
        Verifica se o ticker teve outro sinal nas últimas 48h.

        `signal_type` é o tipo do sinal ACTUAL (ainda não escrito), usado
        apenas para decidir se os sinais anteriores são de tipo diferente.
        """
        window = config.CONVERGENCE_WINDOW_HOURS
        formula = (
            f"AND({{ticker}}='{ticker}',"
            f"IS_AFTER({{date}}, DATEADD(NOW(), -{window}, 'hours')))"
        )
        records = self._list({"filterByFormula": formula, "pageSize": 100})
        prior_types = [
            r["fields"].get("signal_type", "")
            for r in records
            if r.get("fields", {}).get("signal_type")
        ]
        detected = len(records) > 0
        distinct_types = any(t and t != signal_type for t in prior_types)
        return Convergence(
            detected=detected,
            distinct_types=distinct_types,
            prior_types=prior_types,
        )

    def recent_signals(self, hours: int = 24, min_score: int = 6) -> list[dict]:
        """
        Registos das últimas `hours` com raw_score >= min_score.
        Usado pelo briefing (min_score=6) e pela view de alta prioridade
        (min_score=8). Devolve os `fields` ordenados por score decrescente.
        """
        formula = (
            f"AND(IS_AFTER({{date}}, DATEADD(NOW(), -{hours}, 'hours')),"
            f"{{raw_score}} >= {min_score})"
        )
        records = self._list(
            {
                "filterByFormula": formula,
                "sort[0][field]": "raw_score",
                "sort[0][direction]": "desc",
            }
        )
        return [r.get("fields", {}) for r in records]

    # ── Escrita ──────────────────────────────────────────────────────────────

    def write_signal(self, fields: dict) -> str:
        """Cria um registo. Devolve o id do registo criado."""
        payload = {"records": [{"fields": fields}], "typecast": True}
        resp = requests.post(self._url, headers=self._headers, json=payload, timeout=30)
        resp.raise_for_status()
        return resp.json()["records"][0]["id"]


def _enrich_headline(signal: dict) -> str:
    """Enriquece a headline com dados estruturados de insider/options."""
    base = signal.get("headline", "")
    stype = signal.get("signal_type", "")

    if stype == "insider":
        parts = []
        name = signal.get("insider_name") or signal.get("insiderName")
        title = signal.get("insider_title") or signal.get("insiderTitle")
        amount = signal.get("insider_amount_usd") or signal.get("insiderAmountUsd")
        if name:
            parts.append(name)
        if title:
            parts.append(f"({title})")
        if amount:
            parts.append(f"${amount:,}")
        extra = " — " + " ".join(parts) if parts else ""
        return base + extra

    if stype == "options":
        parts = []
        otype = signal.get("options_type") or signal.get("optionsType")
        premium = signal.get("options_premium_usd") or signal.get("optionsPremiumUsd")
        if otype:
            parts.append(otype.upper())
        if premium:
            parts.append(f"${premium:,} premium")
        extra = " — " + " ".join(parts) if parts else ""
        return base + extra

    return base


def build_record(signal: dict, scored, convergence: bool, source: str) -> dict:
    """
    Constrói o dict de campos do Airtable a partir de um sinal classificado
    e do resultado do scoring (objecto ScoredSignal).
    """
    ticker = signal.get("ticker", "")
    entry_price = _fetch_price(ticker)
    record: dict = {
        "date": datetime.now(timezone.utc).isoformat(),
        "ticker": ticker,
        "signal_type": signal.get("signal_type", ""),
        "catalyst_strength": int(signal.get("catalyst_strength", 0)),
        "horizon": signal.get("horizon", ""),
        "durability_12h": bool(signal.get("durability_12h", False)),
        "convergence": bool(convergence),
        "headline": _enrich_headline(signal),
        "source": source,
        "raw_score": int(scored.final_score),
        "alerted": scored.priority == "high",
        "outcome": "open",
    }
    if entry_price is not None:
        record["entry_price"] = round(entry_price, 2)
        record["price_now"] = round(entry_price, 2)
        record["pnl_pct"] = 0.0
    return record
