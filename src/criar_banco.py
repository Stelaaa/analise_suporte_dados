"""
Cria banco/case_suporte.db (SQLite) com as tabelas de origem stg_* carregadas
a partir de data/raw/*.csv. Usa só a biblioteca padrão do Python.

Depois de criado, o banco pode ser aberto no DBeaver ou no HeidiSQL e as
consultas de sql/ (somente leitura) reproduzem os números do painel.
Ver docs/banco_sql.md.

Uso:  python src/criar_banco.py
"""
import csv
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
DB = ROOT / "banco" / "case_suporte.db"

TIPOS = {
    "quantidade": "INTEGER", "valor_total": "REAL", "pontos": "INTEGER",
    "meta_faturamento": "REAL", "meta_positivacao": "INTEGER", "preco_unitario": "REAL",
}
TABELAS = ["campanha", "participantes", "metas", "produtos", "vendas", "resgates", "chamados"]


def converter(col, valor):
    tipo = TIPOS.get(col)
    if tipo == "INTEGER":
        return int(float(valor))
    if tipo == "REAL":
        return float(valor)
    return valor


def main():
    DB.parent.mkdir(exist_ok=True)
    if DB.exists():
        DB.unlink()
    con = sqlite3.connect(DB)
    for t in TABELAS:
        with open(RAW / f"{t}.csv", encoding="utf-8", newline="") as f:
            leitor = csv.DictReader(f)
            cols = leitor.fieldnames
            defs = ", ".join(f'"{c}" {TIPOS.get(c, "TEXT")}' for c in cols)
            con.execute(f"CREATE TABLE stg_{t} ({defs})")
            linhas = [[converter(c, r[c]) for c in cols] for r in leitor]
            marcas = ", ".join("?" for _ in cols)
            con.executemany(f"INSERT INTO stg_{t} VALUES ({marcas})", linhas)
        print(f"  stg_{t:<14} {len(linhas):>6} linhas")
    con.commit()
    con.close()
    print("Banco criado em", DB)


if __name__ == "__main__":
    main()
