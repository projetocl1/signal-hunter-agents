"""
Classificador de notícias via Claude API.

Recebe uma notícia (headline + contexto + fonte) e devolve a classificação
estruturada exigida pelo sistema. A saída é forçada por um schema Pydantic
através de `client.messages.parse()`, pelo que é sempre JSON válido.

Nota: `convergence_detected` é produzido pelo modelo como melhor estimativa,
mas a convergência AUTORITATIVA é recalculada a partir do Airtable em
airtable_writer.detect_convergence(). O pipeline usa sempre a do Airtable.
"""

from __future__ import annotations

from typing import Literal

import anthropic
from pydantic import BaseModel, Field

from . import config

# ── Schema de saída ────────────────────────────────────────────────────────


class Classification(BaseModel):
    """Estrutura exacta do output pedido na spec."""

    ticker: str = Field(description="Símbolo do ticker, ex: NVDA")
    signal_type: Literal["analyst", "earnings", "product", "macro", "rotation"]
    catalyst_strength: int = Field(ge=1, le=10, description="Força 1-10")
    horizon: Literal["3d", "10d", "30d", "90d"]
    durability_12h: bool = Field(
        description="O catalisador continua válido 12h após detecção?"
    )
    convergence_detected: bool = Field(
        description="Estimativa do modelo (a convergência real vem do Airtable)"
    )
    reasoning: str = Field(description="Máximo 2 frases")


# ── Prompt ──────────────────────────────────────────────────────────────────

_SYSTEM = f"""És um analista de catalisadores de mercado para swing trading na NYSE/NASDAQ.
O operador entra em posição 12 HORAS após receber o sinal, por isso só
interessam catalisadores que permaneçam válidos nesse horizonte.

PASSAM O FILTRO (durability_12h=true só se for um destes e com números concretos):
{chr(10).join("- " + c for c in config.CATALYSTS_PASS)}

NÃO PASSAM (durability_12h=false):
{chr(10).join("- " + c for c in config.CATALYSTS_REJECT)}

REGRAS DE CLASSIFICAÇÃO:
- catalyst_strength: 1-10 conforme a força e a credibilidade do catalisador.
- horizon: prazo provável de impacto (3d/10d/30d/90d).
- durability_12h: false se for ruído, rumor não confirmado, in-line, ou
  marketing sem números. Em caso de dúvida sobre durabilidade, devolve false.
- convergence_detected: a tua melhor estimativa de se há outro sinal recente
  no mesmo ticker (será confirmado depois contra a base de dados).
- reasoning: no máximo 2 frases, em português.

Sê conservador: é preferível descartar (durability_12h=false) do que deixar
passar ruído."""


def classify(
    client: anthropic.Anthropic,
    headline: str,
    source: str,
    context: str = "",
    ticker_hint: str = "",
) -> Classification:
    """Classifica uma única notícia e devolve um objecto Classification."""
    user = f"FONTE: {source}\n"
    if ticker_hint:
        user += f"TICKER (sugerido): {ticker_hint}\n"
    user += f"HEADLINE: {headline}\n"
    if context:
        user += f"\nCONTEXTO:\n{context}\n"
    user += "\nClassifica esta notícia segundo o schema."

    response = client.messages.parse(
        model=config.CLAUDE_MODEL,
        max_tokens=1024,
        system=_SYSTEM,
        messages=[{"role": "user", "content": user}],
        output_format=Classification,
    )

    parsed = response.parsed_output
    if parsed is None:
        raise RuntimeError(
            f"Classificação falhou (stop_reason={response.stop_reason}) para: {headline!r}"
        )
    return parsed
