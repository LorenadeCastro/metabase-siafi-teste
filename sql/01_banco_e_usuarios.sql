-- Executar como superusuario:  sudo -u postgres psql -v ON_ERROR_STOP=1 -f 01_banco_e_usuarios.sql \
--     -v owner_pw="'...'" -v ro_pw="'...'"
--
-- Segue o passo a passo do post do handbook (banco-de-dados-do-projeto-datamart),
-- com UMA melhoria: em vez de um unico usuario com tudo, criamos DOIS papeis:
--   siafi_owner      -> dono do banco/schema; usado so para CARREGAR dados (ETL).
--   metabase_leitor  -> somente leitura; e o usuario que o METABASE usa para conectar.
-- Motivo: o Metabase so controla o que acontece DENTRO dele. O teto real de acesso
-- aos dados e o papel do banco. Se o Metabase conectar como dono, qualquer admin do
-- Metabase (ou um SQL nativo mal escrito) consegue DROP/DELETE nas tabelas.

-- 1) Papeis (usuarios)
CREATE USER siafi_owner     WITH PASSWORD :owner_pw;
CREATE USER metabase_leitor WITH PASSWORD :ro_pw;

-- Ajustes por usuario, identicos aos do post (UTF-8, isolamento, fuso UTC)
ALTER ROLE siafi_owner     SET client_encoding TO 'utf8';
ALTER ROLE siafi_owner     SET default_transaction_isolation TO 'read committed';
ALTER ROLE siafi_owner     SET timezone TO 'UTC';
ALTER ROLE metabase_leitor SET client_encoding TO 'utf8';
ALTER ROLE metabase_leitor SET default_transaction_isolation TO 'read committed';
ALTER ROLE metabase_leitor SET timezone TO 'UTC';

-- Camada extra: o leitor nunca consegue escrever, mesmo que alguem conceda por engano
ALTER ROLE metabase_leitor SET default_transaction_read_only TO on;

-- 2) Banco de dados (dono = siafi_owner)
CREATE DATABASE siafi_2026
    OWNER siafi_owner
    ENCODING 'UTF8'
    LC_COLLATE 'C.UTF-8'
    LC_CTYPE 'C.UTF-8'
    TEMPLATE template0;

-- Por padrao qualquer papel pode CONECTAR em qualquer banco (privilegio de PUBLIC).
-- Revogamos e concedemos so a quem deve.
REVOKE ALL ON DATABASE siafi_2026 FROM PUBLIC;
GRANT CONNECT ON DATABASE siafi_2026 TO siafi_owner, metabase_leitor;
