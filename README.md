# Teste Metabase + Postgres com dados SIAFI 2026

Instância de teste do Metabase (open source) com Postgres e os dados do
[dados-siafi-2026](https://github.com/splor-mg/dados-siafi-2026). O relatório completo está em `docs/index.md`.

Passo a passo (Docker, Python 3 e git):
1. `cp .env.exemplo .env` e troque as 3 senhas
2. `git clone https://github.com/splor-mg/dados-siafi-2026.git ../dados-siafi-2026`
3. `docker compose up -d`
4. `scripts/docker_db.sh ../dados-siafi-2026`
5. `python3 -m venv .venv && .venv/bin/pip install requests`
6. `set -a; . ./.env; set +a; .venv/bin/python scripts/metabase_setup.py`
7. Abra http://localhost:3000

Os dados não estão neste repositório. O `.env` com as senhas nunca deve ser versionado.
