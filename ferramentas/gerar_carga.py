"""
Gera sql/02_carga.sql com dados ficticios e coerentes para a Escola de Musica.

Por que um gerador e nao INSERTs digitados a mao:
- a tabela de frequencia passa de 700 linhas; digitar isso a mao gera erro;
- a semente fixa (random.seed) faz o arquivo sair sempre igual, entao qualquer
  integrante roda de novo e obtem exatamente a mesma carga;
- as regras de negocio (pre-requisito, habilitacao do professor, vagas) sao
  respeitadas por construcao, aqui no codigo.

Todos os nomes, CPFs, e-mails e telefones sao inventados. Os CPFs sao
sequencias aleatorias de 11 digitos, sem digito verificador valido.

Uso:  python ferramentas/gerar_carga.py
"""

import random
from datetime import date, datetime, timedelta
from pathlib import Path

random.seed(2026)

HOJE = date(2026, 9, 18)  # data de referencia da carga
SAIDA = Path(__file__).resolve().parent.parent / "sql" / "02_carga.sql"

PRIMEIROS = [
    "Ana", "Bruno", "Carla", "Daniel", "Eduarda", "Felipe", "Gabriela", "Heitor",
    "Isabela", "João", "Larissa", "Lucas", "Mariana", "Mateus", "Natália", "Otávio",
    "Paula", "Rafael", "Sofia", "Thiago", "Valentina", "Vinícius", "Yasmin", "Arthur",
    "Beatriz", "Caio", "Débora", "Enzo", "Fernanda", "Gustavo", "Helena", "Igor",
    "Júlia", "Leonardo", "Manuela", "Nicolas", "Olívia", "Pedro", "Raquel", "Samuel",
    "Tatiane", "Ulisses", "Vitória", "Wagner", "Alice", "Bernardo", "Cecília", "Davi",
    "Elisa", "Fábio", "Giovana", "Henrique", "Lívia", "Miguel",
]
SOBRENOMES = [
    "Almeida", "Barbosa", "Cardoso", "Dias", "Esteves", "Ferreira", "Gomes", "Henriques",
    "Lima", "Machado", "Nogueira", "Oliveira", "Pereira", "Queiroz", "Ribeiro", "Santos",
    "Teixeira", "Vasconcelos", "Xavier", "Moreira", "Rocha", "Siqueira", "Pacheco", "Campos",
]
REGIOES = [  # (bairro, cidade, prefixo de CEP)
    ("Asa Norte", "Brasília", "707"), ("Asa Sul", "Brasília", "702"),
    ("Águas Claras", "Brasília", "719"), ("Taguatinga Norte", "Brasília", "721"),
    ("Guará II", "Brasília", "710"), ("Sudoeste", "Brasília", "706"),
    ("Lago Norte", "Brasília", "715"), ("Sobradinho", "Brasília", "730"),
]
LOGRADOUROS = {
    "Asa Norte": "SQN {q} Bloco {b}", "Asa Sul": "SQS {q} Bloco {b}",
    "Águas Claras": "Rua {q} Lote {b}", "Taguatinga Norte": "QNA {q} Casa {b}",
    "Guará II": "QE {q} Conjunto {b}", "Sudoeste": "SQSW {q} Bloco {b}",
    "Lago Norte": "SHIN QI {q} Conjunto {b}", "Sobradinho": "Quadra {q} Conjunto {b}",
}


def q(v):
    """Converte um valor Python para literal SQL."""
    if v is None:
        return "NULL"
    if isinstance(v, bool):
        return "TRUE" if v else "FALSE"
    if isinstance(v, (int, float)):
        return str(v)
    if isinstance(v, datetime):
        return "'" + v.strftime("%Y-%m-%d %H:%M:%S") + "'"
    if isinstance(v, date):
        return "'" + v.isoformat() + "'"
    return "'" + str(v).replace("'", "''") + "'"


