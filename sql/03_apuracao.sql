-- =====================================================================
-- 03_apuracao.sql
-- Apuração da campanha a partir das vendas válidas.
--   Regra 1 · Faturamento: atingimento = faturamento / meta → faixa de pontos
--   Regra 2 · Positivação: clientes distintos >= meta → bônus
--   Elegibilidade: participante Ativo e com meta cadastrada
-- Também calcula o "impacto" se a apuração tivesse rodado sem o tratamento
-- de qualidade — é o número que mostra ao cliente o valor da conferência.
-- =====================================================================

DROP TABLE IF EXISTS apuracao;
CREATE TABLE apuracao AS
WITH realizado AS (
    SELECT matricula,
           ROUND(SUM(valor_total), 2)      AS faturamento,
           COUNT(DISTINCT cod_cliente)     AS clientes_positivados,
           COUNT(*)                        AS qtd_vendas
    FROM vw_vendas_validas
    GROUP BY matricula
),
base AS (
    SELECT p.matricula, p.nome, p.cargo, p.regional, p.status,
           m.meta_faturamento, m.meta_positivacao,
           COALESCE(r.faturamento, 0)          AS faturamento,
           COALESCE(r.clientes_positivados, 0) AS clientes_positivados,
           COALESCE(r.qtd_vendas, 0)           AS qtd_vendas,
           CASE WHEN m.meta_faturamento > 0
                THEN COALESCE(r.faturamento, 0) / m.meta_faturamento END AS atingimento
    FROM vw_participantes p
    LEFT JOIN stg_metas m ON m.matricula = p.matricula
    LEFT JOIN realizado r ON r.matricula = p.matricula
)
SELECT b.*,
       CASE WHEN b.status <> 'Ativo'          THEN 'Inelegível - inativo'
            WHEN b.meta_faturamento IS NULL   THEN 'Pendente - sem meta'
            ELSE 'Elegível' END                                         AS situacao,
       f.faixa,
       CASE WHEN b.status = 'Ativo' AND b.meta_faturamento IS NOT NULL
            THEN f.pontos ELSE 0 END                                    AS pontos_faturamento,
       CASE WHEN b.status = 'Ativo' AND b.meta_faturamento IS NOT NULL
             AND b.clientes_positivados >= b.meta_positivacao
            THEN (SELECT pontos FROM par_bonus WHERE mecanica = 'Positivação')
            ELSE 0 END                                                  AS pontos_positivacao
FROM base b
LEFT JOIN par_faixas_faturamento f
       ON b.atingimento >= f.ating_min AND b.atingimento < f.ating_max;

ALTER TABLE apuracao ADD COLUMN pontos_total INTEGER;
UPDATE apuracao SET pontos_total = pontos_faturamento + pontos_positivacao;

-- ---------------------------------------------------------------------
-- Apuração "ingênua": mesma regra, mas usando stg_vendas sem tratamento.
-- Serve só para medir o impacto da etapa de qualidade.
-- ---------------------------------------------------------------------
DROP TABLE IF EXISTS apuracao_sem_tratamento;
CREATE TABLE apuracao_sem_tratamento AS
WITH realizado AS (
    SELECT UPPER(TRIM(matricula)) AS matricula,
           SUM(valor_total) AS faturamento,
           COUNT(DISTINCT cod_cliente) AS clientes_positivados
    FROM stg_vendas
    GROUP BY UPPER(TRIM(matricula))
)
SELECT p.matricula,
       CASE WHEN p.status = 'Ativo' AND m.meta_faturamento IS NOT NULL
            THEN f.pontos ELSE 0 END
     + CASE WHEN p.status = 'Ativo' AND m.meta_faturamento IS NOT NULL
             AND COALESCE(r.clientes_positivados, 0) >= m.meta_positivacao
            THEN (SELECT pontos FROM par_bonus WHERE mecanica = 'Positivação') ELSE 0 END
       AS pontos_total
FROM vw_participantes p
LEFT JOIN stg_metas m ON m.matricula = p.matricula
LEFT JOIN realizado r ON r.matricula = p.matricula
LEFT JOIN par_faixas_faturamento f
       ON COALESCE(r.faturamento, 0) / m.meta_faturamento >= f.ating_min
      AND COALESCE(r.faturamento, 0) / m.meta_faturamento <  f.ating_max;

DROP VIEW IF EXISTS vw_impacto_qualidade;
CREATE VIEW vw_impacto_qualidade AS
SELECT a.matricula, a.nome, a.regional,
       s.pontos_total               AS pontos_sem_tratamento,
       a.pontos_total               AS pontos_apurados,
       s.pontos_total - a.pontos_total AS diferenca
FROM apuracao a
JOIN apuracao_sem_tratamento s ON s.matricula = a.matricula
WHERE s.pontos_total <> a.pontos_total;

-- Resumo por faixa (para o painel de Campanhas)
DROP VIEW IF EXISTS vw_apuracao_faixas;
CREATE VIEW vw_apuracao_faixas AS
SELECT COALESCE(faixa, '(sem meta)') AS faixa,
       COUNT(*)                      AS participantes,
       SUM(pontos_total)             AS pontos
FROM apuracao
WHERE situacao = 'Elegível'
GROUP BY faixa
ORDER BY faixa;
