-- =====================================================================
-- DEMONSTRACAO AO VIVO: EXPLAIN antes e depois do indice (roteiro 6.2)
-- Executar no MySQL Workbench (raio) ou:  mysql -u root -p --table < sql/08_demo_explain.sql
-- Pode rodar quantas vezes quiser: no fim o indice fica criado, como estava.
--
-- O que mostrar na tela: a coluna "type" e a coluna "key".
--   ANTES:  type = ALL   key = NULL             -> le a tabela inteira
--   DEPOIS: type = range key = idx_pessoa_nome  -> vai direto nos nomes;
--           rows cai de 54 para 5 e some o "Using filesort" (nao precisa ordenar)
-- (O estudo completo, com 50 mil linhas e tempos, esta em 06_otimizacao.sql
--  e em docs/resultados-otimizacao.txt.)
-- =====================================================================
USE escola_musica;
SET NAMES utf8mb4;

DROP INDEX idx_pessoa_nome ON pessoa;

ANALYZE TABLE pessoa;  -- atualiza as estatisticas que o otimizador usa

-- ANTES (sem indice)
EXPLAIN SELECT id_pessoa, nome FROM pessoa WHERE nome LIKE 'Ra%' ORDER BY nome;

CREATE INDEX idx_pessoa_nome ON pessoa (nome);

ANALYZE TABLE pessoa;

-- DEPOIS (com indice)
EXPLAIN SELECT id_pessoa, nome FROM pessoa WHERE nome LIKE 'Ra%' ORDER BY nome;
