-- =====================================================================
-- Projeto Final - Laboratorio de Banco de Dados (UCB 2026/2)
-- Tema: Escola de Musica
-- B3 - Transacoes e controle de concorrencia  (Etapa 2)
--
-- Executar com --force (para o script continuar depois do erro
-- PROPOSITAL da parte 2):
--   mysql -u root -p --force --table < sql/07_transacoes.sql
--
-- A OPERACAO DE NEGOCIO: MATRICULAR UM ALUNO EM UMA TURMA
-- E a mesma que a aplicacao executa (app/repositorio.py, matricular()).
-- Ela altera TRES tabelas, e as tres precisam acontecer juntas:
--   1. MATRICULA            - o vinculo aluno x turma (situacao ATIVA)
--   2. HISTORICO_SITUACAO   - o primeiro evento da matricula (RN17)
--   3. MENSALIDADE          - a primeira cobranca
-- Se a mensalidade falhar e a matricula ficar, temos aluno estudando sem
-- cobranca. Se a matricula falhar e a mensalidade ficar, cobramos quem
-- nao estuda. Por isso: tudo ou nada.
--
-- E antes de inserir, a transacao TRAVA a linha da turma
-- (SELECT ... FOR UPDATE) para contar as vagas. Ver parte 3.
-- =====================================================================

USE escola_musica;
SET NAMES utf8mb4;  -- garante acentos corretos mesmo em terminal sem UTF-8

-- Aluno 23 nao esta na turma 8 (VIO-B1-26C: 8 vagas, 6 ocupadas, nivel sem pre-requisito).
SELECT 'Situacao inicial' AS etapa;
SELECT COUNT(*) AS matriculas_aluno23_turma8
  FROM matricula WHERE id_aluno = 23 AND id_turma = 8;

-- =====================================================================
-- PARTE 1 - TRANSACAO COM SUCESSO (COMMIT)
-- =====================================================================
SELECT 'PARTE 1 - sucesso' AS etapa;

START TRANSACTION;

    -- trava a turma e confere vagas (RN13)
    SELECT t.vagas,
           (SELECT COUNT(*) FROM matricula m
             WHERE m.id_turma = t.id_turma AND m.situacao = 'ATIVA') AS ocupadas
      FROM turma t
     WHERE t.id_turma = 8
       FOR UPDATE;

    INSERT INTO matricula (id_aluno, id_turma, data_matricula, situacao)
    VALUES (23, 8, CURDATE(), 'ATIVA');
    SET @nova = LAST_INSERT_ID();

    INSERT INTO historico_situacao (id_matricula, situacao, data_alteracao, motivo)
    VALUES (@nova, 'ATIVA', NOW(), 'Matricula inicial');

    INSERT INTO mensalidade (id_matricula, competencia, valor, data_vencimento)
    VALUES (@nova, DATE_FORMAT(CURDATE(), '%Y-%m-01'), 320.00,
            DATE_FORMAT(CURDATE(), '%Y-%m-10') + INTERVAL 1 MONTH);

COMMIT;

SELECT m.id_matricula, m.situacao,
       (SELECT COUNT(*) FROM historico_situacao h WHERE h.id_matricula = m.id_matricula) AS historicos,
       (SELECT COUNT(*) FROM mensalidade s WHERE s.id_matricula = m.id_matricula)       AS mensalidades
  FROM matricula m WHERE m.id_aluno = 23 AND m.id_turma = 8;
-- Esperado: 1 matricula, 1 historico, 1 mensalidade.

-- =====================================================================
-- PARTE 2 - FALHA PROVOCADA NO MEIO (ROLLBACK)
-- Aluno 24 na turma 8. A mensalidade vai com valor 0, o que viola
-- ck_mensalidade_valor (RN24). Os dois primeiros INSERTs funcionam;
-- o terceiro falha.
-- =====================================================================
SELECT 'PARTE 2 - falha provocada' AS etapa;

START TRANSACTION;

    SELECT vagas FROM turma WHERE id_turma = 8 FOR UPDATE;

    INSERT INTO matricula (id_aluno, id_turma, data_matricula, situacao)
    VALUES (24, 8, CURDATE(), 'ATIVA');
    SET @nova = LAST_INSERT_ID();

    INSERT INTO historico_situacao (id_matricula, situacao, data_alteracao, motivo)
    VALUES (@nova, 'ATIVA', NOW(), 'Matricula inicial');

    -- ERRO PROPOSITAL: ERROR 3819 Check constraint 'ck_mensalidade_valor' is violated
    INSERT INTO mensalidade (id_matricula, competencia, valor, data_vencimento)
    VALUES (@nova, DATE_FORMAT(CURDATE(), '%Y-%m-01'), 0.00,
            DATE_FORMAT(CURDATE(), '%Y-%m-10') + INTERVAL 1 MONTH);

    -- PONTO IMPORTANTE: no MySQL um erro desfaz SO O COMANDO que falhou,
    -- nao a transacao. A matricula do aluno 24 AINDA EXISTE dentro desta
    -- sessao. Quem desfaz o resto e o ROLLBACK (na aplicacao, o bloco
    -- except chama rollback()).
    SELECT 'dentro da transacao, apos o erro' AS momento, COUNT(*) AS matriculas_aluno24
      FROM matricula WHERE id_aluno = 24 AND id_turma = 8;

