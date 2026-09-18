-- =====================================================================
-- Projeto Final - Laboratorio de Banco de Dados (UCB 2026/2)
-- Tema: Escola de Musica
-- A6 - Script fisico (DDL)
-- SGBD: MySQL 8.4
--
-- Executar do inicio ao fim em base limpa:
--   mysql -u root < sql/01_ddl.sql
--
-- Convencao de nomes das restricoes:
--   pk_ chave primaria   | uq_ unicidade   | fk_ chave estrangeira
--   ck_ verificacao      | idx_ indice
--
-- Politica de ON DELETE / ON UPDATE (ver secao A4 do relatorio):
--   ON UPDATE RESTRICT em todas as FKs: as chaves sao substitutas e nunca
--   mudam; se alguem tentar mudar, um erro e melhor que uma propagacao
--   silenciosa.
--   ON DELETE RESTRICT por padrao (preserva historico academico e financeiro).
--   ON DELETE CASCADE so onde o filho nao existe sem o pai: subclasses de
--   PESSOA, TELEFONE (atributo multivalorado) e AVALIACAO (entidade fraca).
-- =====================================================================

DROP DATABASE IF EXISTS escola_musica;
CREATE DATABASE escola_musica
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_0900_ai_ci;
USE escola_musica;

-- ---------------------------------------------------------------------
-- PESSOA (superclasse da especializacao ALUNO / PROFESSOR)
-- ---------------------------------------------------------------------
CREATE TABLE pessoa (
    id_pessoa        INT UNSIGNED  NOT NULL AUTO_INCREMENT,
    nome             VARCHAR(100)  NOT NULL,
    cpf              CHAR(11)      NOT NULL,
    data_nascimento  DATE          NOT NULL,
    email            VARCHAR(120)  NULL,
    -- endereco: atributo composto, decomposto em colunas
    logradouro       VARCHAR(120)  NULL,
    numero           VARCHAR(10)   NULL,
    bairro           VARCHAR(60)   NULL,
    cidade           VARCHAR(60)   NULL,
    uf               CHAR(2)       NULL,
    cep              CHAR(8)       NULL,
    data_cadastro    DATE          NOT NULL DEFAULT (CURRENT_DATE),
    CONSTRAINT pk_pessoa PRIMARY KEY (id_pessoa),
    -- RN01: o CPF e unico e tem exatamente 11 digitos numericos
    CONSTRAINT uq_pessoa_cpf UNIQUE (cpf),
    CONSTRAINT ck_pessoa_cpf CHECK (cpf REGEXP '^[0-9]{11}$'),
    -- RN02: o e-mail, quando informado, nao se repete
    CONSTRAINT uq_pessoa_email UNIQUE (email),
    -- RN03: data de nascimento plausivel (limite inferior no banco;
    --       "nao futura" fica na aplicacao, pois o MySQL nao aceita
    --       CURRENT_DATE dentro de CHECK)
    CONSTRAINT ck_pessoa_nascimento CHECK (data_nascimento >= '1920-01-01'),
    CONSTRAINT ck_pessoa_uf  CHECK (uf  IS NULL OR uf  REGEXP '^[A-Z]{2}$'),
    CONSTRAINT ck_pessoa_cep CHECK (cep IS NULL OR cep REGEXP '^[0-9]{8}$')
) ENGINE = InnoDB;

