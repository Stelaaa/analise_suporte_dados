"""
Gera a base fictícia do case.

Cenário: a "Distribuidora Horizonte" (empresa fictícia) roda a campanha de
vendas "Desafio Trimestral Q3/2026" para sua força de vendas. Os dados
chegam por importação de planilhas enviadas pelo cliente — e, como na vida
real, chegam com problemas. As inconsistências abaixo são inseridas de
propósito, com quantidades conhecidas, para que as regras de qualidade
possam ser verificadas contra um gabarito.

Inconsistências injetadas (gabarito em data/raw/_gabarito.json):
  1. vendas duplicadas (mesma linha importada duas vezes)
  2. vendas de matrículas que não estão cadastradas na campanha
  3. vendas com data fora do período da campanha
  4. vendas com valor zero ou negativo (estornos lançados como venda)
  5. participantes sem meta cadastrada
  6. participantes com matrícula com espaços / caixa diferente
  7. resgates acima do saldo de pontos

Execução:  python data/generate_data.py
Tudo é determinístico (seed fixa): rodar de novo gera os mesmos arquivos.
"""
from __future__ import annotations

import csv
import json
import random
from datetime import date, datetime, timedelta
from pathlib import Path

SEED = 42
OUT = Path(__file__).resolve().parent / "raw"

CAMPANHA = {
    "id_campanha": "CMP-2026-Q3",
    "nome": "Desafio Trimestral Q3/2026",
    "cliente": "Distribuidora Horizonte (fictícia)",
    "data_inicio": "2026-07-01",
    "data_fim": "2026-09-30",
}

REGIONAIS = ["Centro-Oeste", "Sudeste", "Sul", "Nordeste", "Norte"]
CARGOS = ["Vendedor", "Vendedor", "Vendedor", "Vendedor", "Supervisor"]
PRODUTOS = [
    ("P01", "Refrigerante 2L", "Bebidas", 8.90),
    ("P02", "Água Mineral 500ml", "Bebidas", 2.10),
    ("P03", "Suco 1L", "Bebidas", 6.50),
    ("P04", "Biscoito Recheado", "Alimentos", 3.40),
    ("P05", "Salgadinho 100g", "Alimentos", 5.20),
    ("P06", "Creme Dental", "Higiene", 4.80),
    ("P07", "Sabonete", "Higiene", 2.60),
    ("P08", "Desodorante", "Higiene", 12.90),
]
NOMES = ["Ana", "Bruno", "Carla", "Diego", "Elisa", "Fábio", "Gabriela", "Hugo",
         "Isabela", "João", "Karen", "Lucas", "Marina", "Nicolas", "Olívia",
         "Paulo", "Queila", "Rafael", "Sabrina", "Tiago", "Úrsula", "Vinícius",
         "Wesley", "Yasmin"]
SOBRENOMES = ["Silva", "Souza", "Oliveira", "Santos", "Lima", "Pereira",
              "Costa", "Rodrigues", "Almeida", "Nascimento", "Carvalho", "Melo"]

N_PARTICIPANTES = 180
N_VENDAS_BASE = 9000
N_CHAMADOS = 640

# quantidades injetadas
INJ = {
    "vendas_duplicadas": None,  # calculado: reimportação de lotes
    "vendas_matricula_inexistente": 55,
    "vendas_fora_periodo": 70,
    "vendas_valor_invalido": 38,
    "participantes_sem_meta": 6,
    "matriculas_formato_irregular": 12,
    "resgates_acima_saldo": 9,
}


def write_csv(name: str, rows: list[dict]) -> None:
    path = OUT / name
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"  {name:<22} {len(rows):>6} linhas")


def rand_date(rng: random.Random, start: date, end: date) -> date:
    return start + timedelta(days=rng.randint(0, (end - start).days))