ROLLBACK;

SELECT 'depois do ROLLBACK' AS momento, COUNT(*) AS matriculas_aluno24
  FROM matricula WHERE id_aluno = 24 AND id_turma = 8;
SELECT COUNT(*) AS historicos_orfaos
  FROM historico_situacao h
 WHERE NOT EXISTS (SELECT 1 FROM matricula m WHERE m.id_matricula = h.id_matricula);
-- Esperado: 1 dentro da transacao, 0 depois; 0 historicos orfaos.
-- O banco ficou integro.

-- =====================================================================
-- PARTE 3 - EXPERIMENTO DE CONCORRENCIA (duas sessoes)
--
-- Nivel de isolamento em vigor:
SELECT @@transaction_isolation AS isolamento;   -- REPEATABLE-READ (padrao do InnoDB)
--
-- Abrir DOIS terminais:  mysql -u root -p escola_musica
-- A turma 7 (VIO-B2-26B) tem 8 vagas e 7 ocupadas: sobra UMA vaga.
--
-- ---- 3a. SEM trava: duas pessoas pegam a ultima vaga ----
--   SESSAO A                                  SESSAO B
--   START TRANSACTION;
--   SELECT COUNT(*) FROM matricula
--    WHERE id_turma=7 AND situacao='ATIVA';
--   -- ve 7: tem vaga
--                                             START TRANSACTION;
--                                             SELECT COUNT(*) FROM matricula
--                                              WHERE id_turma=7 AND situacao='ATIVA';
--                                             -- tambem ve 7: tem vaga
--   INSERT INTO matricula (id_aluno,id_turma,data_matricula)
--   VALUES (40, 7, CURDATE());
--   COMMIT;
--                                             INSERT INTO matricula (id_aluno,id_turma,data_matricula)
--                                             VALUES (23, 7, CURDATE());
--                                             COMMIT;
--   RESULTADO OBSERVADO: 9 matriculas ativas numa turma de 8 vagas.
--   Nenhum erro, nenhuma espera. O REPEATABLE READ nao protege: cada
--   sessao leu uma "foto" consistente, mas as duas fotos estavam certas
--   e a decisao tomada com base nelas, juntas, ficou errada.
--
-- ---- 3b. COM trava (o que a aplicacao faz) ----
--   SESSAO A                                  SESSAO B
--   START TRANSACTION;
--   SELECT vagas FROM turma
--    WHERE id_turma=7 FOR UPDATE;
--   SELECT COUNT(*) ... -- ve 7
--                                             START TRANSACTION;
--                                             SELECT vagas FROM turma
--                                              WHERE id_turma=7 FOR UPDATE;
--                                             -- FICA ESPERANDO (bloqueio)
--   INSERT ... (aluno 40);
--   COMMIT;
--                                             -- e liberada; o COUNT agora ve 8
--                                             -- a aplicacao recusa: turma lotada
--                                             ROLLBACK;
--   RESULTADO OBSERVADO: a sessao B esperou ate o COMMIT da A e depois
--   viu a vaga ja ocupada. Nenhum excesso de matricula.
--   Se a A demorar mais que innodb_lock_wait_timeout (50 s), a B recebe
--   ERROR 1205 Lock wait timeout exceeded.
--
-- Este experimento foi executado automaticamente por
-- ferramentas/experimento_concorrencia.py; a saida, com os tempos de
-- espera medidos, esta em docs/resultados-concorrencia.txt.
--
-- JUSTIFICATIVA DO NIVEL DE ISOLAMENTO: mantivemos REPEATABLE READ.
--   - READ COMMITTED tambem deixaria o caso 3a acontecer: o problema nao e
--     o nivel, e que "ler, decidir e gravar" precisa de trava explicita.
--   - SERIALIZABLE evitaria o caso 3a sozinho, mas transforma TODA leitura
--     em leitura com trava compartilhada: as telas de consulta e o
--     relatorio passariam a bloquear e ser bloqueados pelas matriculas.
--   - Com REPEATABLE READ + FOR UPDATE so na linha da turma, a trava fica
--     onde o conflito existe (duas matriculas na MESMA turma), e
--     matriculas em turmas diferentes continuam em paralelo.
-- =====================================================================

-- Limpeza: desfaz a matricula da parte 1 para o script poder rodar de novo.
DELETE FROM mensalidade        WHERE id_matricula = (SELECT id_matricula FROM matricula WHERE id_aluno = 23 AND id_turma = 8);
DELETE FROM historico_situacao WHERE id_matricula = (SELECT id_matricula FROM matricula WHERE id_aluno = 23 AND id_turma = 8);
DELETE FROM matricula          WHERE id_aluno = 23 AND id_turma = 8;
