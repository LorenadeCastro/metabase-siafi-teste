#!/usr/bin/env python3
"""Cria so os 3 usuarios de teste em um Metabase JA configurado.

Use quando o metabase_setup.py rodou, mas a criacao dos usuarios falhou com
"You cannot add or remove users to/from the 'All Users' group". Rodar o
metabase_setup.py de novo duplicaria conexao, grupos, colecoes e perguntas;
este script nao mexe em nada disso.

Uso:
    set -a; . ./.env; set +a
    .venv/bin/python scripts/criar_usuarios.py
Variaveis opcionais: MB_URL, MB_ADMIN_EMAIL, MB_ADMIN_PASSWORD
"""
import os
import sys

import requests

MB = os.environ.get("MB_URL", "http://localhost:3000").rstrip("/")
ADMIN_EMAIL = os.environ.get("MB_ADMIN_EMAIL", "admin@teste.local")
ADMIN_PASSWORD = os.environ.get("MB_ADMIN_PASSWORD", "Trocar-Esta-Senha-123")

s = requests.Session()
s.trust_env = False   # ignora proxy do terminal (evita HTTP 407 em localhost)


def call(metodo, caminho, **kw):
    r = s.request(metodo, f"{MB}/api{caminho}", timeout=60, **kw)
    print(f"[{'OK ' if r.ok else 'ERRO'} {r.status_code}] {metodo} {caminho}")
    if not r.ok:
        print("       ", r.text[:300])
        return None
    return r.json() if r.text else {}


sess = call("POST", "/session", json={"username": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
if not sess:
    sys.exit("Nao consegui entrar como admin. Ajuste MB_ADMIN_EMAIL / MB_ADMIN_PASSWORD.")
s.headers["X-Metabase-Session"] = sess["id"]

grupos = {g["name"].lower(): g["id"] for g in call("GET", "/permissions/group") or []}
if "all users" not in grupos:
    sys.exit("Grupo All Users nao encontrado.")

for nome, email, grupo in [("Ana Analista", "analista@teste.local", "Analistas"),
                           ("Lia Leitora", "leitor@teste.local", "Leitores"),
                           ("Gil Gestor", "gestor@teste.local", "Gestores")]:
    if grupo.lower() not in grupos:
        print(f"Grupo {grupo} nao existe; pulando {email}")
        continue
    call("POST", "/user", json={
        "first_name": nome.split()[0], "last_name": nome.split()[1],
        "email": email, "password": "Teste-Senha-123",
        "user_group_memberships": [
            {"id": grupos["all users"], "is_group_manager": False},
            {"id": grupos[grupo.lower()], "is_group_manager": False},
        ],
    })
print("\nConfira em Admin settings > People.")