def insert(tabela, colunas, linhas, comentario):
    out = [f"-- {comentario} ({len(linhas)} linhas)"]
    out.append(f"INSERT INTO {tabela} ({', '.join(colunas)}) VALUES")
    out.append(",\n".join("  (" + ", ".join(q(v) for v in l) + ")" for l in linhas) + ";")
    return "\n".join(out) + "\n"


def sem_acento(s):
    tabela = str.maketrans("áàâãéêíóôõúçÁÉÍÓÚÂÊÔÃÕÇ", "aaaaeeiooouc" + "AEIOUAEOAOC")
    return s.translate(tabela)


# ------------------------------------------------------------------ pessoas
nomes_usados = set()


def novo_nome():
    while True:
        n = f"{random.choice(PRIMEIROS)} {random.choice(SOBRENOMES)} {random.choice(SOBRENOMES)}"
        p = n.split()
        if p[1] != p[2] and n not in nomes_usados:
            nomes_usados.add(n)
            return n


cpfs = set()


def novo_cpf():
    while True:
        c = "".join(random.choice("0123456789") for _ in range(11))
        if c not in cpfs and len(set(c)) > 1:
            cpfs.add(c)
            return c


pessoas, telefones = [], []


def nova_pessoa(pid, nascimento, com_email=True, com_endereco=True, n_tel=1):
    nome = novo_nome()
    email = None
    if com_email:
        p = sem_acento(nome).lower().split()
        email = f"{p[0]}.{p[2]}{pid}@exemplo.com"
    end = [None] * 6
    if com_endereco:
        bairro, cidade, pref = random.choice(REGIOES)
        if bairro.startswith("Asa"):
            # superquadras reais do Plano Piloto: 102-116, 202-216, 302-316, 402-416
            quadra = random.choice([100, 200, 300, 400]) + random.randint(2, 16)
        else:
            quadra = random.randint(1, 30)
        log = LOGRADOUROS[bairro].format(q=quadra, b=random.choice("ABCDEFGHIJ"))
        end = [log, str(random.randint(1, 300)) if "Casa" in log or "Lote" in log else None,
               bairro, cidade, "DF", pref + f"{random.randint(0, 99999):05d}"]
    cadastro = None  # preenchido depois (data de ingresso/admissao)
    pessoas.append([pid, nome, novo_cpf(), nascimento, email, *end, cadastro])
    for i in range(n_tel):
        tel = "619" + f"{random.randint(0, 99999999):08d}"
        tipo = "CELULAR" if i == 0 else random.choice(["FIXO", "RECADO"])
        if tipo == "FIXO":
            tel = "613" + f"{random.randint(0, 9999999):07d}"
        telefones.append([pid, tel, tipo])
    return nome


def nasc(ano_ini, ano_fim):
    return date(random.randint(ano_ini, ano_fim), random.randint(1, 12), random.randint(1, 28))


# ------------------------------------------------------------ instrumentos
instrumentos = [
    [1, "Violão", "CORDAS"], [2, "Piano", "TECLAS"], [3, "Violino", "CORDAS"],
    [4, "Bateria", "PERCUSSAO"], [5, "Canto", "VOZ"], [6, "Flauta transversal", "SOPRO"],
]

# niveis: (id, instrumento, nome, ordem, carga, prerequisito)
niveis = [
    [1, 1, "Violão Básico I", 1, 40, None], [2, 1, "Violão Básico II", 2, 40, 1],
    [3, 1, "Violão Intermediário", 3, 60, 2],
    [4, 2, "Piano Básico I", 1, 40, None], [5, 2, "Piano Básico II", 2, 40, 4],
    [6, 2, "Piano Intermediário", 3, 60, 5],
    [7, 3, "Violino Básico I", 1, 40, None], [8, 3, "Violino Básico II", 2, 40, 7],
    [9, 4, "Bateria Básico I", 1, 40, None], [10, 4, "Bateria Básico II", 2, 40, 9],
    [11, 5, "Canto Básico I", 1, 30, None], [12, 5, "Canto Intermediário", 2, 45, 11],
    [13, 6, "Flauta Básico I", 1, 40, None],  # nivel ainda sem turma (caso de contorno)
]
nivel_por_id = {n[0]: n for n in niveis}

