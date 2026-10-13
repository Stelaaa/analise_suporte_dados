# Rodando o SQL no DBeaver, no HeidiSQL e em outros bancos

O case usa **SQLite**: o banco é um arquivo único, sem servidor para instalar. Ele abre direto no **DBeaver** e no **HeidiSQL**.

## 1. O banco pronto

O arquivo [`banco/case_suporte.db`](../banco/case_suporte.db) já vem com as tabelas de origem carregadas:

| Tabela            | Linhas |
| ----------------- | -----: |
| stg_campanha      |      1 |
| stg_participantes |    180 |
| stg_metas         |    174 |
| stg_produtos      |      8 |
| stg_vendas        |  9.999 |
| stg_resgates      |     87 |
| stg_chamados      |    640 |

Para recriar o banco a partir dos CSVs: `python src/criar_banco.py`.

## 2. Abrir no DBeaver

1. **Banco de dados → Nova conexão** (ou o ícone de tomada com +).
2. Escolha **SQLite** → **Próximo**.
3. Em **Caminho (Path)**, clique em **Abrir...** e selecione `banco/case_suporte.db`.
4. Se o DBeaver pedir para **baixar o driver**, clique em **Download**.
5. **Concluir**. As tabelas `stg_*` aparecem em **Tabelas**.

**Rodar uma consulta:** **Arquivo → Abrir arquivo** → escolha uma consulta de `sql/` (por exemplo `01_visao_geral_indicadores.sql`) → associe à conexão do case → **Executar** (`Ctrl + Enter`). O resultado aparece na grade embaixo.

## 3. Abrir no HeidiSQL

1. Na tela **Gerenciador de sessões**, clique em **Nova**.
2. Em **Tipo de rede**, escolha **SQLite**.
3. Em **Nome do arquivo de banco de dados**, clique na pasta e selecione `banco/case_suporte.db`.
4. **Abrir**.

**Rodar uma consulta:** **Arquivo → Carregar arquivo SQL** → escolha uma consulta de `sql/` → **Executar** (`F9`).

> O HeidiSQL suporta SQLite a partir da versão 11.0. Se a opção não aparecer em "Tipo de rede", atualize o programa.

## 4. As consultas e o resultado esperado

As consultas de `sql/` são **somente leitura** (`SELECT`): leem as tabelas `stg_*` e não criam, alteram nem apagam nada. Cada uma reproduz um visual do painel Power BI e pode ser rodada em qualquer ordem.

| Consulta | Visual no Power BI | Resultado esperado |
|---|---|---|
| `01_visao_geral_indicadores.sql` | cartões da Visão geral | 640 chamados · backlog 52 · TMR 13,4 h · reabertura 7,8% · SLA resolução 73,3% · SLA 1ª resposta 66,4% |
| `02_chamados_por_semana.sql` | Chamados por semana | picos de 90 (semana 5) e 91 (semana 9) |
| `03_sla_por_prioridade.sql` | SLA por prioridade | Crítica: 29,0% de 1ª resposta no prazo |
| `04_recorrencia_pontuacao_x_duplicadas.sql` | Chamados de pontuação × vendas duplicadas | semana 5: 60 chamados e 696 duplicadas · semana 9: 59 e 248 |
| `05_mapa_calor_categoria_semana.sql` | Mapa de calor | Pontuação divergente: 60 (s05) e 59 (s09), total 207 |
| `06_pareto_categorias.sql` | Pareto | Pontuação divergente 32,3% · 4 categorias somam 77,7% |

> Os scripts que preparam os dados para o Power BI (com `CREATE`, `INSERT` etc.) ficam separados em `src/sql_preparacao/` e são usados só pelo pipeline em Python.

## 5. Adaptando para MySQL, SQL Server ou PostgreSQL

A lógica é a mesma; muda a sintaxe em poucos pontos.

| SQLite (no case) | MySQL 8.0+ | SQL Server | PostgreSQL |
|---|---|---|---|
| `(julianday(b) - julianday(a)) * 24` (horas) | `TIMESTAMPDIFF(MINUTE, a, b) / 60` | `DATEDIFF(MINUTE, a, b) / 60.0` | `EXTRACT(EPOCH FROM (b - a)) / 3600` |
| `julianday(b) - julianday(a)` (dias) | `DATEDIFF(b, a)` | `DATEDIFF(DAY, a, b)` | `b::date - a::date` |
| `strftime('%Y-W%W', d)` | `DATE_FORMAT(d, '%x-W%v')` | `CONCAT(YEAR(d), '-W', DATEPART(WEEK, d))` | `to_char(d, 'IYYY-"W"IW')` |
| <code>a &#124;&#124; b</code> (concatenação) | `CONCAT(a, b)` | `CONCAT(a, b)` | <code>a &#124;&#124; b</code> |
| `SUM(cond)` com booleano | `SUM(cond)` (igual) | `SUM(CASE WHEN cond THEN 1 ELSE 0 END)` | `SUM((cond)::int)` ou `COUNT(*) FILTER (WHERE cond)` |
| `WINDOW w AS (...)` | igual | repetir o `OVER (...)` em cada função | igual |
| `CREATE TABLE x AS WITH ... SELECT` | `CREATE TABLE x WITH ... SELECT` (sem `AS`) | `WITH ... SELECT ... INTO x` | igual |
| `ALTER TABLE ... ADD COLUMN` + `UPDATE` | `GENERATED ALWAYS AS (a + b) STORED` | coluna computada `AS (a + b)` | `GENERATED ALWAYS AS (a + b) STORED` |

Window functions (`ROW_NUMBER`, `FIRST_VALUE`, `SUM() OVER`) funcionam nos quatro. No MySQL, exigem a versão **8.0 ou superior** (no MariaDB, 10.2 ou superior).

**Cuidado no MySQL:** <code>&#124;&#124;</code> significa **OU lógico**, não concatenação, a menos que o modo `PIPES_AS_CONCAT` esteja ligado. Use sempre `CONCAT()`.

### Para rodar em MySQL ou MariaDB (pelo HeidiSQL)

1. Conecte no servidor MySQL/MariaDB e crie um banco: `CREATE DATABASE case_suporte;`
2. Importe cada CSV de `data/raw/` como tabela `stg_<nome>`: **Ferramentas → Importar arquivo CSV**, separador **vírgula**, primeira linha como cabeçalho.
3. Abra os scripts de `sql/` e troque os trechos da tabela acima antes de executar.

Fontes: [MySQL 8.0, WITH (CTE)](https://dev.mysql.com/doc/refman/8.0/en/with.html) · [MySQL 8.0, janelas nomeadas](https://dev.mysql.com/doc/refman/8.0/en/window-functions-named-windows.html) · [DBeaver, driver SQLite](https://dbeaver.com/docs/dbeaver/Database-driver-SQLite/) · [HeidiSQL](https://en.wikipedia.org/wiki/HeidiSQL)
