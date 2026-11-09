# 00 — Inventário de ligações

Recolhido em 2026-11-09.

## Connectors claude.ai

| Connector | Estado | Relevância |
|---|---|---|
| Airtable | ✅ ligado (mas **API em limite mensal — 429**) | Base de dados dos sinais |
| Supabase | ✅ ligado | Alternativa ao Airtable (sem limite mensal de pedidos à API) |
| Clinical Trials | ✅ ligado | Útil para o Pharma-intel (catalisadores FDA/PDUFA) |
| Alpha Vantage | ⚠️ precisa de nova ligação | Preços, fundamentais, notícias |
| FMP | ⚠️ precisa de nova ligação | Dados financeiros |
| LunarCrush | ⚠️ precisa de nova ligação | Sentimento social |
| Notion | ⚠️ precisa de nova ligação | — |
| Addepar | ❌ configuração incompleta | — |
| Canva | ❌ configuração incompleta | — |

Plugins de dados que falharam ao ligar nesta sessão: Amplitude, Atlassian, BigQuery, Definite e Hex.

## Airtable — 4 bases

| Base | ID | Estado do inventário |
|---|---|---|
| Portfolio KJsuited | `appu93otEUk7tqsBs` | ✅ lido |
| Pharma-intel | `appG1KIaCqbt5lChG` | ❌ bloqueado (429) |
| V2 | `apprrTasI8TX9iKRU` | ❌ bloqueado (429) |
| News | `appX7WNtimrwV8y7H` | ❌ bloqueado (429) |

Automações Airtable: **nenhuma**, nas 4 bases.

### Portfolio KJsuited → tabela `Portfolio` (`tbl6PAb8HcL5In3Sw`)

| Campo | Tipo |
|---|---|
| Ticker | texto |
| Nome | texto |
| Classe de Activo | single select |
| Sector | single select |
| Preço Médio de Entrada | moeda |
| Quantidade | número |
| Peso no Portfólio (%) | percentagem |
| Data de Entrada | data |
| Notas/Tese | texto longo |

Os registos não foram lidos, para não gastar pedidos e porque são dados privados de portfólio.

### Schema esperado pelo sistema v1 (tabela `catalyst_signals`)

Este schema vem do código e não foi confirmado no Airtable:
`date, ticker, signal_type, catalyst_strength, horizon, durability_12h,
convergence, headline, source, raw_score, alerted`.

**Por verificar:** em qual das bases (News / V2 / Pharma-intel) está o
`AIRTABLE_BASE_ID` que o v1 usava. O README do reset diz que as três foram limpas.

## Supabase

- Organização: **Aprendizagem**
- Projectos: **0**

## GitHub

- Repo: `projetocl1/signal-hunter-agents`
- Secrets em Actions, segundo o README; não é possível lê-los daqui:
  `ANTHROPIC_API_KEY`, `AIRTABLE_TOKEN`, `AIRTABLE_BASE_ID`
- Repo relacionado e citado no código: `pharma-intel-agents` (sem acesso nesta sessão)

## Ambiente cloud Claude Code

| Item | Valor |
|---|---|
| Ambiente actual | Default (pessoal) |
| Rede | limitada: gestores de pacotes e MCP |
| Hosts extra / secrets / setup script | nenhum |
| Outros ambientes | `kjsuited`, `protótipo` |
