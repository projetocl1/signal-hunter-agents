# 04 — Tarefas e histórico

## Tarefas activas hoje

| Tipo | Quantidade |
|---|---|
| Tarefas agendadas (Claude) | 0 |
| Workflows GitHub Actions | 0 |
| Automações Airtable | 0 |
| Edge functions Supabase | 0 (não há projectos) |

## Tarefas do sistema v1 (todas desactivadas)

| Workflow | Cron (UTC) | Função | Execuções | Sucesso |
|---|---|---|---|---|
| `morning_scan` | `30 6 * * *` | analyst upgrades overnight + SEC 8-K | 18 | 0 |
| `afternoon_scan` | `0 14 * * *` | rotação sectorial + macro | 18 | 0 |
| `close_scan` | `0 21 * * *` | earnings after-hours + briefing diário (commit em `briefings/`) | 18 | 0 |
| Copilot cloud agent | — | execução pontual | 1 | 1 |

Detalhe de cada execução: [`02-execucoes-github-actions.csv`](02-execucoes-github-actions.csv).

**Nota:** as execuções agendadas começaram com atrasos de várias horas face ao
cron (por exemplo, `morning_scan` às 18:10 em vez de 06:30). O GitHub Actions
não garante a hora certa em repositórios com pouca actividade.

## Linha temporal

| Data | Evento |
|---|---|
| 2026-06-18 | Initial commit + sistema v1 completo (PR #1, mergeado) |
| 2026-06-18 → 07-05 | 54 execuções agendadas, **todas falhadas** |
| 2026-06-28 | PR #2 aberto: correcção para limpar newlines dos secrets. **Nunca mergeado** |
| 2026-07-06 | PR #3: reset, código removido e registos Airtable limpos |
| 2026-09-05 | PR #4 aberto: glossário Git/GitHub (docs) |
| 2026-11-09 | Arquivo criado · PRs #2 e #4 fechados · decisão de reset total |

## Pull requests

| PR | Título | Estado |
|---|---|---|
| [#1](https://github.com/projetocl1/signal-hunter-agents/pull/1) | sistema de rastreamento de catalisadores | mergeado |
| [#2](https://github.com/projetocl1/signal-hunter-agents/pull/2) | sanitize secrets | fechado 2026-11-09 (obsoleto) |
| [#3](https://github.com/projetocl1/signal-hunter-agents/pull/3) | reset | mergeado |
| [#4](https://github.com/projetocl1/signal-hunter-agents/pull/4) | glossário Git/GitHub | fechado 2026-11-09 (conteúdo no arquivo) |

Conteúdo dos PRs #2 e #4: [`03-prs-abertos/`](03-prs-abertos/).
