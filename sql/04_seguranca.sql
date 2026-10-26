-- =====================================================================
-- Projeto Final - Laboratorio de Banco de Dados (UCB 2026/2)
-- Tema: Escola de Musica
-- B5 - Seguranca e controle de acesso  (Etapa 2)
-- SGBD: MySQL 8
--
-- Executar DEPOIS de 01_ddl.sql e 02_carga.sql:
--   mysql -u root < sql/04_seguranca.sql
--
-- O que este script cria:
--   1. USUARIO_APP: usuarios da aplicacao, com senha em hash + sal
--   2. Tres visoes: uma de restricao de colunas e duas de apoio a aplicacao
--   3. Quatro papeis (roles) do MySQL, com GRANT e um REVOKE demonstrado
--
-- Os USUARIOS do MySQL (com senha) NAO sao criados aqui, de proposito:
-- senha de banco nao pode ficar no repositorio (item B2 do enunciado).
-- Eles sao criados por ferramentas/criar_usuarios_banco.py, que le as
-- senhas do arquivo .env (que esta no .gitignore).
-- =====================================================================

USE escola_musica;
SET NAMES utf8mb4;  -- garante acentos corretos mesmo em terminal sem UTF-8

-- ---------------------------------------------------------------------
-- 1. USUARIO_APP
-- Quem faz login na aplicacao. A senha NUNCA e gravada: grava-se o
-- resultado de PBKDF2-HMAC-SHA256 (200 000 iteracoes) sobre a senha
-- com um sal aleatorio de 16 bytes, diferente para cada usuario.
-- O sal impede que duas senhas iguais gerem o mesmo hash e inutiliza
-- tabelas pre-calculadas (rainbow tables).
-- ---------------------------------------------------------------------
CREATE TABLE usuario_app (
    id_usuario    SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT,
    login         VARCHAR(30)       NOT NULL,
    senha_hash    CHAR(64)          NOT NULL,  -- 32 bytes em hexadecimal
    sal           CHAR(32)          NOT NULL,  -- 16 bytes em hexadecimal
    perfil        VARCHAR(10)       NOT NULL,
    id_pessoa     INT UNSIGNED      NULL,      -- professor ligado ao login, se houver
    ativo         BOOLEAN           NOT NULL DEFAULT TRUE,
    ultimo_login  DATETIME          NULL,
    CONSTRAINT pk_usuario_app PRIMARY KEY (id_usuario),
    -- RN31: o login e unico
    CONSTRAINT uq_usuario_app_login UNIQUE (login),
    -- RN32: todo usuario da aplicacao tem exatamente um perfil de acesso
    CONSTRAINT ck_usuario_app_perfil CHECK (perfil IN ('ADMIN', 'SECRETARIA', 'PROFESSOR')),
    CONSTRAINT ck_usuario_app_hash CHECK (senha_hash REGEXP '^[0-9a-f]{64}$'),
    CONSTRAINT ck_usuario_app_sal  CHECK (sal REGEXP '^[0-9a-f]{32}$'),
    CONSTRAINT fk_usuario_app_pessoa FOREIGN KEY (id_pessoa)
        REFERENCES pessoa (id_pessoa)
        ON DELETE SET NULL ON UPDATE RESTRICT
) ENGINE = InnoDB;

-- Usuarios de demonstracao. As senhas em texto claro existem SO no
-- README (secao "Logins de demonstracao"); aqui ficam apenas hash e sal.
INSERT INTO usuario_app (login, senha_hash, sal, perfil, id_pessoa) VALUES
('admin',
 'cce9661c94b195a23313582c02504d395becb3679172678c82beb06c072c012f',
 '556928cf86ca73e3548a43d187bf1202', 'ADMIN', NULL),
('secretaria',
 'ded9f93fca3b1166b665c1775db2b0ad473a1579250e823da19fcc41987d2947',
 '8eddd611ab89a1e5fc7dde13d6f3e7c1', 'SECRETARIA', NULL),
('prof.julia',
 '4b7a523654956c322ebd808647b7eb370e53fd4e65897738d8db84ca1d0ae082',
 'a907ad842a93275927a819e797de574f', 'PROFESSOR', 1);

-- ---------------------------------------------------------------------
-- 2. VISOES
-- ---------------------------------------------------------------------

