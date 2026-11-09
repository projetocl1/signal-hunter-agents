"""
Recolha de notícias navegando directamente as fontes.

Em GitHub Actions não há browser interactivo, por isso a "navegação directa"
é feita pela ferramenta de web search da Claude API (`web_search_20260209`),
restrita à allowlist de domínios em config.SOURCE_DOMAINS. O agente pesquisa,
lê os resultados e devolve uma lista de candidatos a catalisador.

Cada candidato é um dict: {ticker, headline, source, url, summary, published}.
A classificação/scoring acontece depois (classifier + durability_check).
"""

from __future__ import annotations

import json
import re

import anthropic

from . import config

WEB_SEARCH_TOOL = {"type": "web_search_20260209", "name": "web_search"}


def _extract_json_array(text: str) -> list[dict]:
    """Extrai o primeiro array JSON de um bloco de texto, de forma tolerante."""
    if not text:
        return []
    # Remove cercas de código markdown, se existirem.
    text = re.sub(r"```(?:json)?", "", text).strip()
    start = text.find("[")
    end = text.rfind("]")
    if start == -1 or end == -1 or end <= start:
        return []
    try:
        data = json.loads(text[start : end + 1])
        return data if isinstance(data, list) else []
    except json.JSONDecodeError:
        return []


def fetch_news(
    client: anthropic.Anthropic,
    focus: str,
    universe: list[str] | None = None,
    max_items: int = 25,
    max_turns: int = 6,
) -> list[dict]:
    """
    Navega as fontes e devolve candidatos a catalisador.

    `focus` descreve o que procurar (ex: "analyst upgrades overnight + SEC 8-K
    das últimas 8h"). `universe` é a lista de tickers a priorizar (opcional).
    """
    sources_desc = "\n".join(f"- {d}: {desc}" for d, desc in config.SOURCES.items())
    universe_line = ""
    if universe:
        universe_line = (
            "\nPRIORIZA tickers deste universo (mas aceita outros relevantes):\n"
            + ", ".join(universe[:120])
        )

    system = (
        "És um agente de rastreamento de catalisadores de mercado para swing "
        "trading NASDAQ/NYSE. Navegas fontes financeiras e extrais notícias "
        "concretas com potencial de catalisador, com NÚMEROS sempre que possível."
    )

    user = f"""Procura nas seguintes fontes:
{sources_desc}

FOCO desta passagem:
{focus}
{universe_line}

Faz as pesquisas necessárias (usa a ferramenta de web search) e devolve
APENAS um array JSON, sem texto à volta, com no máximo {max_items} itens.
Cada item:
{{
  "ticker": "SÍMBOLO ou \\"\\" se desconhecido",
  "headline": "título factual e curto",
  "source": "domínio da fonte, ex: benzinga.com",
  "url": "link directo se disponível",
  "summary": "1-2 frases com os números relevantes",
  "published": "data/hora aproximada se disponível"
}}

Inclui apenas notícias plausíveis como catalisador (upgrades, price targets,
earnings beats, FDA/PDUFA, deals >= $100M, novos produtos com guidance,
rotação sectorial). Ignora dividendos regulares, ratings mantidos e marketing
sem números."""

    messages = [{"role": "user", "content": user}]
    final_text = ""

    for _ in range(max_turns):
        response = client.messages.create(
            model=config.CLAUDE_MODEL,
            max_tokens=8000,
            system=system,
            tools=[
                {
                    **WEB_SEARCH_TOOL,
                    "allowed_domains": config.SOURCE_DOMAINS,
                    "max_uses": 10,
                }
            ],
            messages=messages,
        )

        # Acumula texto produzido nesta volta.
        final_text = "".join(
            b.text for b in response.content if getattr(b, "type", "") == "text"
        )

        if response.stop_reason == "pause_turn":
            # O loop server-side de web search pausou — reenvia para continuar.
            messages.append({"role": "assistant", "content": response.content})
            continue
        break

    return _extract_json_array(final_text)[:max_items]
