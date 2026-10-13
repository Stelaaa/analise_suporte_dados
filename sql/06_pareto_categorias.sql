-- =====================================================================
-- 06 · Recorrência · gráfico de Pareto por categoria
--
-- Resultado esperado:
--   Pontuação divergente     207  32,3%
--   Acesso / login           103  48,4%
--   Resgate não creditado     98  63,8%
--   Dúvida de regulamento     89  77,7%
--   Relatório / dashboard     51  85,6%
--   Importação de base        47  93,0%
--   Cadastro de participante  45 100,0%
-- =====================================================================

WITH por_categoria AS (
    SELECT categoria, COUNT(*) AS chamados
    FROM stg_chamados
    GROUP BY categoria
)
SELECT
    categoria,
    chamados,
    ROUND(100.0 * chamados / SUM(chamados) OVER (), 1) AS pct_volume,
    ROUND(100.0 * SUM(chamados) OVER (ORDER BY chamados DESC
                                      ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)
                / SUM(chamados) OVER (), 1)            AS pct_acumulado
FROM por_categoria
ORDER BY chamados DESC;
