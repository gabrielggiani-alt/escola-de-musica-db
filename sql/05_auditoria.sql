-- =====================================================================
-- Projeto Final - Laboratorio de Banco de Dados (UCB 2026/2)
-- Tema: Escola de Musica
-- B6 - Gatilhos e auditoria  (Etapa 2)
--
-- Executar DEPOIS de 04_seguranca.sql:
--   mysql -u root < sql/05_auditoria.sql
--
-- O QUE AUDITAR E POR QUE (justificativa pelo dominio):
--
--  1. MENSALIDADE: e dinheiro. Uma baixa de pagamento lancada por engano,
--     ou um valor alterado depois do vencimento, vira prejuizo ou
--     cobranca indevida ao aluno. Precisamos saber quem mudou, quando e
--     de que valor para qual valor.
--
--  2. MATRICULA (situacao): trancar ou cancelar uma matricula libera vaga,
--     interrompe cobranca e muda o historico academico do aluno. Uma
--     mudanca indevida prejudica o aluno e a escola. HISTORICO_SITUACAO
--     registra O QUE mudou na vida academica; a AUDITORIA registra QUEM
--     mudou, qual usuario da aplicacao e qual usuario do banco.
--
-- Nao auditamos AULA nem FREQUENCIA: sao a tabela de maior movimento e
-- as alteracoes nelas nao tem impacto financeiro; auditar tudo gera
-- volume sem utilidade.
--
-- AUTOR: a aplicacao executa  SET @usuario_app = '<login>'  logo apos
-- conectar. Se a alteracao vier direto do terminal, @usuario_app fica
-- NULL e o gatilho registra o usuario do MySQL (USER()).
-- Os gatilhos executam com os privilegios de quem os criou (DEFINER),
-- por isso os papeis r_secretaria e r_professor NAO precisam de
-- permissao na tabela AUDITORIA, e nem podem le-la ou apaga-la.
-- =====================================================================

USE escola_musica;
SET NAMES utf8mb4;  -- garante acentos corretos mesmo em terminal sem UTF-8

CREATE TABLE auditoria (
    id_auditoria    BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    tabela          VARCHAR(30)     NOT NULL,
    operacao        CHAR(6)         NOT NULL,
    chave           VARCHAR(40)     NOT NULL,  -- PK do registro alterado
    valores_antes   JSON            NULL,
    valores_depois  JSON            NULL,
    usuario_app     VARCHAR(30)     NULL,      -- login da aplicacao (se houver)
    usuario_banco   VARCHAR(100)    NOT NULL,  -- usuario do MySQL que executou
    data_hora       DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    CONSTRAINT pk_auditoria PRIMARY KEY (id_auditoria),
    CONSTRAINT ck_auditoria_operacao CHECK (operacao IN ('INSERT', 'UPDATE', 'DELETE')),
    INDEX idx_auditoria_tabela_chave (tabela, chave),
    INDEX idx_auditoria_data (data_hora)
) ENGINE = InnoDB;

DELIMITER $$

-- ---------------------------------------------------------------------
-- Gatilho 1: alteracao de MENSALIDADE
-- RN34: toda alteracao de mensalidade fica registrada com autor, data e
--       valores anterior e posterior.
-- So grava se algum campo relevante realmente mudou (evita registro
-- vazio quando um UPDATE regrava o mesmo valor).
-- ---------------------------------------------------------------------
DROP TRIGGER IF EXISTS trg_mensalidade_au $$
CREATE TRIGGER trg_mensalidade_au
AFTER UPDATE ON mensalidade
FOR EACH ROW
BEGIN
    IF NOT (OLD.valor           <=> NEW.valor)
    OR NOT (OLD.data_vencimento <=> NEW.data_vencimento)
    OR NOT (OLD.data_pagamento  <=> NEW.data_pagamento)
    OR NOT (OLD.forma_pagamento <=> NEW.forma_pagamento) THEN
        INSERT INTO auditoria
            (tabela, operacao, chave, valores_antes, valores_depois,
             usuario_app, usuario_banco)
        VALUES
            ('mensalidade', 'UPDATE', CAST(NEW.id_mensalidade AS CHAR),
             JSON_OBJECT('valor', OLD.valor,
                         'data_vencimento', OLD.data_vencimento,
                         'data_pagamento', OLD.data_pagamento,
                         'forma_pagamento', OLD.forma_pagamento),
             JSON_OBJECT('valor', NEW.valor,
                         'data_vencimento', NEW.data_vencimento,
                         'data_pagamento', NEW.data_pagamento,
                         'forma_pagamento', NEW.forma_pagamento),
             @usuario_app, USER());
    END IF;
END $$

-- ---------------------------------------------------------------------
-- Gatilho 2: mudanca de situacao da MATRICULA
-- RN35: toda mudanca de situacao de matricula fica registrada com autor,
--       data e situacao anterior e nova.
-- ---------------------------------------------------------------------
DROP TRIGGER IF EXISTS trg_matricula_au $$
CREATE TRIGGER trg_matricula_au
AFTER UPDATE ON matricula
FOR EACH ROW
BEGIN
    IF NOT (OLD.situacao <=> NEW.situacao)
    OR NOT (OLD.id_turma <=> NEW.id_turma) THEN
        INSERT INTO auditoria
            (tabela, operacao, chave, valores_antes, valores_depois,
             usuario_app, usuario_banco)
        VALUES
            ('matricula', 'UPDATE', CAST(NEW.id_matricula AS CHAR),
             JSON_OBJECT('situacao', OLD.situacao, 'id_turma', OLD.id_turma),
             JSON_OBJECT('situacao', NEW.situacao, 'id_turma', NEW.id_turma),
             @usuario_app, USER());
    END IF;
END $$

DELIMITER ;

-- Teste rapido (pode rodar no terminal para ver o gatilho funcionando):
--   SET @usuario_app = 'teste_terminal';
--   UPDATE mensalidade SET data_pagamento = CURDATE(), forma_pagamento = 'PIX'
--    WHERE id_mensalidade = (SELECT id FROM (SELECT MIN(id_mensalidade) id
--          FROM mensalidade WHERE data_pagamento IS NULL) x);
--   SELECT * FROM auditoria ORDER BY id_auditoria DESC LIMIT 5;
