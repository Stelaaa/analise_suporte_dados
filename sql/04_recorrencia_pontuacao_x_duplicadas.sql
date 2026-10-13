-- =====================================================================
-- 04 · Recorrência · gráfico "Chamados de pontuação x vendas duplicadas"
--
-- Uma venda é duplicada quando aparece de novo com exatamente o mesmo
-- conteúdo (matrícula, data, cliente, produto, quantidade e valor). A
-- primeira ocorrência é a original; as seguintes são duplicatas.
--
-- Resultado esperado:
--   semana 5 → 696 vendas duplicadas e 60 chamados de pontuação
--   semana 9 → 248 vendas duplicadas e 59 chamados de pontuação
--   demais semanas → 0 duplicadas e de 3 a 14 chamados
--   total de vendas duplicadas: 944
-- =====================================================================

WITH vendas_numeradas AS (
    SELECT data_venda,
           ROW_NUMBER() OVER (
               PARTITION BY matricula, data_venda, cod_cliente, cod_produto, quantidade, valor_total
               ORDER BY id_venda
           ) AS ocorrencia
    FROM stg_vendas
),
duplicadas_por_semana AS (
    SELECT CAST((julianday(data_venda) - julianday('2026-07-01')) / 7 AS INTEGER) + 1 AS semana,
           COUNT(*) AS vendas_duplicadas
    FROM vendas_numeradas
    WHERE ocorrencia > 1
    GROUP BY semana
),
pontuacao_por_semana AS (
    SELECT CAST((julianday(date(data_abertura)) - julianday('2026-07-01')) / 7 AS INTEGER) + 1 AS semana,
           COUNT(*) AS chamados_pontuacao
    FROM stg_chamados
    WHERE categoria = 'Pontuação divergente'
      AND date(data_abertura) BETWEEN '2026-07-01' AND '2026-09-29'
    GROUP BY semana
)
SELECT p.semana,
       p.chamados_pontuacao,
       COALESCE(d.vendas_duplicadas, 0) AS vendas_duplicadas
FROM pontuacao_por_semana p
LEFT JOIN duplicadas_por_semana d ON d.semana = p.semana
ORDER BY p.semana;
