"""
Validação de setup — corre ANTES de activar os schedulers.

Verifica:
  1. Variáveis de ambiente presentes.
  2. Claude API responde (mensagem mínima).
  3. Airtable acessível e a tabela tem os campos esperados (escreve + apaga
     um registo de teste).

Uso (local, com .env exportado):
    python -m scripts.validate_setup
"""

from __future__ import annotations

import os
import sys

REQUIRED_ENV = ["ANTHROPIC_API_KEY", "AIRTABLE_TOKEN", "AIRTABLE_BASE_ID"]
EXPECTED_FIELDS = [
    "date", "ticker", "signal_type", "catalyst_strength", "horizon",
    "durability_12h", "convergence", "headline", "source", "raw_score", "alerted",
]


def check_env() -> bool:
    missing = [k for k in REQUIRED_ENV if not os.environ.get(k)]
    if missing:
        print(f"✗ env em falta: {', '.join(missing)}")
        return False
    print("✓ variáveis de ambiente presentes")
    return True


def check_claude() -> bool:
    import anthropic
    from core import config

    client = anthropic.Anthropic()
    resp = client.messages.create(
        model=config.CLAUDE_MODEL,
        max_tokens=16,
        messages=[{"role": "user", "content": "Responde apenas: OK"}],
    )
    text = "".join(b.text for b in resp.content if getattr(b, "type", "") == "text")
    print(f"✓ Claude API responde ({resp.model}): {text.strip()!r}")
    return True


def check_airtable() -> bool:
    import requests

    from core.airtable_writer import AirtableClient
    from datetime import datetime, timezone

    at = AirtableClient()
    # Escreve um registo de teste com todos os campos e apaga-o em seguida.
    test_fields = {
        "date": datetime.now(timezone.utc).isoformat(),
        "ticker": "TESTE",
        "signal_type": "analyst",
        "catalyst_strength": 1,
        "horizon": "3d",
        "durability_12h": False,
        "convergence": False,
        "headline": "registo de validação (apagar)",
        "source": "validate_setup",
        "raw_score": 0,
        "alerted": False,
    }
    rec_id = at.write_signal(test_fields)
    print(f"✓ Airtable: escrita OK ({rec_id})")

    # Apaga o registo de teste.
    url = f"{at._url}/{rec_id}"
    resp = requests.delete(url, headers=at._headers, timeout=30)
    resp.raise_for_status()
    print("✓ Airtable: leitura/escrita/remoção OK; campos aceites")
    print(f"  (campos esperados: {', '.join(EXPECTED_FIELDS)})")
    return True


def main() -> int:
    ok = check_env()
    if not ok:
        return 1
    try:
        check_claude()
        check_airtable()
    except Exception as exc:  # noqa: BLE001
        print(f"✗ validação falhou: {exc}")
        return 1
    print("\n✅ Setup válido — pronto para activar os schedulers.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
