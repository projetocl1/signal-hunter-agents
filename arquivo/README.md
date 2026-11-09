# 📦 Arquivo — inventário para análise

> Criado em 2026-11-09. Fotografia de **todas as ligações, conteúdos e
> tarefas** associadas aos projectos, para analisar antes de reconstruir.
> Nada aqui corre automaticamente: é só para leitura.

## Índice

| Ficheiro / pasta | O que contém |
|---|---|
| [`00-inventario-ligacoes.md`](00-inventario-ligacoes.md) | Connectors claude.ai, bases Airtable, Supabase, ambiente cloud, secrets |
| [`01-sistema-v1-codigo/`](01-sistema-v1-codigo/) | Código completo do sistema v1, recuperado do commit `9b1ad69` |
| [`02-execucoes-github-actions.csv`](02-execucoes-github-actions.csv) | Todas as 55 execuções do GitHub Actions (data, workflow, resultado, link) |
| [`03-prs-abertos/`](03-prs-abertos/) | Conteúdo dos PRs #2 e #4 (fechados em 2026-11-09) |
| [`04-tarefas-e-historico.md`](04-tarefas-e-historico.md) | Linha temporal, tarefas agendadas e PRs |
| [`05-analise-e-licoes.md`](05-analise-e-licoes.md) | O que falhou, porquê, e o que fazer no próximo sistema |
| [`06-reset-e-novas-ligacoes.md`](06-reset-e-novas-ligacoes.md) | **Guia de reset + criação de chaves/ligações (com registo)** |

## Resumo em 5 linhas

1. **Sistema v1** (signal-hunter): 3 agentes agendados (06:30 / 14:00 / 21:00 UTC), Claude API + Airtable.
2. **Correu 54 vezes e falhou 54 vezes** (18 de junho a 5 de julho de 2026). Nenhum sinal chegou ao Airtable.
3. **Causa provável:** o secret `ANTHROPIC_API_KEY` estava mal formatado. O PR #2, com a correcção, nunca foi mergeado.
4. **Hoje:** não há código, workflows nem tarefas agendadas activas. Ficam 4 bases Airtable e 1 organização Supabase vazia.
5. **Bloqueio actual:** a API do Airtable atingiu o **limite mensal do plano** (erro 429), por isso 3 das 4 bases não puderam ser inventariadas.

## Como reactivar o código v1 (se um dia quiseres)

Os workflows estão em `01-sistema-v1-codigo/workflows-DESACTIVADOS/`.
O GitHub só executa ficheiros que estão em `.github/workflows/` na raiz do repositório, por isso aqui estão desligados.
Para os reactivar teria de os mover para lá. **Não o faças sem corrigir antes os secrets.**