salas = [
    [1, "Sala Villa-Lobos", 8, True], [2, "Sala Chiquinha Gonzaga", 6, True],
    [3, "Sala Tom Jobim", 10, False], [4, "Sala Pixinguinha", 8, False],
    [5, "Estúdio de Bateria", 4, False], [6, "Auditório", 30, True],
]
sala_por_id = {s[0]: s for s in salas}

# ------------------------------------------------------------- professores
# (id_pessoa, admissao, valor_hora, formacao, habilitacoes[(instr, prof, data)])
professores_def = [
    (1, date(2019, 2, 4), 85.00, "Licenciatura em Música - UnB", [(1, "ESPECIALISTA", date(2015, 12, 10)), (5, "INTERMEDIARIO", date(2018, 6, 20))]),
    (2, date(2020, 3, 2), 95.00, "Bacharelado em Piano - UnB", [(2, "ESPECIALISTA", date(2014, 7, 1))]),
    (3, date(2021, 8, 2), 90.00, "Bacharelado em Violino - UFG", [(3, "ESPECIALISTA", date(2016, 12, 15))]),
    (4, date(2022, 2, 7), 75.00, None, [(4, "AVANCADO", date(2019, 11, 30))]),
    (5, date(2018, 8, 6), 88.00, "Licenciatura em Música - UFMG", [(5, "ESPECIALISTA", date(2012, 12, 12)), (2, "INTERMEDIARIO", date(2017, 3, 5))]),
    (6, date(2023, 8, 1), 70.00, "Técnico em Música - Escola de Música de Brasília", [(1, "AVANCADO", date(2021, 12, 3))]),
    (7, date(2024, 2, 5), 80.00, "Bacharelado em Música Popular - Unicamp", [(4, "ESPECIALISTA", date(2020, 12, 1)), (1, "INTERMEDIARIO", date(2022, 5, 9))]),
    (8, date(2026, 8, 3), 78.00, "Bacharelado em Flauta - UnB", [(6, "ESPECIALISTA", date(2024, 12, 18))]),  # sem turma ainda
]
professores, habilitacoes = [], []
for pid, adm, vh, form, habs in professores_def:
    nova_pessoa(pid, nasc(1972, 1998), com_email=True, com_endereco=pid != 4, n_tel=2 if pid in (1, 5) else 1)
    pessoas[-1][-1] = adm
    professores.append([pid, adm, vh, form])
    for instr, prof, dt in habs:
        habilitacoes.append([pid, instr, prof, dt])
habilitados = {(h[0], h[1]) for h in habilitacoes}

# ----------------------------------------------------------------- alunos
N_ALUNOS = 46
alunos = []
ids_alunos = list(range(9, 9 + N_ALUNOS))
for pid in ids_alunos:
    menor = random.random() < 0.3
    nascimento = nasc(2010, 2015) if menor else nasc(1968, 2007)
    # casos de contorno: alguns sem e-mail, sem endereco ou sem telefone
    nova_pessoa(pid, nascimento,
                com_email=random.random() > 0.15,
                com_endereco=random.random() > 0.12,
                n_tel=0 if random.random() < 0.08 else (2 if random.random() < 0.2 else 1))
    responsavel = None
    if menor:
        responsavel = novo_nome()
    alunos.append([pid, None, responsavel])  # data_ingresso definida pela 1a matricula
aluno_por_id = {a[0]: a for a in alunos}

# o professor 6 tambem estuda piano: especializacao SOBREPOSTA
alunos.append([6, None, None])
aluno_por_id[6] = alunos[-1]

