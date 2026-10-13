-- =====================================================================
-- 05_chamados_sla.sql
-- Indicadores da fila de suporte: SLA de 1ª resposta e de resolução,
-- backlog, reabertura e recorrência por categoria.
-- Observação: o tempo está em horas corridas. Em produção o SLA costuma
-- ser em horas úteis — ver docs/matriz_sla.md (seção "Limitações").
-- =====================================================================

DROP VIEW IF EXISTS vw_chamados;
CREATE VIEW vw_chamados AS
SELECT c.*,
       s.horas_primeira_resposta                                      AS sla_resp_h,
       s.horas_resolucao                                              AS sla_res_h,
       ROUND((julianday(c.data_primeira_resposta) - julianday(c.data_abertura)) * 24, 2) AS horas_resposta,
       CASE WHEN c.data_resolucao <> ''
            THEN ROUND((julianday(c.data_resolucao) - julianday(c.data_abertura)) * 24, 2) END AS horas_resolucao,
       strftime('%Y-W%W', c.data_abertura)                            AS semana,
       CAST((julianday(date(c.data_abertura)) - julianday('2026-07-01')) / 7 AS INTEGER) + 1 AS semana_campanha
FROM stg_chamados c
JOIN par_sla s ON s.prioridade = c.prioridade;

DROP VIEW IF EXISTS vw_chamados_sla;
CREATE VIEW vw_chamados_sla AS
SELECT *,
       CASE WHEN horas_resposta <= sla_resp_h THEN 1 ELSE 0 END AS resp_no_prazo,
       CASE WHEN horas_resolucao IS NULL THEN NULL
            WHEN horas_resolucao <= sla_res_h THEN 1 ELSE 0 END AS res_no_prazo
FROM vw_chamados;

-- KPIs por categoria
DROP VIEW IF EXISTS vw_kpi_categoria;
CREATE VIEW vw_kpi_categoria AS
SELECT categoria,
       COUNT(*)                                                       AS chamados,
       ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM stg_chamados), 1) AS pct_volume,
       ROUND(100.0 * AVG(resp_no_prazo), 1)                           AS pct_sla_resposta,
       ROUND(100.0 * AVG(res_no_prazo), 1)                            AS pct_sla_resolucao,
       ROUND(AVG(horas_resolucao), 1)                                 AS tmr_horas,
       ROUND(100.0 * SUM(reaberto = 'Sim') / COUNT(*), 1)             AS pct_reabertura,
       SUM(status <> 'Resolvido')                                     AS backlog
FROM vw_chamados_sla
GROUP BY categoria
ORDER BY chamados DESC;

-- KPIs por prioridade
DROP VIEW IF EXISTS vw_kpi_prioridade;
CREATE VIEW vw_kpi_prioridade AS
SELECT c.prioridade,
       COUNT(*)                                   AS chamados,
       MAX(c.sla_res_h)                           AS sla_resolucao_h,
       ROUND(100.0 * AVG(c.resp_no_prazo), 1)     AS pct_sla_resposta,
       ROUND(100.0 * AVG(c.res_no_prazo), 1)      AS pct_sla_resolucao,
       ROUND(AVG(c.horas_resolucao), 1)           AS tmr_horas
FROM vw_chamados_sla c
JOIN par_sla s ON s.prioridade = c.prioridade
GROUP BY c.prioridade
ORDER BY MIN(s.ordem);

-- KPIs por analista (para gestão de fila, não para ranking punitivo)
DROP VIEW IF EXISTS vw_kpi_analista;
CREATE VIEW vw_kpi_analista AS
SELECT analista,
       COUNT(*)                                AS chamados,
       ROUND(100.0 * AVG(res_no_prazo), 1)     AS pct_sla_resolucao,
       ROUND(AVG(horas_resolucao), 1)          AS tmr_horas,
       SUM(status <> 'Resolvido')              AS backlog
FROM vw_chamados_sla
GROUP BY analista
ORDER BY analista;

-- Visão geral (cards do topo do dashboard)
DROP VIEW IF EXISTS vw_kpi_geral;
CREATE VIEW vw_kpi_geral AS
SELECT COUNT(*)                                          AS chamados,
       SUM(status = 'Resolvido')                         AS resolvidos,
       SUM(status <> 'Resolvido')                        AS backlog,
       ROUND(100.0 * AVG(resp_no_prazo), 1)              AS pct_sla_resposta,
       ROUND(100.0 * AVG(res_no_prazo), 1)               AS pct_sla_resolucao,
       ROUND(AVG(horas_resolucao), 1)                    AS tmr_horas,
       ROUND(100.0 * SUM(reaberto = 'Sim') / COUNT(*), 1) AS pct_reabertura
FROM vw_chamados_sla;
