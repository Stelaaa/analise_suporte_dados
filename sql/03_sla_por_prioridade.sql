-- =====================================================================
-- 03 · Visão geral · gráfico "SLA por prioridade"
--
-- Resultado esperado (% no prazo):
--   prioridade | 1ª resposta | resolução
--   Baixa      |    98,1     |   79,4
--   Média      |    81,0     |   80,8
--   Alta       |    52,7     |   68,5
--   Crítica    |    29,0     |   62,7
-- =====================================================================

WITH sla AS (
    SELECT 'Crítica' AS prioridade, 0.5 AS h_resposta,  4 AS h_resolucao, 4 AS ordem UNION ALL
    SELECT 'Alta',                  1.0,                8,                3          UNION ALL
    SELECT 'Média',                 2.0,               24,                2          UNION ALL
    SELECT 'Baixa',                 4.0,               48,                1
),
chamados AS (
    SELECT c.prioridade, s.h_resposta, s.h_resolucao, s.ordem,
           (julianday(c.data_primeira_resposta) - julianday(c.data_abertura)) * 24 AS horas_resposta,
           CASE WHEN c.data_resolucao <> ''
                THEN (julianday(c.data_resolucao) - julianday(c.data_abertura)) * 24 END AS horas_resolucao
    FROM stg_chamados c
    JOIN sla s ON s.prioridade = c.prioridade
)
SELECT
    prioridade,
    COUNT(*)                                                                      AS chamados,
    ROUND(100.0 * AVG(CASE WHEN horas_resposta <= h_resposta THEN 1 ELSE 0 END), 1) AS pct_sla_primeira_resposta,
    ROUND(100.0 * AVG(CASE WHEN horas_resolucao IS NULL THEN NULL
                           WHEN horas_resolucao <= h_resolucao THEN 1 ELSE 0 END), 1) AS pct_sla_resolucao
FROM chamados
GROUP BY prioridade, ordem
ORDER BY ordem;
