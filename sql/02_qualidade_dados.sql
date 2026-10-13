-- =====================================================================
-- 02_qualidade_dados.sql
-- Regras de qualidade aplicadas ANTES da apuração.
-- Cada regra grava ocorrências em dq_ocorrencias com código, registro e
-- detalhe — isso vira a evidência que vai para o chamado e para o cliente.
--
-- Pré-requisito: tabelas stg_* carregadas a partir de data/raw/*.csv
-- =====================================================================

DROP TABLE IF EXISTS dq_ocorrencias;
CREATE TABLE dq_ocorrencias (
    regra        TEXT NOT NULL,
    severidade   TEXT NOT NULL,      -- Bloqueia (sai da apuração) | Alerta (corrige e segue)
    tabela       TEXT NOT NULL,
    id_registro  TEXT,
    matricula    TEXT,
    detalhe      TEXT
);

-- ---------------------------------------------------------------------
-- DQ06 · Matrícula com espaço ou caixa diferente no cadastro
-- Alerta: é o mesmo participante digitado errado. Normaliza e segue.
-- ---------------------------------------------------------------------
INSERT INTO dq_ocorrencias
SELECT 'DQ06 Matrícula fora do padrão', 'Alerta', 'participantes',
       matricula, UPPER(TRIM(matricula)),
       'Valor original: "' || matricula || '" → normalizado: "' || UPPER(TRIM(matricula)) || '"'
FROM stg_participantes
WHERE matricula <> UPPER(TRIM(matricula));

-- Cadastro normalizado usado daqui em diante
DROP VIEW IF EXISTS vw_participantes;
CREATE VIEW vw_participantes AS
SELECT UPPER(TRIM(matricula)) AS matricula, nome, cargo, regional, data_adesao, status
FROM stg_participantes;

-- ---------------------------------------------------------------------
-- DQ05 · Participante sem meta cadastrada
-- Bloqueia: sem meta não há como apurar. Precisa de retorno do cliente.
-- ---------------------------------------------------------------------
INSERT INTO dq_ocorrencias
SELECT 'DQ05 Participante sem meta', 'Bloqueia', 'metas',
       p.matricula, p.matricula,
       p.nome || ' (' || p.regional || ') não consta no arquivo de metas'
FROM vw_participantes p
LEFT JOIN stg_metas m ON m.matricula = p.matricula
WHERE m.matricula IS NULL;

-- ---------------------------------------------------------------------
-- DQ01 · Venda duplicada (mesmo conteúdo, id diferente)
-- Típico de reimportação de lote. Mantém a 1ª ocorrência, bloqueia as demais.
-- ---------------------------------------------------------------------
INSERT INTO dq_ocorrencias
SELECT 'DQ01 Venda duplicada', 'Bloqueia', 'vendas', id_venda, matricula,
       'Duplicata de ' || id_original || ' no ' || lote_importacao
FROM (
    SELECT v.*,
           ROW_NUMBER()      OVER w AS rn,
           FIRST_VALUE(id_venda) OVER w AS id_original
    FROM stg_vendas v
    WINDOW w AS (PARTITION BY matricula, data_venda, cod_cliente, cod_produto,
                              quantidade, valor_total
                 ORDER BY id_venda)
)
WHERE rn > 1;

-- ---------------------------------------------------------------------
-- DQ02 · Venda de matrícula que não participa da campanha
-- ---------------------------------------------------------------------
INSERT INTO dq_ocorrencias
SELECT 'DQ02 Matrícula não cadastrada', 'Bloqueia', 'vendas', v.id_venda, v.matricula,
       'Matrícula ausente do cadastro de participantes'
FROM stg_vendas v
LEFT JOIN vw_participantes p ON p.matricula = UPPER(TRIM(v.matricula))
WHERE p.matricula IS NULL;

-- ---------------------------------------------------------------------
-- DQ03 · Venda fora do período da campanha
-- ---------------------------------------------------------------------
INSERT INTO dq_ocorrencias
SELECT 'DQ03 Venda fora do período', 'Bloqueia', 'vendas', v.id_venda, v.matricula,
       'Data ' || v.data_venda || ' fora de ' || c.data_inicio || ' a ' || c.data_fim
FROM stg_vendas v
CROSS JOIN stg_campanha c
WHERE v.data_venda < c.data_inicio OR v.data_venda > c.data_fim;

-- ---------------------------------------------------------------------
-- DQ04 · Valor zero ou negativo (estorno lançado como venda)
-- ---------------------------------------------------------------------
INSERT INTO dq_ocorrencias
SELECT 'DQ04 Valor inválido', 'Bloqueia', 'vendas', id_venda, matricula,
       'valor_total = ' || valor_total
FROM stg_vendas
WHERE valor_total <= 0;

-- ---------------------------------------------------------------------
-- Vendas aptas para apuração = tudo que não tem ocorrência bloqueante
-- ---------------------------------------------------------------------
DROP VIEW IF EXISTS vw_vendas_validas;
CREATE VIEW vw_vendas_validas AS
SELECT v.*
FROM stg_vendas v
WHERE NOT EXISTS (
    SELECT 1 FROM dq_ocorrencias o
    WHERE o.tabela = 'vendas' AND o.severidade = 'Bloqueia' AND o.id_registro = v.id_venda
);

-- Resumo por regra (vai para o relatório)
DROP VIEW IF EXISTS vw_dq_resumo;
CREATE VIEW vw_dq_resumo AS
SELECT regra, severidade, tabela, COUNT(*) AS ocorrencias
FROM dq_ocorrencias
GROUP BY regra, severidade, tabela
ORDER BY regra;
