"""
Gera os documentos da Etapa 1 em HTML e converte para PDF com o Microsoft Edge:
  docs/relatorio-etapa1.pdf   (A1 a A5 + implementacao + uso de IA)
  docs/modelo-logico.pdf      (A4)
  docs/dicionario-dados.pdf   (A3)

O conteudo fica aqui em estruturas Python para que o dicionario, o modelo
logico e o relatorio usem a MESMA fonte e nao divirjam entre si.

Uso:  python ferramentas/gerar_docs.py
"""

import subprocess
from html import escape
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DOCS = RAIZ / "docs"
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

# ============================================================== A1 - REGRAS
# (codigo, regra, forma de atendimento, onde)
REGRAS = [
    ("RN01", "O CPF de uma pessoa é único no cadastro e tem exatamente 11 dígitos numéricos.", "Restrição", "uq_pessoa_cpf, ck_pessoa_cpf"),
    ("RN02", "O e-mail é opcional, mas quando informado não pode se repetir entre pessoas.", "Restrição", "uq_pessoa_email"),
    ("RN03", "A data de nascimento não é anterior a 01/01/1920 nem posterior à data do cadastro.", "Restrição + aplicação", "ck_pessoa_nascimento (limite inferior); o limite “não futura” fica na aplicação"),
    ("RN04", "Todo aluno menor de 18 anos tem um responsável registrado.", "Consulta", "C15 (auditoria) e C01"),
    ("RN05", "O valor da hora-aula de um professor é maior que zero.", "Restrição", "ck_professor_valor_hora"),
    ("RN06", "O nome de um instrumento é único, e sua família é CORDAS, SOPRO, PERCUSSAO, TECLAS ou VOZ.", "Restrição", "uq_instrumento_nome, ck_instrumento_familia"),
    ("RN07", "A proficiência de um professor em um instrumento é INTERMEDIARIO, AVANCADO ou ESPECIALISTA.", "Restrição", "ck_habilitacao_proficiencia"),
    ("RN08", "Dentro de um instrumento, cada posição (1 a 10) na sequência de níveis é ocupada por um único nível.", "Restrição", "uq_nivel_instrumento_ordem, ck_nivel_ordem"),
    ("RN09", "Um nível pode exigir no máximo um nível como pré-requisito; um nível que é pré-requisito de outro não pode ser excluído.", "Restrição", "fk_nivel_prerequisito (ON DELETE RESTRICT)"),
    ("RN10", "A capacidade de uma sala fica entre 1 e 30 pessoas.", "Restrição", "ck_sala_capacidade"),
    ("RN11", "A escola funciona de segunda a sábado, e as aulas começam entre 08h e 21h.", "Restrição", "ck_turma_dia, ck_turma_horario"),
    ("RN12", "A data de término de uma turma é posterior à data de início.", "Restrição", "ck_turma_periodo"),
    ("RN13", "Uma turma oferece de 1 a 20 vagas, sem ultrapassar a capacidade da sala onde acontece.", "Restrição + aplicação", "ck_turma_vagas; a comparação com a sala fica na aplicação"),
    ("RN14", "Um aluno não pode ter duas matrículas na mesma turma.", "Restrição", "uq_matricula_aluno_turma"),
    ("RN15", "A situação de uma matrícula é ATIVA, CONCLUIDA, TRANCADA ou CANCELADA.", "Restrição", "ck_matricula_situacao, ck_historico_situacao"),
    ("RN16", "Um aluno que possui matrícula não pode ser excluído do cadastro.", "Restrição", "fk_matricula_aluno (ON DELETE RESTRICT)"),
    ("RN17", "Toda mudança de situação de uma matrícula fica registrada com data e hora, e duas mudanças da mesma matrícula não ocorrem no mesmo instante.", "Restrição + aplicação", "tabela historico_situacao, uq_historico_matricula_data; o registro é feito pela aplicação (na Etapa 2, por gatilho)"),
    ("RN18", "Dentro de uma turma, o número e a data de cada aula não se repetem.", "Restrição", "uq_aula_turma_numero, uq_aula_turma_data"),
    ("RN19", "A presença de um aluno é registrada uma única vez por aula.", "Restrição", "pk_frequencia"),
    ("RN20", "Só existe justificativa para falta; presença não tem justificativa.", "Restrição", "ck_frequencia_justificativa"),
    ("RN21", "Uma avaliação é do tipo PRATICA, TEORICA ou RECITAL.", "Restrição", "ck_avaliacao_tipo"),
    ("RN22", "A nota de uma avaliação vai de 0 a 10.", "Restrição", "ck_avaliacao_nota"),
    ("RN23", "Existe no máximo uma mensalidade por matrícula em cada mês de competência, e a competência é sempre o dia 1 do mês.", "Restrição", "uq_mensalidade_matricula_competencia, ck_mensalidade_competencia"),
    ("RN24", "O valor da mensalidade é positivo, e o vencimento cai no mês de competência ou depois.", "Restrição", "ck_mensalidade_valor, ck_mensalidade_vencimento"),
    ("RN25", "Mensalidade paga tem data e forma de pagamento (PIX, CARTAO, BOLETO ou DINHEIRO); mensalidade em aberto não tem nenhuma das duas.", "Restrição", "ck_mensalidade_pagamento"),
    ("RN26", "Toda pessoa cadastrada é aluno, professor ou ambos.", "Consulta", "C15 (auditoria)"),
    ("RN27", "O professor de uma turma é habilitado no instrumento do nível daquela turma.", "Consulta", "C15 (auditoria)"),
    ("RN28", "Um aluno só se matricula em um nível com pré-requisito se tiver matrícula CONCLUIDA no nível pré-requisito.", "Consulta", "C15 (auditoria)"),
    ("RN29", "O aluno é aprovado no nível quando tem média das avaliações maior ou igual a 6,0 e frequência maior ou igual a 75%.", "Consulta", "C11"),
    ("RN30", "A frequência de uma matrícula só é lançada em aulas da turma daquela matrícula.", "Consulta + aplicação", "C15 (auditoria); a tela de chamada lista apenas os alunos da turma"),
]

