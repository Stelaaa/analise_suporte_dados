# Matriz de SLA

Parâmetros em `src/sql_preparacao/01_parametros.sql` (tabela `par_sla`).

| Prioridade | Critério | 1ª resposta | Resolução | Exemplo |
|---|---|---:|---:|---|
| Crítica | campanha parada, base inteira afetada, risco financeiro | 30 min | 4 h | importação falhou; pontuação errada para uma regional |
| Alta | um participante sem pontos ou sem prêmio | 1 h | 8 h | pontuação divergente; resgate não creditado |
| Média | funcionalidade com contorno | 2 h | 24 h | erro de login; relatório desatualizado |
| Baixa | dúvida, orientação | 4 h | 48 h | dúvida de regulamento |

## Resultado no trimestre

| Prioridade | Chamados | 1ª resposta no prazo | Resolução no prazo | Tempo médio de resolução |
|---|---:|---:|---:|---:|
| Crítica | 62 | 29,0% | 62,7% | 4,0 h |
| Alta | 281 | 52,7% | 68,5% | 8,0 h |
| Média | 189 | 81,0% | 80,8% | 15,1 h |
| Baixa | 108 | 98,1% | 79,4% | 29,7 h |

**Leitura:** o SLA de 1ª resposta piora conforme a prioridade sobe — o inverso do desejado. Os chamados críticos estão entrando na mesma fila dos demais. Ação: alerta na abertura e fila separada (ver [proposta](proposta_melhoria.md), ação 7).

## Regras de contagem

- Relógio começa na abertura e para na 1ª resposta humana (resposta automática não conta).
- "Aguardando cliente" deveria pausar o relógio de resolução — **neste case não pausa** (limitação conhecida).
- Chamados em aberto entram no backlog e não no percentual de resolução.

## Limitações

O cálculo usa horas corridas (`julianday`). Para horas úteis, é preciso uma tabela calendário com expediente e feriados e somar apenas os minutos dentro do expediente — no Power BI, isso fica numa coluna calculada sobre a tabela `dCalendario` (ver [modelo Power BI](powerbi_modelo.md)).
