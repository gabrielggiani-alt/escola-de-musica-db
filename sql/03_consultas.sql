-- =====================================================================
-- Projeto Final - Laboratorio de Banco de Dados (UCB 2026/2)
-- A8 - Consultas de verificacao - Escola de Musica
-- Executar depois de 01_ddl.sql e 02_carga.sql.
-- Data de referencia dos dados: 18/09/2026 (usada nas consultas que falam
-- de "hoje", para o resultado nao mudar conforme o dia em que se roda).
--
-- Basicas ......... C01 a C05
-- Juncoes/agregacao C06 a C10
-- Avancadas ....... C11 a C15
-- =====================================================================
USE escola_musica;

SET @hoje = DATE '2026-09-18';

-- =====================================================================
-- BASICAS
-- =====================================================================

-- C01 | Projecao, WHERE e ORDER BY
-- Pergunta: quais alunos sao menores de idade e quem e o responsavel por
--           cada um? (apoia a RN04)
SELECT p.nome,
       TIMESTAMPDIFF(YEAR, p.data_nascimento, @hoje) AS idade,
       a.nome_responsavel
FROM aluno a
JOIN pessoa p ON p.id_pessoa = a.id_pessoa
WHERE TIMESTAMPDIFF(YEAR, p.data_nascimento, @hoje) < 18
ORDER BY idade, p.nome;

-- C02 | LIKE
-- Pergunta: quais pessoas moram nas Asas (Norte ou Sul), para montar a rota
--           de divulgacao do recital no Plano Piloto?
SELECT nome, bairro, logradouro
FROM pessoa
WHERE bairro LIKE 'Asa %'
ORDER BY bairro, nome;

-- C03 | BETWEEN + tratamento de NULL (IS NULL)
-- Pergunta: quais mensalidades venceram entre 01/08/2026 e hoje e continuam
--           sem pagamento?
SELECT id_mensalidade, id_matricula, competencia, data_vencimento, valor
FROM mensalidade
WHERE data_vencimento BETWEEN '2026-08-01' AND @hoje
  AND data_pagamento IS NULL
ORDER BY data_vencimento;

-- C04 | IN
-- Pergunta: quais turmas do semestre 2026/2 acontecem as segundas, quartas ou
--           sextas-feiras? (dias em que a recepcao funciona em horario reduzido)
SELECT codigo, dia_semana, horario_inicio, id_sala
FROM turma
WHERE dia_semana IN (2, 4, 6)
  AND data_inicio >= '2026-08-01'
ORDER BY dia_semana, horario_inicio;

-- C05 | Tratamento de NULL (COALESCE / IS NULL)
-- Pergunta: qual o melhor contato de cada pessoa, e quem esta com cadastro
--           incompleto (sem e-mail ou sem endereco)?
SELECT nome,
       COALESCE(email, 'sem e-mail cadastrado')      AS contato_email,
       COALESCE(cidade, 'endereco nao informado')    AS cidade,
       CASE WHEN email IS NULL OR logradouro IS NULL
            THEN 'INCOMPLETO' ELSE 'COMPLETO' END    AS cadastro
FROM pessoa
WHERE email IS NULL OR logradouro IS NULL
ORDER BY nome;

-- =====================================================================
-- JUNCOES E AGREGACAO
-- =====================================================================

-- C06 | Juncao com tres tabelas ou mais
-- Pergunta: quem sao os alunos ativos de cada turma, com o nivel e o
--           professor responsavel?
SELECT t.codigo,
       n.nome   AS nivel,
       pp.nome  AS professor,
       pa.nome  AS aluno
FROM matricula m
JOIN turma  t  ON t.id_turma  = m.id_turma
JOIN nivel  n  ON n.id_nivel  = t.id_nivel
JOIN pessoa pa ON pa.id_pessoa = m.id_aluno
JOIN pessoa pp ON pp.id_pessoa = t.id_professor
WHERE m.situacao = 'ATIVA'
ORDER BY t.codigo, pa.nome;

-- C07 | LEFT JOIN
-- Pergunta: quantas turmas ja foram abertas para cada nivel, incluindo os
--           niveis que nunca tiveram turma?
SELECT i.nome AS instrumento,
       n.nome AS nivel,
       COUNT(t.id_turma) AS qtd_turmas