# ============================================ A3 - DICIONARIO (conceitual)
# entidade: (descricao, [(atributo, descricao, dominio, obrigatorio, observacao)])
DIC = {
    "PESSOA": ("Qualquer pessoa cadastrada na escola. Superclasse da especialização total e sobreposta em ALUNO e PROFESSOR.", [
        ("id_pessoa", "Identificador interno da pessoa", "Inteiro sequencial", "Sim", "Chave primária substituta"),
        ("cpf", "Cadastro de pessoa física", "11 dígitos numéricos", "Sim", "RN01 — não pode repetir"),
        ("nome", "Nome completo", "Texto de até 100 caracteres", "Sim", ""),
        ("data_nascimento", "Data de nascimento", "Data a partir de 01/01/1920", "Sim", "RN03"),
        ("/idade", "Idade em anos completos", "Inteiro, calculado", "—", "Derivado de data_nascimento; não armazenado"),
        ("email", "E-mail de contato", "Texto de até 120 caracteres", "Não", "RN02 — único quando informado"),
        ("endereco", "Endereço residencial (composto)", "logradouro (120), numero (10), bairro (60), cidade (60), uf (2 letras), cep (8 dígitos)", "Não", "Atributo composto; aceita ausência"),
        ("{telefone}", "Telefones de contato (multivalorado)", "número com DDD (10 ou 11 dígitos) + tipo CELULAR, FIXO ou RECADO", "Não", "Uma pessoa pode ter vários"),
        ("data_cadastro", "Data em que a pessoa entrou no cadastro", "Data", "Sim", "Padrão: data atual"),
    ]),
    "ALUNO": ("Pessoa que estuda na escola (subclasse de PESSOA).", [
        ("data_ingresso", "Data da primeira matrícula ou inscrição", "Data", "Sim", ""),
        ("nome_responsavel", "Responsável legal pelo aluno", "Texto de até 100 caracteres", "Não", "RN04 — obrigatório para menor de 18 anos"),
    ]),
    "PROFESSOR": ("Pessoa que leciona na escola (subclasse de PESSOA).", [
        ("data_admissao", "Data de admissão na escola", "Data", "Sim", ""),
        ("valor_hora", "Valor pago por hora-aula", "Decimal em reais, até 99.999,99", "Sim", "RN05 — maior que zero"),
        ("formacao", "Formação acadêmica ou técnica", "Texto de até 100 caracteres", "Não", ""),
    ]),
    "INSTRUMENTO": ("Instrumento musical (ou voz) ensinado pela escola.", [
        ("id_instrumento", "Identificador interno do instrumento", "Inteiro sequencial", "Sim", "Chave primária substituta"),
        ("nome", "Nome do instrumento", "Texto de até 40 caracteres", "Sim", "RN06 — único"),
        ("familia", "Família do instrumento", "CORDAS, SOPRO, PERCUSSAO, TECLAS ou VOZ", "Sim", "RN06"),
    ]),
    "HABILITACAO": ("Associativa: habilitação de um professor em um instrumento (N:N PROFESSOR × INSTRUMENTO).", [
        ("nivel_proficiencia", "Grau de domínio do professor no instrumento", "INTERMEDIARIO, AVANCADO ou ESPECIALISTA", "Sim", "RN07"),
        ("data_certificacao", "Data em que obteve a certificação", "Data", "Sim", ""),
    ]),
    "NIVEL": ("Etapa do curso de um instrumento. Possui autorrelacionamento de pré-requisito.", [
        ("id_nivel", "Identificador interno do nível", "Inteiro sequencial", "Sim", "Chave primária substituta"),
        ("nome", "Nome do nível", "Texto de até 40 caracteres", "Sim", "Ex.: Violão Básico II"),
        ("ordem", "Posição do nível na sequência do instrumento", "Inteiro de 1 a 10", "Sim", "RN08 — única por instrumento"),
        ("carga_horaria", "Carga horária total do nível", "Inteiro de 8 a 200 horas", "Sim", ""),
        ("(pré-requisito)", "Nível que precisa ser concluído antes", "Referência a outro NIVEL", "Não", "RN09, RN28 — autorrelacionamento (0,1)"),
    ]),
    "SALA": ("Espaço físico onde as turmas acontecem.", [
        ("id_sala", "Identificador interno da sala", "Inteiro sequencial", "Sim", "Chave primária substituta"),
        ("nome", "Nome da sala", "Texto de até 30 caracteres", "Sim", "Único"),
        ("capacidade", "Número máximo de pessoas", "Inteiro de 1 a 30", "Sim", "RN10"),
        ("possui_piano", "Indica se a sala tem piano", "Verdadeiro ou falso", "Sim", "Padrão: falso"),
    ]),
    "TURMA": ("Oferta de um nível em um semestre, com professor, sala e horário fixos.", [
        ("id_turma", "Identificador interno da turma", "Inteiro sequencial", "Sim", "Chave primária substituta"),
        ("codigo", "Código legível da turma", "Texto de até 12 caracteres, ex.: VIO-B2-26B", "Sim", "Único"),
        ("dia_semana", "Dia da semana da aula", "Inteiro de 2 (segunda) a 7 (sábado)", "Sim", "RN11"),
        ("horario_inicio", "Horário de início da aula", "Hora entre 08:00 e 21:00", "Sim", "RN11"),
        ("data_inicio", "Primeiro dia de aula", "Data", "Sim", ""),
        ("data_fim", "Último dia do período letivo", "Data posterior a data_inicio", "Sim", "RN12"),
        ("vagas", "Número de vagas oferecidas", "Inteiro de 1 a 20", "Sim", "RN13"),
        ("/qtd_matriculados", "Alunos ativos na turma", "Inteiro, calculado", "—", "Derivado; calculado na consulta C08"),
    ]),
    "MATRICULA": ("Associativa: vínculo de um aluno com uma turma (N:N ALUNO × TURMA). Dona das avaliações, frequências e mensalidades.", [
        ("id_matricula", "Identificador interno da matrícula", "Inteiro sequencial", "Sim", "Chave primária substituta"),
        ("data_matricula", "Data em que a matrícula foi feita", "Data", "Sim", ""),
        ("situacao", "Situação atual da matrícula", "ATIVA, CONCLUIDA, TRANCADA ou CANCELADA", "Sim", "RN15 — padrão ATIVA"),
        ("/media_final", "Média das avaliações", "Decimal de 0 a 10, calculado", "—", "Derivado; consulta C11 (RN29)"),
        ("/percentual_frequencia", "Percentual de presença nas aulas realizadas", "0 a 100%, calculado", "—", "Derivado; consulta C11 (RN29)"),
    ]),
    "HISTORICO_SITUACAO": ("Registro datado de cada situação por que a matrícula passou (atributo temporal).", [
        ("id_historico", "Identificador interno do registro", "Inteiro sequencial", "Sim", "Chave primária substituta"),
        ("situacao", "Situação assumida naquele momento", "ATIVA, CONCLUIDA, TRANCADA ou CANCELADA", "Sim", "RN15"),
        ("data_alteracao", "Data e hora da mudança", "Data e hora", "Sim", "RN17 — única por matrícula"),
        ("motivo", "Motivo da mudança", "Texto de até 200 caracteres", "Não", ""),
    ]),
    "AULA": ("Encontro de uma turma em uma data.", [
        ("id_aula", "Identificador interno da aula", "Inteiro sequencial", "Sim", "Chave primária substituta"),
        ("numero_aula", "Número sequencial da aula na turma", "Inteiro de 1 a 255", "Sim", "RN18 — único na turma"),
        ("data_aula", "Data em que a aula ocorreu", "Data", "Sim", "RN18 — única na turma"),
        ("conteudo", "Conteúdo trabalhado", "Texto de até 200 caracteres", "Não", ""),
        ("status", "Se a aula aconteceu", "REALIZADA ou CANCELADA", "Sim", "Padrão: REALIZADA"),
    ]),
    "FREQUENCIA": ("Associativa: presença de uma matrícula em uma aula (N:N MATRICULA × AULA). Tabela de maior movimento.", [
        ("presente", "Se o aluno esteve na aula", "Verdadeiro ou falso", "Sim", "RN19"),
        ("justificativa", "Justificativa da falta", "Texto de até 200 caracteres", "Não", "RN20 — só em falta"),
    ]),
    "AVALIACAO": ("Entidade fraca: avaliação de desempenho, que só existe dentro de uma matrícula.", [
        ("numero_avaliacao", "Número da avaliação dentro da matrícula (discriminador)", "Inteiro de 1 a 10", "Sim", "Identifica junto com a matrícula"),
        ("tipo", "Tipo de avaliação", "PRATICA, TEORICA ou RECITAL", "Sim", "RN21"),
        ("data_avaliacao", "Data da avaliação", "Data", "Sim", ""),
        ("nota", "Nota obtida", "Decimal de 0,00 a 10,00", "Sim", "RN22"),
    ]),
    "MENSALIDADE": ("Cobrança mensal referente a uma matrícula.", [
        ("id_mensalidade", "Identificador interno da mensalidade", "Inteiro sequencial", "Sim", "Chave primária substituta"),
        ("competencia", "Mês de referência", "Data, sempre dia 1", "Sim", "RN23 — única por matrícula"),
        ("valor", "Valor cobrado", "Decimal em reais, maior que zero", "Sim", "RN24"),
        ("data_vencimento", "Data de vencimento", "Data igual ou posterior à competência", "Sim", "RN24"),
        ("data_pagamento", "Data em que foi paga", "Data", "Não", "RN25 — ausente = em aberto"),
        ("forma_pagamento", "Meio de pagamento", "PIX, CARTAO, BOLETO ou DINHEIRO", "Não", "RN25 — obrigatória se paga"),
    ]),
}

