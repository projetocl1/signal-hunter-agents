"""
Signal Hunter — REST API.

Execução:
    uvicorn api.main:app --reload --port 8000

Documentação interactiva: http://localhost:8000/docs
"""
from __future__ import annotations

import os
from datetime import date
from typing import Optional

import pandas as pd
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

# Importar depois do load_dotenv para garantir que env vars estão disponíveis
from dashboard.data import compute_kpis, load_signals_raw  # noqa: E402

app = FastAPI(
    title="Signal Hunter API",
    description="REST API para acesso aos sinais de catalisadores e métricas de performance.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


def _df_to_records(df: pd.DataFrame) -> list[dict]:
    """Converte DataFrame para lista de dicts serializável em JSON."""
    if df.empty:
        return []
    out = df.copy()
    # Remover colunas de trabalho internas
    for col in ("date_pt", "date_only"):
        if col in out.columns:
            out = out.drop(columns=[col])
    # Converter timestamps para string ISO
    if "date" in out.columns:
        out["date"] = out["date"].astype(str)
    return out.where(pd.notnull(out), None).to_dict(orient="records")


@app.get("/health")
def health():
    """Verifica se a API está operacional."""
    return {"status": "ok", "date": str(date.today())}


@app.get("/api/signals/summary")
def get_summary(days: int = Query(30, ge=1, le=365, description="Período em dias")):
    """
    Retorna KPIs principais: sinais hoje, taxa de acerto, P&L médio, etc.
    """
    try:
        df = load_signals_raw(days)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Erro Airtable: {e}")
    return {"period_days": days, "kpis": compute_kpis(df)}


@app.get("/api/signals")
def get_signals(
    days: int = Query(30, ge=1, le=365, description="Período em dias"),
    signal_type: Optional[str] = Query(None, description="Filtrar por tipo: analyst|earnings|product|macro|rotation"),
    outcome: Optional[str] = Query(None, description="Filtrar por estado: open|hit|stopped|expired"),
    horizon: Optional[str] = Query(None, description="Filtrar por horizonte: 3d|10d|30d|90d"),
    min_score: int = Query(0, ge=0, le=13, description="Score mínimo"),
    convergence_only: bool = Query(False, description="Apenas sinais com convergência"),
):
    """
    Lista sinais com filtros opcionais.
    Ordenados por data descendente.
    """
    try:
        df = load_signals_raw(days)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Erro Airtable: {e}")

    if df.empty:
        return {"total": 0, "signals": []}

    if "raw_score" in df.columns:
        df = df[df["raw_score"] >= min_score]
    if signal_type and "signal_type" in df.columns:
        df = df[df["signal_type"] == signal_type]
    if outcome and "outcome" in df.columns:
        df = df[df["outcome"] == outcome]
    if horizon and "horizon" in df.columns:
        df = df[df["horizon"] == horizon]
    if convergence_only and "convergence" in df.columns:
        df = df[df["convergence"] == True]

    return {"total": len(df), "signals": _df_to_records(df)}


@app.get("/api/signals/active")
def get_active(
    days: int = Query(30, ge=1, le=365),
    min_score: int = Query(0, ge=0, le=13),
):
    """
    Lista posições abertas (outcome = open), ordenadas por score descendente.
    Inclui P&L actual de cada posição.
    """
    try:
        df = load_signals_raw(days)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Erro Airtable: {e}")

    if df.empty:
        return {"total": 0, "signals": []}

    active = df[df["outcome"] == "open"].copy()
    if "raw_score" in active.columns:
        active = active[active["raw_score"] >= min_score]
        active = active.sort_values("raw_score", ascending=False)

    return {"total": len(active), "signals": _df_to_records(active)}


@app.get("/api/signals/performance")
def get_performance(days: int = Query(90, ge=1, le=365)):
    """
    Métricas de performance agrupadas por tipo de sinal e horizonte.
    Inclui hit rate, P&L médio e número de sinais.
    """
    try:
        df = load_signals_raw(days)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Erro Airtable: {e}")

    closed = df[df["outcome"].isin(["hit", "stopped", "expired"])]
    if closed.empty:
        return {"period_days": days, "by_type": [], "by_horizon": []}

    def _perf(group_col: str) -> list[dict]:
        if group_col not in closed.columns:
            return []
        result = []
        for key, grp in closed.groupby(group_col):
            total = len(grp)
            hits = (grp["outcome"] == "hit").sum()
            avg_pnl = float(grp["pnl_pct"].mean()) if "pnl_pct" in grp.columns and not grp["pnl_pct"].isna().all() else None
            result.append({
                group_col: key,
                "total": total,
                "hit": int(hits),
                "stopped": int((grp["outcome"] == "stopped").sum()),
                "expired": int((grp["outcome"] == "expired").sum()),
                "hit_rate_pct": round(hits / total * 100, 1),
                "avg_pnl_pct": round(avg_pnl, 2) if avg_pnl is not None else None,
            })
        return sorted(result, key=lambda x: x["hit_rate_pct"], reverse=True)

    return {
        "period_days": days,
        "by_type": _perf("signal_type"),
        "by_horizon": _perf("horizon"),
    }


@app.get("/api/signals/convergences")
def get_convergences(days: int = Query(7, ge=1, le=90)):
    """
    Lista sinais com convergência detectada no período,
    agrupados por ticker.
    """
    try:
        df = load_signals_raw(days)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Erro Airtable: {e}")

    if df.empty or "convergence" not in df.columns:
        return {"total": 0, "convergences": []}

    conv = df[df["convergence"] == True].copy()
    if conv.empty:
        return {"total": 0, "convergences": []}

    # Agrupar por ticker para mostrar quantos tipos diferentes
    grouped = []
    if "ticker" in conv.columns:
        for ticker, grp in conv.groupby("ticker"):
            types = grp["signal_type"].unique().tolist() if "signal_type" in grp.columns else []
            grouped.append({
                "ticker": ticker,
                "signal_count": len(grp),
                "signal_types": types,
                "distinct_types": len(types),
                "max_score": int(grp["raw_score"].max()) if "raw_score" in grp.columns else None,
                "outcomes": grp["outcome"].value_counts().to_dict(),
            })
        grouped = sorted(grouped, key=lambda x: x["distinct_types"], reverse=True)

    return {"total": len(conv), "convergences": grouped}