-- ---------------------------------------------------------------------
-- TELEFONE (atributo multivalorado de PESSOA)
-- ---------------------------------------------------------------------
CREATE TABLE telefone (
    id_pessoa  INT UNSIGNED NOT NULL,
    numero     VARCHAR(15)  NOT NULL,
    tipo       VARCHAR(8)   NOT NULL DEFAULT 'CELULAR',
    CONSTRAINT pk_telefone PRIMARY KEY (id_pessoa, numero),
    CONSTRAINT ck_telefone_tipo CHECK (tipo IN ('CELULAR', 'FIXO', 'RECADO')),
    CONSTRAINT ck_telefone_numero CHECK (numero REGEXP '^[0-9]{10,11}$'),
    CONSTRAINT fk_telefone_pessoa FOREIGN KEY (id_pessoa)
        REFERENCES pessoa (id_pessoa)
        ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE = InnoDB;

-- ---------------------------------------------------------------------
-- ALUNO (subclasse de PESSOA)
-- ---------------------------------------------------------------------
CREATE TABLE aluno (
    id_pessoa         INT UNSIGNED NOT NULL,
    data_ingresso     DATE         NOT NULL,
    -- RN04: aluno menor de 18 anos precisa de responsavel (verificada por consulta)
    nome_responsavel  VARCHAR(100) NULL,
    CONSTRAINT pk_aluno PRIMARY KEY (id_pessoa),
    CONSTRAINT fk_aluno_pessoa FOREIGN KEY (id_pessoa)
        REFERENCES pessoa (id_pessoa)
        ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE = InnoDB;

-- ---------------------------------------------------------------------
-- PROFESSOR (subclasse de PESSOA)
-- ---------------------------------------------------------------------
CREATE TABLE professor (
    id_pessoa      INT UNSIGNED  NOT NULL,
    data_admissao  DATE          NOT NULL,
    valor_hora     DECIMAL(7,2)  NOT NULL,
    formacao       VARCHAR(100)  NULL,
    CONSTRAINT pk_professor PRIMARY KEY (id_pessoa),
    -- RN05: o valor da hora-aula do professor e positivo
    CONSTRAINT ck_professor_valor_hora CHECK (valor_hora > 0),
    CONSTRAINT fk_professor_pessoa FOREIGN KEY (id_pessoa)
        REFERENCES pessoa (id_pessoa)
        ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE = InnoDB;

-- ---------------------------------------------------------------------
-- INSTRUMENTO
-- ---------------------------------------------------------------------
CREATE TABLE instrumento (
    id_instrumento  SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT,
    nome            VARCHAR(40)       NOT NULL,
    familia         VARCHAR(10)       NOT NULL,
    CONSTRAINT pk_instrumento PRIMARY KEY (id_instrumento),
    -- RN06: o nome do instrumento e unico e a familia pertence a um conjunto fixo
    CONSTRAINT uq_instrumento_nome UNIQUE (nome),
    CONSTRAINT ck_instrumento_familia
        CHECK (familia IN ('CORDAS', 'SOPRO', 'PERCUSSAO', 'TECLAS', 'VOZ'))
) ENGINE = InnoDB;

-- ---------------------------------------------------------------------
-- HABILITACAO (N:N PROFESSOR x INSTRUMENTO, com atributos proprios)
-- ---------------------------------------------------------------------
CREATE TABLE habilitacao (
    id_professor        INT UNSIGNED      NOT NULL,
    id_instrumento      SMALLINT UNSIGNED NOT NULL,
    nivel_proficiencia  VARCHAR(13)       NOT NULL,
    data_certificacao   DATE              NOT NULL,
    CONSTRAINT pk_habilitacao PRIMARY KEY (id_professor, id_instrumento),
    -- RN07: a proficiencia do professor e INTERMEDIARIO, AVANCADO ou ESPECIALISTA
    CONSTRAINT ck_habilitacao_proficiencia
        CHECK (nivel_proficiencia IN ('INTERMEDIARIO', 'AVANCADO', 'ESPECIALISTA')),
    CONSTRAINT fk_habilitacao_professor FOREIGN KEY (id_professor)
        REFERENCES professor (id_pessoa)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_habilitacao_instrumento FOREIGN KEY (id_instrumento)
        REFERENCES instrumento (id_instrumento)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    INDEX idx_habilitacao_instrumento (id_instrumento)
) ENGINE = InnoDB;

-- ---------------------------------------------------------------------
-- NIVEL (com AUTORRELACIONAMENTO de pre-requisito)
-- ---------------------------------------------------------------------
CREATE TABLE nivel (
    id_nivel               SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT,
    id_instrumento         SMALLINT UNSIGNED NOT NULL,
    nome                   VARCHAR(40)       NOT NULL,
    ordem                  TINYINT UNSIGNED  NOT NULL,
    carga_horaria          SMALLINT UNSIGNED NOT NULL,
    id_nivel_prerequisito  SMALLINT UNSIGNED NULL,
    CONSTRAINT pk_nivel PRIMARY KEY (id_nivel),
    -- RN08: dentro de um instrumento, cada posicao na sequencia de niveis e unica
    CONSTRAINT uq_nivel_instrumento_ordem UNIQUE (id_instrumento, ordem),
    CONSTRAINT ck_nivel_ordem CHECK (ordem BETWEEN 1 AND 10),
    CONSTRAINT ck_nivel_carga CHECK (carga_horaria BETWEEN 8 AND 200),
    CONSTRAINT fk_nivel_instrumento FOREIGN KEY (id_instrumento)
        REFERENCES instrumento (id_instrumento)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    -- RN09: um nivel pode exigir outro nivel como pre-requisito;
    --       um nivel que e pre-requisito de outro nao pode ser excluido
    CONSTRAINT fk_nivel_prerequisito FOREIGN KEY (id_nivel_prerequisito)
        REFERENCES nivel (id_nivel)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    INDEX idx_nivel_prerequisito (id_nivel_prerequisito)
) ENGINE = InnoDB;

-- ---------------------------------------------------------------------
-- SALA
-- ---------------------------------------------------------------------
CREATE TABLE sala (
    id_sala       TINYINT UNSIGNED NOT NULL AUTO_INCREMENT,
    nome          VARCHAR(30)      NOT NULL,
    capacidade    TINYINT UNSIGNED NOT NULL,
    possui_piano  BOOLEAN          NOT NULL DEFAULT FALSE,
    CONSTRAINT pk_sala PRIMARY KEY (id_sala),
    CONSTRAINT uq_sala_nome UNIQUE (nome),
    -- RN10: a capacidade da sala fica entre 1 e 30 pessoas
    CONSTRAINT ck_sala_capacidade CHECK (capacidade BETWEEN 1 AND 30)
) ENGINE = InnoDB;

-- ---------------------------------------------------------------------
-- TURMA
-- ---------------------------------------------------------------------
CREATE TABLE turma (
    id_turma        INT UNSIGNED      NOT NULL AUTO_INCREMENT,
    codigo          VARCHAR(12)       NOT NULL,
    id_nivel        SMALLINT UNSIGNED NOT NULL,
    id_professor    INT UNSIGNED      NOT NULL,
    id_sala         TINYINT UNSIGNED  NOT NULL,
    dia_semana      TINYINT UNSIGNED  NOT NULL,  -- padrao DAYOFWEEK: 2=segunda ... 7=sabado
    horario_inicio  TIME              NOT NULL,
    data_inicio     DATE              NOT NULL,
    data_fim        DATE              NOT NULL,
    vagas           TINYINT UNSIGNED  NOT NULL,
    CONSTRAINT pk_turma PRIMARY KEY (id_turma),
    CONSTRAINT uq_turma_codigo UNIQUE (codigo),
    -- RN11: a escola funciona de segunda a sabado, com inicio de aula entre 08h e 21h
    CONSTRAINT ck_turma_dia CHECK (dia_semana BETWEEN 2 AND 7),
    CONSTRAINT ck_turma_horario CHECK (horario_inicio BETWEEN '08:00:00' AND '21:00:00'),
    -- RN12: a data de termino da turma e posterior a data de inicio
    CONSTRAINT ck_turma_periodo CHECK (data_fim > data_inicio),
    -- RN13: uma turma oferece de 1 a 20 vagas (nao exceder a sala fica na aplicacao)
    CONSTRAINT ck_turma_vagas CHECK (vagas BETWEEN 1 AND 20),
    CONSTRAINT fk_turma_nivel FOREIGN KEY (id_nivel)
        REFERENCES nivel (id_nivel)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_turma_professor FOREIGN KEY (id_professor)
        REFERENCES professor (id_pessoa)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_turma_sala FOREIGN KEY (id_sala)
        REFERENCES sala (id_sala)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    INDEX idx_turma_nivel (id_nivel),
    INDEX idx_turma_professor (id_professor),
    INDEX idx_turma_sala (id_sala)
) ENGINE = InnoDB;

-- ---------------------------------------------------------------------
-- MATRICULA (N:N ALUNO x TURMA, com atributos proprios)
-- ---------------------------------------------------------------------
CREATE TABLE matricula (
    id_matricula    INT UNSIGNED NOT NULL AUTO_INCREMENT,
    id_aluno        INT UNSIGNED NOT NULL,
    id_turma        INT UNSIGNED NOT NULL,
    data_matricula  DATE         NOT NULL,
    situacao        VARCHAR(10)  NOT NULL DEFAULT 'ATIVA',
    CONSTRAINT pk_matricula PRIMARY KEY (id_matricula),
    -- RN14: um aluno nao se matricula duas vezes na mesma turma
    CONSTRAINT uq_matricula_aluno_turma UNIQUE (id_aluno, id_turma),
    -- RN15: a situacao atual da matricula e ATIVA, CONCLUIDA, TRANCADA ou CANCELADA
    CONSTRAINT ck_matricula_situacao
        CHECK (situacao IN ('ATIVA', 'CONCLUIDA', 'TRANCADA', 'CANCELADA')),
    -- RN16: aluno com matricula nao pode ser excluido (preserva historico)
    CONSTRAINT fk_matricula_aluno FOREIGN KEY (id_aluno)
        REFERENCES aluno (id_pessoa)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_matricula_turma FOREIGN KEY (id_turma)
        REFERENCES turma (id_turma)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    INDEX idx_matricula_turma (id_turma)
) ENGINE = InnoDB;

-- ---------------------------------------------------------------------
-- HISTORICO_SITUACAO (atributo temporal: situacao da matricula ao longo do tempo)
-- ---------------------------------------------------------------------
CREATE TABLE historico_situacao (
    id_historico    INT UNSIGNED NOT NULL AUTO_INCREMENT,
    id_matricula    INT UNSIGNED NOT NULL,
    situacao        VARCHAR(10)  NOT NULL,
    data_alteracao  DATETIME     NOT NULL,
    motivo          VARCHAR(200) NULL,
    CONSTRAINT pk_historico_situacao PRIMARY KEY (id_historico),
    -- RN17: toda mudanca de situacao da matricula fica registrada com data e hora;
    --       duas mudancas da mesma matricula nao ocorrem no mesmo instante
    CONSTRAINT uq_historico_matricula_data UNIQUE (id_matricula, data_alteracao),
    CONSTRAINT ck_historico_situacao
        CHECK (situacao IN ('ATIVA', 'CONCLUIDA', 'TRANCADA', 'CANCELADA')),
    CONSTRAINT fk_historico_matricula FOREIGN KEY (id_matricula)
        REFERENCES matricula (id_matricula)
        ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB;

-- ---------------------------------------------------------------------
-- AULA
-- ---------------------------------------------------------------------
CREATE TABLE aula (
    id_aula      INT UNSIGNED     NOT NULL AUTO_INCREMENT,
    id_turma     INT UNSIGNED     NOT NULL,
    numero_aula  TINYINT UNSIGNED NOT NULL,
    data_aula    DATE             NOT NULL,
    conteudo     VARCHAR(200)     NULL,
    status       VARCHAR(10)      NOT NULL DEFAULT 'REALIZADA',
    CONSTRAINT pk_aula PRIMARY KEY (id_aula),
    -- RN18: dentro de uma turma, o numero da aula e a data da aula nao se repetem
    CONSTRAINT uq_aula_turma_numero UNIQUE (id_turma, numero_aula),
    CONSTRAINT uq_aula_turma_data UNIQUE (id_turma, data_aula),
    CONSTRAINT ck_aula_status CHECK (status IN ('REALIZADA', 'CANCELADA')),
    CONSTRAINT fk_aula_turma FOREIGN KEY (id_turma)
        REFERENCES turma (id_turma)
        ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB;

-- ---------------------------------------------------------------------
-- FREQUENCIA (N:N MATRICULA x AULA, com atributos proprios)
-- Tabela de maior movimento do sistema.
-- ---------------------------------------------------------------------
CREATE TABLE frequencia (
    id_matricula   INT UNSIGNED NOT NULL,
    id_aula        INT UNSIGNED NOT NULL,
    presente       BOOLEAN      NOT NULL,
    justificativa  VARCHAR(200) NULL,
    -- RN19: a presenca de um aluno e registrada uma unica vez por aula
    CONSTRAINT pk_frequencia PRIMARY KEY (id_matricula, id_aula),
    -- RN20: justificativa so existe para falta
    CONSTRAINT ck_frequencia_justificativa
        CHECK (presente = FALSE OR justificativa IS NULL),
    CONSTRAINT fk_frequencia_matricula FOREIGN KEY (id_matricula)
        REFERENCES matricula (id_matricula)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_frequencia_aula FOREIGN KEY (id_aula)
        REFERENCES aula (id_aula)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    INDEX idx_frequencia_aula (id_aula)
) ENGINE = InnoDB;

-- ---------------------------------------------------------------------
-- AVALIACAO (ENTIDADE FRACA: identificada pela MATRICULA + numero)
-- ---------------------------------------------------------------------
CREATE TABLE avaliacao (
    id_matricula      INT UNSIGNED     NOT NULL,
    numero_avaliacao  TINYINT UNSIGNED NOT NULL,
    tipo              VARCHAR(8)       NOT NULL,
    data_avaliacao    DATE             NOT NULL,
    nota              DECIMAL(4,2)     NOT NULL,
    CONSTRAINT pk_avaliacao PRIMARY KEY (id_matricula, numero_avaliacao),
    -- RN21: a avaliacao e PRATICA, TEORICA ou RECITAL
    CONSTRAINT ck_avaliacao_tipo CHECK (tipo IN ('PRATICA', 'TEORICA', 'RECITAL')),
    -- RN22: a nota da avaliacao vai de 0 a 10
    CONSTRAINT ck_avaliacao_nota CHECK (nota BETWEEN 0 AND 10),
    CONSTRAINT ck_avaliacao_numero CHECK (numero_avaliacao BETWEEN 1 AND 10),
    -- entidade fraca: nao existe sem a matricula dona, por isso CASCADE
    CONSTRAINT fk_avaliacao_matricula FOREIGN KEY (id_matricula)
        REFERENCES matricula (id_matricula)
        ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE = InnoDB;

-- ---------------------------------------------------------------------
-- MENSALIDADE
-- ---------------------------------------------------------------------
CREATE TABLE mensalidade (
    id_mensalidade   INT UNSIGNED  NOT NULL AUTO_INCREMENT,
    id_matricula     INT UNSIGNED  NOT NULL,
    competencia      DATE          NOT NULL,  -- sempre o dia 1 do mes de referencia
    valor            DECIMAL(8,2)  NOT NULL,
    data_vencimento  DATE          NOT NULL,
    data_pagamento   DATE          NULL,      -- NULL = mensalidade em aberto
    forma_pagamento  VARCHAR(8)    NULL,
    CONSTRAINT pk_mensalidade PRIMARY KEY (id_mensalidade),
    -- RN23: existe no maximo uma mensalidade por matricula em cada mes
    CONSTRAINT uq_mensalidade_matricula_competencia UNIQUE (id_matricula, competencia),
    CONSTRAINT ck_mensalidade_competencia CHECK (DAY(competencia) = 1),
    -- RN24: o valor da mensalidade e positivo e o vencimento cai no mes de referencia ou depois
    CONSTRAINT ck_mensalidade_valor CHECK (valor > 0),
    CONSTRAINT ck_mensalidade_vencimento CHECK (data_vencimento >= competencia),
    -- RN25: mensalidade paga tem data e forma de pagamento; em aberto nao tem nenhuma das duas
    CONSTRAINT ck_mensalidade_pagamento CHECK (
        (data_pagamento IS NULL AND forma_pagamento IS NULL)
        OR (data_pagamento IS NOT NULL
            AND forma_pagamento IN ('PIX', 'CARTAO', 'BOLETO', 'DINHEIRO'))
    ),
    CONSTRAINT fk_mensalidade_matricula FOREIGN KEY (id_matricula)
        REFERENCES matricula (id_matricula)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    INDEX idx_mensalidade_pagamento (data_pagamento)
) ENGINE = InnoDB;

-- Regras sem restricao direta no DDL (atendidas por consulta ou aplicacao):
--   RN03 data de nascimento nao futura               -> aplicacao
--   RN04 aluno menor de 18 anos tem responsavel      -> consulta C15 (e C01)
--   RN13 vagas da turma nao excedem a sala           -> aplicacao
--   RN26 especializacao total: toda pessoa e aluno, professor ou ambos -> consulta C15
--   RN27 professor da turma e habilitado no instrumento do nivel      -> consulta C15
--   RN28 matricula em nivel com pre-requisito exige o anterior CONCLUIDO -> consulta C15
--   RN29 aprovacao: media >= 6,0 e frequencia >= 75%                  -> consulta C11
--   RN30 frequencia so e lancada para aula da turma da propria matricula -> consulta C15 / aplicacao