# ================================================ A4 - MODELO LOGICO
# (tabela, [(coluna, pk, fk_destino)])
LOGICO = [
    ("pessoa", [("id_pessoa", 1, None), ("nome", 0, None), ("cpf", 0, None), ("data_nascimento", 0, None), ("email", 0, None), ("logradouro", 0, None), ("numero", 0, None), ("bairro", 0, None), ("cidade", 0, None), ("uf", 0, None), ("cep", 0, None), ("data_cadastro", 0, None)]),
    ("telefone", [("id_pessoa", 1, "pessoa"), ("numero", 1, None), ("tipo", 0, None)]),
    ("aluno", [("id_pessoa", 1, "pessoa"), ("data_ingresso", 0, None), ("nome_responsavel", 0, None)]),
    ("professor", [("id_pessoa", 1, "pessoa"), ("data_admissao", 0, None), ("valor_hora", 0, None), ("formacao", 0, None)]),
    ("instrumento", [("id_instrumento", 1, None), ("nome", 0, None), ("familia", 0, None)]),
    ("habilitacao", [("id_professor", 1, "professor"), ("id_instrumento", 1, "instrumento"), ("nivel_proficiencia", 0, None), ("data_certificacao", 0, None)]),
    ("nivel", [("id_nivel", 1, None), ("id_instrumento", 0, "instrumento"), ("nome", 0, None), ("ordem", 0, None), ("carga_horaria", 0, None), ("id_nivel_prerequisito", 0, "nivel")]),
    ("sala", [("id_sala", 1, None), ("nome", 0, None), ("capacidade", 0, None), ("possui_piano", 0, None)]),
    ("turma", [("id_turma", 1, None), ("codigo", 0, None), ("id_nivel", 0, "nivel"), ("id_professor", 0, "professor"), ("id_sala", 0, "sala"), ("dia_semana", 0, None), ("horario_inicio", 0, None), ("data_inicio", 0, None), ("data_fim", 0, None), ("vagas", 0, None)]),
    ("matricula", [("id_matricula", 1, None), ("id_aluno", 0, "aluno"), ("id_turma", 0, "turma"), ("data_matricula", 0, None), ("situacao", 0, None)]),
    ("historico_situacao", [("id_historico", 1, None), ("id_matricula", 0, "matricula"), ("situacao", 0, None), ("data_alteracao", 0, None), ("motivo", 0, None)]),
    ("aula", [("id_aula", 1, None), ("id_turma", 0, "turma"), ("numero_aula", 0, None), ("data_aula", 0, None), ("conteudo", 0, None), ("status", 0, None)]),
    ("frequencia", [("id_matricula", 1, "matricula"), ("id_aula", 1, "aula"), ("presente", 0, None), ("justificativa", 0, None)]),
    ("avaliacao", [("id_matricula", 1, "matricula"), ("numero_avaliacao", 1, None), ("tipo", 0, None), ("data_avaliacao", 0, None), ("nota", 0, None)]),
    ("mensalidade", [("id_mensalidade", 1, None), ("id_matricula", 0, "matricula"), ("competencia", 0, None), ("valor", 0, None), ("data_vencimento", 0, None), ("data_pagamento", 0, None), ("forma_pagamento", 0, None)]),
]

