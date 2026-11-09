-- =====================================================================
-- DEMONSTRACAO AO VIVO: o banco integro depois da transacao (roteiro 6.2)
-- Rodar no MySQL Workbench (raio) DEPOIS de fazer na aplicacao:
--   1. matricula do Wagner Rocha Siqueira na VIO-B1-26C com valor 320  (sucesso)
--   2. matricula do Rafael Nogueira Almeida na VIO-B1-26C com valor 0  (falha)
--
-- O que mostrar:
--   Wagner: 1 matricula, 1 historico, 1 mensalidade -> as tres tabelas gravadas (COMMIT)
--   Rafael: 0, 0, 0                                -> nada ficou pela metade (ROLLBACK)
--   Orfaos: 0 em tudo                              -> o banco continua integro
-- =====================================================================
USE escola_musica;
SET NAMES utf8mb4;

-- 1. O que cada aluno tem na turma VIO-B1-26C, nas tres tabelas da transacao
SELECT p.nome AS aluno,
       COUNT(DISTINCT m.id_matricula)   AS matriculas,
       COUNT(DISTINCT h.id_historico)   AS historicos,
       COUNT(DISTINCT ms.id_mensalidade) AS mensalidades
  FROM pessoa p
  LEFT JOIN matricula m ON m.id_aluno = p.id_pessoa
        AND m.id_turma = (SELECT id_turma FROM turma WHERE codigo = 'VIO-B1-26C')
  LEFT JOIN historico_situacao h ON h.id_matricula = m.id_matricula
  LEFT JOIN mensalidade ms       ON ms.id_matricula = m.id_matricula
 WHERE p.nome IN ('Wagner Rocha Siqueira', 'Rafael Nogueira Almeida')
 GROUP BY p.nome;

-- 2. Nenhum registro pela metade em lugar nenhum do banco
SELECT
  (SELECT COUNT(*) FROM matricula m
    WHERE NOT EXISTS (SELECT 1 FROM historico_situacao h
                       WHERE h.id_matricula = m.id_matricula)) AS matriculas_sem_historico,
  (SELECT COUNT(*) FROM historico_situacao h
    WHERE NOT EXISTS (SELECT 1 FROM matricula m
                       WHERE m.id_matricula = h.id_matricula)) AS historicos_orfaos,
  (SELECT COUNT(*) FROM mensalidade ms
    WHERE NOT EXISTS (SELECT 1 FROM matricula m
                       WHERE m.id_matricula = ms.id_matricula)) AS mensalidades_orfas;

-- 3. Ocupacao da turma: eram 6, agora 7 (so o Wagner entrou)
SELECT codigo, vagas, ocupadas, livres FROM vw_ocupacao_turma WHERE codigo = 'VIO-B1-26C';
