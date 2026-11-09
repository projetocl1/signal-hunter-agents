# Glossário Git & GitHub

Referência rápida de todos os conceitos do sistema de controlo de versões e colaboração.

---

## Conceitos fundamentais

### Repository (Repositório / Repo)
Pasta do projecto que contém todo o histórico de alterações, ficheiros e metadados. Pode existir localmente (no teu computador) e remotamente (no GitHub).

### Git
Sistema de controlo de versões distribuído. Regista cada alteração feita ao código, quem a fez e quando. Funciona offline — o GitHub é apenas um servidor remoto que aloja repositórios Git.

### GitHub
Plataforma web que aloja repositórios Git e adiciona ferramentas de colaboração: Issues, Pull Requests, Actions (CI/CD), etc.

---

## Ramos e versões

### Branch (Ramo)
Linha de desenvolvimento independente. Podes criar um branch para desenvolver uma funcionalidade sem afectar o código principal. É apenas um apontador para um commit.

```
main ──●──●──●
             └── feat/nova-funcionalidade ──●──●
```

### Main (ou Master)
O branch principal do projecto. É a versão "oficial" e estável do código. Em projectos modernos chama-se `main`; antigamente chamava-se `master`.

### HEAD
Apontador que indica onde estás agora mesmo — qual o branch e commit activo na tua área de trabalho local.

### Tag
Marcador permanente num commit específico, normalmente usado para assinalar versões (`v1.0.0`, `v2.3.1`). Ao contrário de um branch, não avança.

### Release
Versão publicada do projecto no GitHub, associada a uma tag. Pode incluir notas de lançamento e ficheiros binários para download.

---

## Operações locais

### Commit
Fotografia do estado dos ficheiros num determinado momento. Cada commit tem:
- Um identificador único (SHA/hash, ex: `5195df5`)
- Uma mensagem descritiva
- O autor e a data
- Referência ao commit anterior (o "pai")

### Staging Area (Área de preparação / Index)
Zona intermédia entre o teu directório de trabalho e o próximo commit. Adicionas ficheiros com `git add` antes de confirmar com `git commit`.

```
Working Tree  →  Staging Area  →  Repositório
   (editas)       (git add)       (git commit)
```

### Working Tree (Directório de trabalho)
Os ficheiros como os vês no teu editor — ainda não adicionados nem commitados.

### Diff
Comparação entre duas versões de um ficheiro ou commit, mostrando exactamente o que foi adicionado (+) e removido (−).

### Stash
Guarda temporariamente as alterações não commitadas para poderes mudar de branch e recuperá-las depois com `git stash pop`.

---

## Operações com o remoto

### Remote (Remoto)
Versão do repositório alojada noutro servidor (normalmente o GitHub). O remoto padrão chama-se `origin`.

### Origin
Nome convencional do repositório remoto principal (o que está no GitHub). `git push origin main` envia o branch `main` para o GitHub.

### Clone
Copia um repositório remoto para o teu computador, incluindo todo o histórico.

### Push
Envia os teus commits locais para o repositório remoto.

### Pull
Traz os commits do repositório remoto para o teu local e faz merge automático.

### Fetch
Traz as actualizações do remoto mas **não** faz merge — apenas actualiza a referência local do remoto. Mais seguro que pull quando queres inspecionar antes de integrar.

---

## Colaboração

### Fork
Cópia independente de um repositório para a tua conta GitHub. Usada quando não tens permissões de escrita no projecto original — fazes as alterações no fork e propões via Pull Request.

### Pull Request (PR)
Pedido para integrar as alterações de um branch (ou fork) noutro branch. É o ponto central de revisão de código:
- O autor descreve o que mudou e porquê
- Os revisores comentam linha a linha
- Pode ter CI automático a correr testes
- Quando aprovado, faz-se merge

### Draft PR
Pull Request marcada como rascunho — indica que o trabalho ainda não está pronto para revisão, mas já é visível para a equipa.

### Merge
Integração das alterações de um branch noutro. Existem três estratégias:
- **Merge commit** — cria um commit de merge explícito
- **Squash** — colapsa todos os commits do branch num só
- **Rebase** — reaplica os commits sobre o branch de destino, mantendo histórico linear

### Rebase
Reescreve o histórico do teu branch como se tivesse partido de um ponto mais recente. Útil para manter histórico limpo, mas não deve ser feito em branches públicos.

### Conflict (Conflito)
Quando dois branches alteraram a mesma linha do mesmo ficheiro de formas diferentes. O Git não resolve automaticamente — tens de escolher qual versão fica (ou combinar ambas).

### Review (Revisão de código)
Processo de análise de um PR por outro elemento da equipa. Pode resultar em: aprovação, pedido de alterações ou comentários.

### Approve / Request Changes
Acções de revisão: **Approve** dá luz verde ao merge; **Request Changes** bloqueia o merge até as questões serem resolvidas.

---

## Issues e gestão

### Issue
Tarefa, bug, pedido de funcionalidade ou discussão registada no GitHub. Pode ser referenciada em commits e PRs (`closes #42` fecha a issue automaticamente no merge).

### Label
Etiqueta colorida para categorizar Issues e PRs (ex: `bug`, `enhancement`, `documentation`).

### Milestone
Agrupamento de Issues e PRs com um objectivo e data limite comuns — equivalente a um sprint ou versão.

### Assignee
Pessoa responsável por uma Issue ou PR.

---

## CI/CD e automação

### GitHub Actions
Sistema de automação integrado no GitHub. Corre workflows (sequências de passos) em resposta a eventos: push, abertura de PR, schedule (cron), etc.

### Workflow
Ficheiro YAML em `.github/workflows/` que define quando e o quê correr automaticamente (testes, linting, deploy, scans de agentes, etc.).

### Job
Unidade de trabalho dentro de um workflow. Corre num runner (máquina virtual). Vários jobs podem correr em paralelo.

### Step
Passo individual dentro de um job — um comando shell ou uma Action reutilizável.

### Runner
Máquina (virtual ou self-hosted) onde os jobs do GitHub Actions executam.

### Secrets
Variáveis de ambiente sensíveis (API keys, tokens) guardadas de forma segura no GitHub e injectadas nos workflows em runtime. Nunca aparecem em logs nem no código.

### Artifact
Ficheiro ou directório produzido por um workflow e guardado temporariamente no GitHub (logs, relatórios, binários compilados).

---

## Referências e navegação

### SHA / Hash
Identificador único de um commit — string hexadecimal de 40 caracteres (normalmente abreviada para os primeiros 7, ex: `5195df5`).

### Checkout
Muda o teu working tree para um branch, commit ou tag específico (`git checkout feat/x` ou `git switch feat/x` na sintaxe moderna).

### Cherry-pick
Aplica um commit específico de outro branch no branch actual, sem fazer merge de todo o histórico.

### Blame
Mostra para cada linha de um ficheiro quem foi o último a alterá-la e em que commit.

### Log
Histórico de commits do repositório ou de um ficheiro específico.

---

## Neste projecto

| Conceito | Instância concreta |
|----------|--------------------|
| Repo | `projetocl1/signal-hunter-agents` |
| Branch principal | `main` |
| Branch de desenvolvimento | `feat/signal-hunter-system` / `claude/run-pt867x` |
| Secrets necessários | `ANTHROPIC_API_KEY`, `AIRTABLE_TOKEN`, `AIRTABLE_BASE_ID` |
| Workflows | `morning.yml`, `afternoon.yml`, `close.yml` |
| Tabela Airtable | `catalyst_signals` |