# (tabela, tipo de chave, justificativa)
CHAVES = [
    ("pessoa", "Substituta (id_pessoa); CPF fica como chave alternativa (UNIQUE)", "O CPF é natural, mas é dado pessoal: espalhá-lo como FK em aluno, professor, telefone e matrícula multiplicaria a exposição. Uma correção de CPF digitado errado também exigiria atualizar todas as tabelas filhas."),
    ("telefone", "Natural composta (id_pessoa, numero)", "Ninguém referencia telefone; o próprio número dentro da pessoa já identifica a linha. Criar id seria coluna sem uso."),
    ("aluno / professor", "Herdada da superclasse (id_pessoa)", "Na especialização, a subclasse usa a mesma chave da superclasse, que é ao mesmo tempo PK e FK. Garante o 1:1 com pessoa."),
    ("instrumento, sala", "Substituta; nome como chave alternativa", "O nome poderia ser PK, mas pode ser renomeado (ex.: “Sala 3” vira “Sala Tom Jobim”), e PK não deve mudar."),
    ("habilitacao", "Natural composta (id_professor, id_instrumento)", "A combinação é exatamente o que a tabela registra e não pode se repetir; ninguém a referencia."),
    ("nivel", "Substituta; (id_instrumento, ordem) como chave alternativa", "É referenciado por turma e pelo próprio autorrelacionamento; uma chave simples deixa essas FKs curtas."),
    ("turma", "Substituta; codigo como chave alternativa", "O código é legível para a secretaria, mas segue convenção que pode mudar."),
    ("matricula", "Substituta (id_matricula); (id_aluno, id_turma) como chave alternativa", "É referenciada por quatro tabelas (histórico, frequência, avaliação, mensalidade). Carregar a chave composta em todas elas deixaria cada filha maior e as junções mais verbosas."),
    ("historico_situacao, mensalidade", "Substituta; (id_matricula, data_alteracao) e (id_matricula, competencia) como chaves alternativas", "Mantém uma chave simples e estável para a aplicação da Etapa 2 atualizar e auditar a linha."),
    ("aula", "Substituta; (id_turma, numero_aula) e (id_turma, data_aula) como chaves alternativas", "É referenciada pela frequência, a tabela de maior volume; uma FK de uma coluna só economiza espaço em cada uma das centenas de linhas."),
    ("frequencia", "Natural composta (id_matricula, id_aula)", "É a tabela associativa pura: o par é o fato registrado e impede presença duplicada (RN19)."),
    ("avaliacao", "Composta com a chave da dona (id_matricula, numero_avaliacao)", "Entidade fraca: a identificação depende da matrícula; numero_avaliacao sozinho não identifica nada."),
]

DECISOES = [
    ("Especialização PESSOA → ALUNO / PROFESSOR (total, sobreposta)",
     "Mapeada em <b>três tabelas</b>: uma para a superclasse (pessoa) e uma para cada subclasse (aluno, professor), com a chave da superclasse repetida como PK e FK. "
     "Por que não <b>tabela única</b>: a especialização é sobreposta (a pessoa 6 é professora e também aluna de piano); uma tabela só teria colunas de aluno e de professor quase sempre nulas e não permitiria que matrícula apontasse “só para alunos” nem que turma apontasse “só para professores”. "
     "Por que não <b>uma tabela por subclasse sem superclasse</b>: quem é as duas coisas teria nome, CPF e endereço gravados duas vezes, e o CPF único deixaria de ser garantido pelo banco. "
     "Com três tabelas, fk_matricula_aluno e fk_turma_professor garantem que só aluno se matricula e só professor leciona. "
     "Limitação assumida: a totalidade (toda pessoa ter pelo menos um papel) não é garantida pelo DDL; é verificada pela consulta C15 (RN26)."),
    ("Relacionamentos 1:1",
     "Os únicos 1:1 do modelo são pessoa–aluno e pessoa–professor, que vêm da especialização. Eles foram <b>mantidos separados</b> pelos motivos acima. "
     "Não há outro 1:1 no domínio: um professor tem várias turmas, uma matrícula tem várias mensalidades, e assim por diante."),
    ("Relacionamentos N:N",
     "Os três N:N viraram tabelas associativas, cada uma com as FKs para os dois lados e os atributos próprios da associação: "
     "<b>habilitacao</b> (professor × instrumento, com proficiência e data), "
     "<b>matricula</b> (aluno × turma, com data e situação) e "
     "<b>frequencia</b> (matrícula × aula, com presença e justificativa)."),
    ("Autorrelacionamento",
     "O pré-requisito entre níveis (0,1 para 0,N) virou a coluna <b>id_nivel_prerequisito</b> em nivel, anulável e com FK para a própria tabela. "
     "Não foi preciso tabela à parte, porque cada nível tem no máximo um pré-requisito."),
    ("Entidade fraca",
     "AVALIACAO recebeu a PK <b>(id_matricula, numero_avaliacao)</b>, que inclui a chave da entidade dona, com ON DELETE CASCADE: se a matrícula deixa de existir, suas avaliações também deixam."),
    ("Atributos compostos, multivalorados e derivados",
     "O endereço composto foi <b>achatado</b> em colunas (logradouro, número, bairro, cidade, UF, CEP), porque cada parte é consultada isoladamente (a consulta C02 filtra por bairro). "
     "O telefone multivalorado virou a tabela <b>telefone</b>. "
     "Os derivados (idade, média, percentual de frequência, quantidade de matriculados) <b>não são armazenados</b>: são calculados nas consultas, para nunca ficarem desatualizados."),
    ("Atributo temporal",
     "A situação da matrícula ao longo do tempo fica em <b>historico_situacao</b>, uma linha por mudança com data e hora. "
     "A coluna matricula.situacao guarda só a situação atual, para leitura rápida; ver a seção A5 sobre essa redundância."),
    ("Ações referenciais (ON DELETE / ON UPDATE)",
     "<b>ON UPDATE RESTRICT</b> em todas as FKs: as chaves são substitutas e nunca mudam. "
     "<b>ON DELETE RESTRICT</b> como padrão, para preservar o histórico acadêmico e financeiro (RN16): não se apaga aluno com matrícula, nem turma com aulas, nem nível que é pré-requisito. "
     "<b>ON DELETE CASCADE</b> só onde o filho não existe sem o pai: aluno e professor (subclasses), telefone (atributo multivalorado) e avaliação (entidade fraca)."),
]