-- vw_aluno_contato: VISAO DE RESTRICAO DE COLUNAS (exigida em B5).
-- O professor precisa saber quem sao seus alunos e como falar com eles,
-- mas nao precisa de CPF, endereco nem data de nascimento completa.
-- O papel professor recebe SELECT nesta visao e NAO recebe na tabela
-- PESSOA: e assim que o banco impede o acesso aos dados pessoais.
CREATE OR REPLACE VIEW vw_aluno_contato AS
SELECT a.id_pessoa                                        AS id_aluno,
       p.nome,
       p.email,
       (SELECT MIN(t.numero) FROM telefone t
         WHERE t.id_pessoa = p.id_pessoa)                 AS telefone,
       TIMESTAMPDIFF(YEAR, p.data_nascimento, CURDATE()) < 18 AS menor_de_idade,
       a.nome_responsavel
  FROM aluno a
  JOIN pessoa p ON p.id_pessoa = a.id_pessoa;

-- vw_ocupacao_turma: vagas ocupadas e livres de cada turma.
-- Usada na tela de matricula e no relatorio de ocupacao.
CREATE OR REPLACE VIEW vw_ocupacao_turma AS
SELECT t.id_turma,
       t.codigo,
       i.nome                                   AS instrumento,
       n.nome                                   AS nivel,
       pp.nome                                  AS professor,
       t.data_inicio,
       t.data_fim,
       t.vagas,
       COUNT(m.id_matricula)                    AS ocupadas,
       t.vagas - COUNT(m.id_matricula)          AS livres
  FROM turma t
  JOIN nivel n        ON n.id_nivel = t.id_nivel
  JOIN instrumento i  ON i.id_instrumento = n.id_instrumento
  JOIN pessoa pp      ON pp.id_pessoa = t.id_professor
  LEFT JOIN matricula m ON m.id_turma = t.id_turma AND m.situacao = 'ATIVA'
 GROUP BY t.id_turma, t.codigo, i.nome, n.nome, pp.nome,
          t.data_inicio, t.data_fim, t.vagas;

-- vw_relatorio_financeiro: relatorio consolidado por mes (B1 pede
-- "uma tela de relatorio consolidado, alimentada por visao").
CREATE OR REPLACE VIEW vw_relatorio_financeiro AS
SELECT ms.competencia,
       COUNT(*)                                                       AS qtd_mensalidades,
       SUM(ms.valor)                                                  AS valor_previsto,
       SUM(CASE WHEN ms.data_pagamento IS NOT NULL THEN ms.valor ELSE 0 END) AS valor_recebido,
       SUM(CASE WHEN ms.data_pagamento IS NULL THEN ms.valor ELSE 0 END)     AS valor_em_aberto,
       SUM(CASE WHEN ms.data_pagamento IS NULL
                 AND ms.data_vencimento < CURDATE() THEN 1 ELSE 0 END) AS qtd_vencidas,
       ROUND(100 * SUM(CASE WHEN ms.data_pagamento IS NULL THEN ms.valor ELSE 0 END)
                 / SUM(ms.valor), 1)                                  AS pct_em_aberto
  FROM mensalidade ms
 GROUP BY ms.competencia;

-- ---------------------------------------------------------------------
-- 3. PAPEIS (ROLES) E PRIVILEGIOS - principio do menor privilegio
--
--   papel             | para quem              | pode
--   ------------------+------------------------+-------------------------------
--   r_login           | tela de login          | so ler USUARIO_APP
--   r_admin           | direcao / TI da escola | tudo no banco escola_musica
--   r_secretaria      | atendimento            | cadastro, matricula, mensalidade
--   r_professor       | professores            | aulas, frequencia, avaliacoes;
--                     |                        | alunos SO pela visao, sem CPF
--
-- Os papeis sao globais no servidor (nao somem com DROP DATABASE),
-- por isso o script os apaga antes de recriar: assim ele pode ser
-- executado de novo sem erro.
-- ---------------------------------------------------------------------
DROP ROLE IF EXISTS r_login, r_admin, r_secretaria, r_professor;
CREATE ROLE r_login, r_admin, r_secretaria, r_professor;