FROM nivel n
JOIN instrumento i ON i.id_instrumento = n.id_instrumento
LEFT JOIN turma t  ON t.id_nivel = n.id_nivel
GROUP BY i.nome, n.nome, n.ordem
ORDER BY i.nome, n.ordem;

-- C08 | LEFT JOIN + GROUP BY + HAVING
-- Pergunta: quais turmas de 2026/2 estao com menos da metade das vagas
--           ocupadas por alunos ativos? (candidatas a campanha de captacao)
SELECT t.codigo,
       t.vagas,
       COUNT(m.id_matricula) AS ativos,
       ROUND(100 * COUNT(m.id_matricula) / t.vagas, 1) AS ocupacao_pct
FROM turma t
LEFT JOIN matricula m
       ON m.id_turma = t.id_turma AND m.situacao = 'ATIVA'
WHERE t.data_inicio >= '2026-08-01'
GROUP BY t.id_turma, t.codigo, t.vagas
HAVING COUNT(m.id_matricula) < t.vagas / 2
ORDER BY ocupacao_pct;

-- C09 | GROUP BY com funcoes de agregacao
-- Pergunta: quanto a escola recebeu por mes de competencia e por forma de
--           pagamento?
SELECT DATE_FORMAT(competencia, '%Y-%m') AS mes,
       forma_pagamento,
       COUNT(*)   AS qtd_pagamentos,
       SUM(valor) AS total_recebido
FROM mensalidade
WHERE data_pagamento IS NOT NULL
GROUP BY mes, forma_pagamento
ORDER BY mes, total_recebido DESC;

-- C10 | GROUP BY + HAVING
-- Pergunta: quais turmas tem frequencia media abaixo de 85% nas aulas
--           realizadas? (alerta pedagogico)
SELECT t.codigo,
       COUNT(*) AS registros,
       ROUND(100 * AVG(f.presente), 1) AS frequencia_pct
FROM frequencia f
JOIN aula  a ON a.id_aula  = f.id_aula
JOIN turma t ON t.id_turma = a.id_turma
GROUP BY t.id_turma, t.codigo
HAVING AVG(f.presente) < 0.85
ORDER BY frequencia_pct;

-- =====================================================================
-- AVANCADAS
-- =====================================================================

-- C11 | Pergunta de negocio nao trivial (RN29)
-- Pergunta: no semestre 2026/1, quais alunos foram aprovados em cada nivel?
--           Aprovado = media das avaliacoes >= 6,0 E frequencia >= 75%.
SELECT pa.nome AS aluno,
       t.codigo,
       notas.media,
       freq.frequencia_pct,
       CASE WHEN notas.media >= 6 AND freq.frequencia_pct >= 75
            THEN 'APROVADO' ELSE 'REPROVADO' END AS resultado
FROM matricula m
JOIN turma  t  ON t.id_turma   = m.id_turma
JOIN pessoa pa ON pa.id_pessoa = m.id_aluno
JOIN (SELECT id_matricula, ROUND(AVG(nota), 2) AS media
      FROM avaliacao GROUP BY id_matricula) AS notas
     ON notas.id_matricula = m.id_matricula
JOIN (SELECT id_matricula, ROUND(100 * AVG(presente), 1) AS frequencia_pct
      FROM frequencia GROUP BY id_matricula) AS freq
     ON freq.id_matricula = m.id_matricula
WHERE t.data_fim < @hoje
  AND m.situacao = 'CONCLUIDA'
ORDER BY t.codigo, resultado, pa.nome;

-- C12 | Subconsulta correlacionada
-- Pergunta: quais alunos tiveram media acima da media da propria turma?
SELECT pa.nome, t.codigo, ROUND(AVG(av.nota), 2) AS media_aluno
FROM avaliacao av
JOIN matricula m  ON m.id_matricula = av.id_matricula
JOIN turma     t  ON t.id_turma     = m.id_turma
JOIN pessoa    pa ON pa.id_pessoa   = m.id_aluno
GROUP BY av.id_matricula, pa.nome, t.codigo, m.id_turma
HAVING AVG(av.nota) > (
    -- correlacionada: recalculada para a turma de cada linha externa
    SELECT AVG(av2.nota)
    FROM avaliacao av2
    JOIN matricula m2 ON m2.id_matricula = av2.id_matricula
    WHERE m2.id_turma = m.id_turma
)
ORDER BY t.codigo, media_aluno DESC;

