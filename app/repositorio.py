"""
Camada de acesso a dados (item B2).

REGRA DESTE ARQUIVO: todo valor que vem do usuario entra no SQL como
PARAMETRO (%s), nunca concatenado no texto. O driver envia o valor
separado do comando, entao um nome como  ' OR '1'='1  e tratado como
texto a ser procurado, e nao como SQL. (Demonstracao no relatorio, B2.)

Onde aparece f-string em SQL, o que entra e NOME DE TABELA/COLUNA vindo das
listas fixas em ENTIDADES, definidas no codigo, nunca do usuario.
Nomes de tabela nao podem ser parametro (%s), por isso a lista branca.
"""

import hashlib
import hmac
from datetime import date

from erros import ErroNegocio

# ---------------------------------------------------------------- login

ITERACOES = 200_000


def gerar_hash(senha, sal_hex):
    """PBKDF2-HMAC-SHA256: o mesmo algoritmo usado para gerar os hashes de
    sql/04_seguranca.sql. Lento de proposito (200 mil iteracoes) para
    encarecer ataque de forca bruta."""
    return hashlib.pbkdf2_hmac("sha256", senha.encode(), bytes.fromhex(sal_hex), ITERACOES).hex()


def autenticar(con, login, senha):
    with con.cursor() as cur:
        cur.execute(
            "SELECT id_usuario, login, senha_hash, sal, perfil, id_pessoa "
            "FROM usuario_app WHERE login = %s AND ativo = TRUE",
            (login,),
        )
        u = cur.fetchone()
        if not u:
            return None
        # compare_digest compara em tempo constante (nao vaza, pelo tempo de
        # resposta, quantos caracteres do hash bateram)
        if not hmac.compare_digest(gerar_hash(senha, u["sal"]), u["senha_hash"]):
            return None
        cur.execute("UPDATE usuario_app SET ultimo_login = NOW() WHERE id_usuario = %s",
                    (u["id_usuario"],))
    con.commit()
    return u


# --------------------------------------------- CRUD generico (lista branca)
# campo: (rotulo, tipo, origem_das_opcoes)
ENTIDADES = {
    "instrumento": {
        "titulo": "Instrumentos", "pk": "id_instrumento", "ordem": "nome",
        "campos": {
            "nome": ("Nome", "text", None),
            "familia": ("Familia", "select", ["CORDAS", "SOPRO", "PERCUSSAO", "TECLAS", "VOZ"]),
        },
    },
    "sala": {
        "titulo": "Salas", "pk": "id_sala", "ordem": "nome",
        "campos": {
            "nome": ("Nome", "text", None),
            "capacidade": ("Capacidade", "number", None),
            "possui_piano": ("Possui piano", "select", [("1", "Sim"), ("0", "Nao")]),
        },
    },
    "turma": {
        "titulo": "Turmas", "pk": "id_turma", "ordem": "codigo",
        "campos": {
            "codigo": ("Codigo", "text", None),
            "id_nivel": ("Nivel", "select", "niveis"),
            "id_professor": ("Professor", "select", "professores"),
            "id_sala": ("Sala", "select", "salas"),
            "dia_semana": ("Dia da semana", "select",
                           [("2", "Segunda"), ("3", "Terca"), ("4", "Quarta"),
                            ("5", "Quinta"), ("6", "Sexta"), ("7", "Sabado")]),
            "horario_inicio": ("Inicio da aula", "time", None),
            "data_inicio": ("Data de inicio", "date", None),
            "data_fim": ("Data de termino", "date", None),
            "vagas": ("Vagas", "number", None),
        },
    },
}


def listar(con, ent):
    e = ENTIDADES[ent]
    with con.cursor() as cur:
        cur.execute(f"SELECT * FROM {ent} ORDER BY {e['ordem']}")
        return cur.fetchall()


def obter(con, ent, pk):
    e = ENTIDADES[ent]
    with con.cursor() as cur:
        cur.execute(f"SELECT * FROM {ent} WHERE {e['pk']} = %s", (pk,))
        return cur.fetchone()


def salvar(con, ent, dados, pk=None):
    e = ENTIDADES[ent]
    campos = list(e["campos"])
    valores = [dados.get(c) or None for c in campos]
    with con.cursor() as cur:
        if pk is None:
            marcadores = ", ".join(["%s"] * len(campos))
            cur.execute(f"INSERT INTO {ent} ({', '.join(campos)}) VALUES ({marcadores})", valores)
        else:
            atrib = ", ".join(f"{c} = %s" for c in campos)
            cur.execute(f"UPDATE {ent} SET {atrib} WHERE {e['pk']} = %s", valores + [pk])
    con.commit()


