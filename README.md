# 📡 signal-hunter-agents

Sistema autónomo de rastreamento de **catalisadores de mercado** para swing
trading em tickers NASDAQ/NYSE. Detecta sinais de entrada **antes** do
movimento de preço, com foco em catalisadores que permanecem válidos **12
horas após detecção** — o horizonte de actuação do operador.

> Repositório **totalmente independente** do `pharma-intel-agents`. Zero
> ficheiros partilhados, zero dependências cruzadas, base Airtable dedicada.

---

## Como funciona

Cada scan corre o mesmo pipeline:

```
navegar fontes  →  classificar  →  durabilidade  →  convergência  →  scoring  →  Airtable
 (web search)      (Claude API)    (filtro 12h)     (Airtable 48h)   (regras)    (+ briefing)
```

1. **Navegação de fontes** (`core/news_fetcher.py`) — em GitHub Actions não há
   browser interactivo, por isso a "navegação directa" é feita através da
   **ferramenta de web search da Claude API** (`web_search_20260209`),
   restrita a uma allowlist de domínios (Benzinga, TipRanks, SEC EDGAR,
   GlobeNewswire, PR Newswire, Reuters, Slickcharts). O agente pesquisa, lê e
   devolve candidatos a catalisador.
2. **Classificação** (`core/classifier.py`) — cada notícia é classificada pela
   Claude API com saída estruturada (schema Pydantic, sempre JSON válido).
3. **Durabilidade + scoring** (`core/durability_check.py`) — aplica as regras
   de decisão (ver abaixo).
4. **Convergência** (`core/airtable_writer.py`) — consulta o Airtable: o mesmo
   ticker teve outro sinal nas últimas 48h?
5. **Registo** — sinais com score ≥ 6 vão para o Airtable; o `close_scan`
   gera ainda o briefing diário em Markdown.

### Modelo de classificação (output)

```json
{
  "ticker": "SYMBOL",
  "signal_type": "analyst|earnings|product|macro|rotation",
  "catalyst_strength": 1-10,
  "horizon": "3d|10d|30d|90d",
  "durability_12h": true/false,
  "convergence_detected": true/false,
  "reasoning": "max 2 frases"
}
```

### Regras de scoring

| Regra | Efeito |
|-------|--------|
| `durability_12h = false` | **descarta sempre** |
| `catalyst_strength` | score base (1-10) |
| `convergence_detected = true` | **+3** ao score |
| score final **≥ 8** | 🔴 Alta prioridade → Airtable + briefing |
| score final **6-7** | 🟡 Monitorização → Airtable + briefing |
| score final **< 6** | descarta |

**Convergência:** a estimativa do modelo é ignorada; a convergência
*autoritativa* vem do Airtable (mesmo ticker, outro sinal em 48h). Dois tipos
**diferentes** de sinal no mesmo ticker = **prioridade máxima**.

---

## Estrutura

```
signal-hunter-agents/
├── agents/
│   ├── __init__.py          # pipeline partilhado (run_scan)
│   ├── morning_scan.py      # 06:30 UTC — upgrades overnight + SEC 8-K
│   ├── afternoon_scan.py    # 14:00 UTC — sector rotation + macro
│   └── close_scan.py        # 21:00 UTC — earnings AH + briefing diário
├── core/
│   ├── config.py            # fontes, critérios, constantes de scoring
│   ├── ticker_universe.py   # Nasdaq 100 + expansão dinâmica
│   ├── news_fetcher.py      # navegação de fontes (web search)
│   ├── classifier.py        # classificação (Claude + schema)
│   ├── durability_check.py  # filtro 12h + scoring
│   ├── airtable_writer.py   # I/O Airtable + convergência
│   └── briefing.py          # gerador de briefing markdown
├── scripts/
│   └── validate_setup.py    # valida env + Claude + Airtable
├── tests/                   # testes unitários (offline)
├── briefings/               # briefings diários gerados (commitados)
├── .github/workflows/       # morning / afternoon / close
├── .env.example
└── requirements.txt
```

---

## Setup

### 1. Variáveis de ambiente

Copia `.env.example` para `.env` e preenche:

