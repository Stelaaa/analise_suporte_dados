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

**Executar os scripts:** abra `sql/01_parametros.sql` (**Arquivo → Abrir arquivo**), associe à conexão do case e use **Executar script** (`Alt + X`). Repita de `01` a `06`, **na ordem**.

## 3. Abrir no HeidiSQL

1. Na tela **Gerenciador de sessões**, clique em **Nova**.
2. Em **Tipo de rede**, escolha **SQLite**.
3. Em **Nome do arquivo de banco de dados**, clique na pasta e selecione `banco/case_suporte.db`.
4. **Abrir**.

**Executar os scripts:** **Arquivo → Carregar arquivo SQL** → escolha `sql/01_parametros.sql` → **Executar** (`F9`). Repita de `01` a `06`, **na ordem**.

> O HeidiSQL suporta SQLite a partir da versão 11.0. Se a opção não aparecer em "Tipo de rede", atualize o programa.

## 4. Conferir se deu certo

Depois do script `06`, rode:

```sql
SELECT regra, COUNT(*) AS ocorrencias FROM dq_ocorrencias GROUP BY regra;
SELECT SUM(pontos_total) AS pontos FROM apuracao;
SELECT * FROM vw_kpi_geral;
```

| Conferência | Valor esperado |
|---|---:|
| DQ01 Venda duplicada | 944 |
| DQ02 Matrícula não cadastrada | 55 |
| DQ03 Venda fora do período | 70 |
| DQ04 Valor inválido | 38 |
| DQ05 Participante sem meta | 6 |
| DQ06 Matrícula fora do padrão | 12 |
| DQ07 Resgate acima do saldo | 28 |
| Pontos apurados | 388.000 |
| Chamados / Backlog | 640 / 52 |
| % SLA 1ª resposta / resolução | 66,4% / 73,3% |

As consultas de cada etapa ficam salvas como **views** (`vw_...`) e podem ser abertas como tabelas no DBeaver ou no HeidiSQL.

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