def excluir(con, ent, pk):
    e = ENTIDADES[ent]
    with con.cursor() as cur:
        cur.execute(f"DELETE FROM {ent} WHERE {e['pk']} = %s", (pk,))
    con.commit()


def opcoes(con, origem):
    """Listas para os <select> de chave estrangeira."""
    sql = {
        "niveis": "SELECT n.id_nivel AS v, CONCAT(i.nome, ' - ', n.nome) AS r "
                  "FROM nivel n JOIN instrumento i ON i.id_instrumento = n.id_instrumento "
                  "ORDER BY i.nome, n.ordem",
        "professores": "SELECT p.id_pessoa AS v, p.nome AS r FROM professor pr "
                       "JOIN pessoa p ON p.id_pessoa = pr.id_pessoa ORDER BY p.nome",
        "salas": "SELECT id_sala AS v, nome AS r FROM sala ORDER BY nome",
        "instrumentos": "SELECT id_instrumento AS v, nome AS r FROM instrumento ORDER BY nome",
        "alunos": "SELECT id_aluno AS v, nome AS r FROM vw_aluno_contato ORDER BY nome",
        "turmas": "SELECT id_turma AS v, CONCAT(codigo, ' - ', instrumento, ' ', nivel, "
                  "' (', livres, ' vagas livres)') AS r FROM vw_ocupacao_turma "
                  "WHERE data_fim >= CURDATE() ORDER BY codigo",
    }[origem]
    with con.cursor() as cur:
        cur.execute(sql)
        return [(str(r["v"]), r["r"]) for r in cur.fetchall()]


# ------------------------------------------------- CRUD de ALUNO (2 tabelas)

def listar_alunos(con, busca=""):
    with con.cursor() as cur:
        # LIKE com parametro: o curinga % e somado ao VALOR, nao ao SQL.
        cur.execute(
            "SELECT a.id_pessoa, p.nome, p.cpf, p.email, p.data_nascimento, a.data_ingresso "
            "FROM aluno a JOIN pessoa p ON p.id_pessoa = a.id_pessoa "
            "WHERE p.nome LIKE %s ORDER BY p.nome",
            (busca + "%",),
        )
        return cur.fetchall()


def obter_aluno(con, id_pessoa):
    with con.cursor() as cur:
        cur.execute(
            "SELECT p.*, a.data_ingresso, a.nome_responsavel FROM aluno a "
            "JOIN pessoa p ON p.id_pessoa = a.id_pessoa WHERE a.id_pessoa = %s",
            (id_pessoa,),
        )
        return cur.fetchone()


def _idade(nasc):
    hoje = date.today()
    return hoje.year - nasc.year - ((hoje.month, hoje.day) < (nasc.month, nasc.day))


def salvar_aluno(con, d, id_pessoa=None):
    """PESSOA + ALUNO numa transacao: aluno nao existe sem pessoa."""
    try:
        nasc = date.fromisoformat(d.get("data_nascimento", ""))
    except ValueError:
        raise ErroNegocio("Informe a data de nascimento.")
    # RN03 (parte que o CHECK do MySQL nao aceita: CURRENT_DATE)
    if nasc > date.today():
        raise ErroNegocio("A data de nascimento nao pode ser futura (RN03).")
    # RN04
    if _idade(nasc) < 18 and not d.get("nome_responsavel", "").strip():
        raise ErroNegocio("Aluno menor de 18 anos precisa de responsavel (RN04).")

    p = (d.get("nome"), d.get("cpf"), nasc, d.get("email") or None)
    try:
        con.begin()
        with con.cursor() as cur:
            if id_pessoa is None:
                cur.execute("INSERT INTO pessoa (nome, cpf, data_nascimento, email) "
                            "VALUES (%s, %s, %s, %s)", p)
                id_pessoa = cur.lastrowid
                cur.execute("INSERT INTO aluno (id_pessoa, data_ingresso, nome_responsavel) "
                            "VALUES (%s, %s, %s)",
                            (id_pessoa, d.get("data_ingresso") or date.today(),
                             d.get("nome_responsavel") or None))
            else:
                cur.execute("UPDATE pessoa SET nome=%s, cpf=%s, data_nascimento=%s, email=%s "
                            "WHERE id_pessoa=%s", p + (id_pessoa,))
                cur.execute("UPDATE aluno SET data_ingresso=%s, nome_responsavel=%s "
                            "WHERE id_pessoa=%s",
                            (d.get("data_ingresso"), d.get("nome_responsavel") or None, id_pessoa))
        con.commit()
    except Exception:
        con.rollback()
        raise


