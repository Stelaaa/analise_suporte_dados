-- =====================================================================
-- 01 · Visão geral · cartões do painel
-- Consulta somente leitura sobre stg_chamados (banco/case_suporte.db).
--
-- Resultado esperado (igual ao Power BI):
--   chamados 640 · backlog 52 · tmr_horas 13,4 · pct_reabertura 7,8
--   pct_sla_resolucao 73,3 · pct_sla_primeira_resposta 66,4
-- =====================================================================

WITH sla AS (                                  -- prazos de SLA em horas
    SELECT 'Crítica' AS prioridade, 0.5 AS h_resposta,  4 AS h_resolucao UNION ALL
    SELECT 'Alta',                  1.0,                8                UNION ALL
    SELECT 'Média',                 2.0,               24                UNION ALL
    SELECT 'Baixa',                 4.0,               48
),
chamados AS (
    SELECT c.*,
           (julianday(c.data_primeira_resposta) - julianday(c.data_abertura)) * 24 AS horas_resposta,
           CASE WHEN c.data_resolucao <> ''
                THEN (julianday(c.data_resolucao) - julianday(c.data_abertura)) * 24 END AS horas_resolucao,
           s.h_resposta, s.h_resolucao
    FROM stg_chamados c
    JOIN sla s ON s.prioridade = c.prioridade
)
SELECT
    COUNT(*)                                                         AS chamados,
    SUM(CASE WHEN status <> 'Resolvido' THEN 1 ELSE 0 END)           AS backlog,
    ROUND(AVG(horas_resolucao), 1)                                   AS tmr_horas,
    ROUND(100.0 * SUM(CASE WHEN reaberto = 'Sim' THEN 1 ELSE 0 END) / COUNT(*), 1)
                                                                     AS pct_reabertura,
    ROUND(100.0 * AVG(CASE WHEN horas_resolucao IS NULL THEN NULL
                           WHEN horas_resolucao <= h_resolucao THEN 1 ELSE 0 END), 1)
                                                                     AS pct_sla_resolucao,
    ROUND(100.0 * AVG(CASE WHEN horas_resposta <= h_resposta THEN 1 ELSE 0 END), 1)
                                                                     AS pct_sla_primeira_resposta
FROM chamados;
