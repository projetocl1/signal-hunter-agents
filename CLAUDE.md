# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## O que é este repositório

Sistema autónomo de rastreamento de catalisadores de mercado para swing trading NASDAQ/NYSE. Três agentes agendados (morning/afternoon/close) correm via GitHub Actions, cada um executando o mesmo pipeline partilhado. Os sinais são guardados numa base Airtable dedicada; o close scan também commita um briefing diário em markdown em `briefings/`.

## Comandos

```bash
# Instalar dependências
pip install -r requirements.txt

# Correr os testes (offline, sem credenciais)
python -m unittest discover -s tests -v

# Correr um único ficheiro de testes
python -m unittest tests.test_durability -v

# Validar credenciais + serviços externos antes de activar os schedulers
python -m scripts.validate_setup

# Correr um agente manualmente (requer credenciais no env)
python -m agents.morning_scan
python -m agents.afternoon_scan
python -m agents.close_scan
```

Não há linter, formatter nem passo de build configurados.

## Arquitectura

### Pipeline partilhado — `agents/__init__.py:run_scan`

```
get_universe → fetch_news → classify → evaluate → detect_convergence → write_signal
```

Cada agente chama `run_scan(focus, expand, max_items)`. O argumento `focus` orienta o que o agente de web search procura; `expand=True` (apenas no morning) acrescenta tickers dinâmicos via uma segunda ronda de web search.

### Responsabilidades dos módulos

| Módulo | Responsabilidade |
|---|---|
| `core/config.py` | Fonte única de verdade para todas as constantes ajustáveis: thresholds de scoring, allowlist de fontes, critérios do universo, tipos de sinal |
| `core/news_fetcher.py` | Chama a Claude API com a ferramenta `web_search_20260209`; gere o loop `pause_turn`; devolve dicts de candidatos em bruto |
| `core/classifier.py` | Chama `client.messages.parse()` com schema Pydantic (`Classification`) para output JSON sempre válido |
| `core/durability_check.py` | Função pura `evaluate(signal, convergence)` → `ScoredSignal`; sem I/O |
| `core/airtable_writer.py` | Cliente REST do Airtable: `detect_convergence()` (leitura), `write_signal()` (escrita), `recent_signals()` (para o briefing) |
| `core/ticker_universe.py` | Base estática Nasdaq 100 + expansão dinâmica best-effort via web search |
| `core/briefing.py` | Construtor puro de markdown; o `close_scan` chama `write_briefing()` que guarda em `briefings/` |

### Regras de scoring (todas as constantes em `core/config.py`)

1. `durability_12h = false` → **descarta sempre**, independentemente do score
2. Score base = `catalyst_strength` (1–10, dado pelo classificador Claude)
3. `convergence_detected = true` → **+3** (`CONVERGENCE_BONUS`)
4. `final_score >= 8` → alta prioridade (`alerted=True` no Airtable)
5. `final_score 6–7` → monitorização
6. `final_score < 6` → descarta

**A convergência autoritativa vem do Airtable, não do modelo.** O `classifier.py` produz uma estimativa `convergence_detected`, mas o `run_scan` sobrepõe-na sempre com o resultado de `AirtableClient.detect_convergence()`. Dois tipos de sinal *diferentes* no mesmo ticker em 48h (`distinct_types=True`) força `priority = "high"` independentemente do score.

### Padrões de uso da Claude API

- **Recolha de notícias** (`news_fetcher.py`): `client.messages.create()` com ferramenta `web_search_20260209`, `allowed_domains` restrito a `config.SOURCE_DOMAINS`. Trata `stop_reason == "pause_turn"` reenviando o turno do assistente e repetindo (até `max_turns=6`).
- **Classificação** (`classifier.py`): `client.messages.parse()` com `output_format=Classification` (Pydantic). Devolve `response.parsed_output`; lança `RuntimeError` se `None`.
- **Expansão do universo** (`ticker_universe.py`): mesmo padrão de web search que a recolha de notícias; falhas são apanhadas e ignoradas (best-effort).

### Dependências externas

- **Anthropic API**: classificação + web search. Modelo por defeito `claude-opus-4-8`, substituível via variável `CLAUDE_MODEL`.
- **Airtable REST API** (`https://api.airtable.com/v0`): usa `typecast: true` nas escritas para criar automaticamente valores de single-select. Nome da tabela por defeito `catalyst_signals`.
- Sem base de dados própria, sem broker, sem feed de mercado — todos os dados de mercado chegam através do web search da Claude.

### GitHub Actions

Três workflows (`morning.yml`, `afternoon.yml`, `close.yml`) requerem três secrets: `ANTHROPIC_API_KEY`, `AIRTABLE_TOKEN`, `AIRTABLE_BASE_ID`. Todos suportam `workflow_dispatch` para execução manual. O `close.yml` tem `permissions: contents: write` para commitar o briefing diário.

## Invariantes importantes

- Este repositório partilha **zero código e zero base Airtable** com o `pharma-intel-agents`. Nunca referenciar nem importar desse repositório.
- O directório `briefings/` é commitado ao git automaticamente pelo workflow do `close_scan`.
- A lista Nasdaq 100 em `ticker_universe.py` é um snapshot estático e deve ser refrescada periodicamente.
- Custo de web search: cada scan dispara até 10 chamadas de web search (`max_uses=10`). Ter em conta os limites `max_items` e `max_turns` ao alterar o comportamento de recolha.
