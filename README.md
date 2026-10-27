# Teste Metabase + Postgres com dados SIAFI 2026

Instância de teste do Metabase (open source) com Postgres e os dados do
[dados-siafi-2026](https://github.com/splor-mg/dados-siafi-2026). Tudo roda em Docker.
A documentação de uso está em `docs/index.md`.

## Passo a passo

Requisitos: Docker, Python 3 e git.

1. `cp .env.exemplo .env` e troque as 3 senhas
2. `git clone https://github.com/splor-mg/dados-siafi-2026.git ../dados-siafi-2026`
3. `docker compose up -d`
4. `scripts/docker_db.sh ../dados-siafi-2026`
5. `python3 -m venv .venv && .venv/bin/pip install requests`
6. `set -a; . ./.env; set +a; .venv/bin/python scripts/metabase_setup.py`
7. Abra http://localhost:3000

O passo 4 cria o banco, carrega os dados e termina mostrando a contagem de linhas de
`siafi.execucao`. Ele pode ser executado de novo sem apagar nada.

Login do admin: `admin@teste.local`, com a senha definida em `MB_ADMIN_PASSWORD`
(o padrão está em `scripts/metabase_setup.py`; troque após o primeiro acesso).

## Problemas comuns

- **Erro 407 ao rodar o script:** a rede usa proxy. O `metabase_setup.py` já ignora o proxy ao falar com `localhost`.
- **Usuários de teste não foram criados:** rode `.venv/bin/python scripts/criar_usuarios.py`. Não execute o `metabase_setup.py` de novo, porque ele duplicaria grupos, coleções e perguntas.
- **Painel sem dados:** em Admin settings > Databases > SIAFI 2026, clique em "Sync database schema now".
- **Recomeçar do zero:** `docker compose down -v` apaga os volumes (banco e Metabase).

## Observações

Os dados não estão neste repositório; vêm do `dados-siafi-2026`. O `.env` com as senhas nunca deve ser versionado.
