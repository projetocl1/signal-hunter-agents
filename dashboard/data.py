"""
Camada de dados do dashboard.
Lê do Airtable via REST API e devolve DataFrames pandas prontos a usar.
Cache de 1h por defeito (DASHBOARD_CACHE_TTL env var em segundos).
"""
from __future__ import annotations

import os
from datetime import date
from typing import Any

import pandas as pd
import requests
import streamlit as st

_API_BASE = "https://api.airtable.com/v0"
_CACHE_TTL = int(os.environ.get("DASHBOARD_CACHE_TTL", "3600"))


def _headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {os.environ['AIRTABLE_TOKEN']}"}


def _list_records(formula: str = "", sort_field: str = "date", sort_dir: str = "desc") -> list[dict]:
    base = os.environ["AIRTABLE_BASE_ID"]
    table = os.environ.get("AIRTABLE_TABLE", "catalyst_signals")
    url = f"{_API_BASE}/{base}/{table}"
    params: dict[str, Any] = {
        "pageSize": 100,
        "sort[0][field]": sort_field,
        "sort[0][direction]": sort_dir,
    }
    if formula:
        params["filterByFormula"] = formula

    records: list[dict] = []
    offset: str | None = None
    while True:
        q = {**params, **({"offset": offset} if offset else {})}
        resp = requests.get(url, headers=_headers(), params=q, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        records.extend(data.get("records", []))
        offset = data.get("offset")
        if not offset:
            break
    return records


def _to_df(records: list[dict]) -> pd.DataFrame:
    if not records:
        return pd.DataFrame()
    df = pd.DataFrame([r.get("fields", {}) for r in records])

    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], utc=True)
        df["date_pt"] = df["date"].dt.tz_convert("Europe/Lisbon")
        df["date_only"] = df["date_pt"].dt.date

    for col in ("catalyst_strength", "raw_score", "entry_price", "price_now", "pnl_pct"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    for col in ("durability_12h", "convergence", "alerted"):
        if col in df.columns:
            df[col] = df[col].fillna(False).astype(bool)

    if "outcome" in df.columns:
        df["outcome"] = df["outcome"].fillna("open")
    else:
        df["outcome"] = "open"

    return df


@st.cache_data(ttl=_CACHE_TTL)
def load_signals(days: int = 30) -> pd.DataFrame:
    """Carrega sinais dos últimos `days` dias do Airtable."""
    formula = f"IS_AFTER({{date}}, DATEADD(NOW(), -{days * 24}, 'hours'))"
    return _to_df(_list_records(formula))


def load_signals_raw(days: int = 30) -> pd.DataFrame:
    """Versão sem cache — para a API FastAPI."""
    formula = f"IS_AFTER({{date}}, DATEADD(NOW(), -{days * 24}, 'hours'))"
    return _to_df(_list_records(formula))


def compute_kpis(df: pd.DataFrame) -> dict:
    """Calcula KPIs principais a partir do DataFrame completo."""
    if df.empty:
        return {
            "sinais_hoje": 0, "alta_prioridade_hoje": 0, "posicoes_abertas": 0,
            "hit_rate_pct": 0.0, "avg_pnl_pct": 0.0, "convergencias_ativas": 0, "total_sinais": 0,
        }
    today = date.today()
    today_df = df[df["date_only"] == today] if "date_only" in df.columns else df.iloc[0:0]
    open_df = df[df["outcome"] == "open"] if "outcome" in df.columns else df.iloc[0:0]
    closed_df = df[df["outcome"].isin(["hit", "stopped", "expired"])] if "outcome" in df.columns else df.iloc[0:0]
    hit_df = df[df["outcome"] == "hit"] if "outcome" in df.columns else df.iloc[0:0]

    total_closed = len(closed_df)
    hit_rate = len(hit_df) / total_closed * 100 if total_closed > 0 else 0.0
    avg_pnl = (
        float(closed_df["pnl_pct"].mean())
        if "pnl_pct" in closed_df.columns and not closed_df.empty and not closed_df["pnl_pct"].isna().all()
        else 0.0
    )

    return {
        "sinais_hoje": len(today_df),
        "alta_prioridade_hoje": int(today_df["alerted"].sum()) if "alerted" in today_df.columns and not today_df.empty else 0,
        "posicoes_abertas": len(open_df),
        "hit_rate_pct": round(hit_rate, 1),
        "avg_pnl_pct": round(avg_pnl if not pd.isna(avg_pnl) else 0.0, 2),
        "convergencias_ativas": int(open_df["convergence"].sum()) if "convergence" in open_df.columns else 0,
        "total_sinais": len(df),
    }
