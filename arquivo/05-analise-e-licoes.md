# 05 — Análise e lições

## Factos

- 54 de 54 execuções falharam ao longo de 18 dias.
- O PR #2 (correcção dos secrets) foi aberto 10 dias depois do arranque e nunca foi mergeado.
- Os 14 testes unitários offline do v1 **continuam a passar** (verificado em 2026-11-09).
- A API do Airtable está bloqueada pelo limite mensal do plano (429).
- O modelo configurado no v1 (`claude-opus-4-8`) já não é o mais recente.

## Interpretação

- **A lógica estava bem; a integração é que falhou.** Os testes cobriam
  scoring e convergência, mas nada validava as credenciais antes de o
  scheduler arrancar. O `validate_setup.py` existia, mas nunca chegou a correr com sucesso.
- **O falhanço foi silencioso.** O sistema "correu" 54 vezes sem ninguém
  agir. Faltou um alerta de falha. A analogia é um alarme de casa sem pilhas:
  está instalado mas não avisa de nada.
- **O Airtable é um ponto frágil.** O plano gratuito tem um limite mensal de
  pedidos. Um sistema com 3 scans por dia, cada um a consultar a convergência,
  esgota esse limite depressa. Hoje o limite já está atingido.

## O que fazer diferente no próximo sistema

| # | Lição | Acção concreta |
|---|---|---|
| 1 | Validar credenciais antes de tudo | 1.º passo de cada workflow: health check que pára com erro claro |
| 2 | Falhas têm de fazer barulho | Notificação na 1.ª falha (issue automática no GitHub ou e-mail) |
| 3 | Não depender de um único limite | Considerar **Supabase** (já ligado, sem projectos) como base principal; o Airtable fica só como painel |
| 4 | Corrigir na origem, não no código | Voltar a pôr o valor do secret sem espaços, em vez de o limpar em runtime (o PR #2 faz `echo` do secret na shell, o que é frágil) |
| 5 | Dados de mercado | Voltar a ligar Alpha Vantage / FMP: fontes estruturadas são mais baratas e fiáveis do que web search |
| 6 | Modelo | Actualizar para a família Claude mais recente |

## Decisões pendentes (tuas)

1. Fechar o PR #2 (obsoleto)?
2. Mergear ou fechar o PR #4 (glossário)?
3. Airtable: fazer upgrade do plano, esperar pelo reset mensal ou migrar para Supabase?
4. O próximo projecto continua a ser sobre catalisadores de mercado, ou é outro domínio?
