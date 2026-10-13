"""
Exporta as tabelas do modelo Power BI (docs/powerbi_modelo.md) como CSVs
limpos em powerbi/dados/. Rode depois do pipeline:

    python src/pipeline.py
    python src/export_powerbi.py

Os arquivos seguem o padrão Português (Brasil), o mesmo do Power BI em
português: ponto e vírgula como separador de colunas, vírgula como
decimal e datas no formato dd/mm/aaaa. Assim o Power BI importa sem
nenhuma mudança de localidade.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "reports" / "case.db"
OUT = ROOT / "powerbi" / "dados"

CONSULTAS = {
    "fChamados": """
        SELECT id_chamado,
               date(data_abertura)        AS data,
               data_abertura, data_primeira_resposta,
               NULLIF(data_resolucao, '') AS data_resolucao,
               categoria, prioridade, canal, status, analista,
               NULLIF(matricula, '')      AS matricula,
               reaberto, sla_resp_h, sla_res_h,
               horas_resposta, horas_resolucao,
               resp_no_prazo, res_no_prazo, semana_campanha
        FROM vw_chamados_sla""",
    "fVendas": """
        SELECT v.id_venda, v.data_venda AS data, UPPER(TRIM(v.matricula)) AS matricula,
               v.cod_cliente, v.cod_produto, v.quantidade, v.valor_total, v.lote_importacao,
               CASE WHEN o.regra IS NULL THEN 1 ELSE 0 END AS venda_valida,
               COALESCE(o.regra, 'Válida')                  AS motivo_bloqueio
        FROM stg_vendas v
        LEFT JOIN (SELECT id_registro, MIN(regra) AS regra
                   FROM dq_ocorrencias
                   WHERE tabela = 'vendas' AND severidade = 'Bloqueia'
                   GROUP BY id_registro) o ON o.id_registro = v.id_venda""",
    "fOcorrenciasDQ": "SELECT * FROM dq_ocorrencias",
    "fApuracao": "SELECT * FROM apuracao",
    "fResgates": "SELECT id_resgate, data_resgate AS data, UPPER(TRIM(matricula)) AS matricula, item, pontos FROM stg_resgates",
    "dParticipante": "SELECT * FROM vw_participantes",
    "dProduto": "SELECT * FROM stg_produtos",
    "dPrioridade": "SELECT prioridade, horas_primeira_resposta, horas_resolucao, ordem FROM par_sla",
}


def calendario() -> pd.DataFrame:
    dias = pd.date_range("2026-06-01", "2026-10-31", freq="D")
    nomes = ["seg", "ter", "qua", "qui", "sex", "sáb", "dom"]
    meses = ["", "jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]
    ini = pd.Timestamp("2026-07-01")
    df = pd.DataFrame({"data": dias.strftime("%Y-%m-%d")})
    df["ano"] = dias.year
    df["mes_num"] = dias.month
    df["mes"] = [meses[m] for m in dias.month]
    df["dia_semana"] = [nomes[d] for d in dias.dayofweek]
    df["dia_util"] = (dias.dayofweek < 5).astype(int)
    semana = ((dias - ini).days // 7) + 1
    df["semana_campanha"] = [s if 1 <= s <= 13 else None for s in semana]
    df["periodo_campanha"] = ["Dentro" if pd.Timestamp("2026-07-01") <= d <= pd.Timestamp("2026-09-30")
                              else "Fora" for d in dias]
    df["semana_campanha"] = df["semana_campanha"].astype("Int64")
    return df


COLUNAS_DATA = {"data", "data_adesao"}
COLUNAS_DATA_HORA = {"data_abertura", "data_primeira_resposta", "data_resolucao"}


def para_ptbr(df: pd.DataFrame) -> pd.DataFrame:
    """Converte datas ISO (aaaa-mm-dd) para dd/mm/aaaa."""
    df = df.copy()
    for col in df.columns:
        if col in COLUNAS_DATA:
            df[col] = pd.to_datetime(df[col]).dt.strftime("%d/%m/%Y")
        elif col in COLUNAS_DATA_HORA:
            df[col] = pd.to_datetime(df[col]).dt.strftime("%d/%m/%Y %H:%M")
    return df


def salvar(df: pd.DataFrame, nome: str) -> None:
    para_ptbr(df).to_csv(OUT / f"{nome}.csv", index=False, sep=";", decimal=",",
                         encoding="utf-8-sig")


def main() -> None:
    if not DB.exists():
        raise SystemExit("Rode antes: python src/pipeline.py")
    OUT.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB)
    for nome, sql in CONSULTAS.items():
        df = pd.read_sql_query(sql, con)
        for col in ("resp_no_prazo", "res_no_prazo", "semana_campanha", "venda_valida"):
            if col in df.columns:
                df[col] = df[col].astype("Int64")
        salvar(df, nome)
        print(f"  {nome:<16} {len(df):>6} linhas")
    cal = calendario()
    salvar(cal, "dCalendario")
    print(f"  {'dCalendario':<16} {len(cal):>6} linhas")
    con.close()


if __name__ == "__main__":
    main()
