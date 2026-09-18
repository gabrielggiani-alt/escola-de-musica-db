# Guia da equipe — Etapa 1

Este guia é para quem não participou da montagem. Na arguição, o professor pode
perguntar **qualquer parte a qualquer integrante** (seção 3 do enunciado), então
todo mundo precisa conseguir responder o que está aqui.

## 1. Como rodar em 2 minutos

1. Ter o MySQL 8 rodando (MySQL Workbench ou terminal).
2. Executar, nesta ordem: `sql/01_ddl.sql`, `sql/02_carga.sql`, `sql/03_consultas.sql`.
3. A última consulta (C15) precisa mostrar **0** em todas as linhas.

## 2. O domínio em uma frase

A escola tem **instrumentos**, e cada instrumento tem **níveis** em sequência. Cada
semestre abre **turmas** de um nível, com professor, sala e horário. O **aluno** se
**matricula** na turma, tem **aulas** com **frequência**, faz **avaliações** e paga
**mensalidades**.

## 3. As perguntas que o professor provavelmente vai fazer

**"Onde está cada requisito mínimo?"**

| Requisito | Onde |
|---|---|
| Especialização | PESSOA → ALUNO / PROFESSOR, total e sobreposta |
| Autorrelacionamento | NIVEL → NIVEL (pré-requisito) |
| Entidade fraca | AVALIACAO (só existe dentro da MATRICULA) |
| N:N com atributo | HABILITACAO, MATRICULA, FREQUENCIA |
| Atributo temporal | HISTORICO_SITUACAO |

**"Por que a especialização virou três tabelas?"**
Porque ela é **sobreposta**: a pessoa 6 é professora e também aluna. Com uma tabela
só, sobrariam colunas vazias. Com uma tabela por subclasse sem a superclasse, o CPF
de quem é as duas coisas ficaria gravado duas vezes. Com três tabelas, a FK de
matrícula aponta só para aluno, e a de turma só para professor.

**"O que significa total e sobreposta?"**
- **Total:** não existe pessoa sem papel.
- **Sobreposta:** a mesma pessoa pode ser aluno e professor ao mesmo tempo.

A parte "total" o banco não consegue garantir sozinho, então a consulta C15 verifica.

**"Por que AVALIACAO é fraca?"**
O número da avaliação sozinho não identifica nada: "avaliação 2" de quem? Ela só é
identificada junto com a matrícula. Por isso a chave é (id_matricula,
numero_avaliacao), com `ON DELETE CASCADE`.

**"Por que chave substituta (id) e não o CPF?"**
O CPF é dado pessoal e pode ter sido digitado errado. Se fosse PK, apareceria em
todas as tabelas filhas, e corrigir exigiria mexer em todas elas. Ele continua
**único**, pela restrição `uq_pessoa_cpf`.

**"O banco está na 3FN?"**
Sim, e quase tudo está em FNBC. A exceção deliberada é o **CEP**: no mundo real o
CEP determina cidade e bairro, o que é dependência transitiva. Normalizar exigiria
a base de CEPs dos Correios, que a escola não tem. A decisão está justificada na
seção A5 do relatório.

**"Por que ON DELETE RESTRICT quase sempre?"**
Para não perder histórico: apagar um aluno não pode sumir com as notas e os
pagamentos dele. `CASCADE` só aparece onde o filho não existe sem o pai: telefone,
avaliação e as subclasses.

**"Por que VARCHAR com CHECK, e não ENUM?"**
O erro aparece com o nome da regra (por exemplo `ck_matricula_situacao`), e
acrescentar um valor novo não reescreve a tabela.

**"Os dados são reais?"**
Não. Foram gerados pelo `ferramentas/gerar_carga.py`, com CPF inválido de propósito
e e-mails `@exemplo.com`.

**"Onde a IA foi usada?"**
Está declarado na seção 8 do relatório. O que importa na arguição é saber explicar
cada decisão, e este guia serve para isso.

## 4. Roteiro da apresentação (12 minutos)

| Tempo | Parte | Quem |
|---|---|---|
| 2 min | Domínio e regras de negócio (A1) | Gabriel |
| 2,5 min | MER: especialização, fraca, autorrelacionamento, N:N (A2) | ______ |
| 2,5 min | Modelo lógico: decisões de mapeamento e chaves (A4) | ______ |
| 2 min | Normalização: dependências funcionais, 3FN e o caso do CEP (A5) | ______ |
| 2 min | Scripts: rodar DDL, carga e as consultas C11 e C15 ao vivo | ______ |
| 1 min | Perguntas | todos |

## 5. Antes de entregar (checklist do Anexo B)

- [x] DDL roda em base limpa sem erro
- [x] Carga roda em seguida sem erro
- [x] 15 consultas retornam resultado coerente
- [x] Restrições nomeadas com pk_, uq_, fk_, ck_, idx_
- [x] ON DELETE e ON UPDATE explícitos em toda FK
- [x] Requisitos mínimos atendidos
- [x] 20 ou mais regras numeradas e rastreadas
- [x] MER numa notação só
- [x] Decisões de mapeamento justificadas em texto
- [x] Dependências funcionais listadas
- [x] Relatório em PDF paginado
- [ ] **Preencher o nome dos integrantes** (capa do relatório e README)
- [ ] Repositório acessível ao professor
- [ ] **Todo mundo ler este guia**
