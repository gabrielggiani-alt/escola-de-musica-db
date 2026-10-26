-- =====================================================================
-- Projeto Final - Laboratorio de Banco de Dados (UCB 2026/2)
-- Tema: Escola de Musica
-- B4 - Otimizacao de consultas  (Etapa 2)
--
-- Executar DEPOIS de 05_auditoria.sql:
--   mysql -u root -p --table < sql/06_otimizacao.sql > docs/resultados-otimizacao.txt
--
-- Roteiro para cada uma das 3 consultas criticas:
--   1. EXPLAIN (plano) e EXPLAIN ANALYZE (tempo real) ANTES do indice
--   2. CREATE INDEX, com a justificativa das colunas e da ordem
--   3. EXPLAIN e EXPLAIN ANALYZE DEPOIS
-- A leitura de cada plano esta no relatorio da Etapa 2, secao B4.
--
-- VOLUME: com os dados da Etapa 1 (54 pessoas, 246 mensalidades) qualquer
-- consulta roda em menos de 1 ms e o indice nao faz diferenca medivel.
-- Por isso a PARTE 1 gera volume sintetico (50 000 pessoas e cerca de
-- 30 000 mensalidades). Todo dado sintetico e marcado e e APAGADO na
-- PARTE 3; os indices ficam.
-- =====================================================================

USE escola_musica;
SET NAMES utf8mb4;  -- garante acentos corretos mesmo em terminal sem UTF-8

-- =====================================================================
-- PARTE 1 - VOLUME DE TESTE
-- =====================================================================
SET SESSION cte_max_recursion_depth = 100000;

-- 50 000 pessoas ficticias. CPF a partir de 90000000001 (faixa que a carga
-- da Etapa 1 nao usa) e a palavra "Sintetico" no nome, para apagar depois.
INSERT INTO pessoa (nome, cpf, data_nascimento, data_cadastro)
WITH RECURSIVE seq (n) AS (
    SELECT 1 UNION ALL SELECT n + 1 FROM seq WHERE n < 50000
)
SELECT CONCAT(ELT(1 + n % 12, 'Ana', 'Bruno', 'Carla', 'Diego', 'Elisa', 'Fabio',
                  'Gabriela', 'Hugo', 'Isabela', 'Joao', 'Larissa', 'Marcos'),
              ' ',
              ELT(1 + (n DIV 12) % 10, 'Almeida', 'Barbosa', 'Costa', 'Duarte', 'Esteves',
                  'Ferreira', 'Gomes', 'Lima', 'Moura', 'Nunes'),
              ' Sintetico ', n),
       CAST(90000000000 + n AS CHAR),
       DATE '1960-01-01' + INTERVAL (n % 18000) DAY,
       DATE '2026-01-01'
  FROM seq;

-- Mensalidades de 1990 a 2025 para cada matricula ja existente
-- (a carga da Etapa 1 so tem 2026, entao nao ha conflito com
-- uq_mensalidade_matricula_competencia). Uma em cada sete fica em aberto.
INSERT INTO mensalidade (id_matricula, competencia, valor, data_vencimento,
                         data_pagamento, forma_pagamento)
WITH RECURSIVE mes (k) AS (
    SELECT 0 UNION ALL SELECT k + 1 FROM mes WHERE k < 431
)
SELECT m.id_matricula,
       DATE '1990-01-01' + INTERVAL mes.k MONTH,
       280.00,
       DATE '1990-01-10' + INTERVAL mes.k MONTH,
       CASE WHEN (m.id_matricula + mes.k) % 7 = 0 THEN NULL
            ELSE DATE '1990-01-10' + INTERVAL mes.k MONTH END,
       CASE WHEN (m.id_matricula + mes.k) % 7 = 0 THEN NULL ELSE 'PIX' END
  FROM matricula m CROSS JOIN mes;

ANALYZE TABLE pessoa, mensalidade;

SELECT 'pessoa' AS tabela, COUNT(*) AS linhas FROM pessoa
UNION ALL SELECT 'mensalidade', COUNT(*) FROM mensalidade;

-- =====================================================================
-- PARTE 2 - AS TRES CONSULTAS CRITICAS
-- =====================================================================

-- ---------------------------------------------------------------------
-- CONSULTA 1 - Busca de pessoa pelo inicio do nome
-- Onde aparece: tela de busca de alunos da aplicacao (digitada a todo
-- momento pela secretaria no atendimento).
-- ---------------------------------------------------------------------
SELECT '=== CONSULTA 1 - ANTES ===' AS etapa;
EXPLAIN
SELECT id_pessoa, nome FROM pessoa WHERE nome LIKE 'Larissa Gomes%' ORDER BY nome;
EXPLAIN ANALYZE
SELECT id_pessoa, nome FROM pessoa WHERE nome LIKE 'Larissa Gomes%' ORDER BY nome;

-- Indice em NOME. LIKE com o curinga so no FINAL ('texto%') e uma faixa
-- ordenada da arvore B, entao o indice serve para filtrar E para o
-- ORDER BY. (LIKE '%texto' nao aproveitaria indice nenhum.)
-- Como o InnoDB guarda a PK em todo indice secundario, (nome) ja carrega
-- id_pessoa: a consulta e respondida so pelo indice (indice de cobertura).
CREATE INDEX idx_pessoa_nome ON pessoa (nome);

