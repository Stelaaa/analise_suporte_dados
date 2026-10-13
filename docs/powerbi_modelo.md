# Modelo Power BI · Painel de Suporte & Apuração

Especificação do painel para Power BI a partir das saídas do pipeline. As tabelas vêm de `reports/case.db` (via ODBC SQLite) ou das abas de `reports/indicadores_suporte.xlsx` e `reports/apuracao_campanha.xlsx`.

## Modelo estrela

```
                 dCalendario
                      │ (data)
dPrioridade ── fChamados ── dCategoria
      │
   par_sla

dParticipante ── fApuracao
      │
      ├── fVendas ── dProduto
      ├── fResgates
      └── fOcorrenciasDQ
```

| Tabela | Origem | Grão |
|---|---|---|
| fChamados | `vw_chamados_sla` | 1 linha por chamado |
| fVendas | `stg_vendas` + coluna `motivo_bloqueio` (merge com `dq_ocorrencias` no Power Query) | 1 linha por venda |
| fOcorrenciasDQ | `dq_ocorrencias` | 1 linha por ocorrência |
| fApuracao | `apuracao` | 1 linha por participante |
| fResgates | `stg_resgates` | 1 linha por resgate |
| dParticipante | `vw_participantes` | matrícula |
| dCalendario | gerada no Power Query | dia, com coluna `DiaUtil` |

## Medidas DAX

```dax
Chamados = COUNTROWS ( fChamados )

Backlog =
CALCULATE ( [Chamados], fChamados[status] <> "Resolvido" )

% SLA Resolução =
DIVIDE (
    CALCULATE ( [Chamados], fChamados[res_no_prazo] = 1 ),
    CALCULATE ( [Chamados], NOT ISBLANK ( fChamados[res_no_prazo] ) )
)

% SLA 1ª Resposta =
DIVIDE ( CALCULATE ( [Chamados], fChamados[resp_no_prazo] = 1 ), [Chamados] )

TMR (h) = AVERAGE ( fChamados[horas_resolucao] )

% Reabertura =
DIVIDE ( CALCULATE ( [Chamados], fChamados[reaberto] = "Sim" ), [Chamados] )

% do Volume =
DIVIDE ( [Chamados], CALCULATE ( [Chamados], ALL ( fChamados[categoria] ) ) )

Pareto % Acumulado =
VAR _atual = [Chamados]
VAR _tabela =
    ADDCOLUMNS ( ALL ( fChamados[categoria] ), "@qtd", [Chamados] )
RETURN
    DIVIDE (
        SUMX ( FILTER ( _tabela, [@qtd] >= _atual ), [@qtd] ),
        SUMX ( _tabela, [@qtd] )
    )

Pontos Apurados = SUM ( fApuracao[pontos_total] )

Ocorrências Bloqueantes =
CALCULATE ( COUNTROWS ( fOcorrenciasDQ ), fOcorrenciasDQ[severidade] = "Bloqueia" )

Faturamento Inflado (duplicatas) =
CALCULATE (
    SUM ( fVendas[valor_total] ),
    fVendas[motivo_bloqueio] = "DQ01 Venda duplicada"
)

Chamados Semana Anterior =
CALCULATE ( [Chamados], DATEADD ( dCalendario[Data], -7, DAY ) )

Variação Semanal % = DIVIDE ( [Chamados] - [Chamados Semana Anterior], [Chamados Semana Anterior] )
```

## Páginas

| Página | Para quem | Visuais |
|---|---|---|
| 1 · Visão geral da fila | gestão do Suporte | cartões (Chamados, Backlog, % SLA Resolução, % SLA 1ª Resposta, TMR, % Reabertura) · linha semanal de chamados · barras de SLA por prioridade |
| 2 · Categorias e recorrência | Suporte & Dados | Pareto (colunas + linha acumulada) · matriz categoria × semana com formatação condicional · barras de reabertura |
| 3 · Qualidade da base | Negócio / Campanhas | barras por regra de qualidade · tabela de ocorrências com filtro por lote e matrícula · cartão Faturamento Inflado |
| 4 · Apuração | Campanhas / cliente | distribuição por faixa · pontos por regional · tabela por participante com drill-through para o extrato de vendas |

## Boas práticas aplicadas

- Medidas explícitas (nada de soma implícita em coluna).
- Parâmetros de SLA e faixas em tabelas, não em `IF` dentro da medida.
- Drill-through da página 4 para o extrato — é o que o suporte anexa no chamado (ver [KB-001](kb/KB-001-pontuacao-divergente.md)).
- Atualização agendada após cada importação de lote; o cartão "Ocorrências Bloqueantes" fica no topo da página 3 como semáforo.
