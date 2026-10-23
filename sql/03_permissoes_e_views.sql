-- Executar como siafi_owner (dono do banco), depois da carga:
--   psql -h localhost -U siafi_owner -d siafi_2026 -v ON_ERROR_STOP=1 -f sql/03_permissoes_e_views.sql
--
-- Dois schemas, de proposito:
--   siafi  -> tabelas BRUTAS (inclui razao_social_credor e CNPJ/CPF-hash dos credores).
--   painel -> views CURADAS e agregadas, sem dado de credor, para uso nos dashboards.
-- Isso permite demonstrar no Metabase permissao por SCHEMA/TABELA: um grupo pode ver
-- so o schema "painel" e nunca as tabelas brutas.

SET ROLE siafi_owner;

-- ============================================================
-- 1) Leitura para o usuario que o Metabase usa
-- ============================================================
GRANT USAGE ON SCHEMA siafi TO metabase_leitor;
GRANT SELECT ON ALL TABLES IN SCHEMA siafi TO metabase_leitor;
-- Tabelas futuras (ex.: recarga com DROP/CREATE) tambem ficam legiveis:
ALTER DEFAULT PRIVILEGES FOR ROLE siafi_owner IN SCHEMA siafi
    GRANT SELECT ON TABLES TO metabase_leitor;

-- ============================================================
-- 2) Schema "painel": views agregadas para dashboards
-- ============================================================
CREATE SCHEMA IF NOT EXISTS painel AUTHORIZATION siafi_owner;

-- Execucao da despesa por mes x orgao x funcao x grupo x fonte
CREATE OR REPLACE VIEW painel.execucao_mensal AS
SELECT  ano,
        mes_cod::int                         AS mes,
        uo_cod, uo_sigla, uo_nome,
        funcao_cod, funcao_desc,
        grupo_cod,  grupo_desc,
        fonte_cod,  fonte_desc,
        SUM(vlr_empenhado)                   AS vlr_empenhado,
        SUM(vlr_liquidado)                   AS vlr_liquidado,
        SUM(vlr_pago_orcamentario)           AS vlr_pago_orcamentario,
        COUNT(*)                             AS qtd_registros
FROM    siafi.execucao
GROUP BY ano, mes_cod, uo_cod, uo_sigla, uo_nome,
         funcao_cod, funcao_desc, grupo_cod, grupo_desc, fonte_cod, fonte_desc;

-- Receita por mes x orgao x fonte
CREATE OR REPLACE VIEW painel.receita_mensal AS
SELECT  ano,
        mes_cod::int                         AS mes,
        uo_cod, uo_sigla, uo_nome,
        fonte_cod, fonte_desc,
        SUM(vlr_previsto_inicial)            AS vlr_previsto_inicial,
        SUM(vlr_previsto_atualizado)         AS vlr_previsto_atualizado,
        SUM(vlr_efetivado_ajustado)          AS vlr_efetivado_ajustado
FROM    siafi.receita
GROUP BY ano, mes_cod, uo_cod, uo_sigla, uo_nome, fonte_cod, fonte_desc;

-- Credito (dotacao) por orgao x funcao x grupo
CREATE OR REPLACE VIEW painel.credito_por_orgao AS
SELECT  ano,
        uo_cod, uo_sigla, uo_nome,
        funcao_cod, funcao_desc,
        grupo_cod,  grupo_desc,
        SUM(vlr_credito_inicial)             AS vlr_credito_inicial,
        SUM(vlr_credito_autorizado)          AS vlr_credito_autorizado
FROM    siafi.credito
GROUP BY ano, uo_cod, uo_sigla, uo_nome, funcao_cod, funcao_desc, grupo_cod, grupo_desc;

GRANT USAGE ON SCHEMA painel TO metabase_leitor;
GRANT SELECT ON ALL TABLES IN SCHEMA painel TO metabase_leitor;
ALTER DEFAULT PRIVILEGES FOR ROLE siafi_owner IN SCHEMA painel
    GRANT SELECT ON TABLES TO metabase_leitor;

RESET ROLE;
