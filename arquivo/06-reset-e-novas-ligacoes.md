# 06 — Reset das ferramentas + criação de novas chaves e ligações

> Guia passo-a-passo, reutilizável em qualquer projecto futuro.
> Decisões de 2026-11-09: **apagar as 4 bases Airtable · repo novo ·
> fechar PRs #2 e #4 · Supabase como base de dados**.
>
> 🔒 **Regra de ouro:** nunca escrevas o VALOR de uma chave neste ficheiro,
> no chat ou num commit. Aqui regista-se só *que* a chave existe, *onde* está
> e *quando* foi criada. Guarda os valores num gestor de passwords (Bitwarden,
> 1Password, ou o gestor do Google no Android).

---

## Fase 0 — Feito pelo Claude ✅

| Passo | Estado |
|---|---|
| Inventário de tudo e código v1 guardado em `arquivo/` | ✅ 2026-11-09 |
| PR #2 fechado (obsoleto) | ✅ 2026-11-09 |
| PR #4 fechado (glossário guardado em `03-prs-abertos/`) | ✅ 2026-11-09 |

---

## Fase 1 — RESET (desligar tudo o que é antigo)

A ordem importa: **primeiro salvar, depois revogar, por fim apagar.**

### 1.1 ⚠️ Exportar a Portfolio ANTES de apagar (irreversível)
Os registos da base "Portfolio KJsuited" **não estão** no arquivo (a API estava bloqueada).
1. Abre o Airtable → base **Portfolio KJsuited** → tabela **Portfolio**
2. Menu da view (⋯) → **Download CSV**
3. Guarda o ficheiro fora do Airtable (Drive ou tablet)

### 1.2 Revogar a chave Anthropic antiga
Analogia: mudar a fechadura antes de dar chaves novas.
1. [console.anthropic.com](https://console.anthropic.com) → **Settings → API Keys**
2. Identifica a chave usada pelo signal-hunter → **Disable / Delete**
3. Se houver chaves que não reconheces → apaga também

### 1.3 Revogar o token Airtable antigo
1. [airtable.com/create/tokens](https://airtable.com/create/tokens)
2. Apaga o token usado pelo signal-hunter (e qualquer outro sem uso)

### 1.4 Apagar os secrets do repo antigo
1. GitHub → `projetocl1/signal-hunter-agents` → **Settings → Secrets and variables → Actions**
2. Apaga `ANTHROPIC_API_KEY`, `AIRTABLE_TOKEN`, `AIRTABLE_BASE_ID`

### 1.5 Apagar as 4 bases Airtable (irreversível — só depois do 1.1)
Para cada base (Portfolio KJsuited, Pharma-intel, V2, News):
Airtable home → ⋯ na base → **Delete base**.
*(Ficam ~7 dias no Trash antes de desaparecerem de vez.)*

### 1.6 Connectors claude.ai
[claude.ai → Settings → Connectors](https://claude.ai/settings/connectors)
| Connector | Acção |
|---|---|
| Airtable | **Desligar** (deixamos de o usar) |
| Addepar, Canva | Remover (nunca ficaram configurados) |
| Notion | Remover, a menos que o novo projecto o use |
| Alpha Vantage, FMP, LunarCrush | Deixar para a Fase 2: só se o novo projecto usar dados de mercado |
| Supabase, Clinical Trials | Manter |

### 1.7 Ambientes Claude Code
Em claude.ai/code → **Settings → Environments**:
| Ambiente | Situação | Acção sugerida |
|---|---|---|
| `kjsuited` | rede **sem restrições**, vazio | Apagar (rede aberta sem necessidade é risco) |
| `protótipo` | vazio; o acento no nome impede operações automáticas | Apagar, ou renomear para `prototipo` |
| `Default` | o actual | Manter |

### 1.8 (Opcional) Repo antigo
Depois de o novo projecto arrancar: `signal-hunter-agents` → **Settings → Archive this repository**.
Fica só de leitura, com o arquivo intacto. Nota: a pasta `arquivo/` está no branch
`claude/clever-carson-msrbl9`. Faz o merge para `main` antes de arquivar o repo.

---

## Fase 2 — CRIAR (novas chaves e ligações)

Faz isto só depois de definirmos o projecto (nome e domínio).

### 2.1 Repo novo no GitHub
1. github.com → **New repository** → owner `projetocl1`
2. Nome: o que o projecto **faz**, em kebab-case (ex.: `market-radar`)
3. Private · com README
4. Diz-me o nome → eu ligo-o a uma sessão Claude Code

### 2.2 Nova chave Anthropic
1. console.anthropic.com → **API Keys → Create Key**
2. Nome: `<projecto>-gha-<AAAA-MM>` (ex.: `market-radar-gha-2026-11`)
3. Copia **uma vez** para o gestor de passwords
4. ⚠️ Ao colar no GitHub: cola, **sem Enter no fim e sem espaços**. Foi um newline no secret que causou as 54 falhas do v1.
5. (Recomendado) **Settings → Limits**: define um limite de gasto mensal

### 2.3 Projecto Supabase
1. Eu crio-o via connector quando o nome estiver decidido. Mostro o custo antes e só avanço com o teu OK.
2. Depois, em supabase.com → projecto → **Settings → API**, tira:
   - `SUPABASE_URL` (não é secreto)
   - `SUPABASE_SERVICE_ROLE_KEY` (**secreto**: só para GitHub Actions, nunca no frontend)

### 2.4 Secrets no repo novo
GitHub → repo novo → **Settings → Secrets and variables → Actions → New repository secret**:
| Nome | Origem |
|---|---|
| `ANTHROPIC_API_KEY` | 2.2 |
| `SUPABASE_URL` | 2.3 |
| `SUPABASE_SERVICE_ROLE_KEY` | 2.3 |

### 2.5 Health check obrigatório
O primeiro workflow do repo novo é **só** um teste de ligação:
Claude responde? Supabase responde? Se falhar → erro vermelho imediato + issue automática.
Só depois disto se criam os agentes agendados (lição n.º 1 e n.º 2 do ficheiro 05).

---

## Registo (preenche à medida que fazes)

| Data | Passo | Feito por | Nome da chave/recurso (NUNCA o valor) | Notas |
|---|---|---|---|---|
| 2026-11-09 | Fase 0 | Claude | — | arquivo + PRs fechados |
| | 1.1 Export Portfolio | | | |
| | 1.2 Revogar Anthropic | | | |
| | 1.3 Revogar Airtable | | | |
| | 1.4 Secrets repo antigo | | | |
| | 1.5 Apagar bases | | | |
| | 1.6 Connectors | | | |
| | 1.7 Ambientes | | | |
| | 2.1 Repo novo | | | |
| 2026-11-09 | 2.2 Chave Anthropic | KJsuited | (nome por preencher) | criada; falta guardar no gestor de passwords e colocar no repo novo |
| | 2.3 Supabase | | | |
| | 2.4 Secrets repo novo | | | |
| | 2.5 Health check | | | |

## Calendário de rotação
- Chave Anthropic e service role Supabase: rodar a cada **6 meses**, ou de imediato se houver suspeita de fuga.
- Próxima rotação sugerida: **2027-05**.