# ------------------------------------------------------------------ turmas
S1 = (date(2026, 2, 9), date(2026, 6, 27))
S2 = (date(2026, 8, 3), date(2026, 12, 12))
# (id, codigo, nivel, professor, sala, dia_semana(2=seg), horario, semestre, vagas)
turmas_def = [
    (1, "VIO-B1-26A", 1, 1, 3, 2, "18:30:00", S1, 8),
    (2, "PIA-B1-26A", 4, 2, 1, 3, "14:00:00", S1, 6),
    (3, "VNO-B1-26A", 7, 3, 4, 4, "16:00:00", S1, 6),
    (4, "BAT-B1-26A", 9, 4, 5, 5, "19:00:00", S1, 4),
    (5, "CAN-B1-26A", 11, 5, 6, 7, "09:00:00", S1, 12),
    (6, "VIO-B1-26B", 1, 6, 3, 4, "19:30:00", S1, 8),
    (7, "VIO-B2-26B", 2, 1, 3, 2, "18:30:00", S2, 8),
    (8, "VIO-B1-26C", 1, 6, 3, 4, "19:30:00", S2, 8),
    (9, "PIA-B2-26B", 5, 2, 1, 3, "14:00:00", S2, 6),
    (10, "PIA-B1-26B", 4, 5, 2, 6, "10:00:00", S2, 5),
    (11, "VNO-B2-26B", 8, 3, 4, 4, "16:00:00", S2, 6),
    (12, "BAT-B2-26B", 10, 7, 5, 5, "19:00:00", S2, 4),
    (13, "CAN-IN-26B", 12, 5, 6, 7, "09:00:00", S2, 12),
    (14, "VIO-IN-26B", 3, 7, 4, 6, "15:00:00", S2, 6),  # turma sem alunos (caso de contorno)
]
turmas = []
for tid, cod, niv, prof, sala, dia, hora, (ini, fim), vagas in turmas_def:
    instr = nivel_por_id[niv][1]
    assert (prof, instr) in habilitados, f"professor {prof} nao habilitado na turma {cod}"
    assert vagas <= sala_por_id[sala][2], f"turma {cod} com mais vagas que a sala"
    # data_inicio = primeira ocorrencia do dia da semana a partir do inicio do semestre
    d = ini
    while (d.isoweekday() % 7) + 1 != dia:
        d += timedelta(days=1)
    turmas.append([tid, cod, niv, prof, sala, dia, hora, d, fim, vagas])
turma_por_id = {t[0]: t for t in turmas}

# ------------------------------------------------------------ matriculas
matriculas, historico = [], []
mid = 0
concluiu = {}  # (aluno, nivel) concluido


def matricular(aluno, turma, situacao, eventos):
    """eventos: lista de (situacao, datetime, motivo) a partir da 2a situacao."""
    global mid
    mid += 1
    t = turma_por_id[turma]
    dm = t[7] - timedelta(days=random.randint(3, 25))
    matriculas.append([mid, aluno, turma, dm, situacao])
    historico.append([mid, "ATIVA", datetime(dm.year, dm.month, dm.day, random.randint(9, 18), random.choice([0, 15, 30, 45])), "Matrícula realizada"])
    for sit, dt, mot in eventos:
        historico.append([mid, sit, dt, mot])
    a = aluno_por_id[aluno]
    if a[1] is None or dm < a[1]:
        a[1] = dm
    # so conta como pre-requisito cumprido quem foi APROVADO (RN28)
    if situacao == "CONCLUIDA" and "Aprovado" in (eventos[-1][2] or ""):
        concluiu[(aluno, t[2])] = True
    return mid


pool = ids_alunos[:]
random.shuffle(pool)
# Semestre 1: 6 turmas
distrib_s1 = {1: 7, 2: 5, 3: 5, 4: 4, 5: 9, 6: 6}
alunos_s1 = {}
cursor = 0
for tid, qtd in distrib_s1.items():
    alunos_s1[tid] = pool[cursor:cursor + qtd]
    cursor += qtd
restantes = pool[cursor:]

