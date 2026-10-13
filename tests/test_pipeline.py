"""
Confere as regras de qualidade e a apuração contra o gabarito gerado em
data/generate_data.py. Rode com:  python -m pytest tests -q
"""
import json
import sqlite3
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import pipeline  # noqa: E402

GABARITO = json.loads((ROOT / "data" / "raw" / "_gabarito.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def con():
    c = sqlite3.connect(":memory:")
    pipeline.carregar(c)
    pipeline.executar_sql(c)
    yield c
    c.close()


def contar(con, regra):
    return con.execute("SELECT COUNT(*) FROM dq_ocorrencias WHERE regra LIKE ?", (regra + "%",)).fetchone()[0]


@pytest.mark.parametrize("regra,chave", [
    ("DQ01", "vendas_duplicadas"),
    ("DQ02", "vendas_matricula_inexistente"),
    ("DQ03", "vendas_fora_periodo"),
    ("DQ04", "vendas_valor_invalido"),
    ("DQ05", "participantes_sem_meta"),
    ("DQ06", "matriculas_formato_irregular"),
])
def test_regra_bate_com_gabarito(con, regra, chave):
    assert contar(con, regra) == GABARITO[chave]


def test_sem_meta_sao_os_participantes_certos(con):
    achados = {r[0] for r in con.execute(
        "SELECT matricula FROM dq_ocorrencias WHERE regra LIKE 'DQ05%'")}
    assert achados == set(GABARITO["lista_participantes_sem_meta"])


def test_resgates_anomalos_todos_bloqueados(con):
    achados = {r[0] for r in con.execute(
        "SELECT matricula FROM dq_ocorrencias WHERE regra LIKE 'DQ07%'")}
    assert set(GABARITO["lista_resgates_acima_saldo"]) <= achados


def test_vendas_validas_sem_nenhuma_bloqueante(con):
    brutas = con.execute("SELECT COUNT(*) FROM stg_vendas").fetchone()[0]
    validas = con.execute("SELECT COUNT(*) FROM vw_vendas_validas").fetchone()[0]
    bloqueadas = con.execute("""SELECT COUNT(DISTINCT id_registro) FROM dq_ocorrencias
                                WHERE tabela = 'vendas' AND severidade = 'Bloqueia'""").fetchone()[0]
    assert brutas - validas == bloqueadas


def test_ninguem_inelegivel_pontua(con):
    n = con.execute("SELECT COUNT(*) FROM apuracao WHERE situacao <> 'Elegível' AND pontos_total > 0").fetchone()[0]
    assert n == 0


def test_faixa_coerente_com_atingimento(con):
    erradas = con.execute("""
        SELECT COUNT(*) FROM apuracao a JOIN par_faixas_faturamento f ON f.faixa = a.faixa
        WHERE a.situacao = 'Elegível'
          AND NOT (a.atingimento >= f.ating_min AND a.atingimento < f.ating_max)""").fetchone()[0]
    assert erradas == 0


def test_tratamento_nunca_aumenta_pontos(con):
    """Remover registros inválidos só pode manter ou reduzir pontos."""
    n = con.execute("SELECT COUNT(*) FROM vw_impacto_qualidade WHERE diferenca < 0").fetchone()[0]
    assert n == 0


def test_sla_entre_0_e_100(con):
    r = con.execute("SELECT pct_sla_resposta, pct_sla_resolucao FROM vw_kpi_geral").fetchone()
    assert all(0 <= x <= 100 for x in r)
