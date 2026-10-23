#!/usr/bin/env bash
# Cria e carrega o banco SIAFI DENTRO do container Postgres do docker-compose.
# Equivale aos passos da secao 2 do docs/RELATORIO.md, sem instalar nada na maquina.
#
# Uso (na pasta do projeto, com o compose no ar):
#     scripts/docker_db.sh /caminho/para/dados-siafi-2026
set -euo pipefail

REPO="${1:?informe o caminho do repositorio dados-siafi-2026 (a pasta que tem datapackage.json e data/)}"
cd "$(dirname "$0")/.."
set -a; . ./.env; set +a

# psql dentro do container. -T: sem terminal, necessario para receber dados por pipe.
# O socket local da imagem oficial nao pede senha, entao nao ha PGPASSWORD aqui.
psql_admin() { docker compose exec -T postgres psql -U postgres -v ON_ERROR_STOP=1 -q "$@"; }
psql_owner() { docker compose exec -T postgres psql -U siafi_owner -d "$SIAFI_DB" -v ON_ERROR_STOP=1 -q "$@"; }

echo "1/6 criando usuarios e banco..."
# Se ja existir (rodou antes), recomece do zero:  docker compose down -v
psql_admin -v owner_pw="'$SIAFI_OWNER_PASSWORD'" -v ro_pw="'$METABASE_RO_PASSWORD'" -f - < sql/01_banco_e_usuarios.sql

echo "2/6 criando schema..."
psql_owner -c "CREATE SCHEMA siafi AUTHORIZATION siafi_owner;"

echo "3/6 gerando e aplicando as tabelas a partir do datapackage.json..."
python3 scripts/gen_ddl.py "$REPO/datapackage.json" > sql/02_tabelas.sql
psql_owner -f - < sql/02_tabelas.sql 2>&1 | grep -v NOTICE || true

echo "4/6 carregando os CSV..."
for arquivo in "$REPO"/data/*.csv.gz; do
    tabela="$(basename "$arquivo" .csv.gz)"
    IFS= read -r colunas < <(zcat "$arquivo")
    colunas="${colunas%$'\r'}"          # os CSV tem final de linha CRLF
    zcat "$arquivo" | psql_owner -c "\copy siafi.${tabela} (${colunas}) FROM STDIN WITH (FORMAT csv, HEADER true)"
    n=$(psql_owner -Atc "SELECT count(*) FROM siafi.${tabela};")
    printf '   %-28s %10s linhas\n' "$tabela" "$n"
    psql_owner -c "ANALYZE siafi.${tabela};"
done

echo "5/6 criando views e permissoes..."
psql_owner -f - < sql/03_permissoes_e_views.sql

echo "6/6 conferindo com o usuario somente leitura..."
docker compose exec -T postgres psql -U metabase_leitor -d "$SIAFI_DB" -Atc \
  "SELECT 'siafi.execucao', count(*) FROM siafi.execucao UNION ALL SELECT 'painel.execucao_mensal', count(*) FROM painel.execucao_mensal;"
echo "Pronto. Proximo passo: python scripts/metabase_setup.py"