for tid, lista in alunos_s1.items():
    fim = turma_por_id[tid][8]
    for i, a in enumerate(lista):
        r = random.random()
        if i == 0 and tid in (1, 5):
            # cancelou no meio do semestre
            dt = datetime(2026, 4, random.randint(1, 28), 10, 0)
            matricular(a, tid, "CANCELADA", [("CANCELADA", dt, "Mudança de cidade")])
        elif i == 1 and tid == 3:
            # trancou e voltou: historico com mais de um evento
            matricular(a, tid, "CONCLUIDA", [
                ("TRANCADA", datetime(2026, 3, 16, 11, 20), "Viagem a trabalho"),
                ("ATIVA", datetime(2026, 4, 6, 9, 45), "Retorno da viagem"),
                ("CONCLUIDA", datetime(fim.year, fim.month, fim.day, 18, 0), "Aprovado no nível"),
            ])
        elif r < 0.12:
            matricular(a, tid, "CONCLUIDA", [("CONCLUIDA", datetime(fim.year, fim.month, fim.day, 18, 0), "Reprovado por nota - encerrado")])
        else:
            matricular(a, tid, "CONCLUIDA", [("CONCLUIDA", datetime(fim.year, fim.month, fim.day, 18, 0), "Aprovado no nível")])

# Semestre 2: quem concluiu nivel 1 segue para o nivel 2 (respeita pre-requisito)
progressao = {1: 7, 4: 9, 7: 11, 9: 12, 11: 13}  # nivel concluido -> turma do proximo nivel
for tid, lista in alunos_s1.items():
    nivel = turma_por_id[tid][2]
    for a in lista:
        if concluiu.get((a, nivel)) and random.random() < 0.8:
            destino = progressao[nivel]
            t = turma_por_id[destino]
            ocupadas = sum(1 for m in matriculas if m[2] == destino)
            if ocupadas < t[9]:
                matricular(a, destino, "ATIVA", [])

# novos alunos nas turmas de nivel basico do semestre 2
novas = {8: 7, 10: 4}
for tid, qtd in novas.items():
    for _ in range(qtd):
        if restantes:
            matricular(restantes.pop(), tid, "ATIVA", [])
# professor 6 estudando piano
matricular(6, 10, "ATIVA", [])
# uma matricula TRANCADA em aberto no semestre 2
alvo = next(m for m in matriculas if m[2] == 8 and m[4] == "ATIVA")
alvo[4] = "TRANCADA"
historico.append([alvo[0], "TRANCADA", datetime(2026, 9, 2, 14, 10), "Problema de saúde"])
# os alunos que sobraram em `restantes` ficam cadastrados SEM matricula
# (caso de contorno: acabaram de se inscrever e aguardam turma)

for a in alunos:
    if a[1] is None:
        a[1] = date(2026, 9, 10)  # cadastrado, ainda sem matricula
for p in pessoas:
    if p[-1] is None:
        p[-1] = aluno_por_id[p[0]][1]

# ------------------------------------------------------------------ aulas
aulas, aid = [], 0
CONTEUDOS = ["Postura e leitura de cifra", "Escalas maiores", "Leitura rítmica",
             "Técnica de mão direita", "Repertório: peça 1", "Repertório: peça 2",
             "Percepção musical", "Dinâmica e expressão", "Ensaio para recital", None]
aulas_por_turma = {}
for t in turmas:
    tid, ini, fim = t[0], t[7], t[8]
    d, n = ini, 0
    aulas_por_turma[tid] = []
    while d <= min(fim, HOJE - timedelta(days=1)):
        if tid == 14:
            break  # turma sem alunos ainda nao comecou a ter aula registrada
        n += 1
        aid += 1
        status = "CANCELADA" if (tid, n) in {(2, 6), (5, 10), (7, 3)} else "REALIZADA"
        conteudo = "Aula cancelada - professor em congresso" if status == "CANCELADA" else random.choice(CONTEUDOS)
        aulas.append([aid, tid, n, d, conteudo, status])
        aulas_por_turma[tid].append((aid, d, status))
        d += timedelta(days=7)