def main() -> None:
    rng = random.Random(SEED)
    OUT.mkdir(parents=True, exist_ok=True)
    ini = date.fromisoformat(CAMPANHA["data_inicio"])
    fim = date.fromisoformat(CAMPANHA["data_fim"])

    # ---------------- participantes ----------------
    participantes = []
    for i in range(1, N_PARTICIPANTES + 1):
        participantes.append({
            "matricula": f"HZ{i:04d}",
            "nome": f"{rng.choice(NOMES)} {rng.choice(SOBRENOMES)}",
            "cargo": rng.choice(CARGOS),
            "regional": rng.choice(REGIONAIS),
            "data_adesao": rand_date(rng, ini - timedelta(days=20), ini + timedelta(days=15)).isoformat(),
            "status": "Ativo" if rng.random() > 0.04 else "Inativo",
        })
    matriculas_validas = [p["matricula"] for p in participantes]

    # matrícula com espaço/caixa irregular (o mesmo participante, digitado errado)
    irregulares = rng.sample(range(N_PARTICIPANTES), INJ["matriculas_formato_irregular"])
    for idx in irregulares:
        m = participantes[idx]["matricula"]
        participantes[idx]["matricula"] = rng.choice([f" {m}", f"{m} ", m.lower()])

    # ---------------- vendas ----------------
    # cada participante tem uma "força" (desempenho) e uma carteira de clientes
    forca = {m: rng.uniform(0.6, 1.4) for m in matriculas_validas}
    carteira = {m: rng.sample(range(1, 901), 60) for m in matriculas_validas}
    vendas = []
    vid = 1
    for _ in range(N_VENDAS_BASE):
        m = rng.choices(matriculas_validas, weights=[forca[x] for x in matriculas_validas])[0]
        prod = rng.choice(PRODUTOS)
        qtd = max(1, int(rng.gauss(25, 10) * forca[m]))
        vendas.append({
            "id_venda": f"V{vid:06d}",
            "matricula": m,
            "data_venda": rand_date(rng, ini, fim).isoformat(),
            "cod_cliente": f"C{rng.choice(carteira[m]):04d}",
            "cod_produto": prod[0],
            "quantidade": qtd,
            "valor_total": round(qtd * prod[3], 2),
            "lote_importacao": None,
        })
        vid += 1

    # ---------------- metas ----------------
    # meta definida pelo cliente a partir do histórico: o realizado "esperado"
    # multiplicado por um fator de desafio (umas metas fáceis, outras duras)
    fat_base: dict[str, float] = {}
    cli_base: dict[str, set] = {}
    for v in vendas:
        fat_base[v["matricula"]] = fat_base.get(v["matricula"], 0) + v["valor_total"]
        cli_base.setdefault(v["matricula"], set()).add(v["cod_cliente"])
    sem_meta = set(rng.sample(matriculas_validas, INJ["participantes_sem_meta"]))
    metas = []
    for m in matriculas_validas:
        if m in sem_meta:
            continue
        metas.append({
            "id_campanha": CAMPANHA["id_campanha"],
            "matricula": m,
            "meta_faturamento": round(fat_base.get(m, 5000) * rng.uniform(0.8, 1.3), -2),
            "meta_positivacao": 5 * round(len(cli_base.get(m, ())) * rng.uniform(0.9, 1.15) / 5),
        })

    # matrícula inexistente
    for _ in range(INJ["vendas_matricula_inexistente"]):
        prod = rng.choice(PRODUTOS)
        qtd = rng.randint(5, 40)
        vendas.append({
            "id_venda": f"V{vid:06d}",
            "matricula": f"HZ{rng.randint(5000, 5999):04d}",
            "data_venda": rand_date(rng, ini, fim).isoformat(),
            "cod_cliente": f"C{rng.randint(1, 900):04d}",
            "cod_produto": prod[0],
            "quantidade": qtd,
            "valor_total": round(qtd * prod[3], 2),
            "lote_importacao": None,
        })
        vid += 1

    # fora do período (junho e outubro)
    alvos = rng.sample(range(N_VENDAS_BASE), INJ["vendas_fora_periodo"])
    for idx in alvos:
        if rng.random() < 0.5:
            d = rand_date(rng, ini - timedelta(days=30), ini - timedelta(days=1))
        else:
            d = rand_date(rng, fim + timedelta(days=1), fim + timedelta(days=12))
        vendas[idx]["data_venda"] = d.isoformat()

    # valor inválido (estorno lançado como venda)
    pool = [i for i in range(N_VENDAS_BASE) if i not in set(alvos)]
    for idx in rng.sample(pool, INJ["vendas_valor_invalido"]):
        vendas[idx]["valor_total"] = rng.choice([0.0, -round(vendas[idx]["valor_total"], 2)])

    # lotes de importação: 13 semanas → 13 lotes
    for v in vendas:
        d = date.fromisoformat(v["data_venda"])
        semana = max(0, min(12, (d - ini).days // 7))
        v["lote_importacao"] = f"LOTE-{semana + 1:02d}"

    # duplicadas: o LOTE-05 foi reimportado inteiro e o LOTE-09 parcialmente
    # (a importação caiu no meio e o operador subiu o arquivo de novo)
    lote05 = [v for v in vendas[:N_VENDAS_BASE]
              if v["lote_importacao"] == "LOTE-05" and v["valor_total"] > 0]
    lote09 = [v for v in vendas[:N_VENDAS_BASE]
              if v["lote_importacao"] == "LOTE-09" and v["valor_total"] > 0]
    reimportadas = lote05 + rng.sample(lote09, int(len(lote09) * 0.35))
    INJ["vendas_duplicadas"] = len(reimportadas)
    for v in reimportadas:
        dup = dict(v)
        dup["id_venda"] = f"V{vid:06d}"
        vid += 1
        vendas.append(dup)

    rng.shuffle(vendas)

    # ---------------- resgates ----------------
    # Saldo real só é conhecido depois da apuração; aqui geramos resgates
    # "plausíveis" e alguns propositalmente altos demais.
    resgates = []
    rid = 1
    catalogo = [("Vale-compras R$50", 500), ("Fone Bluetooth", 1800),
                ("Crédito no cartão R$100", 1000), ("Smartwatch", 4500),
                ("Air Fryer", 3800), ("Vale-combustível R$200", 2000)]
    # resgates normais: só quem vinha bem na campanha (o app libera resgate
    # parcial com base na prévia de pontos)
    bons = [m for m in matriculas_validas if forca[m] > 1.2 and m not in sem_meta]
    for m in rng.sample(bons, min(60, len(bons))):
        for _ in range(rng.randint(1, 2)):
            item = rng.choice(catalogo[:3])
            resgates.append({
                "id_resgate": f"R{rid:05d}", "matricula": m,
                "data_resgate": rand_date(rng, fim + timedelta(days=3), fim + timedelta(days=12)).isoformat(),
                "item": item[0], "pontos": item[1],
            })
            rid += 1
    acima_saldo = rng.sample([x for x in matriculas_validas if x not in sem_meta], INJ["resgates_acima_saldo"])
    for m in acima_saldo:
        resgates.append({
            "id_resgate": f"R{rid:05d}", "matricula": m,
            "data_resgate": rand_date(rng, fim + timedelta(days=3), fim + timedelta(days=12)).isoformat(),
            "item": "Smartwatch + Air Fryer (pedido combinado)", "pontos": 25000,
        })
        rid += 1

    # ---------------- chamados (tickets) ----------------
    categorias = [
        # (categoria, peso, prioridade mais comum)
        ("Pontuação divergente", 26, "Alta"),
        ("Resgate não creditado", 17, "Alta"),
        ("Acesso / login", 18, "Média"),
        ("Importação de base", 10, "Crítica"),
        ("Dúvida de regulamento", 14, "Baixa"),
        ("Relatório / dashboard", 9, "Média"),
        ("Cadastro de participante", 6, "Média"),
    ]
    pesos = [c[1] for c in categorias]
    sla_horas = {"Crítica": 4, "Alta": 8, "Média": 24, "Baixa": 48}
    canais = ["Portal", "E-mail", "WhatsApp", "Portal", "Portal"]
    analistas = ["Analista A", "Analista B", "Analista C"]
    status_opts = ["Resolvido"] * 18 + ["Em andamento", "Aguardando cliente"]

    chamados = []
    inicio_ch = datetime(2026, 7, 1, 8, 0)
    for i in range(1, N_CHAMADOS + 1):
        cat, _, prio_base = rng.choices(categorias, weights=pesos)[0]
        prio = prio_base if rng.random() < 0.75 else rng.choice(list(sla_horas))
        aberto = inicio_ch + timedelta(minutes=rng.randint(0, 92 * 24 * 60))
        # picos de "Pontuação divergente" nas semanas das reimportações (lotes 5 e 9)
        if cat != "Pontuação divergente" and rng.random() < 0.10:
            cat, prio = "Pontuação divergente", "Alta"
        if cat == "Pontuação divergente" and rng.random() < 0.55:
            semana = rng.choice([4, 8])  # semanas dos lotes 05 e 09 (base 0)
            aberto = inicio_ch + timedelta(days=semana * 7 + rng.randint(0, 6), minutes=rng.randint(0, 600))
        # 1ª resposta
        resp = aberto + timedelta(minutes=max(5, int(rng.expovariate(1 / 70))))
        # resolução: o SLA tende a estourar em Pontuação divergente (exige cruzar dados)
        fator = 1.6 if cat == "Pontuação divergente" else (1.3 if cat == "Importação de base" else 0.7)
        horas_res = max(0.3, rng.expovariate(1 / (sla_horas[prio] * fator * 0.8)))
        status = rng.choice(status_opts)
        resolvido = aberto + timedelta(hours=horas_res) if status == "Resolvido" else None
        chamados.append({
            "id_chamado": f"CH-{i:05d}",
            "data_abertura": aberto.strftime("%Y-%m-%d %H:%M"),
            "data_primeira_resposta": resp.strftime("%Y-%m-%d %H:%M"),
            "data_resolucao": resolvido.strftime("%Y-%m-%d %H:%M") if resolvido else "",
            "categoria": cat,
            "prioridade": prio,
            "canal": rng.choice(canais),
            "status": status,
            "analista": rng.choice(analistas),
            "matricula": rng.choice(matriculas_validas) if rng.random() < 0.8 else "",
            "reaberto": "Sim" if rng.random() < (0.12 if cat == "Pontuação divergente" else 0.04) else "Não",
        })
    chamados.sort(key=lambda c: c["data_abertura"])

    # ---------------- gravação ----------------
    print("Gerando arquivos em", OUT)
    write_csv("campanha.csv", [CAMPANHA])
    write_csv("participantes.csv", participantes)
    write_csv("metas.csv", metas)
    write_csv("produtos.csv", [{"cod_produto": p[0], "produto": p[1], "categoria": p[2],
                                "preco_unitario": p[3]} for p in PRODUTOS])
    write_csv("vendas.csv", vendas)
    write_csv("resgates.csv", resgates)
    write_csv("chamados.csv", chamados)
    gabarito = dict(INJ)
    gabarito["lista_participantes_sem_meta"] = sorted(sem_meta)
    gabarito["lista_resgates_acima_saldo"] = sorted(acima_saldo)
    (OUT / "_gabarito.json").write_text(json.dumps(gabarito, indent=2, ensure_ascii=False), encoding="utf-8")
    print("  _gabarito.json         (quantidades injetadas)")


if __name__ == "__main__":
    main()
