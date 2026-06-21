"""
afternoon_scan — 14:00 UTC.

Foco: sector rotation detector + macro updates.
"""

from __future__ import annotations

from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

from agents import run_scan

FOCUS = (
    "Rotação sectorial: usa Slickcharts para identificar sectores cujo líder "
    "subiu >= 10% e detecta laggards do mesmo sector como candidatos. "
    "Adicionalmente, updates macro e geopolíticos da Reuters com impacto "
    "potencial em tickers NASDAQ. Foco em rotação ('rotation') e 'macro'."
)


def main() -> None:
    print("=== afternoon_scan (14:00 UTC) ===")
    run_scan(FOCUS, expand=False)


if __name__ == "__main__":
    main()
