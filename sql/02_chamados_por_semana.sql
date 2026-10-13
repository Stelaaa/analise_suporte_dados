-- =====================================================================
-- 02 · Visão geral · gráfico "Chamados por semana"
-- Semana da campanha: semana 1 começa em 01/07/2026 (13 semanas no total).
--
-- Resultado esperado: picos de 90 chamados na semana 5 e 91 na semana 9;
-- as demais semanas ficam entre 30 e 51.
-- =====================================================================

SELECT
    CAST((julianday(date(data_abertura)) - julianday('2026-07-01')) / 7 AS INTEGER) + 1 AS semana,
    COUNT(*) AS chamados
FROM stg_chamados
WHERE date(data_abertura) BETWEEN '2026-07-01' AND '2026-09-29'   -- semanas 1 a 13
GROUP BY semana
ORDER BY semana;