# ================================================== A5 - NORMALIZACAO
# (tabela, [dependencias funcionais], forma normal, comentario)
NORMAL = [
    ("pessoa", ["id_pessoa → nome, cpf, data_nascimento, email, logradouro, numero, bairro, cidade, uf, cep, data_cadastro",
                "cpf → id_pessoa (chave candidata)", "email → id_pessoa (chave candidata, quando não nula)",
                "cep → logradouro, bairro, cidade, uf (dependência do mundo real, ver abaixo)"],
     "3FN com desnormalização deliberada", "Ver a justificativa sobre o CEP logo abaixo da tabela."),
    ("telefone", ["(id_pessoa, numero) → tipo"], "FNBC", "Único determinante é a chave."),
    ("aluno", ["id_pessoa → data_ingresso, nome_responsavel"], "FNBC", "Único determinante é a chave."),
    ("professor", ["id_pessoa → data_admissao, valor_hora, formacao"], "FNBC", "Único determinante é a chave."),
    ("instrumento", ["id_instrumento → nome, familia", "nome → id_instrumento"], "FNBC", "Os dois determinantes são chaves candidatas."),
    ("habilitacao", ["(id_professor, id_instrumento) → nivel_proficiencia, data_certificacao"], "FNBC", "A proficiência depende do par, não de um lado só; por isso não viola a 2FN."),
    ("nivel", ["id_nivel → id_instrumento, nome, ordem, carga_horaria, id_nivel_prerequisito", "(id_instrumento, ordem) → id_nivel"], "FNBC", "Os dois determinantes são chaves candidatas."),
    ("sala", ["id_sala → nome, capacidade, possui_piano", "nome → id_sala"], "FNBC", "Os dois determinantes são chaves candidatas."),
    ("turma", ["id_turma → codigo, id_nivel, id_professor, id_sala, dia_semana, horario_inicio, data_inicio, data_fim, vagas", "codigo → id_turma"],
     "FNBC", "O instrumento da turma não foi guardado aqui: ele é obtido por turma → nivel → instrumento. Guardá-lo criaria a dependência transitiva id_turma → id_nivel → id_instrumento."),
    ("matricula", ["id_matricula → id_aluno, id_turma, data_matricula, situacao", "(id_aluno, id_turma) → id_matricula"], "FNBC", "Os dois determinantes são chaves candidatas."),
    ("historico_situacao", ["id_historico → id_matricula, situacao, data_alteracao, motivo", "(id_matricula, data_alteracao) → id_historico"], "FNBC", "Os dois determinantes são chaves candidatas."),
    ("aula", ["id_aula → id_turma, numero_aula, data_aula, conteudo, status", "(id_turma, numero_aula) → id_aula", "(id_turma, data_aula) → id_aula"], "FNBC", "Os três determinantes são chaves candidatas."),
    ("frequencia", ["(id_matricula, id_aula) → presente, justificativa"], "FNBC", "Presença depende do par inteiro (aluno naquela aula)."),
    ("avaliacao", ["(id_matricula, numero_avaliacao) → tipo, data_avaliacao, nota"], "FNBC", "Entidade fraca; a chave é a da dona mais o discriminador."),
    ("mensalidade", ["id_mensalidade → id_matricula, competencia, valor, data_vencimento, data_pagamento, forma_pagamento", "(id_matricula, competencia) → id_mensalidade"],
     "FNBC", "O valor não é função do nível: é o preço combinado naquele mês, que pode ter desconto ou reajuste. Por isso não há dependência nivel → valor, e o valor fica na própria mensalidade."),
]


# ================================================================ HTML
CSS = """
@page { size: A4; margin: 20mm 18mm 20mm 18mm;
        @bottom-center { content: "Página " counter(page) " de " counter(pages); font: 9pt Arial; color:#555; } }
body { font-family: Arial, Helvetica, sans-serif; font-size: 10.5pt; line-height: 1.45; color: #111; }
h1 { font-size: 20pt; margin: 0 0 6px; } h2 { font-size: 14pt; border-bottom: 2px solid #333; padding-bottom: 3px; margin-top: 26px; page-break-after: avoid; }
h3 { font-size: 11.5pt; margin: 16px 0 6px; page-break-after: avoid; }
table { border-collapse: collapse; width: 100%; margin: 6px 0 12px; font-size: 9pt; page-break-inside: auto; }
tr { page-break-inside: avoid; } th, td { border: 1px solid #999; padding: 3px 5px; vertical-align: top; text-align: left; }
th { background: #e8e8e8; } code { font-family: Consolas, monospace; font-size: 9pt; }
.capa { text-align: center; padding-top: 180px; page-break-after: always; } .capa p { margin: 4px; }
.rel { font-family: Consolas, monospace; font-size: 9.5pt; margin: 3px 0; } .pk { text-decoration: underline; font-weight: bold; }
.fk { font-style: italic; } .quebra { page-break-before: always; } .nota { background:#f6f6f6; border-left:3px solid #888; padding:6px 10px; }
img.mer { width: 100%; border: 1px solid #ccc; }
"""


def pagina(titulo, corpo):
    return (f"<!doctype html><html lang='pt-br'><head><meta charset='utf-8'><title>{escape(titulo)}</title>"
            f"<style>{CSS}</style></head><body>{corpo}</body></html>")


def tabela(cab, linhas):
    h = "".join(f"<th>{c}</th>" for c in cab)
    b = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in l) + "</tr>" for l in linhas)
    return f"<table><thead><tr>{h}</tr></thead><tbody>{b}</tbody></table>"


def html_dicionario():
    out = []
    for ent, (desc, attrs) in DIC.items():
        out.append(f"<h3>{ent}</h3><p>{escape(desc)}</p>")
        out.append(tabela(["Atributo", "Descrição", "Domínio", "Obrig.", "Observação"],
                          [[f"<code>{escape(a)}</code>", escape(d), escape(dm), o, escape(ob)] for a, d, dm, o, ob in attrs]))
    return "".join(out)


def html_logico():
    out = ["<p>Notação: <span class='pk'>sublinhado</span> = chave primária; <span class='fk'>itálico</span> seguido de → = chave estrangeira e tabela referenciada.</p>"]
    for t, cols in LOGICO:
        partes = []
        for c, pk, fk in cols:
            s = escape(c)
            if fk:
                s = f"<span class='fk'>{s}</span>→{fk}"
            if pk:
                s = f"<span class='pk'>{s}</span>"
            partes.append(s)
        out.append(f"<p class='rel'><b>{t.upper()}</b> ( {', '.join(partes)} )</p>")
    out.append("<h3>Onde está cada N:N</h3>")
    out.append(tabela(["Relacionamento N:N no MER", "Tabela associativa", "Chaves estrangeiras", "Atributos próprios"], [
        ["PROFESSOR × INSTRUMENTO", "habilitacao", "id_professor → professor, id_instrumento → instrumento", "nivel_proficiencia, data_certificacao"],
        ["ALUNO × TURMA", "matricula", "id_aluno → aluno, id_turma → turma", "data_matricula, situacao"],
        ["MATRICULA × AULA", "frequencia", "id_matricula → matricula, id_aula → aula", "presente, justificativa"],
    ]))
    out.append("<h3>Decisões de mapeamento</h3>")
    for tit, txt in DECISOES:
        out.append(f"<p><b>{escape(tit)}.</b> {txt}</p>")
    out.append("<h3>Chave natural × chave substituta</h3>")
    out.append(tabela(["Relação", "Escolha", "Justificativa"], [[f"<code>{a}</code>", escape(b), escape(c)] for a, b, c in CHAVES]))
    return "".join(out)