def excluir_aluno(con, id_pessoa):
    try:
        con.begin()
        with con.cursor() as cur:
            # falha com erro 1451 se o aluno tiver matricula (RN16)
            cur.execute("DELETE FROM aluno WHERE id_pessoa = %s", (id_pessoa,))
            # se a pessoa tambem e professor, a PESSOA fica
            cur.execute("DELETE FROM pessoa WHERE id_pessoa = %s AND NOT EXISTS "
                        "(SELECT 1 FROM professor WHERE id_pessoa = %s)", (id_pessoa, id_pessoa))
        con.commit()
    except Exception:
        con.rollback()
        raise


# -------------------------------------------- consultas parametrizadas (B1)

def consulta_desempenho(con, id_instrumento, media_minima):
    """Alunos de um instrumento com media de notas >= informada.
    Juncao de 6 fontes + GROUP BY + HAVING. Usa a visao vw_aluno_contato
    para o nome, entao funciona tambem para o perfil PROFESSOR."""
    with con.cursor() as cur:
        cur.execute(
            """
            SELECT ac.nome AS aluno, t.codigo AS turma, n.nome AS nivel,
                   COUNT(av.numero_avaliacao) AS avaliacoes,
                   ROUND(AVG(av.nota), 2)     AS media
              FROM avaliacao av
              JOIN matricula m         ON m.id_matricula = av.id_matricula
              JOIN vw_aluno_contato ac ON ac.id_aluno = m.id_aluno
              JOIN turma t             ON t.id_turma = m.id_turma
              JOIN nivel n             ON n.id_nivel = t.id_nivel
             WHERE n.id_instrumento = %s
             GROUP BY ac.nome, t.codigo, n.nome
            HAVING AVG(av.nota) >= %s
             ORDER BY media DESC, aluno
            """,
            (id_instrumento, media_minima),
        )
        return cur.fetchall()


def consulta_inadimplencia(con, venc_de, venc_ate, valor_minimo):
    """Alunos com mensalidades em aberto vencidas no periodo, com total
    devido >= valor informado. Juncao de 3 tabelas + SUM + HAVING."""
    with con.cursor() as cur:
        cur.execute(
            """
            SELECT p.nome AS aluno, p.email,
                   COUNT(*)                   AS parcelas_em_aberto,
                   SUM(ms.valor)              AS total_devido,
                   MIN(ms.data_vencimento)    AS vencimento_mais_antigo
              FROM mensalidade ms
              JOIN matricula m ON m.id_matricula = ms.id_matricula
              JOIN pessoa p    ON p.id_pessoa = m.id_aluno
             WHERE ms.data_pagamento IS NULL
               AND ms.data_vencimento BETWEEN %s AND %s
               AND ms.data_vencimento < CURDATE()
             GROUP BY p.id_pessoa, p.nome, p.email
            HAVING SUM(ms.valor) >= %s
             ORDER BY total_devido DESC
            """,
            (venc_de, venc_ate, valor_minimo),
        )
        return cur.fetchall()


# ------------------------------------------------------ relatorios (visoes)

def relatorio_financeiro(con):
    with con.cursor() as cur:
        cur.execute("SELECT * FROM vw_relatorio_financeiro ORDER BY competencia")
        return cur.fetchall()


def ocupacao_turmas(con):
    with con.cursor() as cur:
        cur.execute("SELECT codigo, instrumento, nivel, professor, data_inicio, data_fim, "
                    "vagas, ocupadas, livres FROM vw_ocupacao_turma ORDER BY codigo")
        return cur.fetchall()


def auditoria(con):
    with con.cursor() as cur:
        cur.execute("SELECT id_auditoria, data_hora, tabela, chave, usuario_app, usuario_banco, "
                    "valores_antes, valores_depois FROM auditoria "
                    "ORDER BY id_auditoria DESC LIMIT 100")
        return cur.fetchall()


