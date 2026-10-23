#!/usr/bin/env bash
# Carrega os CSV.gz de splor-mg/dados-siafi-2026 nas tabelas do schema "siafi".
#
# Uso:  scripts/load.sh /caminho/dados-siafi-2026/data
#
# Pontos de atencao:
#  - zcat | \copy ... FROM STDIN: descompacta em fluxo, sem criar arquivo temporario
#    (execucao.csv.gz tem 58 MB compactado).
#  - A lista de colunas vem do CABECALHO do proprio CSV, entao a carga nao quebra se a
#    ordem das colunas mudar.
#  - TRUNCATE antes de cada carga -> o script e idempotente (pode rodar de novo).
#  - CSV com HEADER: a 1a linha e descartada. Campo vazio vira NULL (padrao do CSV no COPY).
set -euo pipefail

DADOS_DIR="${1:?informe o diretorio data/ do repositorio}"
cd "$(dirname "$0")/.."
set -a; . ./.env; set +a
export PGPASSWORD="$SIAFI_OWNER_PASSWORD"
PSQL=(psql -h "$PGHOST" -p "$PGPORT" -U "$SIAFI_OWNER" -d "$SIAFI_DB" -v ON_ERROR_STOP=1 -q)

for arquivo in "$DADOS_DIR"/*.csv.gz; do
    tabela="$(basename "$arquivo" .csv.gz)"
    # Le SO a 1a linha, sem pipe: "zcat | head -1" + pipefail => SIGPIPE (141) e o
    # set -e aborta o script em silencio. Os CSV tem final de linha CRLF, entao
    # removemos o \r do fim do cabecalho (senao a ultima coluna vira "xxx\r").
    IFS= read -r colunas < <(zcat "$arquivo")
    colunas="${colunas%$'\r'}"
    inicio=$(date +%s)
    "${PSQL[@]}" -c "TRUNCATE siafi.${tabela};"
    zcat "$arquivo" | "${PSQL[@]}" -c "\copy siafi.${tabela} (${colunas}) FROM STDIN WITH (FORMAT csv, HEADER true)"
    linhas=$("${PSQL[@]}" -Atc "SELECT count(*) FROM siafi.${tabela};")
    printf '%-28s %10s linhas  (%ss)\n' "$tabela" "$linhas" "$(( $(date +%s) - inicio ))"
done

# Estatisticas para o planejador de consultas (importante p/ o Metabase ficar rapido)
for arquivo in "$DADOS_DIR"/*.csv.gz; do
    "${PSQL[@]}" -c "ANALYZE siafi.$(basename "$arquivo" .csv.gz);"
done
echo "ANALYZE concluido."
