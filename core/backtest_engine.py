"""
Motor de backtest histórico.

Para cada evento histórico (headline + data + ticker + fonte), simula o que
o sistema teria feito: classifica, calcula score, e compara com o movimento
real do preço usando yfinance.

Resultado: BacktestResult com score simulado + P&L real em 4 horizontes.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import date, timedelta
from pathlib import Path

import anthropic

from . import config
from .classifier import classify
from .durability_check import evaluate
from .performance_analyzer import load_cache, performance_bonus

RESULTS_PATH = Path("data/backtest_results.json")

# Thresholds de hit (iguais ao outcome_tracker)
HIT_THRESHOLDS = {"3d": 5.0, "10d": 8.0, "30d": 15.0, "90d": 25.0}
STOP_LOSS_PCT = -7.0

HORIZON_DAYS = {"3d": 3, "10d": 10, "30d": 30, "90d": 90}


@dataclass
class BacktestResult:
    event_date: str           # YYYY-MM-DD
    ticker: str
    headline: str
    source: str
    notes: str                # contexto histórico do evento

    # O que o sistema teria feito
    signal_type: str
    catalyst_strength: int
    horizon: str
    durability_12h: bool
    final_score: int
    would_alert: bool         # score >= 8
    would_keep: bool          # score >= 6

    # Preços reais (yfinance)
    price_entry: float | None
    price_3d: float | None
    price_10d: float | None
    price_30d: float | None
    price_90d: float | None

    # P&L calculado
    pnl_3d: float | None
    pnl_10d: float | None
    pnl_30d: float | None
    pnl_90d: float | None

    # Hit/miss para o horizonte classificado
    hit: bool | None          # atingiu o threshold no horizonte classificado?
    stopped: bool | None      # activou stop loss antes de atingir target?

    error: str | None = None  # se houve erro na avaliação


def _fetch_price(ticker: str, target: date) -> float | None:
    """Preço de fecho no ou após target (salta fins de semana e feriados)."""
    try:
        import yfinance as yf
        end = target + timedelta(days=10)
        hist = yf.Ticker(ticker).history(
            start=target.isoformat(), end=end.isoformat()
        )
        if hist.empty:
            return None
        return round(float(hist["Close"].iloc[0]), 2)
    except Exception:
        return None


def _pnl(entry: float | None, exit_: float | None) -> float | None:
    if entry is None or exit_ is None or entry == 0:
        return None
    return round((exit_ - entry) / entry * 100, 2)


def evaluate_event(client: anthropic.Anthropic, event: dict) -> BacktestResult:
    """
    Avalia um evento histórico como se tivesse sido detectado em tempo real.
    Devolve BacktestResult com score simulado + preços reais.
    """
    ticker = event["ticker"]
    headline = event["headline"]
    source = event.get("source", "benzinga.com")
    event_date = date.fromisoformat(event["event_date"])
    notes = event.get("notes", "")

    # --- Classificação ---
    try:
        cls = classify(
            client,
            headline=headline,
            source=source,
            context=notes,
            ticker_hint=ticker,
        )
    except Exception as exc:
        return BacktestResult(
            event_date=event["event_date"], ticker=ticker, headline=headline,
            source=source, notes=notes,
            signal_type="", catalyst_strength=0, horizon="3d",
            durability_12h=False, final_score=0,
            would_alert=False, would_keep=False,
            price_entry=None, price_3d=None, price_10d=None,
            price_30d=None, price_90d=None,
            pnl_3d=None, pnl_10d=None, pnl_30d=None, pnl_90d=None,
            hit=None, stopped=None, error=str(exc),
        )

    signal = cls.model_dump()
    signal["headline"] = headline
    signal["source"] = source

    # --- Scoring (sem convergência — backtest individual) ---
    scored = evaluate(signal, convergence=False)

    # --- Preços reais ---
    p0 = _fetch_price(ticker, event_date)
    p3 = _fetch_price(ticker, event_date + timedelta(days=HORIZON_DAYS["3d"]))
    p10 = _fetch_price(ticker, event_date + timedelta(days=HORIZON_DAYS["10d"]))
    p30 = _fetch_price(ticker, event_date + timedelta(days=HORIZON_DAYS["30d"]))
    p90 = _fetch_price(ticker, event_date + timedelta(days=HORIZON_DAYS["90d"]))

    pnl3 = _pnl(p0, p3)
    pnl10 = _pnl(p0, p10)
    pnl30 = _pnl(p0, p30)
    pnl90 = _pnl(p0, p90)

    # --- Hit/stop para o horizonte classificado ---
    horizon = cls.horizon
    threshold = HIT_THRESHOLDS.get(horizon, 8.0)
    pnl_at_horizon = {"3d": pnl3, "10d": pnl10, "30d": pnl30, "90d": pnl90}.get(horizon)

    hit = None
    stopped = None
    if pnl_at_horizon is not None:
        if pnl_at_horizon >= threshold:
            hit = True
            stopped = False
        elif pnl_at_horizon <= STOP_LOSS_PCT:
            hit = False
            stopped = True
        else:
            hit = False
            stopped = False

    return BacktestResult(
        event_date=event["event_date"],
        ticker=ticker,
        headline=headline,
        source=source,
        notes=notes,
        signal_type=cls.signal_type,
        catalyst_strength=cls.catalyst_strength,
        horizon=cls.horizon,
        durability_12h=cls.durability_12h,
        final_score=scored.final_score,
        would_alert=scored.priority == "high",
        would_keep=scored.kept,
        price_entry=p0,
        price_3d=p3,
        price_10d=p10,
        price_30d=p30,
        price_90d=p90,
        pnl_3d=pnl3,
        pnl_10d=pnl10,
        pnl_30d=pnl30,
        pnl_90d=pnl90,
        hit=hit,
        stopped=stopped,
    )


def save_results(results: list[BacktestResult]) -> None:
    RESULTS_PATH.parent.mkdir(exist_ok=True)
    data = [asdict(r) for r in results]
    with open(RESULTS_PATH, "w") as f:
        json.dump(data, f, indent=2, default=str)


def load_results() -> list[dict]:
    if not RESULTS_PATH.exists():
        return []
    with open(RESULTS_PATH) as f:
        return json.load(f)
