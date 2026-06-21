"""
Analisa performance histórica dos sinais fechados (hit/stopped/expired)
e gera pesos adaptativos para melhorar scoring futuro.

O resultado é guardado em data/performance_cache.json e lido pelo
pipeline antes de cada scan. Com menos de MIN_CLOSED sinais fechados,
o sistema usa pesos neutros (sem ajuste).
"""
from __future__ import annotations

import json
import os
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from .airtable_writer import AirtableClient

MIN_CLOSED = 10          # mínimo de sinais fechados para activar pesos adaptativos
PERF_BONUS_MAX = 2       # bónus máximo por sinal (em cima do scoring base)
HIT_RATE_SOURCE = 0.65   # hit rate mínima de uma fonte para receber +1
HIT_RATE_TYPE = 0.60     # hit rate mínima de tipo+horizonte para receber +1

CACHE_PATH = Path(__file__).parent.parent / "data" / "performance_cache.json"


def _empty_cache() -> dict:
    return {
        "generated_at": None,
        "total_closed": 0,
        "sufficient_data": False,
        "by_source": {},
        "by_type": {},
        "by_horizon": {},
        "by_type_horizon": {},
        "top_sources": [],
        "top_combinations": [],
        "notes": "Sem dados suficientes — pesos neutros activos.",
    }


def _hit_rate(counts: dict) -> float:
    total = counts.get("hit", 0) + counts.get("stopped", 0) + counts.get("expired", 0)
    return counts.get("hit", 0) / total if total > 0 else 0.0


def _avg_pnl(pnls: list[float]) -> float:
    return round(sum(pnls) / len(pnls), 2) if pnls else 0.0


def compute_performance(days: int = 90) -> dict:
    """
    Lê todos os sinais fechados do Airtable e calcula métricas de performance.
    Devolve o dict de cache (também escreve em CACHE_PATH).
    """
    at = AirtableClient()
    formula = (
        f"AND(IS_AFTER({{date}}, DATEADD(NOW(), -{days * 24}, 'hours')),"
        "OR({outcome}='hit',{outcome}='stopped',{outcome}='expired'))"
    )
    records = at._list({"filterByFormula": formula, "pageSize": 100})
    closed = [r.get("fields", {}) for r in records]

    if len(closed) < MIN_CLOSED:
        cache = _empty_cache()
        cache["total_closed"] = len(closed)
        cache["notes"] = (
            f"Apenas {len(closed)} sinais fechados (mínimo: {MIN_CLOSED}). "
            "Pesos neutros activos — sistema aprenderá com mais dados."
        )
        _save(cache)
        return cache

    # ── Acumular contagens por dimensão ───────────────────────────────────
    by_source: dict = defaultdict(lambda: defaultdict(int))
    by_type: dict = defaultdict(lambda: defaultdict(int))
    by_horizon: dict = defaultdict(lambda: defaultdict(int))
    by_combo: dict = defaultdict(lambda: defaultdict(int))
    pnl_source: dict = defaultdict(list)
    pnl_type: dict = defaultdict(list)
    pnl_combo: dict = defaultdict(list)

    for f in closed:
        outcome = f.get("outcome", "")
        source = f.get("source", "desconhecido")
        stype = f.get("signal_type", "desconhecido")
        horizon = f.get("horizon", "desconhecido")
        combo = f"{stype}+{horizon}"
        pnl = f.get("pnl_pct") or 0.0

        by_source[source][outcome] += 1
        by_type[stype][outcome] += 1
        by_horizon[horizon][outcome] += 1
        by_combo[combo][outcome] += 1
        pnl_source[source].append(pnl)
        pnl_type[stype].append(pnl)
        pnl_combo[combo].append(pnl)

    # ── Calcular hit rates e pesos ─────────────────────────────────────────
    def _enrich(counts_dict: dict, pnl_dict: dict) -> dict:
        result = {}
        for key, counts in counts_dict.items():
            hr = _hit_rate(counts)
            result[key] = {
                **counts,
                "total": sum(counts.values()),
                "hit_rate": round(hr, 3),
                "avg_pnl": _avg_pnl(pnl_dict.get(key, [])),
            }
        return dict(sorted(result.items(), key=lambda x: x[1]["hit_rate"], reverse=True))

    src_stats = _enrich(by_source, pnl_source)
    type_stats = _enrich(by_type, pnl_type)
    horizon_stats = _enrich(by_horizon, {})
    combo_stats = _enrich(by_combo, pnl_combo)

    top_sources = [k for k, v in src_stats.items() if v["hit_rate"] >= HIT_RATE_SOURCE]
    top_combos = [k for k, v in combo_stats.items() if v["hit_rate"] >= HIT_RATE_TYPE]

    cache = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_closed": len(closed),
        "sufficient_data": True,
        "by_source": src_stats,
        "by_type": type_stats,
        "by_horizon": horizon_stats,
        "by_type_horizon": combo_stats,
        "top_sources": top_sources,
        "top_combinations": top_combos,
        "notes": (
            f"Baseado em {len(closed)} sinais fechados nos últimos {days} dias. "
            f"Fontes de alta performance: {top_sources or 'nenhuma ainda'}. "
            f"Combinações de alta performance: {top_combos or 'nenhuma ainda'}."
        ),
    }
    _save(cache)
    return cache


def _save(cache: dict) -> None:
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CACHE_PATH.write_text(json.dumps(cache, indent=2, ensure_ascii=False))


def load_cache() -> dict:
    """Carrega cache de performance. Devolve cache neutro se não existir."""
    if not CACHE_PATH.exists():
        return _empty_cache()
    try:
        return json.loads(CACHE_PATH.read_text())
    except Exception:
        return _empty_cache()


def performance_bonus(signal_type: str, horizon: str, source: str) -> int:
    """
    Devolve bónus de performance (0-2) baseado no historial.
    Só activo quando sufficient_data=True.
    """
    cache = load_cache()
    if not cache.get("sufficient_data"):
        return 0

    bonus = 0
    if source in cache.get("top_sources", []):
        bonus += 1
    combo = f"{signal_type}+{horizon}"
    if combo in cache.get("top_combinations", []):
        bonus += 1
    return min(bonus, PERF_BONUS_MAX)
