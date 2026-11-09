"""
Gerador do briefing diário em Markdown.

Produzido pelo close_scan (21:00 UTC). Lê os sinais do dia (Airtable, últimas
24h, raw_score >= 6) e escreve um ficheiro markdown no repositório.

Secções:
  🔴 Alta Prioridade (score >= 8)
  🟡 Monitorização (score 6-7)
  📊 Stats do dia

Formato alinhado com o briefing.py do pharma-intel (mesma estrutura de
secções e tom), mas este repositório é totalmente independente.
"""

from __future__ import annotations

import os
from collections import Counter
from datetime import datetime, timezone

from . import config

BRIEFINGS_DIR = "briefings"


def _row(fields: dict) -> str:
    """Linha de tabela markdown para um sinal."""
    ticker = fields.get("ticker", "?")
    stype = fields.get("signal_type", "?")
    score = fields.get("raw_score", 0)
    horizon = fields.get("horizon", "?")
    conv = "✅" if fields.get("convergence") else "—"
    source = fields.get("source", "?")
    headline = (fields.get("headline", "") or "").replace("|", "/")
    return (
        f"| {ticker} | {stype} | {score} | {horizon} | {conv} | "
        f"{source} | {headline} |"
    )


_TABLE_HEADER = (
    "| Ticker | Tipo | Score | Horizonte | Conv. | Fonte | Headline |\n"
    "|--------|------|-------|-----------|-------|-------|----------|"
)


def build_briefing(signals: list[dict], now: datetime | None = None) -> str:
    """Constrói o markdown do briefing a partir dos sinais (fields do Airtable)."""
    now = now or datetime.now(timezone.utc)
    date_str = now.strftime("%Y-%m-%d")

    high = [s for s in signals if int(s.get("raw_score", 0)) >= config.SCORE_HIGH_PRIORITY]
    monitor = [
        s
        for s in signals
        if config.SCORE_MONITOR_MIN
        <= int(s.get("raw_score", 0))
        < config.SCORE_HIGH_PRIORITY
    ]

    lines: list[str] = []
    lines.append(f"# 📡 Signal Hunter — Briefing Diário {date_str}")
    lines.append("")
    lines.append(f"_Gerado {now.strftime('%Y-%m-%d %H:%M UTC')} · close_scan_")
    lines.append("")

    # 🔴 Alta Prioridade
    lines.append("## 🔴 Alta Prioridade (score >= 8)")
    lines.append("")
    if high:
        lines.append(_TABLE_HEADER)
        lines.extend(_row(s) for s in high)
    else:
        lines.append("_Sem sinais de alta prioridade hoje._")
    lines.append("")

    # 🟡 Monitorização
    lines.append("## 🟡 Monitorização (score 6-7)")
    lines.append("")
    if monitor:
        lines.append(_TABLE_HEADER)
        lines.extend(_row(s) for s in monitor)
    else:
        lines.append("_Sem sinais de monitorização hoje._")
    lines.append("")

    # 📊 Stats
    by_type = Counter(s.get("signal_type", "?") for s in signals)
    conv_count = sum(1 for s in signals if s.get("convergence"))
    lines.append("## 📊 Stats do dia")
    lines.append("")
    lines.append(f"- **Total de sinais (score >= 6):** {len(signals)}")
    lines.append(f"- **Alta prioridade (>= 8):** {len(high)}")
    lines.append(f"- **Monitorização (6-7):** {len(monitor)}")
    lines.append(f"- **Convergências detectadas:** {conv_count}")
    if by_type:
        dist = ", ".join(f"{k}={v}" for k, v in sorted(by_type.items()))
        lines.append(f"- **Por tipo:** {dist}")
    lines.append("")

    return "\n".join(lines)


def write_briefing(markdown: str, now: datetime | None = None) -> str:
    """Escreve o briefing em briefings/YYYY-MM-DD.md e devolve o caminho."""
    now = now or datetime.now(timezone.utc)
    os.makedirs(BRIEFINGS_DIR, exist_ok=True)
    path = os.path.join(BRIEFINGS_DIR, f"{now.strftime('%Y-%m-%d')}.md")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(markdown)
    return path
