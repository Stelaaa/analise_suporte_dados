"""
Pipeline do case: CSV → SQLite → regras de qualidade → apuração → indicadores
→ planilhas Excel + gráficos + resumo em Markdown.

Uso:
    python data/generate_data.py      # (opcional) recria a base fictícia
    python src/pipeline.py            # roda tudo e grava em reports/

Requisitos: Python 3.10+, pandas, openpyxl, matplotlib (requirements.txt)
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
from openpyxl import Workbook  # noqa: E402
from openpyxl.formatting.rule import CellIsRule  # noqa: E402
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side  # noqa: E402
from openpyxl.utils import get_column_letter  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
SQL = ROOT / "sql"
OUT = ROOT / "reports"
IMG = OUT / "img"
DB = OUT / "case.db"

TABELAS = ["campanha", "participantes", "metas", "produtos", "vendas", "resgates", "chamados"]

# ---------------------------------------------------------------- estilo
FONTE = "Arial"
AZUL = "1F4E79"
CINZA = "F2F2F2"
H_FILL = PatternFill("solid", fgColor=AZUL)
H_FONT = Font(name=FONTE, bold=True, color="FFFFFF", size=10)
B_FONT = Font(name=FONTE, size=10)
INPUT_FONT = Font(name=FONTE, size=10, color="0000FF")
TITLE_FONT = Font(name=FONTE, bold=True, size=14, color=AZUL)
NOTE_FONT = Font(name=FONTE, italic=True, size=9, color="595959")
THIN = Border(bottom=Side(style="thin", color="D9D9D9"))

COR = {"principal": "#1F4E79", "destaque": "#C55A11", "neutro": "#A6A6A6",
       "ok": "#548235", "texto": "#262626"}


# ================================================================ etapa 1
def carregar(con: sqlite3.Connection) -> None:
    for t in TABELAS:
        df = pd.read_csv(RAW / f"{t}.csv", dtype=str, keep_default_na=False)
        for col in ("quantidade", "valor_total", "pontos", "meta_faturamento",
                    "meta_positivacao", "preco_unitario"):
            if col in df.columns:
                df[col] = pd.to_numeric(df[col])
        df.to_sql(f"stg_{t}", con, if_exists="replace", index=False)


def executar_sql(con: sqlite3.Connection) -> None:
    for f in sorted(SQL.glob("*.sql")):
        con.executescript(f.read_text(encoding="utf-8"))


def q(con: sqlite3.Connection, sql: str) -> pd.DataFrame:
    return pd.read_sql_query(sql, con)


# ================================================================ excel
def _cabecalho(ws, linha: int, colunas: list[str]) -> None:
    for j, nome in enumerate(colunas, start=1):
        c = ws.cell(row=linha, column=j, value=nome)
        c.fill, c.font = H_FILL, H_FONT
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    ws.row_dimensions[linha].height = 30


def _larguras(ws, larguras: dict[str, int]) -> None:
    for col, w in larguras.items():
        ws.column_dimensions[col].width = w


def aba_tabela(wb: Workbook, nome: str, df: pd.DataFrame, titulo: str,
               nota: str | None = None, formatos: dict[str, str] | None = None) -> None:
    ws = wb.create_sheet(nome)
    ws["A1"], ws["A1"].font = titulo, TITLE_FONT
    linha_h = 3
    if nota:
        ws["A2"], ws["A2"].font = nota, NOTE_FONT
    _cabecalho(ws, linha_h, list(df.columns))
    for i, row in enumerate(df.itertuples(index=False), start=linha_h + 1):
        for j, v in enumerate(row, start=1):
            c = ws.cell(row=i, column=j, value=None if pd.isna(v) else v)
            c.font, c.border = B_FONT, THIN
    formatos = formatos or {}
    for j, col in enumerate(df.columns, start=1):
        letra = get_column_letter(j)
        larg = max(len(str(col)), *(len(str(x)) for x in df[col].head(200))) if len(df) else len(col)
        ws.column_dimensions[letra].width = min(max(10, larg + 2), 60)
        if col in formatos:
            for r in range(linha_h + 1, linha_h + 1 + len(df)):
                ws.cell(row=r, column=j).number_format = formatos[col]
    ws.freeze_panes = ws.cell(row=linha_h + 1, column=1)
    if len(df):
        ws.auto_filter.ref = f"A{linha_h}:{get_column_letter(len(df.columns))}{linha_h + len(df)}"


def planilha_apuracao(con: sqlite3.Connection, destino: Path) -> None:
    """Apuração com fórmulas vivas + conferência contra o resultado do SQL."""
    wb = Workbook()
    wb.remove(wb.active)

    # ---------- Parâmetros (inputs editáveis pela área de Campanhas)
    ws = wb.create_sheet("Parâmetros")
    ws["A1"], ws["A1"].font = "Parâmetros da campanha", TITLE_FONT
    ws["A2"] = "Células em azul são editáveis. As fórmulas da aba Apuração leem daqui."
    ws["A2"].font = NOTE_FONT
    _cabecalho(ws, 4, ["Faixa", "Atingimento mínimo", "Pontos"])
    faixas = q(con, "SELECT faixa, ating_min, pontos FROM par_faixas_faturamento ORDER BY ating_min")
    for i, r in enumerate(faixas.itertuples(index=False), start=5):
        ws.cell(row=i, column=1, value=r.faixa).font = B_FONT
        c = ws.cell(row=i, column=2, value=r.ating_min)
        c.font, c.number_format = INPUT_FONT, "0%"
        c = ws.cell(row=i, column=3, value=int(r.pontos))
        c.font, c.number_format = INPUT_FONT, "#,##0"
    ws["A10"], ws["A10"].font = "Bônus positivação (pontos)", B_FONT
    bonus = int(q(con, "SELECT pontos FROM par_bonus").iloc[0, 0])
    ws["C10"], ws["C10"].font, ws["C10"].number_format = bonus, INPUT_FONT, "#,##0"
    ws["A12"] = ("Fonte: regulamento fictício da campanha Desafio Trimestral Q3/2026 "
                 "(sql/01_parametros.sql).")
    ws["A12"].font = NOTE_FONT
    _larguras(ws, {"A": 30, "B": 20, "C": 14})

    # ---------- Apuração
    ws = wb.create_sheet("Apuração")
    ws["A1"], ws["A1"].font = "Apuração · Desafio Trimestral Q3/2026", TITLE_FONT
    ws["A2"] = ("Colunas I–L são fórmulas do Excel; M traz o resultado do SQL; "
                "M confere as duas. Qualquer 'DIVERGE' precisa de análise.")
    ws["A2"].font = NOTE_FONT
    cols = ["Matrícula", "Nome", "Regional", "Situação", "Meta faturamento (R$)",
            "Faturamento válido (R$)", "Meta positivação", "Clientes positivados",
            "Atingimento", "Pontos faturamento", "Pontos positivação", "Pontos total (Excel)",
            "Pontos total (SQL)", "Conferência"]
    _cabecalho(ws, 4, cols)
    ap = q(con, """SELECT matricula, nome, regional, situacao, meta_faturamento, faturamento,
                          meta_positivacao, clientes_positivados, pontos_total
                   FROM apuracao ORDER BY matricula""")
    for i, r in enumerate(ap.itertuples(index=False), start=5):
        vals = [r.matricula, r.nome, r.regional, r.situacao,
                None if pd.isna(r.meta_faturamento) else r.meta_faturamento,
                r.faturamento,
                None if pd.isna(r.meta_positivacao) else int(r.meta_positivacao),
                int(r.clientes_positivados)]
        for j, v in enumerate(vals, start=1):
            ws.cell(row=i, column=j, value=v).font = B_FONT
        eleg = f'$D{i}="Elegível"'
        ws[f"I{i}"] = f'=IF({eleg},F{i}/E{i},"")'
        ws[f"J{i}"] = f"=IF({eleg},INDEX(Parâmetros!$C$5:$C$8,MATCH(I{i},Parâmetros!$B$5:$B$8,1)),0)"
        ws[f"K{i}"] = f"=IF(AND({eleg},H{i}>=G{i}),Parâmetros!$C$10,0)"
        ws[f"L{i}"] = f"=J{i}+K{i}"
        ws[f"M{i}"] = int(r.pontos_total)
        ws[f"N{i}"] = f'=IF(L{i}=M{i},"OK","DIVERGE")'
        for col in "IJKLMN":
            ws[f"{col}{i}"].font = B_FONT
        ws[f"E{i}"].number_format = ws[f"F{i}"].number_format = "#,##0.00"
        ws[f"I{i}"].number_format = "0.0%"
        for col in "JKLM":
            ws[f"{col}{i}"].number_format = "#,##0"
        for col in "ABCDEFGHIJKLMN":
            ws[f"{col}{i}"].border = THIN
    ultima = 4 + len(ap)
    ws.conditional_formatting.add(
        f"N5:N{ultima}", CellIsRule(operator="equal", formula=['"DIVERGE"'],
                                    fill=PatternFill("solid", fgColor="F8CBAD")))
    total = ultima + 2
    ws[f"K{total}"], ws[f"K{total}"].font = "Totais", Font(name=FONTE, bold=True)
    ws[f"L{total}"] = f"=SUM(L5:L{ultima})"
    ws[f"M{total}"] = f"=SUM(M5:M{ultima})"
    ws[f"N{total}"] = f'=COUNTIF(N5:N{ultima},"DIVERGE")&" divergência(s)"'
    for col in "LMN":
        ws[f"{col}{total}"].font = Font(name=FONTE, bold=True)
        ws[f"{col}{total}"].number_format = "#,##0"
    _larguras(ws, {"A": 11, "B": 20, "C": 14, "D": 20, "E": 15, "F": 15, "G": 12, "H": 12,
                   "I": 12, "J": 13, "K": 13, "L": 14, "M": 14, "N": 13})
    ws.freeze_panes = "C5"
    ws.auto_filter.ref = f"A4:N{ultima}"

    # ---------- demais abas
    aba_tabela(wb, "Qualidade - resumo", q(con, "SELECT * FROM vw_dq_resumo"),
               "Regras de qualidade · ocorrências por regra",
               "Bloqueia = registro sai da apuração · Alerta = corrigido automaticamente")
    aba_tabela(wb, "Qualidade - detalhe", q(con, "SELECT * FROM dq_ocorrencias ORDER BY regra, id_registro"),
               "Ocorrências de qualidade (evidência por registro)")
    aba_tabela(wb, "Impacto", q(con, "SELECT * FROM vw_impacto_qualidade ORDER BY diferenca DESC"),
               "Participantes cuja pontuação mudaria sem o tratamento de qualidade",
               "Diferença positiva = pontos que seriam pagos indevidamente",
               {"pontos_sem_tratamento": "#,##0", "pontos_apurados": "#,##0", "diferenca": "#,##0"})
    aba_tabela(wb, "Resgates x saldo",
               q(con, "SELECT * FROM vw_saldo_resgates WHERE saldo < 0 ORDER BY saldo"),
               "Resgates acima do saldo apurado (bloquear antes de liberar o prêmio)",
               formatos={"pontos_apurados": "#,##0", "pontos_resgatados": "#,##0", "saldo": "#,##0"})
    wb.save(destino)


def planilha_suporte(con: sqlite3.Connection, destino: Path) -> None:
    wb = Workbook()
    wb.remove(wb.active)
    pct = {c: '0.0"%"' for c in ("pct_volume", "pct_sla_resposta", "pct_sla_resolucao",
                                 "pct_reabertura", "pct_acumulado")}
    aba_tabela(wb, "Visão geral", q(con, "SELECT * FROM vw_kpi_geral"),
               "Indicadores da fila de suporte · jul–set/2026", formatos=pct)
    aba_tabela(wb, "Por categoria", q(con, "SELECT * FROM vw_kpi_categoria"),
               "SLA e volume por categoria", formatos=pct)
    aba_tabela(wb, "Por prioridade", q(con, "SELECT * FROM vw_kpi_prioridade"),
               "SLA por prioridade", formatos=pct)
    aba_tabela(wb, "Por analista", q(con, "SELECT * FROM vw_kpi_analista"),
               "Carga e SLA por analista (gestão de fila)", formatos=pct)
    aba_tabela(wb, "Pareto", q(con, "SELECT * FROM vw_pareto_categorias"),
               "Pareto de categorias", formatos=pct)
    aba_tabela(wb, "Recorrência", q(con, "SELECT * FROM vw_recorrencia_semanal"),
               "Chamados de pontuação x duplicatas importadas por semana da campanha")
    aba_tabela(wb, "Base chamados",
               q(con, """SELECT id_chamado, data_abertura, data_primeira_resposta, data_resolucao,
                                categoria, prioridade, canal, status, analista, reaberto,
                                horas_resposta, horas_resolucao, resp_no_prazo, res_no_prazo
                         FROM vw_chamados_sla ORDER BY data_abertura"""),
               "Base de chamados com cálculo de SLA")
    wb.save(destino)


# ================================================================ gráficos
def _estilo(ax, titulo: str, subtitulo: str | None = None) -> None:
    ax.set_title(titulo, loc="left", fontsize=13, fontweight="bold", color=COR["texto"], pad=22)
    if subtitulo:
        ax.text(0, 1.02, subtitulo, transform=ax.transAxes, fontsize=9.5, color="#595959")
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.spines["left"].set_color("#BFBFBF")
    ax.spines["bottom"].set_color("#BFBFBF")
    ax.tick_params(colors="#404040", labelsize=9)


def graficos(con: sqlite3.Connection) -> None:
    IMG.mkdir(parents=True, exist_ok=True)
    plt.rcParams["font.family"] = "DejaVu Sans"

    # 1 · recorrência semanal
    rec = q(con, "SELECT * FROM vw_recorrencia_semanal")
    fig, ax = plt.subplots(figsize=(9, 4.2), dpi=150)
    picos = rec["duplicatas_importadas"] > 0
    ax.bar(rec["semana_campanha"], rec["chamados_pontuacao"],
           color=[COR["destaque"] if p else COR["neutro"] for p in picos])
    for _, r in rec[picos].iterrows():
        ax.annotate(f"{int(r.duplicatas_importadas)} vendas\nduplicadas",
                    (r.semana_campanha, r.chamados_pontuacao), textcoords="offset points",
                    xytext=(0, 6), ha="center", fontsize=8.5, color=COR["destaque"])
    ax.set_xticks(rec["semana_campanha"])
    ax.set_xlabel("Semana da campanha", fontsize=9, color="#404040")
    ax.set_ylabel("Chamados", fontsize=9, color="#404040")
    ax.set_ylim(0, rec["chamados_pontuacao"].max() * 1.3)
    _estilo(ax, "Chamados de “Pontuação divergente” por semana",
            "Laranja: semanas em que um lote de vendas foi reimportado")
    fig.tight_layout()
    fig.savefig(IMG / "recorrencia_pontuacao.png")
    plt.close(fig)

    # 2 · SLA de resolução por categoria
    cat = q(con, "SELECT * FROM vw_kpi_categoria").sort_values("pct_sla_resolucao")
    geral = q(con, "SELECT pct_sla_resolucao FROM vw_kpi_geral").iloc[0, 0]
    fig, ax = plt.subplots(figsize=(9, 4.2), dpi=150)
    pior = cat["pct_sla_resolucao"] == cat["pct_sla_resolucao"].min()
    ax.barh(cat["categoria"], cat["pct_sla_resolucao"],
            color=[COR["destaque"] if p else COR["principal"] for p in pior])
    for y, v in enumerate(cat["pct_sla_resolucao"]):
        ax.text(v + 1, y, f"{v:.0f}%", va="center", fontsize=9, color="#404040")
    ax.axvline(geral, color="#595959", ls="--", lw=1)
    ax.text(geral + 0.5, len(cat) - 0.45, f"média {geral:.0f}%", fontsize=8.5, color="#595959")
    ax.set_xlim(0, 105)
    ax.set_xlabel("% resolvido dentro do SLA", fontsize=9, color="#404040")
    _estilo(ax, "SLA de resolução por categoria", "Chamados resolvidos · horas corridas")
    fig.tight_layout()
    fig.savefig(IMG / "sla_categoria.png")
    plt.close(fig)

    # 3 · ocorrências de qualidade
    dq = q(con, "SELECT * FROM vw_dq_resumo").sort_values("ocorrencias")
    fig, ax = plt.subplots(figsize=(9, 4), dpi=150)
    ax.barh(dq["regra"], dq["ocorrencias"],
            color=[COR["principal"] if s == "Bloqueia" else COR["neutro"] for s in dq["severidade"]])
    for y, v in enumerate(dq["ocorrencias"]):
        ax.text(v + 1.5, y, str(v), va="center", fontsize=9, color="#404040")
    ax.set_xlim(0, dq["ocorrencias"].max() * 1.15)
    _estilo(ax, "Ocorrências encontradas antes da apuração",
            "Azul: bloqueia o registro · Cinza: corrigido automaticamente")
    fig.tight_layout()
    fig.savefig(IMG / "qualidade_dados.png")
    plt.close(fig)


# ================================================================ resumo
def resumo(con: sqlite3.Connection) -> dict:
    g = q(con, "SELECT * FROM vw_kpi_geral").iloc[0].to_dict()
    dq = q(con, "SELECT * FROM vw_dq_resumo")
    imp = q(con, "SELECT COUNT(*) n, SUM(diferenca) pts, SUM(diferenca > 0) a_mais, "
                 "SUM(diferenca < 0) a_menos FROM vw_impacto_qualidade").iloc[0].to_dict()
    res = q(con, "SELECT COUNT(*) n, -SUM(saldo) pts FROM vw_saldo_resgates WHERE saldo < 0").iloc[0].to_dict()
    ap = q(con, "SELECT COUNT(*) total, SUM(situacao='Elegível') elegiveis, "
                "SUM(situacao LIKE 'Pendente%') pendentes, SUM(pontos_total) pontos FROM apuracao").iloc[0].to_dict()
    vendas = q(con, "SELECT (SELECT COUNT(*) FROM stg_vendas) brutas, "
                    "(SELECT COUNT(*) FROM vw_vendas_validas) validas").iloc[0].to_dict()
    cat = q(con, "SELECT * FROM vw_kpi_categoria")
    pont = cat[cat.categoria == "Pontuação divergente"].iloc[0].to_dict()
    rec = q(con, "SELECT * FROM vw_recorrencia_semanal")
    picos = rec[rec.duplicatas_importadas > 0]
    normais = rec[rec.duplicatas_importadas == 0]
    out = {
        "kpi_geral": g,
        "qualidade": dict(zip(dq.regra, dq.ocorrencias)),
        "vendas": vendas,
        "apuracao": ap,
        "impacto": imp,
        "resgates_acima_saldo": res,
        "pontuacao_divergente": pont,
        "media_chamados_pontuacao_semana_pico": round(picos.chamados_pontuacao.mean(), 1),
        "media_chamados_pontuacao_semana_normal": round(normais.chamados_pontuacao.mean(), 1),
    }
    out = json.loads(json.dumps(out, default=lambda x: x.item() if hasattr(x, "item") else str(x)))
    (OUT / "resumo.json").write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    return out


def main() -> None:
    OUT.mkdir(exist_ok=True)
    if DB.exists():
        DB.unlink()
    con = sqlite3.connect(DB)
    carregar(con)
    executar_sql(con)
    planilha_apuracao(con, OUT / "apuracao_campanha.xlsx")
    planilha_suporte(con, OUT / "indicadores_suporte.xlsx")
    graficos(con)
    r = resumo(con)
    con.close()
    import export_powerbi  # tabelas do modelo Power BI em powerbi/dados/
    export_powerbi.main()
    print(json.dumps(r, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