def mensalidades_em_aberto(con):
    with con.cursor() as cur:
        cur.execute(
            "SELECT ms.id_mensalidade, p.nome AS aluno, t.codigo AS turma, ms.competencia, "
            "ms.valor, ms.data_vencimento FROM mensalidade ms "
            "JOIN matricula m ON m.id_matricula = ms.id_matricula "
            "JOIN pessoa p ON p.id_pessoa = m.id_aluno "
            "JOIN turma t ON t.id_turma = m.id_turma "
            "WHERE ms.data_pagamento IS NULL ORDER BY ms.data_vencimento")
        return cur.fetchall()


def registrar_pagamento(con, id_mensalidade, forma):
    """Baixa de pagamento. O gatilho trg_mensalidade_au grava a auditoria."""
    with con.cursor() as cur:
        cur.execute("UPDATE mensalidade SET data_pagamento = CURDATE(), forma_pagamento = %s "
                    "WHERE id_mensalidade = %s AND data_pagamento IS NULL",
                    (forma, id_mensalidade))
    con.commit()


# ========================================================================
# OPERACAO TRANSACIONAL CENTRAL (B1 / B3): MATRICULAR ALUNO
# Altera 3 tabelas: MATRICULA, HISTORICO_SITUACAO e MENSALIDADE.
# Ou as tres acontecem, ou nenhuma (ver sql/07_transacoes.sql).
# ========================================================================

def matricular(con, id_aluno, id_turma, valor):
    try:
        con.begin()                                              # START TRANSACTION
        with con.cursor() as cur:
            # 1. Trava a linha da turma ANTES de qualquer outra leitura.
            #    Outra matricula na mesma turma espera aqui ate o COMMIT/ROLLBACK
            #    desta. Isso impede duas pessoas de pegarem a ultima vaga.
            cur.execute("SELECT vagas, id_nivel, data_fim FROM turma "
                        "WHERE id_turma = %s FOR UPDATE", (id_turma,))
            turma = cur.fetchone()
            if not turma:
                raise ErroNegocio("Turma nao encontrada.")
            if turma["data_fim"] < date.today():
                raise ErroNegocio("Esta turma ja terminou.")

            # 2. Vagas (RN13)
            cur.execute("SELECT COUNT(*) AS n FROM matricula "
                        "WHERE id_turma = %s AND situacao = 'ATIVA'", (id_turma,))
            if cur.fetchone()["n"] >= turma["vagas"]:
                raise ErroNegocio("Turma sem vagas: a matricula nao foi feita.")

            # 3. Pre-requisito (RN28): o nivel anterior precisa estar CONCLUIDO
            cur.execute(
                """
                SELECT n.id_nivel_prerequisito, pre.nome
                  FROM nivel n LEFT JOIN nivel pre ON pre.id_nivel = n.id_nivel_prerequisito
                 WHERE n.id_nivel = %s
                """, (turma["id_nivel"],))
            nivel = cur.fetchone()
            if nivel["id_nivel_prerequisito"] is not None:
                cur.execute(
                    """
                    SELECT 1 FROM matricula m JOIN turma t ON t.id_turma = m.id_turma
                     WHERE m.id_aluno = %s AND t.id_nivel = %s AND m.situacao = 'CONCLUIDA'
                    """, (id_aluno, nivel["id_nivel_prerequisito"]))
                if not cur.fetchone():
                    raise ErroNegocio(f"O aluno ainda nao concluiu o pre-requisito "
                                      f"'{nivel['nome']}' (RN28).")

            # 4. As tres escritas
            cur.execute("INSERT INTO matricula (id_aluno, id_turma, data_matricula, situacao) "
                        "VALUES (%s, %s, CURDATE(), 'ATIVA')", (id_aluno, id_turma))
            id_matricula = cur.lastrowid
            cur.execute("INSERT INTO historico_situacao (id_matricula, situacao, data_alteracao, motivo) "
                        "VALUES (%s, 'ATIVA', NOW(), 'Matricula inicial')", (id_matricula,))
            # valor <= 0 viola ck_mensalidade_valor -> excecao -> ROLLBACK abaixo
            cur.execute("INSERT INTO mensalidade (id_matricula, competencia, valor, data_vencimento) "
                        "VALUES (%s, DATE_FORMAT(CURDATE(), '%%Y-%%m-01'), %s, "
                        "DATE_FORMAT(CURDATE(), '%%Y-%%m-10') + INTERVAL 1 MONTH)",
                        (id_matricula, valor))
        con.commit()                                             # COMMIT
        return id_matricula
    except Exception:
        # No MySQL o erro desfaz so o comando que falhou. Sem este ROLLBACK
        # a matricula e o historico ficariam pendentes na conexao.
        con.rollback()                                           # ROLLBACK
        raise
