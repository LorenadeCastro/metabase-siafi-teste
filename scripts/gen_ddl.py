#!/usr/bin/env python3
"""Gera o DDL do Postgres a partir do datapackage.json do repositório
splor-mg/dados-siafi-2026.

Uso:
    python3 gen_ddl.py /caminho/dados-siafi-2026/datapackage.json > sql/02_tabelas.sql

Regras de mapeamento (Table Schema -> Postgres):
    string   -> text            (códigos têm zeros à esquerda; NUNCA converter p/ número)
    number   -> numeric(18,2)   (os valores têm no máximo 2 casas decimais)
    datetime -> timestamp       (formato de origem: AAAA/MM/DD HH:MM:SS, aceito pelo Postgres)
"""
import json
import sys

TIPOS = {
    "string": "text",
    "number": "numeric(18,2)",
    "datetime": "timestamp",
}


def main(caminho: str) -> None:
    with open(caminho, encoding="utf-8") as f:
        pacote = json.load(f)

    print("-- GERADO por scripts/gen_ddl.py a partir do datapackage.json. Nao editar a mao.")
    print("SET search_path TO siafi;\n")

    for recurso in pacote["resources"]:
        nome = recurso["name"]
        linhas = []
        for campo in recurso["schema"]["fields"]:
            tipo = TIPOS[campo["type"]]
            obrigatorio = campo.get("constraints", {}).get("required", False)
            linhas.append(f'    {campo["name"]} {tipo}' + (" NOT NULL" if obrigatorio else ""))
        print(f"DROP TABLE IF EXISTS {nome} CASCADE;")
        print(f"CREATE TABLE {nome} (")
        print(",\n".join(linhas))
        print(");\n")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
