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
    signal_type: Literal["analyst", "earnings", "product", "macro", "rotation", "insider", "options"]
    catalyst_strength: int = Field(ge=1, le=10, description="Força 1-10")
    horizon: Literal["3d", "10d", "30d", "90d"]
    durability_12h: bool = Field(
        description="O catalisador continua válido 12h após detecção?"
    )
    convergence_detected: bool = Field(
        description="Estimativa do modelo (a convergência real vem do Airtable)"
    )
    reasoning: str = Field(description="Máximo 2 frases")
    # campos opcionais para insider e options (None quando não aplicável)
    insider_name: str | None = Field(default=None, description="Nome do insider (CEO, CFO, Director)")
    insider_title: str | None = Field(default=None, description="Título do insider")
    insider_amount_usd: int | None = Field(default=None, description="Valor em USD da compra de insider")
    options_premium_usd: int | None = Field(default=None, description="Premium total em USD do fluxo de opções")
    options_type: Literal["call", "put"] | None = Field(default=None, description="Tipo de opção")


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

REGRAS ESPECÍFICAS — signal_type="insider":
- Usa APENAS para open-market purchases confirmadas (Form 4 SEC filing).
- Exclui: option exercises, planned 10b5-1, vendas, heranças.
- horizon = 30d se compra isolada; 90d se cluster (2+ insiders no mesmo mês).
- catalyst_strength:
    10 = CEO/CFO/Founder comprou >$1M ou cluster de 3+ insiders
    8-9 = C-suite comprou $500K-$1M ou cluster de 2 insiders
    6-7 = Director comprou $200K-$500K
    ≤5  = <$200K ou título não executivo
- Preenche insider_name, insider_title, insider_amount_usd.

REGRAS ESPECÍFICAS — signal_type="options":
- Usa APENAS para fluxo incomum confirmado: sweeps, blocos grandes OTM,
  volume/OI > 5x. Não classificar hedges de índices ou cobertura rotineira.
- horizon = 3d para opções com expiry < 2 semanas; 10d para 2-6 semanas.
- catalyst_strength:
    10 = Sweep >$1M OTM, expiry < 2 semanas, volume/OI >10x
    8-9 = Bloco >$500K OTM, ou sweep cruzado multi-exchange
    6-7 = Bloco $200K-$500K, ou calls OTM moderadas
    ≤5  = <$200K, ou contexto ambíguo
- Preenche options_premium_usd, options_type.

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
