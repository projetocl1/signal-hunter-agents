"""
Filtro de durabilidade e cálculo de score final.

Regras (ver config.py):
  1. durability_12h == False  → descarta SEMPRE (o operador entra 12h após o
     sinal; se o catalisador já não estiver válido nessa altura, é ruído).
  2. score base = catalyst_strength (1-10), dado pelo classificador.
  3. convergence_detected == True → +CONVERGENCE_BONUS pontos.
  4. score final >= 8  → alta prioridade ("high")
     score final 6-7  → monitorização ("monitor")
     score final < 6  → descarta ("discard")

A convergência NÃO é decidida pelo classificador: é determinada
consultando o Airtable (mesmo ticker, outro sinal nas últimas 48h).
Por isso este módulo recebe `convergence` como argumento explícito.
"""

from __future__ import annotations

from dataclasses import dataclass

from . import config


@dataclass
class ScoredSignal:
    """Resultado da avaliação de um sinal classificado."""

    kept: bool                 # passou o filtro de durabilidade + score >= 6?
    priority: str              # "high" | "monitor" | "discard"
    raw_score: int             # catalyst_strength antes do bónus
    final_score: int           # raw_score + bónus de convergência
    convergence: bool          # convergência confirmada via Airtable
    reason: str                # explicação curta da decisão


def evaluate(signal: dict, convergence: bool) -> ScoredSignal:
    """
    Avalia um sinal já classificado pela Claude.

    `signal` é o dict produzido pelo classifier (ticker, signal_type,
    catalyst_strength, horizon, durability_12h, reasoning, ...).
    `convergence` vem da consulta ao Airtable (não do classificador).
    """
    strength = int(signal.get("catalyst_strength", 0))

    # Regra 1 — durabilidade é eliminatória.
    if not signal.get("durability_12h", False):
        return ScoredSignal(
            kept=False,
            priority="discard",
            raw_score=strength,
            final_score=strength,
            convergence=convergence,
            reason="durability_12h=False — sinal não sobrevive 12h, descartado.",
        )

    # Regras 2 + 3 — score base + bónus de convergência.
    final_score = strength + (config.CONVERGENCE_BONUS if convergence else 0)

    # Regra 4 — thresholds.
    if final_score >= config.SCORE_HIGH_PRIORITY:
        priority, kept = "high", True
        reason = "Score alto — briefing de alta prioridade."
    elif final_score >= config.SCORE_MONITOR_MIN:
        priority, kept = "monitor", True
        reason = "Score de monitorização — registado para acompanhamento."
    else:
        priority, kept = "discard", False
        reason = f"Score final {final_score} < {config.SCORE_MONITOR_MIN} — descartado."

    if convergence and kept:
        reason += " Convergência detectada (+%d)." % config.CONVERGENCE_BONUS

    return ScoredSignal(
        kept=kept,
        priority=priority,
        raw_score=strength,
        final_score=final_score,
        convergence=convergence,
        reason=reason,
    )