SELECT '=== CONSULTA 1 - DEPOIS ===' AS etapa;
EXPLAIN
SELECT id_pessoa, nome FROM pessoa WHERE nome LIKE 'Larissa Gomes%' ORDER BY nome;
EXPLAIN ANALYZE
SELECT id_pessoa, nome FROM pessoa WHERE nome LIKE 'Larissa Gomes%' ORDER BY nome;

-- ---------------------------------------------------------------------
-- CONSULTA 2 - Mensalidades vencidas e nao pagas (cobranca)
-- Onde aparece: rotina diaria de cobranca e consulta C14 (inadimplencia).
-- ---------------------------------------------------------------------
SELECT '=== CONSULTA 2 - ANTES ===' AS etapa;
EXPLAIN
SELECT id_mensalidade, id_matricula, valor, data_vencimento
  FROM mensalidade
 WHERE data_pagamento IS NULL
   AND data_vencimento < DATE '2000-01-01';
EXPLAIN ANALYZE
SELECT id_mensalidade, id_matricula, valor, data_vencimento
  FROM mensalidade
 WHERE data_pagamento IS NULL
   AND data_vencimento < DATE '2000-01-01';

-- Antes ja existia idx_mensalidade_pagamento (data_pagamento), da Etapa 1:
-- ele acha as mensalidades em aberto, mas depois o banco le CADA uma e
-- testa o vencimento. O indice composto resolve as duas condicoes na
-- propria arvore. ORDEM: data_pagamento primeiro, porque o teste e de
-- IGUALDADE (IS NULL); data_vencimento depois, porque e FAIXA (<).
-- Coluna de faixa sempre por ultimo: depois de uma faixa, as colunas
-- seguintes do indice deixam de poder ser usadas para filtrar.
CREATE INDEX idx_mensalidade_aberto_venc ON mensalidade (data_pagamento, data_vencimento);
-- O indice antigo agora e prefixo do novo, entao e redundante: so custaria
-- espaco e tempo de escrita.
DROP INDEX idx_mensalidade_pagamento ON mensalidade;

SELECT '=== CONSULTA 2 - DEPOIS ===' AS etapa;
EXPLAIN
SELECT id_mensalidade, id_matricula, valor, data_vencimento
  FROM mensalidade
 WHERE data_pagamento IS NULL
   AND data_vencimento < DATE '2000-01-01';
EXPLAIN ANALYZE
SELECT id_mensalidade, id_matricula, valor, data_vencimento
  FROM mensalidade
 WHERE data_pagamento IS NULL
   AND data_vencimento < DATE '2000-01-01';

-- ---------------------------------------------------------------------
-- CONSULTA 3 - Relatorio financeiro consolidado por mes
-- Onde aparece: tela de relatorio da aplicacao (visao vw_relatorio_financeiro).
-- ---------------------------------------------------------------------
SELECT '=== CONSULTA 3 - ANTES ===' AS etapa;
EXPLAIN
SELECT competencia, COUNT(*), SUM(valor),
       SUM(CASE WHEN data_pagamento IS NULL THEN valor ELSE 0 END)
  FROM mensalidade
 GROUP BY competencia;
EXPLAIN ANALYZE
SELECT competencia, COUNT(*), SUM(valor),
       SUM(CASE WHEN data_pagamento IS NULL THEN valor ELSE 0 END)
  FROM mensalidade
 GROUP BY competencia;

-- Indice de cobertura (competencia, data_pagamento, valor):
--   competencia primeiro: e a coluna do GROUP BY, entao o banco percorre o
--     indice ja agrupado, sem tabela temporaria;
--   data_pagamento e valor: sao as unicas outras colunas que a consulta
--     usa, entao ela nao precisa ir a tabela.
-- Expectativa honesta: a consulta continua lendo TODAS as linhas (e um
-- relatorio do historico inteiro); o ganho vem de ler um indice menor
-- que a tabela e de nao ordenar. Ver o resultado medido no relatorio.
CREATE INDEX idx_mensalidade_comp_cobertura ON mensalidade (competencia, data_pagamento, valor);

SELECT '=== CONSULTA 3 - DEPOIS ===' AS etapa;
EXPLAIN
SELECT competencia, COUNT(*), SUM(valor),
       SUM(CASE WHEN data_pagamento IS NULL THEN valor ELSE 0 END)
  FROM mensalidade
 GROUP BY competencia;
EXPLAIN ANALYZE
SELECT competencia, COUNT(*), SUM(valor),
       SUM(CASE WHEN data_pagamento IS NULL THEN valor ELSE 0 END)
  FROM mensalidade
 GROUP BY competencia;

-- =====================================================================
-- PARTE 3 - LIMPEZA DO VOLUME DE TESTE (os indices permanecem)
-- =====================================================================
DELETE FROM mensalidade WHERE competencia < DATE '2026-01-01';
DELETE FROM pessoa WHERE cpf >= '90000000001' AND nome LIKE '% Sintetico %';
ANALYZE TABLE pessoa, mensalidade;

SELECT 'pessoa' AS tabela, COUNT(*) AS linhas FROM pessoa
UNION ALL SELECT 'mensalidade', COUNT(*) FROM mensalidade;