| Variável | Descrição |
|----------|-----------|
| `ANTHROPIC_API_KEY` | Chave da Claude API |
| `AIRTABLE_TOKEN` | Personal access token (scopes: `data.records:read`, `data.records:write`) |
| `AIRTABLE_BASE_ID` | ID da **base dedicada** (nunca a do pharma-intel) |
| `AIRTABLE_TABLE` | (opcional) default `catalyst_signals` |
| `CLAUDE_MODEL` | (opcional) default `claude-opus-4-8` |

### 2. Airtable — base dedicada

Cria uma **base nova** e uma tabela `catalyst_signals` com os campos:

| Campo | Tipo |
|-------|------|
| `date` | Date (com hora) |
| `ticker` | Single line text |
| `signal_type` | Single select (`analyst`, `earnings`, `product`, `macro`, `rotation`) |
| `catalyst_strength` | Number (inteiro) |
| `horizon` | Single select (`3d`, `10d`, `30d`, `90d`) |
| `durability_12h` | Checkbox |
| `convergence` | Checkbox |
| `headline` | Long text |
| `source` | Single line text |
| `raw_score` | Number (inteiro) — score final |
| `alerted` | Checkbox (true se alta prioridade) |

> O cliente usa `typecast: true`, por isso os single selects são criados
> automaticamente se ainda não existirem.

**View de monitorização manual:** cria uma view filtrada por
`raw_score >= 8` **E** `date` nas últimas 24h, ordenada por `raw_score`
descendente. É o painel de alta prioridade do operador.

### 3. Secrets do GitHub Actions

Em *Settings → Secrets and variables → Actions*, adiciona:
`ANTHROPIC_API_KEY`, `AIRTABLE_TOKEN`, `AIRTABLE_BASE_ID`.

---

## Correr e testar localmente

```bash
pip install -r requirements.txt

# Testes unitários (offline, sem credenciais)
python -m unittest discover -s tests -v

# Validar setup completo (env + Claude + Airtable) ANTES do scheduler
python -m scripts.validate_setup

# Correr um scan manualmente (precisa de credenciais)
python -m agents.morning_scan
python -m agents.afternoon_scan
python -m agents.close_scan      # corre o scan e gera o briefing
```

Cada agente é executável individualmente. Os workflows também têm
`workflow_dispatch` para execução manual a partir do GitHub.

---

## Output

Sem notificações push. Dois canais apenas:

1. **Briefing diário** (`close_scan`, 21:00 UTC) — ficheiro markdown em
   `briefings/YYYY-MM-DD.md`, commitado ao repositório. Secções:
   🔴 Alta Prioridade, 🟡 Monitorização, 📊 Stats do dia.
2. **Airtable (tempo real)** — todos os sinais com score ≥ 6; view filtrada
   (≥ 8, últimas 24h) para monitorização manual no tablet.

---

## Schedules (GitHub Actions)

| Workflow | Cron (UTC) | Foco |
|----------|-----------|------|
| `morning.yml` | `30 6 * * *` | analyst upgrades overnight + SEC 8-K (8h) |
| `afternoon.yml` | `0 14 * * *` | sector rotation detector + macro |
| `close.yml` | `0 21 * * *` | after-hours earnings + briefing diário |

---

## Notas de implementação

- **Custo / web search:** cada scan faz várias pesquisas web via Claude API —
  têm custo. Os `max_uses` e `max_items` estão limitados em `news_fetcher.py`.
- **Universo dinâmico:** a base Nasdaq 100 está em `ticker_universe.py` (lista
  estática, refrescar periodicamente). A expansão (upgrades 30d + laggards
  sectoriais) é best-effort via web search e não quebra o pipeline se falhar.
- **Separação do pharma-intel:** este repositório não importa, lê nem escreve
  nada do `pharma-intel-agents`; a base Airtable é distinta (`AIRTABLE_BASE_ID`
  próprio). O formato do briefing segue a mesma estrutura de secções do
  `briefing.py` do pharma-intel, mas o código é independente.

---

## Critério de sucesso

- [x] Estrutura de ficheiros criada e cada módulo testável individualmente
- [x] Lógica de scoring/convergência/briefing validada (14 testes a passar)
- [ ] `scripts/validate_setup.py` confirma Claude + Airtable (requer credenciais)
- [ ] Os 3 GitHub Actions correm sem erro (requer secrets configurados)
- [ ] Um sinal real entra no Airtable com todos os campos
- [ ] Briefing diário gerado correctamente
- [x] Zero interferência com o pharma-intel-agents
