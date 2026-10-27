#!/usr/bin/env python3
"""Configura o Metabase via API: admin, banco, grupos, usuarios, colecoes,
permissoes, perguntas (SQL) e um painel.

ATENCAO: este script NAO foi executado contra um Metabase real (o ambiente onde foi
escrito nao conseguiu baixar o Metabase). Os endpoints seguem a API publica, mas pode
haver pequenas diferencas entre versoes. Cada chamada imprime o status; se uma falhar,
o erro aparece e o script segue para o proximo passo.

Uso (Metabase em http://localhost:3000, recem-instalado, ainda sem setup):
    pip install requests
    set -a; . ./.env; set +a
    python3 scripts/metabase_setup.py
Variaveis opcionais: MB_URL, MB_ADMIN_EMAIL, MB_ADMIN_PASSWORD, DB_HOST_FOR_METABASE
"""
import os
import sys

import requests

MB = os.environ.get("MB_URL", "http://localhost:3000").rstrip("/")
ADMIN_EMAIL = os.environ.get("MB_ADMIN_EMAIL", "admin@teste.local")
ADMIN_PASSWORD = os.environ.get("MB_ADMIN_PASSWORD", "Trocar-Esta-Senha-123")
# No docker-compose o Postgres e o servico "postgres" (mesma rede do Metabase)
DB_HOST = os.environ.get("DB_HOST_FOR_METABASE", "postgres")
DB_PORT = 5432  # porta interna do container (a 5433 so existe no seu host)
DB_NAME = os.environ["SIAFI_DB"]
DB_USER = os.environ["METABASE_RO_USER"]
DB_PASS = os.environ["METABASE_RO_PASSWORD"]

s = requests.Session()
# Ignora HTTP_PROXY/HTTPS_PROXY do terminal: o Metabase esta em localhost e, se a chamada
# passar pelo proxy da rede, ele responde 407 (Proxy Authentication Required).
s.trust_env = False


def call(metodo, caminho, **kw):
    r = s.request(metodo, f"{MB}/api{caminho}", timeout=120, **kw)
    ok = "OK " if r.ok else "ERRO"
    print(f"[{ok} {r.status_code}] {metodo} {caminho}")
    if not r.ok:
        print("       ", r.text[:300])
        return None
    return r.json() if r.text else {}


