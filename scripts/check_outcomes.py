"""
Actualiza o desfecho de todos os sinais abertos no Airtable.

Uso:
    python -m scripts.check_outcomes           # actualiza no Airtable
    python -m scripts.check_outcomes --dry-run # só mostra, não escreve
"""

from __future__ import annotations

import sys

from core.outcome_tracker import run_update


def main() -> None:
    dry_run = "--dry-run" in sys.argv
    if dry_run:
        print("[check_outcomes] modo dry-run — sem escrita no Airtable")
    run_update(dry_run=dry_run)


if __name__ == "__main__":
    main()
