# Adaptando o SQL para SQL Server ou PostgreSQL

O case usa SQLite para rodar sem instalar banco. A lógica é a mesma; muda a sintaxe em poucos pontos.

| SQLite (no case) | SQL Server | PostgreSQL |
|---|---|---|
| `(julianday(b) - julianday(a)) * 24` | `DATEDIFF(MINUTE, a, b) / 60.0` | `EXTRACT(EPOCH FROM (b - a)) / 3600` |
| `strftime('%Y-W%W', d)` | `CONCAT(YEAR(d), '-W', DATEPART(WEEK, d))` | `to_char(d, 'IYYY-"W"IW')` |
| `a \|\| b` (concatenação) | `CONCAT(a, b)` | `a \|\| b` |
| `SUM(cond)` com booleano | `SUM(CASE WHEN cond THEN 1 ELSE 0 END)` | `SUM((cond)::int)` ou `COUNT(*) FILTER (WHERE cond)` |
| `WINDOW w AS (...)` | repetir o `OVER (...)` em cada função | igual ao SQLite |
| `CREATE TABLE x AS WITH ...` | `WITH ... SELECT ... INTO x` | igual ao SQLite |
| `ALTER TABLE ... ADD COLUMN` + `UPDATE` | coluna computada `AS (a + b)` | `GENERATED ALWAYS AS (a + b) STORED` |

Window functions (`ROW_NUMBER`, `FIRST_VALUE`, `SUM() OVER`) funcionam nos três.
