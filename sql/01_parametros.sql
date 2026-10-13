-- =====================================================================
-- 01_parametros.sql
-- Tabelas de parâmetro: regras da campanha e matriz de SLA.
-- Manter regra de negócio em tabela (e não "chumbada" no código) permite
-- que a área de negócio altere faixas sem mexer na query de apuração.
-- Dialeto: SQLite (roda sem instalar nada). Ver docs/adaptacao_sql.md
-- para SQL Server / PostgreSQL.
-- =====================================================================

DROP TABLE IF EXISTS par_faixas_faturamento;
CREATE TABLE par_faixas_faturamento (
    faixa           TEXT PRIMARY KEY,
    ating_min       REAL NOT NULL,   -- inclusivo
    ating_max       REAL NOT NULL,   -- exclusivo
    pontos          INTEGER NOT NULL
);
INSERT INTO par_faixas_faturamento VALUES
    ('F0 - abaixo de 80%',   0.00,  0.80,    0),
    ('F1 - 80% a 99%',       0.80,  1.00, 1000),
    ('F2 - 100% a 119%',     1.00,  1.20, 2500),
    ('F3 - 120% ou mais',    1.20, 99.00, 4000);

DROP TABLE IF EXISTS par_bonus;
CREATE TABLE par_bonus (
    mecanica        TEXT PRIMARY KEY,
    pontos          INTEGER NOT NULL,
    descricao       TEXT
);
INSERT INTO par_bonus VALUES
    ('Positivação', 1500, 'Bônus se nº de clientes distintos atendidos >= meta de positivação');

DROP TABLE IF EXISTS par_sla;
CREATE TABLE par_sla (
    prioridade              TEXT PRIMARY KEY,
    horas_primeira_resposta REAL NOT NULL,
    horas_resolucao         REAL NOT NULL,
    ordem                   INTEGER NOT NULL
);
INSERT INTO par_sla VALUES
    ('Crítica', 0.5,  4, 1),
    ('Alta',    1.0,  8, 2),
    ('Média',   2.0, 24, 3),
    ('Baixa',   4.0, 48, 4);