# ---------- 1) setup inicial (cria o administrador) ----------
props = call("GET", "/session/properties") or {}
token = props.get("setup-token")
if token:
    call("POST", "/setup", json={
        "token": token,
        "user": {"first_name": "Admin", "last_name": "Teste",
                 "email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        "prefs": {"site_name": "SPLOR - Teste Metabase", "allow_tracking": False},
    })
else:
    print("Metabase ja foi configurado; seguindo com o login do admin.")

sess = call("POST", "/session", json={"username": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
if not sess:
    sys.exit("Nao consegui autenticar como admin. Ajuste MB_ADMIN_EMAIL/MB_ADMIN_PASSWORD.")
s.headers["X-Metabase-Session"] = sess["id"]

# ---------- 2) conectar ao Postgres (com o usuario SOMENTE LEITURA) ----------
db = call("POST", "/database", json={
    "engine": "postgres", "name": "SIAFI 2026",
    "details": {"host": DB_HOST, "port": DB_PORT, "dbname": DB_NAME,
                "user": DB_USER, "password": DB_PASS, "ssl": False},
    "is_full_sync": True,
})
db_id = db["id"] if db else None

# ---------- 3) grupos ----------
grupos = {}
for nome in ["Analistas", "Leitores", "Gestores"]:
    g = call("POST", "/permissions/group", json={"name": nome})
    if g:
        grupos[nome] = g["id"]

# ---------- 4) usuarios de teste (um por grupo) ----------
# Versoes recentes do Metabase exigem que a lista de grupos inclua o "All Users"
# (todo usuario pertence a ele); sem isso a API responde 400.
todos = call("GET", "/permissions/group") or []
id_all_users = next((x["id"] for x in todos if x["name"].lower() == "all users"), 1)
for nome, email, grupo in [("Ana Analista", "analista@teste.local", "Analistas"),
                           ("Lia Leitora", "leitor@teste.local", "Leitores"),
                           ("Gil Gestor", "gestor@teste.local", "Gestores")]:
    if grupo in grupos:
        call("POST", "/user", json={
            "first_name": nome.split()[0], "last_name": nome.split()[1],
            "email": email, "password": "Teste-Senha-123",
            "user_group_memberships": [
                {"id": id_all_users, "is_group_manager": False},
                {"id": grupos[grupo], "is_group_manager": False},
            ],
        })

# ---------- 5) colecoes ----------
col = {}
for nome in ["Painel Orcamentario", "Area dos Analistas"]:
    c = call("POST", "/collection", json={"name": nome, "parent_id": None})
    if c:
        col[nome] = c["id"]

# ---------- 6) perguntas e painel ----------
SQL = {
    "Empenhado por orgao (top 15)":
        "SELECT uo_sigla, SUM(vlr_empenhado) AS empenhado, SUM(vlr_pago_orcamentario) AS pago "
        "FROM painel.execucao_mensal GROUP BY uo_sigla ORDER BY empenhado DESC LIMIT 15",
    "Execucao mensal":
        "SELECT mes, SUM(vlr_empenhado) AS empenhado, SUM(vlr_liquidado) AS liquidado, "
        "SUM(vlr_pago_orcamentario) AS pago FROM painel.execucao_mensal GROUP BY mes ORDER BY mes",
    "Receita prevista x efetivada por mes":
        "SELECT mes, SUM(vlr_previsto_atualizado) AS previsto, SUM(vlr_efetivado_ajustado) AS efetivado "
        "FROM painel.receita_mensal GROUP BY mes ORDER BY mes",
    "Credito autorizado por funcao":
        "SELECT funcao_desc, SUM(vlr_credito_autorizado) AS autorizado "
        "FROM painel.credito_por_orgao GROUP BY funcao_desc ORDER BY autorizado DESC LIMIT 12",
}
DISPLAY = {"Empenhado por orgao (top 15)": "bar", "Execucao mensal": "line",
           "Receita prevista x efetivada por mes": "line",
           "Credito autorizado por funcao": "bar"}

cards = []
if db_id and "Painel Orcamentario" in col:
    for nome, sql in SQL.items():
        c = call("POST", "/card", json={
            "name": nome, "display": DISPLAY[nome], "visualization_settings": {},
            "collection_id": col["Painel Orcamentario"],
            "dataset_query": {"database": db_id, "type": "native", "native": {"query": sql}},
        })
        if c:
            cards.append(c["id"])

    dash = call("POST", "/dashboard", json={"name": "Execucao Orcamentaria 2026",
                                            "collection_id": col["Painel Orcamentario"]})
    if dash and cards:
        posicoes = [(0, 0), (0, 12), (8, 0), (8, 12)]
        call("PUT", f"/dashboard/{dash['id']}", json={"dashcards": [
            {"id": -(i + 1), "card_id": cid, "row": posicoes[i][0], "col": posicoes[i][1],
             "size_x": 12, "size_y": 8} for i, cid in enumerate(cards)]})

# ---------- 7) permissoes de colecao ----------
#   Analistas = curate ("write"), Leitores = view ("read"), Gestores = view
g = call("GET", "/collection/graph")
if g and grupos and col:
    novo = {}
    for nome, gid in grupos.items():
        novo[str(gid)] = {}
        for cname, cid in col.items():
            if nome == "Analistas":
                nivel = "write"
            elif cname == "Painel Orcamentario":
                nivel = "read"
            else:
                nivel = "none"
            novo[str(gid)][str(cid)] = nivel
    call("PUT", "/collection/graph", json={"revision": g["revision"], "groups": novo})

# ---------- 8) permissoes de dados ----------
#   Analistas: consultas com SQL; Leitores: sem criar consultas; Gestores: so query builder.
#   (Em versao open source o "view-data" nao e configuravel; a chave e ignorada/rejeitada.)
p = call("GET", "/permissions/graph")
if p and db_id:
    niveis = {"Analistas": "query-builder-and-native", "Gestores": "query-builder", "Leitores": "no"}
    for nome, gid in grupos.items():
        p["groups"].setdefault(str(gid), {})[str(db_id)] = {
            "view-data": "unrestricted", "create-queries": niveis[nome]}
    call("PUT", "/permissions/graph", json=p)

print("\nPronto. Abra", MB, "e entre com", ADMIN_EMAIL)