# ------------------------------------------------------------- frequencia
frequencias = []
JUSTIF = ["Atestado médico", "Viagem", "Compromisso escolar", None, None]
hist_por_mat = {}
for h in historico:
    hist_por_mat.setdefault(h[0], []).append(h)


def ativo_em(mid_, dia):
    """A matricula estava ATIVA no dia? Usa o historico de situacao."""
    sit = None
    for h in sorted(hist_por_mat[mid_], key=lambda x: x[2]):
        if h[2].date() <= dia:
            sit = h[1]
    return sit == "ATIVA"


for m in matriculas:
    mid_, aluno, tid = m[0], m[1], m[2]
    assiduidade = random.uniform(0.7, 0.98)
    for (aid_, d, status) in aulas_por_turma[tid]:
        if status != "REALIZADA" or d < m[3] or not ativo_em(mid_, d):
            continue
        presente = random.random() < assiduidade
        just = None if presente else random.choice(JUSTIF)
        frequencias.append([mid_, aid_, presente, just])

# RN29: quem foi APROVADO no semestre 1 precisa ter frequencia >= 75%.
# Se o sorteio deixou algum aprovado abaixo disso, converte faltas em presencas.
aprovados = {h[0] for h in historico if h[3] == "Aprovado no nível"}
for mid_ in aprovados:
    regs = [f for f in frequencias if f[0] == mid_]
    while regs and sum(f[2] for f in regs) / len(regs) < 0.78:
        falta = random.choice([f for f in regs if not f[2]])
        falta[2], falta[3] = True, None

# -------------------------------------------------------------- avaliacoes
avaliacoes = []
for m in matriculas:
    t = turma_por_id[m[2]]
    reprovado = any(h[0] == m[0] and h[3] and "Reprovado" in h[3] for h in historico)
    if t[8] < HOJE and m[4] == "CONCLUIDA":
        base = random.uniform(3.0, 5.2) if reprovado else random.uniform(6.2, 9.6)
        datas = [date(2026, 4, 13), date(2026, 5, 25), t[8] - timedelta(days=random.randint(0, 5))]
        for n, (tipo, dt) in enumerate(zip(["TEORICA", "PRATICA", "RECITAL"], datas), start=1):
            nota = round(min(10, max(0, base + random.uniform(-1.2, 1.2))) * 2) / 2
            avaliacoes.append([m[0], n, tipo, dt, nota])
    elif m[4] == "ATIVA" and t[7] < HOJE and random.random() < 0.7:
        avaliacoes.append([m[0], 1, "TEORICA", date(2026, 9, 14) + timedelta(days=random.randint(0, 3)),
                           round(random.uniform(4.5, 10) * 2) / 2])

# ------------------------------------------------------------- mensalidades
mensalidades, menid = [], 0
BASE = {1: 280, 2: 300, 3: 340}
for m in matriculas:
    t = turma_por_id[m[2]]
    niv = nivel_por_id[t[2]]
    valor = BASE[niv[3]] + (40 if niv[1] == 2 else 0)
    comp = date(t[7].year, t[7].month, 1)
    fim_cobranca = min(t[8], HOJE)
    saida = None
    for h in hist_por_mat[m[0]]:
        if h[1] in ("CANCELADA", "TRANCADA") and m[4] in ("CANCELADA", "TRANCADA"):
            saida = h[2].date()
    while comp <= fim_cobranca:
        if saida and comp > saida:
            break
        menid += 1
        venc = comp + timedelta(days=9)
        if venc > HOJE:
            pag, forma = None, None  # ainda nao venceu e nao foi paga
        elif random.random() < 0.06:
            pag, forma = None, None  # inadimplente: vencida e em aberto
        else:
            atraso = random.choice([-5, -3, -1, 0, 0, 1, 2, 8])
            pag = venc + timedelta(days=atraso)
            forma = random.choice(["PIX", "PIX", "PIX", "CARTAO", "BOLETO", "DINHEIRO"])
        mensalidades.append([menid, m[0], comp, float(valor), venc, pag, forma])
        comp = date(comp.year + (comp.month == 12), comp.month % 12 + 1, 1)

