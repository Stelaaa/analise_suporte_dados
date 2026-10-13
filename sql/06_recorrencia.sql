-- =====================================================================
-- 06_recorrencia.sql
-- Pergunta de negócio: os chamados de "Pontuação divergente" têm causa
-- comum? Hipótese: reimportação de lotes de vendas gera duplicidade, a
-- pontuação no app sobe/oscila e o participante abre chamado.
-- Teste: cruzar volume semanal de chamados com duplicatas por lote.
-- =====================================================================

DROP VIEW IF EXISTS vw_duplicatas_por_lote;
CREATE VIEW vw_duplicatas_por_lote AS
SELECT v.lote_importacao,
       CAST(SUBSTR(v.lote_importacao, 6, 2) AS INTEGER) AS semana_campanha,
       COUNT(*)                                          AS vendas_no_lote,
       SUM(o.id_registro IS NOT NULL)                    AS duplicatas
FROM stg_vendas v
LEFT JOIN dq_ocorrencias o
       ON o.id_registro = v.id_venda AND o.regra = 'DQ01 Venda duplicada'
GROUP BY v.lote_importacao
ORDER BY v.lote_importacao;

DROP VIEW IF EXISTS vw_recorrencia_semanal;
CREATE VIEW vw_recorrencia_semanal AS
SELECT s.semana_campanha,
       COALESCE(d.duplicatas, 0)                                    AS duplicatas_importadas,
       SUM(s.categoria = 'Pontuação divergente')                    AS chamados_pontuacao,
       COUNT(*)                                                     AS chamados_total
FROM vw_chamados_sla s
LEFT JOIN vw_duplicatas_por_lote d ON d.semana_campanha = s.semana_campanha
WHERE s.semana_campanha BETWEEN 1 AND 13
GROUP BY s.semana_campanha
ORDER BY s.semana_campanha;

-- Pareto de categorias: quais respondem por ~80% do volume
DROP VIEW IF EXISTS vw_pareto_categorias;
CREATE VIEW vw_pareto_categorias AS
SELECT categoria, chamados,
       ROUND(100.0 * SUM(chamados) OVER (ORDER BY chamados DESC
                                         ROWS UNBOUNDED PRECEDING)
             / SUM(chamados) OVER (), 1) AS pct_acumulado
FROM (SELECT categoria, COUNT(*) AS chamados FROM stg_chamados GROUP BY categoria)
ORDER BY chamados DESC;
