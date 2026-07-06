# signal-hunter-agents — reset

Este repositório foi limpo deliberadamente para dar espaço a um projeto novo,
mais eficiente e organizado. O sistema anterior (rastreamento de
catalisadores de mercado via GitHub Actions + Claude API + Airtable) foi
removido do código porque estava sistematicamente a falhar (secret
`ANTHROPIC_API_KEY` malformado impedia qualquer scan de correr).

## O que se manteve

- O repositório e o histórico de commits.
- A ligação à base Airtable dedicada (`AIRTABLE_BASE_ID` nos secrets do
  GitHub Actions) — as tabelas e campos existem, mas os registos foram
  limpos.
- Os secrets `ANTHROPIC_API_KEY`, `AIRTABLE_TOKEN`, `AIRTABLE_BASE_ID` em
  *Settings → Secrets and variables → Actions* (por verificar/corrigir
  antes de reconstruir).

## O que foi removido

- Todo o código (`agents/`, `core/`, `scripts/`, `tests/`).
- Os workflows do GitHub Actions (`morning.yml`, `afternoon.yml`,
  `close.yml`).
- `requirements.txt`, `.env.example`, `.gitignore`.
- Todos os registos nas bases Airtable "News", "Pharma-intel" e "V2"
  (tabelas e campos mantidos vazios).

## Próximo passo

Antes de reconstruir, confirmar que o secret `ANTHROPIC_API_KEY` no GitHub
não tem espaços/newlines a mais — foi a causa raiz de todas as falhas
anteriores.
