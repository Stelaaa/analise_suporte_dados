-- =====================================================================
-- 04_resgates.sql
-- Cruza resgates com o saldo apurado. Resgate acima do saldo é o tipo de
-- divergência que, se passar, vira prejuízo (prêmio entregue sem lastro).
-- =====================================================================

DROP VIEW IF EXISTS vw_saldo_resgates;
CREATE VIEW vw_saldo_resgates AS
SELECT a.matricula, a.nome, a.situacao,
       a.pontos_total                          AS pontos_apurados,
       COALESCE(SUM(r.pontos), 0)              AS pontos_resgatados,
       a.pontos_total - COALESCE(SUM(r.pontos), 0) AS saldo,
       COUNT(r.id_resgate)                     AS qtd_resgates
FROM apuracao a
LEFT JOIN stg_resgates r ON r.matricula = a.matricula
GROUP BY a.matricula, a.nome, a.situacao, a.pontos_total;

-- DQ07 · Resgate acima do saldo
INSERT INTO dq_ocorrencias
SELECT 'DQ07 Resgate acima do saldo', 'Bloqueia', 'resgates', NULL, matricula,
       'Apurado ' || pontos_apurados || ' pts, resgatado ' || pontos_resgatados ||
       ' pts (saldo ' || saldo || ')'
FROM vw_saldo_resgates
WHERE saldo < 0;
