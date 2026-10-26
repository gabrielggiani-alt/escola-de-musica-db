"""
Traduz os erros do MySQL em mensagens que o usuario entende (item B1:
"tratamento de erro visivel ao usuario ... e nao a excecao bruta do driver").

A traducao usa o NOME da restricao violada. Por isso, na Etapa 1, todas as
restricoes foram nomeadas (pk_, uq_, fk_, ck_): o nome e a ponte entre o
erro do banco e a regra de negocio.
"""

import re

import pymysql

# nome da restricao -> mensagem (com a regra de negocio entre parenteses)
MENSAGENS = {
    "uq_pessoa_cpf": "Ja existe uma pessoa cadastrada com este CPF (RN01).",
    "ck_pessoa_cpf": "O CPF deve ter exatamente 11 digitos, so numeros (RN01).",
    "uq_pessoa_email": "Este e-mail ja pertence a outra pessoa (RN02).",
    "ck_pessoa_nascimento": "Data de nascimento invalida: anterior a 1920 (RN03).",
    "ck_pessoa_uf": "UF deve ter 2 letras maiusculas, ex.: DF.",
    "ck_pessoa_cep": "CEP deve ter 8 digitos, so numeros.",
    "uq_instrumento_nome": "Ja existe um instrumento com este nome (RN06).",
    "ck_instrumento_familia": "Familia invalida (RN06).",
    "uq_sala_nome": "Ja existe uma sala com este nome.",
    "ck_sala_capacidade": "A capacidade da sala deve ficar entre 1 e 30 (RN10).",
    "uq_turma_codigo": "Ja existe uma turma com este codigo.",
    "ck_turma_dia": "A escola funciona de segunda a sabado (RN11).",
    "ck_turma_horario": "O inicio da aula deve ser entre 08h e 21h (RN11).",
    "ck_turma_periodo": "A data de termino deve ser posterior a de inicio (RN12).",
    "ck_turma_vagas": "A turma deve ter de 1 a 20 vagas (RN13).",
    "uq_matricula_aluno_turma": "Este aluno ja esta matriculado nesta turma (RN14).",
    "ck_mensalidade_valor": "O valor da mensalidade deve ser maior que zero (RN24). "
                            "Nada foi gravado: a matricula foi desfeita (ROLLBACK).",
    "uq_mensalidade_matricula_competencia": "Ja existe mensalidade desta matricula neste mes (RN23).",
}

# exclusao bloqueada por chave estrangeira: tabela filha -> explicacao
EM_USO = {
    "matricula": "o aluno ou a turma tem matriculas (historico e preservado, RN16)",
    "nivel": "existem niveis ligados a este instrumento",
    "habilitacao": "existem professores habilitados neste instrumento",
    "turma": "existem turmas usando este registro",
    "aula": "a turma ja tem aulas lancadas",
    "mensalidade": "existem mensalidades ligadas",
    "historico_situacao": "existe historico ligado",
}


class ErroNegocio(Exception):
    """Regra verificada pela aplicacao (ex.: turma lotada)."""


def traduzir(erro):
    if isinstance(erro, ErroNegocio):
        return str(erro)
    if not isinstance(erro, pymysql.MySQLError) or not erro.args:
        return "Erro inesperado. Tente novamente ou fale com o administrador."
    codigo, texto = erro.args[0], str(erro.args[1]) if len(erro.args) > 1 else ""

    nome = re.search(r"(?:constraint|key) '(?:[\w]+\.)?([\w]+)'", texto)
    if nome and nome.group(1) in MENSAGENS:
        return MENSAGENS[nome.group(1)]
    if codigo == 1062:
        return "Registro duplicado: este valor ja esta cadastrado."
    if codigo == 3819:
        return "Valor fora do permitido pelas regras da escola."
    if codigo in (1451, 1217):  # 1217: mesma falha, sem detalhar a tabela filha
        filha = re.search(r"`\w+`\.`(\w+)`", texto)
        motivo = EM_USO.get(filha.group(1) if filha else "", "ha outros registros que dependem deste")
        return f"Nao e possivel excluir: {motivo}."
    if codigo == 1452:
        return "Referencia invalida: o registro relacionado nao existe."
    if codigo in (1142, 1143, 1227):
        return "Seu perfil nao tem permissao para esta operacao (o banco recusou)."
    if codigo == 1205:
        return "Outra operacao esta usando este registro. Tente de novo em instantes."
    if codigo == 1406:
        return "Texto maior que o permitido para o campo."
    if codigo in (1048, 1364):
        return "Preencha todos os campos obrigatorios."
    if codigo in (1292, 1366):
        return "Valor em formato invalido (data, numero ou texto)."
    return "O banco recusou a operacao. Confira os dados informados."
