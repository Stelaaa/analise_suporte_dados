-- =====================================================================
-- 05 · Recorrência · mapa de calor "Chamados por categoria e semana"
-- Uma linha por categoria e uma coluna por semana da campanha.
-- A coluna "fora" conta os chamados abertos depois da semana 13 (7 no total),
-- que aparecem como coluna em branco na matriz do Power BI.
--
-- Resultado esperado: só "Pontuação divergente" dispara nas semanas 5 (60)
-- e 9 (59); total da linha = 207. Total geral = 640.
-- =====================================================================

WITH chamados AS (
    SELECT categoria,
           CASE WHEN date(data_abertura) BETWEEN '2026-07-01' AND '2026-09-29'
                THEN CAST((julianday(date(data_abertura)) - julianday('2026-07-01')) / 7 AS INTEGER) + 1
           END AS semana
    FROM stg_chamados
)
SELECT
    categoria,
    SUM(CASE WHEN semana IS NULL THEN 1 ELSE 0 END) AS fora,
    SUM(CASE WHEN semana = 1  THEN 1 ELSE 0 END) AS s01,
    SUM(CASE WHEN semana = 2  THEN 1 ELSE 0 END) AS s02,
    SUM(CASE WHEN semana = 3  THEN 1 ELSE 0 END) AS s03,
    SUM(CASE WHEN semana = 4  THEN 1 ELSE 0 END) AS s04,
    SUM(CASE WHEN semana = 5  THEN 1 ELSE 0 END) AS s05,
    SUM(CASE WHEN semana = 6  THEN 1 ELSE 0 END) AS s06,
    SUM(CASE WHEN semana = 7  THEN 1 ELSE 0 END) AS s07,
    SUM(CASE WHEN semana = 8  THEN 1 ELSE 0 END) AS s08,
    SUM(CASE WHEN semana = 9  THEN 1 ELSE 0 END) AS s09,
    SUM(CASE WHEN semana = 10 THEN 1 ELSE 0 END) AS s10,
    SUM(CASE WHEN semana = 11 THEN 1 ELSE 0 END) AS s11,
    SUM(CASE WHEN semana = 12 THEN 1 ELSE 0 END) AS s12,
    SUM(CASE WHEN semana = 13 THEN 1 ELSE 0 END) AS s13,
    COUNT(*)                                      AS total
FROM chamados
GROUP BY categoria
ORDER BY categoria;