-- C13 | EXISTS
-- Pergunta: quais alunos concluiram um nivel e continuaram estudando na escola
--           no semestre seguinte? (indicador de retencao)
SELECT p.nome
FROM aluno a
JOIN pessoa p ON p.id_pessoa = a.id_pessoa
WHERE EXISTS (SELECT 1 FROM matricula m
              WHERE m.id_aluno = a.id_pessoa AND m.situacao = 'CONCLUIDA')
  AND EXISTS (SELECT 1 FROM matricula m
              JOIN turma t ON t.id_turma = m.id_turma
              WHERE m.id_aluno = a.id_pessoa
                AND m.situacao = 'ATIVA'
                AND t.data_inicio >= '2026-08-01')
ORDER BY p.nome;

-- C14 | Pergunta de negocio nao trivial: inadimplencia
-- Pergunta: quem esta devendo hoje, quanto, e ha quantos dias vence a divida
--           mais antiga? Traz o telefone celular para a cobranca.
SELECT p.nome,
       COUNT(*)                               AS parcelas_em_aberto,
       SUM(ms.valor)                          AS total_devido,
       DATEDIFF(@hoje, MIN(ms.data_vencimento)) AS dias_da_mais_antiga,
       (SELECT tl.numero FROM telefone tl
        WHERE tl.id_pessoa = p.id_pessoa AND tl.tipo = 'CELULAR'
        LIMIT 1)                              AS celular
FROM mensalidade ms
JOIN matricula m ON m.id_matricula = ms.id_matricula
JOIN pessoa    p ON p.id_pessoa    = m.id_aluno
WHERE ms.data_pagamento IS NULL
  AND ms.data_vencimento < @hoje
GROUP BY p.id_pessoa, p.nome
ORDER BY total_devido DESC, dias_da_mais_antiga DESC;

-- C15 | NOT EXISTS - auditoria das regras que o DDL nao consegue garantir
-- Pergunta: existe algum registro violando as regras atendidas "por consulta"?
--           Resultado esperado: zero em todas as linhas.
SELECT 'RN04 menor de idade sem responsavel' AS regra, COUNT(*) AS violacoes
FROM aluno a JOIN pessoa p ON p.id_pessoa = a.id_pessoa
WHERE TIMESTAMPDIFF(YEAR, p.data_nascimento, @hoje) < 18
  AND a.nome_responsavel IS NULL
UNION ALL
SELECT 'RN26 pessoa sem papel (nem aluno nem professor)', COUNT(*)
FROM pessoa p
WHERE NOT EXISTS (SELECT 1 FROM aluno a     WHERE a.id_pessoa = p.id_pessoa)
  AND NOT EXISTS (SELECT 1 FROM professor r WHERE r.id_pessoa = p.id_pessoa)
UNION ALL
SELECT 'RN27 professor nao habilitado no instrumento da turma', COUNT(*)
FROM turma t JOIN nivel n ON n.id_nivel = t.id_nivel
WHERE NOT EXISTS (SELECT 1 FROM habilitacao h
                  WHERE h.id_professor = t.id_professor
                    AND h.id_instrumento = n.id_instrumento)
UNION ALL
SELECT 'RN28 matricula sem o pre-requisito concluido', COUNT(*)
FROM matricula m
JOIN turma t ON t.id_turma = m.id_turma
JOIN nivel n ON n.id_nivel = t.id_nivel
WHERE n.id_nivel_prerequisito IS NOT NULL
  AND NOT EXISTS (SELECT 1 FROM matricula m2
                  JOIN turma t2 ON t2.id_turma = m2.id_turma
                  WHERE m2.id_aluno = m.id_aluno
                    AND t2.id_nivel = n.id_nivel_prerequisito
                    AND m2.situacao = 'CONCLUIDA')
UNION ALL
SELECT 'RN30 frequencia lancada em aula de outra turma', COUNT(*)
FROM frequencia f
JOIN matricula m ON m.id_matricula = f.id_matricula
JOIN aula a      ON a.id_aula      = f.id_aula
WHERE a.id_turma <> m.id_turma;
