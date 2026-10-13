# KB-003 · Importação de base

**Categoria:** Importação de base · **Prioridade padrão:** Crítica · **Atualizado em:** out/2026

## Sintoma

O cliente enviou o arquivo de vendas (ou participantes / metas) e a importação falhou, ficou incompleta ou os números ficaram estranhos depois.

## Checklist antes de importar

| # | Verificação | Como |
|---|---|---|
| 1 | Layout: colunas, nomes e ordem | comparar com o modelo do cliente |
| 2 | Tipos: data `AAAA-MM-DD`, valores com ponto decimal | amostra de 20 linhas |
| 3 | **O arquivo já foi importado?** | comparar nome, nº de linhas e soma de `valor_total` com os lotes anteriores |
| 4 | Período: todas as datas dentro da campanha | regra DQ03 |
| 5 | Matrículas existem no cadastro | regra DQ02 |
| 6 | Valores > 0 | regra DQ04 |

## Importação interrompida

Se a importação cair no meio, **não suba o arquivo de novo** sem antes:

1. contar quantas linhas do lote já entraram;
2. remover o lote parcial (ou importar só as linhas faltantes).

Foi exatamente isso que gerou as 248 duplicatas do LOTE-09 neste trimestre.

## Depois de importar

Rodar `python src/pipeline.py` (ou as consultas de `sql/02_qualidade_dados.sql`) e conferir a aba **Qualidade - resumo**. Qualquer ocorrência bloqueante → avisar Campanhas antes de publicar a prévia.
