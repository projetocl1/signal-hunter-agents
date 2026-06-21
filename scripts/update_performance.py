"""
Actualiza o cache de performance histórica e faz commit ao repositório.

Uso:
    python -m scripts.update_performance          # últimos 90 dias
    python -m scripts.update_performance --days 30
"""
from __future__ import annotations

import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

from core.performance_analyzer import compute_performance  # noqa: E402


def main() -> None:
    days = 90
    for arg in sys.argv[1:]:
        if arg.startswith("--days"):
            days = int(arg.split("=")[-1]) if "=" in arg else int(sys.argv[sys.argv.index(arg) + 1])

    print(f"[performance] a analisar últimos {days} dias...")
    cache = compute_performance(days=days)
    print(f"[performance] sinais fechados: {cache['total_closed']}")
    print(f"[performance] dados suficientes: {cache['sufficient_data']}")
    print(f"[performance] {cache['notes']}")

    if cache["sufficient_data"]:
        print("\n[performance] Top fontes:", cache.get("top_sources"))
        print("[performance] Top combinações:", cache.get("top_combinations"))
        print("\n[performance] Por tipo:")
        for t, v in cache.get("by_type", {}).items():
            print(f"  {t:12} hit_rate={v['hit_rate']:.0%}  total={v['total']}  avg_pnl={v['avg_pnl']:+.1f}%")
        print("\n[performance] Por fonte:")
        for s, v in list(cache.get("by_source", {}).items())[:5]:
            print(f"  {s:30} hit_rate={v['hit_rate']:.0%}  total={v['total']}")


if __name__ == "__main__":
    main()