-- r_login: antes do login a aplicacao ainda nao sabe o perfil do usuario,
-- entao conecta com um usuario que so enxerga a tabela de logins.
GRANT SELECT ON escola_musica.usuario_app TO r_login;
GRANT UPDATE (ultimo_login) ON escola_musica.usuario_app TO r_login;

-- r_admin: administrador do sistema.
GRANT SELECT, INSERT, UPDATE, DELETE, EXECUTE ON escola_musica.* TO r_admin;

-- r_secretaria: leitura do cadastro academico e financeiro...
GRANT SELECT ON escola_musica.pessoa             TO r_secretaria;
GRANT SELECT ON escola_musica.telefone           TO r_secretaria;
GRANT SELECT ON escola_musica.aluno              TO r_secretaria;
GRANT SELECT ON escola_musica.professor          TO r_secretaria;
GRANT SELECT ON escola_musica.instrumento        TO r_secretaria;
GRANT SELECT ON escola_musica.nivel              TO r_secretaria;
GRANT SELECT ON escola_musica.sala               TO r_secretaria;
GRANT SELECT ON escola_musica.turma              TO r_secretaria;
GRANT SELECT ON escola_musica.matricula          TO r_secretaria;
GRANT SELECT ON escola_musica.historico_situacao TO r_secretaria;
GRANT SELECT ON escola_musica.mensalidade        TO r_secretaria;
-- leitura academica: a secretaria emite declaracoes e boletins
GRANT SELECT ON escola_musica.aula               TO r_secretaria;
GRANT SELECT ON escola_musica.frequencia         TO r_secretaria;
GRANT SELECT ON escola_musica.avaliacao          TO r_secretaria;
GRANT SELECT ON escola_musica.vw_aluno_contato        TO r_secretaria;
GRANT SELECT ON escola_musica.vw_ocupacao_turma       TO r_secretaria;
GRANT SELECT ON escola_musica.vw_relatorio_financeiro TO r_secretaria;
-- ...e escrita so no que e trabalho da secretaria.
GRANT INSERT, UPDATE, DELETE ON escola_musica.pessoa             TO r_secretaria;
GRANT INSERT, UPDATE, DELETE ON escola_musica.telefone           TO r_secretaria;
GRANT INSERT, UPDATE, DELETE ON escola_musica.aluno              TO r_secretaria;
GRANT INSERT, UPDATE, DELETE ON escola_musica.turma              TO r_secretaria;
GRANT INSERT, UPDATE         ON escola_musica.matricula          TO r_secretaria;
GRANT INSERT                 ON escola_musica.historico_situacao TO r_secretaria;
GRANT INSERT, UPDATE, DELETE ON escola_musica.mensalidade        TO r_secretaria;

-- REVOKE demonstrado: mensalidade e documento financeiro. A secretaria
-- pode lancar e dar baixa, mas nao pode APAGAR uma mensalidade; quem
-- apaga e o administrador. O GRANT acima foi dado "largo" de proposito
-- para mostrar o REVOKE retirando so o DELETE.
-- (RN33: somente o administrador exclui mensalidade)
REVOKE DELETE ON escola_musica.mensalidade FROM r_secretaria;

-- r_professor: nao ve PESSOA nem MENSALIDADE. Ve os alunos so pela
-- visao vw_aluno_contato (sem CPF, sem endereco).
GRANT SELECT ON escola_musica.instrumento       TO r_professor;
GRANT SELECT ON escola_musica.nivel             TO r_professor;
GRANT SELECT ON escola_musica.sala              TO r_professor;
GRANT SELECT ON escola_musica.turma             TO r_professor;
GRANT SELECT ON escola_musica.matricula         TO r_professor;
GRANT SELECT ON escola_musica.vw_aluno_contato  TO r_professor;
GRANT SELECT ON escola_musica.vw_ocupacao_turma TO r_professor;
GRANT SELECT, INSERT, UPDATE ON escola_musica.aula       TO r_professor;
GRANT SELECT, INSERT, UPDATE ON escola_musica.frequencia TO r_professor;
GRANT SELECT, INSERT, UPDATE ON escola_musica.avaliacao  TO r_professor;

-- Conferencia: o que cada papel recebeu.
SHOW GRANTS FOR r_login;
SHOW GRANTS FOR r_secretaria;
SHOW GRANTS FOR r_professor;