def html_normalizacao():
    out = ["<p>Para cada relação estão listadas as dependências funcionais (DF) relevantes. Critério usado: "
           "<b>1FN</b> — todos os atributos são atômicos (o endereço composto foi decomposto e o telefone multivalorado virou tabela); "
           "<b>2FN</b> — nenhum atributo não-chave depende de <i>parte</i> de uma chave composta; "
           "<b>3FN</b> — nenhum atributo não-chave depende de outro atributo não-chave; "
           "<b>FNBC</b> — todo determinante é chave candidata.</p>"]
    linhas = []
    for t, dfs, fn, com in NORMAL:
        linhas.append([f"<code>{t}</code>", "<br>".join(escape(d) for d in dfs), f"<b>{fn}</b>", escape(com)])
    out.append(tabela(["Relação", "Dependências funcionais", "Forma normal", "Análise"], linhas))
    out.append("<h3>Verificação das chaves compostas (2FN)</h3><p>As relações com chave composta são telefone, habilitacao, frequencia e avaliacao. "
               "Em todas elas o atributo não-chave depende da chave <i>inteira</i>: o tipo do telefone depende de qual número de qual pessoa; a proficiência depende de qual professor em qual instrumento; "
               "a presença depende de qual aluno em qual aula; a nota depende de qual avaliação de qual matrícula. Nenhuma dependência parcial.</p>")
    out.append("<h3>Relações deliberadamente desnormalizadas</h3>")
    out.append("<p><b>1. pessoa — CEP.</b> No mundo real o CEP determina logradouro, bairro, cidade e UF, e isso cria uma dependência transitiva "
               "id_pessoa → cep → cidade. Normalizar exigiria uma tabela de logradouros dos Correios, com centenas de milhares de linhas, que a escola não tem e não mantém. "
               "Além disso o endereço é opcional e digitado pelo próprio aluno, e ler o endereço de uma pessoa passaria a exigir junção. "
               "<b>Decisão:</b> manter o endereço inteiro em pessoa. O custo aceito é a possibilidade de o mesmo CEP aparecer com cidades diferentes por erro de digitação. "
               "A Etapa 2 pode revisitar essa escolha se a aplicação passar a buscar o endereço pelo CEP.</p>")
    out.append("<p><b>2. matricula.situacao.</b> A situação atual também pode ser obtida do registro mais recente de historico_situacao, então é uma informação redundante (não viola a 3FN, "
               "já que depende só da chave, mas é duplicação controlada). Justificativa de desempenho: a situação atual é filtrada em quase toda consulta (C06, C08, C13), "
               "e descobrir “o último evento de cada matrícula” exige subconsulta a cada leitura. A consistência entre as duas é garantida pela aplicação e, na Etapa 2, por gatilho.</p>")
    out.append("<h3>Relações em FNBC</h3><p>Todas as relações exceto <code>pessoa</code> estão na <b>Forma Normal de Boyce-Codd</b>: em cada uma, "
               "todo determinante listado é chave candidata.</p>")
    return "".join(out)


REQUISITOS = [
    ("Entidades (mínimo 8, sem associativas)", "11: pessoa, aluno, professor, instrumento, nivel, sala, turma, aula, avaliacao, mensalidade, historico_situacao"),
    ("Relacionamentos N:N com atributo (mínimo 2)", "3: habilitacao, matricula, frequencia"),
    ("Autorrelacionamento (mínimo 1)", "nivel → nivel (pré-requisito)"),
    ("Generalização/especialização (mínimo 1)", "pessoa → aluno / professor, total e sobreposta, 3 tabelas (ver A4)"),
    ("Entidade fraca (mínimo 1)", "avaliacao, identificada por (id_matricula, numero_avaliacao)"),
    ("Atributo temporal (mínimo 1)", "historico_situacao (situação da matrícula ao longo do tempo); frequência aula a aula"),
    ("Regras de negócio (mínimo 20)", "30 regras, RN01 a RN30"),
    ("Volume de carga (40 nas principais, 100 na maior)", "pessoa 54, aluno 47, matricula 71, historico 110, avaliacao 127, aula 167, mensalidade 246, frequencia 901"),
]