# ---------------------------------------------------------------- escrita
blocos = [
    "-- =====================================================================\n"
    "-- Projeto Final - Laboratorio de Banco de Dados (UCB 2026/2)\n"
    "-- A7 - Script de carga (DML) - Escola de Musica\n"
    "-- GERADO por ferramentas/gerar_carga.py (semente fixa 2026). Nao editar a mao:\n"
    "-- altere o gerador e rode de novo.\n"
    "-- Todos os dados sao FICTICIOS. CPFs sao sequencias aleatorias sem digito\n"
    "-- verificador valido; e-mails usam o dominio reservado exemplo.com.\n"
    "-- Ordem de insercao respeita as dependencias entre tabelas.\n"
    "-- =====================================================================\n\n"
    "USE escola_musica;\n\nSTART TRANSACTION;\n",
    insert("pessoa", ["id_pessoa", "nome", "cpf", "data_nascimento", "email", "logradouro", "numero",
                      "bairro", "cidade", "uf", "cep", "data_cadastro"], pessoas, "Pessoas (professores 1-8, alunos 9+)"),
    insert("telefone", ["id_pessoa", "numero", "tipo"], telefones, "Telefones (atributo multivalorado)"),
    insert("professor", ["id_pessoa", "data_admissao", "valor_hora", "formacao"], professores, "Professores"),
    insert("aluno", ["id_pessoa", "data_ingresso", "nome_responsavel"], sorted(alunos), "Alunos (o id 6 tambem e professor)"),
    insert("instrumento", ["id_instrumento", "nome", "familia"], instrumentos, "Instrumentos"),
    insert("habilitacao", ["id_professor", "id_instrumento", "nivel_proficiencia", "data_certificacao"], habilitacoes, "Habilitacoes"),
    insert("nivel", ["id_nivel", "id_instrumento", "nome", "ordem", "carga_horaria", "id_nivel_prerequisito"], niveis, "Niveis (autorrelacionamento de pre-requisito)"),
    insert("sala", ["id_sala", "nome", "capacidade", "possui_piano"], salas, "Salas"),
    insert("turma", ["id_turma", "codigo", "id_nivel", "id_professor", "id_sala", "dia_semana",
                     "horario_inicio", "data_inicio", "data_fim", "vagas"], turmas, "Turmas 2026/1 e 2026/2"),
    insert("matricula", ["id_matricula", "id_aluno", "id_turma", "data_matricula", "situacao"], matriculas, "Matriculas"),
    insert("historico_situacao", ["id_matricula", "situacao", "data_alteracao", "motivo"], historico, "Historico de situacao das matriculas"),
    insert("aula", ["id_aula", "id_turma", "numero_aula", "data_aula", "conteudo", "status"], aulas, "Aulas"),
    insert("frequencia", ["id_matricula", "id_aula", "presente", "justificativa"], frequencias, "Frequencia (tabela de maior movimento)"),
    insert("avaliacao", ["id_matricula", "numero_avaliacao", "tipo", "data_avaliacao", "nota"], avaliacoes, "Avaliacoes (entidade fraca)"),
    insert("mensalidade", ["id_mensalidade", "id_matricula", "competencia", "valor", "data_vencimento",
                           "data_pagamento", "forma_pagamento"], mensalidades, "Mensalidades"),
    "COMMIT;\n",
]
SAIDA.write_text("\n".join(blocos), encoding="utf-8")
print(f"{SAIDA.name}: pessoas={len(pessoas)} telefones={len(telefones)} alunos={len(alunos)} "
      f"matriculas={len(matriculas)} historico={len(historico)} aulas={len(aulas)} "
      f"frequencia={len(frequencias)} avaliacoes={len(avaliacoes)} mensalidades={len(mensalidades)}")
