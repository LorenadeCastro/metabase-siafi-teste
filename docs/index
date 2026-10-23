# Metabase + Postgres com dados SIAFI 2026

Ambiente de teste do Metabase (open source) conectado a um Postgres com os dados do
[dados-siafi-2026](https://github.com/splor-mg/dados-siafi-2026). Tudo roda em Docker.

## O que o projeto contém

| Arquivo | Função |
|---|---|
| `docker-compose.yml` | sobe o Postgres 16 e o Metabase |
| `sql/01_banco_e_usuarios.sql` | cria o banco `siafi_2026` e os usuários do banco |
| `scripts/gen_ddl.py` | gera as tabelas (`sql/02_tabelas.sql`) a partir do `datapackage.json` |
| `scripts/docker_db.sh` | cria e carrega o banco dentro do container |
| `sql/03_permissoes_e_views.sql` | permissões e views do schema `painel` |
| `scripts/metabase_setup.py` | configura o Metabase pela API (grupos, coleções, perguntas, painel) |

## Como rodar

Requisitos: Docker, Python 3 e git.

```bash
cp .env.exemplo .env                                  # troque as 3 senhas
git clone https://github.com/splor-mg/dados-siafi-2026.git ../dados-siafi-2026
docker compose up -d
scripts/docker_db.sh ../dados-siafi-2026
python3 -m venv .venv && .venv/bin/pip install requests
set -a; . ./.env; set +a
.venv/bin/python scripts/metabase_setup.py
```

Depois acesse http://localhost:3000.

## Usuários

No **banco Postgres**:
- `siafi_owner`: dono do banco, usado só para carregar os dados.
- `metabase_leitor`: somente leitura, usado pela conexão do Metabase.

No **Metabase**: um administrador e três usuários de teste (`analista@`, `leitor@` e `gestor@teste.local`),
cada um em um grupo (Analistas, Leitores, Gestores).

## Observações

- Os dados não ficam neste repositório; vêm do `dados-siafi-2026`.
- O `.env` contém senhas e não deve ser versionado.
- Se a rede usa proxy e retorna erro 407, o `metabase_setup.py` já ignora o proxy ao falar com `localhost`.
- O GitHub Pages publica apenas esta documentação; o Metabase não roda no Pages.