def html_relatorio():
    mer = (DOCS / "mer-conceitual.png").as_uri()
    rn = tabela(["Código", "Regra", "Atendida por", "Onde"],
                [[f"<b>{c}</b>", escape(r), escape(f), f"<code>{escape(o)}</code>"] for c, r, f, o in REGRAS])
    return pagina("Relatório Etapa 1 — Escola de Música", f"""
<div class='capa'>
  <p>UNIVERSIDADE CATÓLICA DE BRASÍLIA</p><p>Laboratório de Banco de Dados — GPE17M40083</p>
  <p>Prof. Samuel Novais Moura Júnior</p><br><br>
  <h1>Projeto Final — Etapa 1</h1><p style='font-size:14pt'>Escola de Música: projeto e construção do banco de dados</p><br><br>
  <p><b>Integrantes:</b> ________________________________________</p>
  <p>SGBD: MySQL 8.4 &nbsp;·&nbsp; Notação do MER: Engenharia da Informação (pé de galinha)</p><br>
  <p>Brasília, setembro de 2026</p>
</div>

<h2>Sumário</h2>
<p>1. Requisitos mínimos de complexidade<br>2. A1 — Escopo e regras de negócio<br>3. A2 — Modelo Entidade-Relacionamento conceitual<br>
4. A3 — Dicionário de dados conceitual<br>5. A4 — Modelo lógico relacional<br>6. A5 — Verificação de normalização<br>
7. Implementação física, carga e consultas (A6 a A8)<br>8. Declaração de uso de inteligência artificial</p>

<h2>1. Requisitos mínimos de complexidade</h2>
{tabela(["Requisito do enunciado", "Como o modelo atende"], [[escape(a), escape(b)] for a, b in REQUISITOS])}

<h2 class='quebra'>2. A1 — Escopo e regras de negócio</h2>
<h3>Descrição do domínio</h3>
<p>O sistema atende uma escola de música de Brasília que oferece cursos de violão, piano, violino, bateria, canto e flauta transversal. Cada curso é dividido em <b>níveis</b> sequenciais (Básico I, Básico II, Intermediário). Um nível pode exigir que o aluno tenha concluído o nível anterior, e é esse encadeamento que organiza a trajetória do aluno na escola.</p>
<p>A escola cadastra <b>pessoas</b> com dados de identificação (CPF, nascimento), contato (e-mail e vários telefones) e endereço. Toda pessoa cadastrada é <b>aluno</b>, <b>professor</b> ou as duas coisas: é comum um professor da casa estudar outro instrumento. Do aluno interessa a data de ingresso e, se for menor de idade, o responsável. Do professor interessam a admissão, o valor da hora-aula, a formação e os instrumentos em que é <b>habilitado</b>, com o grau de proficiência e a data da certificação.</p>
<p>A cada semestre a escola abre <b>turmas</b>. Cada turma oferta um nível, tem um professor habilitado naquele instrumento, uma <b>sala</b> (com capacidade e, em algumas, piano), um dia da semana, um horário e um número de vagas. Os alunos se inscrevem por <b>matrícula</b>, que tem data e uma situação: ativa, concluída, trancada ou cancelada. Como a situação muda com o tempo (um aluno tranca por viagem e depois volta), cada mudança é guardada com data, hora e motivo no <b>histórico de situação</b>.</p>
<p>Cada encontro da turma é uma <b>aula</b>, numerada e datada, que pode ser realizada ou cancelada. Em cada aula realizada o professor registra a <b>frequência</b> de cada aluno, com justificativa quando há falta. Ao longo do nível o aluno faz <b>avaliações</b> teóricas, práticas e um recital, que só existem dentro da matrícula. É aprovado quem termina com média de pelo menos 6,0 e frequência de pelo menos 75%.</p>
<p>No financeiro, cada matrícula gera uma <b>mensalidade</b> por mês de competência, com valor e vencimento. Quando paga, registram-se a data e a forma de pagamento; enquanto não paga, fica em aberto, o que permite acompanhar a inadimplência.</p>
<p><b>Fora do escopo desta etapa:</b> folha de pagamento dos professores, venda de instrumentos, controle de acesso e login (Etapa 2).</p>
<h3>Regras de negócio</h3>
<p>“Atendida por” indica se a regra é garantida por <b>restrição</b> do banco (o SGBD rejeita o dado inválido), por <b>consulta</b> (a consulta indicada lista as violações e deve voltar vazia) ou pela <b>aplicação</b> (a verificação depende de algo que o CHECK do MySQL não aceita, como a data atual ou dados de outra tabela).</p>
{rn}

<h2 class='quebra'>3. A2 — Modelo Entidade-Relacionamento conceitual</h2>
<p>Notação de Engenharia da Informação (pé de galinha), mantida em todo o diagrama. O arquivo-fonte editável é <code>docs/mer-conceitual.drawio</code> (abre no draw.io), e a exportação em PDF está em <code>docs/mer-conceitual.pdf</code>.</p>
<img class='mer' src='{mer}' alt='MER conceitual'>
<h3>Leitura do diagrama</h3>
<p><b>Especialização:</b> PESSOA → ALUNO / PROFESSOR, <b>total</b> (não existe pessoa sem papel) e <b>sobreposta</b> (a mesma pessoa pode ser as duas). <b>Autorrelacionamento:</b> NIVEL “é pré-requisito de” NIVEL, (0,1) para (0,N). <b>Entidade fraca:</b> AVALIACAO, de borda dupla, ligada a MATRICULA pelo relacionamento identificador de linha grossa; seu discriminador é numero_avaliacao. <b>Associativas</b> (N:N com atributos, fundo cinza): HABILITACAO, MATRICULA e FREQUENCIA. <b>Atributo composto:</b> endereco; <b>multivalorado:</b> {{telefone}}; <b>derivados:</b> /idade, /media_final, /percentual_frequencia, /qtd_matriculados.</p>
<p><b>Cardinalidades principais:</b> um aluno realiza (0,N) matrículas, e cada matrícula é de exatamente (1,1) aluno. Uma turma recebe (0,N) matrículas. Um professor possui (1,N) habilitações, porque só é professor quem é habilitado em algo. Uma matrícula registra (1,N) mudanças de situação, porque ela nasce com o registro “ATIVA”. Uma turma tem (0,N) aulas, e cada aula registra (0,N) presenças.</p>

<h2 class='quebra'>4. A3 — Dicionário de dados conceitual</h2>
<p>Formato do Anexo A do enunciado. A coluna Observação traz a regra de negócio associada. Atributos marcados com “/” são derivados e não são armazenados.</p>
{html_dicionario()}

<h2 class='quebra'>5. A4 — Modelo lógico relacional</h2>
{html_logico()}

<h2 class='quebra'>6. A5 — Verificação de normalização</h2>
{html_normalizacao()}

<h2 class='quebra'>7. Implementação física, carga e consultas (A6 a A8)</h2>
<h3>A6 — 01_ddl.sql</h3>
<p>Cria o banco <code>escola_musica</code> (utf8mb4) e as 15 tabelas, na ordem de dependência. Todas as restrições são nomeadas com os prefixos <code>pk_ uq_ fk_ ck_ idx_</code>, e cada restrição que implementa uma regra traz o código dela em comentário. Toda FK declara ON DELETE e ON UPDATE explicitamente.</p>
<p><b>Observação sobre o MySQL:</b> o MySQL aceita a sintaxe <code>CONSTRAINT pk_tabela PRIMARY KEY</code>, mas sempre grava a chave primária com o nome interno <code>PRIMARY</code>. O nome pk_ fica no script como documentação. As demais restrições (uq_, fk_, ck_, idx_) ficam gravadas com o nome dado.</p>
<p><b>Critério dos tipos de dados:</b></p>
{tabela(["Tipo", "Onde", "Por quê"], [
    ["INT UNSIGNED", "ids de pessoa, turma, matrícula, aula, mensalidade", "Tabelas que crescem todo semestre; UNSIGNED dobra a faixa positiva, e id nunca é negativo."],
    ["SMALLINT / TINYINT UNSIGNED", "instrumento, nível, sala, ordem, vagas, número da aula", "Cadastros pequenos e estáveis: 1 ou 2 bytes em vez de 4."],
    ["CHAR(11), CHAR(8), CHAR(2)", "cpf, cep, uf", "Tamanho sempre fixo. São guardados como texto, e não número, para não perder zeros à esquerda."],
    ["VARCHAR(n)", "nomes, e-mail, códigos, domínios textuais", "Tamanho variável, com limite pensado no dado real (e-mail 120, nome 100)."],
    ["DECIMAL(7,2) / (8,2) / (4,2)", "valor_hora, valor da mensalidade, nota", "Valor exato. FLOAT gera erro de arredondamento em dinheiro."],
    ["DATE / DATETIME / TIME", "datas, histórico, horário da turma", "O histórico precisa da hora, porque duas mudanças podem ocorrer no mesmo dia; as demais datas só precisam do dia."],
    ["BOOLEAN", "presente, possui_piano", "Sim/não; no MySQL é um TINYINT(1)."],
    ["VARCHAR + CHECK IN (...)", "situação, tipo, família, forma de pagamento", "Preferido ao ENUM porque o nome da restrição (ck_) aparece na mensagem de erro, e acrescentar um valor novo não reescreve a tabela."],
])}
<h3>A7 — 02_carga.sql</h3>
<p>Gerado pelo script <code>ferramentas/gerar_carga.py</code>, com semente fixa: rodar de novo produz exatamente o mesmo arquivo. Dados fictícios: nomes combinados aleatoriamente, CPFs sem dígito verificador válido e e-mails no domínio reservado <code>exemplo.com</code>. A carga cobre os semestres 2026/1 (concluído) e 2026/2 (em andamento até 18/09/2026).</p>
{tabela(["Caso de contorno exigido", "Onde aparece na carga"], [
    ["Atributos opcionais em branco", "5 pessoas sem e-mail, pessoas sem endereço, 3 pessoas sem telefone, professor sem formação, aulas sem conteúdo, faltas sem justificativa"],
    ["Situações em aberto", "mensalidades em aberto (11 vencidas e não pagas); matrícula TRANCADA em 2026/2; turma VIO-IN-26B sem alunos; nível Flauta Básico I sem turma; professor 8 sem turma"],
    ["Histórico com mais de um evento", "matrícula que foi ATIVA → TRANCADA → ATIVA → CONCLUIDA; todas as matrículas concluídas têm pelo menos 2 eventos; aluno que concluiu 2026/1 e está ativo em 2026/2"],
    ["Especialização sobreposta", "pessoa 6 é professora de violão e aluna de piano"],
    ["Aula cancelada", "3 aulas CANCELADA, sem frequência lançada"],
])}
<h3>A8 — 03_consultas.sql</h3>
{tabela(["#", "Categoria", "Pergunta de negócio", "Recurso exigido"], [
    ["C01", "Básica", "Quais alunos são menores e quem é o responsável?", "Projeção, WHERE, ORDER BY"],
    ["C02", "Básica", "Quem mora nas Asas (Norte/Sul)?", "LIKE"],
    ["C03", "Básica", "Que mensalidades venceram desde 01/08 e seguem sem pagamento?", "BETWEEN, IS NULL"],
    ["C04", "Básica", "Quais turmas de 2026/2 são às segundas, quartas ou sextas?", "IN"],
    ["C05", "Básica", "Quem está com cadastro incompleto?", "COALESCE, IS NULL"],
    ["C06", "Junção", "Alunos ativos de cada turma, com nível e professor", "Junção de 5 tabelas"],
    ["C07", "Junção", "Turmas abertas por nível, incluindo níveis sem turma", "LEFT JOIN"],
    ["C08", "Junção", "Turmas de 2026/2 com menos da metade das vagas ocupadas", "LEFT JOIN, GROUP BY, HAVING"],
    ["C09", "Agregação", "Receita por mês e forma de pagamento", "GROUP BY, SUM, COUNT"],
    ["C10", "Agregação", "Turmas com frequência média abaixo de 85%", "GROUP BY, HAVING"],
    ["C11", "Avançada", "Quem foi aprovado em 2026/1 (média ≥ 6 e frequência ≥ 75%)?", "Pergunta não trivial, tabelas derivadas"],
    ["C12", "Avançada", "Quem teve média acima da média da própria turma?", "Subconsulta correlacionada"],
    ["C13", "Avançada", "Quem concluiu um nível e continuou no semestre seguinte?", "EXISTS"],
    ["C14", "Avançada", "Quem está inadimplente, quanto deve e há quantos dias?", "Pergunta não trivial"],
    ["C15", "Avançada", "Alguma regra atendida “por consulta” está sendo violada?", "NOT EXISTS, UNION ALL"],
])}
<h3>Teste em base limpa</h3>
<p class='nota'>Os três scripts foram executados em sequência sobre um servidor MySQL 8.4.9 recém-inicializado, depois de <code>DROP DATABASE</code>, sem nenhum erro. As 15 consultas retornaram resultado, e a auditoria C15 retornou zero violações em todas as regras. Comandos:<br>
<code>mysql -u root &lt; sql/01_ddl.sql</code><br><code>mysql -u root &lt; sql/02_carga.sql</code><br><code>mysql -u root --table &lt; sql/03_consultas.sql</code></p>

<h2 class='quebra'>8. Declaração de uso de inteligência artificial</h2>
<p>Em atendimento à seção 9 do enunciado, a equipe declara que usou o assistente de IA <b>Claude (Anthropic)</b>, via Claude Code, como apoio nas seguintes partes:</p>
<ul>
<li><b>Modelagem:</b> discussão das alternativas de mapeamento da especialização, das chaves e da normalização, e redação inicial das justificativas das seções A4 e A5.</li>
<li><b>Scripts:</b> escrita inicial do 01_ddl.sql, do 03_consultas.sql e dos geradores em Python (carga de dados, diagrama e documentos).</li>
<li><b>Documentação:</b> rascunho do dicionário de dados e deste relatório.</li>
</ul>
<p><b>Como o resultado foi verificado:</b></p>
<ul>
<li>Execução real dos três scripts em base limpa, no MySQL 8.4.9.</li>
<li>Consultas de conferência sobre a carga. Elas encontraram, e levaram a corrigir, dois erros da primeira versão: uma coluna curta demais para o valor INTERMEDIARIO, e alunos reprovados por falta que apareciam matriculados no nível seguinte.</li>
<li>Consulta de auditoria C15.</li>
<li>Revisão, pela equipe, de cada decisão de modelagem, para que todos os integrantes consigam explicá-la na arguição.</li>
</ul>
""")


def pdf(html_path, pdf_path):
    subprocess.run([EDGE, "--headless", "--disable-gpu", "--no-pdf-header-footer",
                    f"--print-to-pdf={pdf_path}", html_path.as_uri()], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=120)


if __name__ == "__main__":
    tmp = RAIZ / "ferramentas" / "_html"
    tmp.mkdir(exist_ok=True)
    arquivos = {
        "relatorio-etapa1": html_relatorio(),
        "modelo-logico": pagina("Modelo lógico — Escola de Música", "<h1>A4 — Modelo lógico relacional</h1>" + html_logico()),
        "dicionario-dados": pagina("Dicionário de dados — Escola de Música", "<h1>A3 — Dicionário de dados conceitual</h1>" + html_dicionario()),
    }
    for nome, conteudo in arquivos.items():
        h = tmp / f"{nome}.html"
        h.write_text(conteudo, encoding="utf-8")
        pdf(h, DOCS / f"{nome}.pdf")
        print("gerado:", DOCS / f"{nome}.pdf")
