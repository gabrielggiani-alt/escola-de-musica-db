"""
B3 - Experimento de concorrencia com DUAS sessoes simultaneas.

Reproduz automaticamente os casos 3a e 3b descritos em sql/07_transacoes.sql,
com duas conexoes reais ao MySQL rodando em paralelo (threads), e mede o
tempo que a sessao B fica esperando.

Uso (com o banco carregado e o .env preenchido):
    python ferramentas/experimento_concorrencia.py > docs/resultados-concorrencia.txt

O script desfaz tudo o que inseriu no final.
"""

import os
import threading
import time
from pathlib import Path

import pymysql
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

TURMA = 7          # VIO-B2-26B: 8 vagas, 7 ocupadas -> sobra uma
ALUNO_A, ALUNO_B = 40, 23
T0 = time.perf_counter()


def conectar():
    return pymysql.connect(
        host=os.getenv("DB_HOST", "localhost"), port=int(os.getenv("DB_PORT", "3306")),
        user="root", password=os.getenv("DB_ROOT_PASSWORD", ""),
        database=os.getenv("DB_NAME", "escola_musica"), autocommit=False,
    )


def log(sessao, msg):
    print(f"[{time.perf_counter() - T0:6.2f}s] sessao {sessao}: {msg}", flush=True)


def ocupadas(cur):
    cur.execute("SELECT COUNT(*) FROM matricula WHERE id_turma=%s AND situacao='ATIVA'", (TURMA,))
    return cur.fetchone()[0]


def matricular(sessao, aluno, com_trava, leu_evento, outro_leu, pausa):
    con = conectar()
    cur = con.cursor()
    con.begin()
    log(sessao, "START TRANSACTION")
    if com_trava:
        inicio = time.perf_counter()
        log(sessao, "SELECT vagas FROM turma WHERE id_turma=7 FOR UPDATE")
        cur.execute("SELECT vagas FROM turma WHERE id_turma=%s FOR UPDATE", (TURMA,))
        espera = time.perf_counter() - inicio
        log(sessao, f"obteve a trava (esperou {espera:.2f} s)")
    vagas = 8
    n = ocupadas(cur)
    log(sessao, f"COUNT de matriculas ativas = {n} de {vagas} vagas")
    leu_evento.set()
    if outro_leu is not None:
        outro_leu.wait(timeout=3)
    time.sleep(pausa)
    if n < vagas:
        cur.execute(
            "INSERT INTO matricula (id_aluno, id_turma, data_matricula) VALUES (%s,%s,CURDATE())",
            (aluno, TURMA),
        )
        con.commit()
        log(sessao, f"tinha vaga -> INSERT aluno {aluno} e COMMIT")
    else:
        con.rollback()
        log(sessao, "turma lotada -> ROLLBACK (aplicacao mostra 'turma sem vagas')")
    con.close()


def rodar(com_trava):
    a_leu, b_leu = threading.Event(), threading.Event()
    # Sem trava: cada sessao espera a outra ler antes de gravar (o pior caso).
    # Com trava: A segura a trava 2 s; B tenta travar 0,5 s depois.
    if com_trava:
        ta = threading.Thread(target=matricular, args=("A", ALUNO_A, True, a_leu, None, 2.0))
        tb = threading.Thread(target=matricular, args=("B", ALUNO_B, True, b_leu, None, 0.0))
        ta.start(); a_leu.wait(); time.sleep(0.5); tb.start()
    else:
        ta = threading.Thread(target=matricular, args=("A", ALUNO_A, False, a_leu, b_leu, 0.0))
        tb = threading.Thread(target=matricular, args=("B", ALUNO_B, False, b_leu, a_leu, 0.3))
        ta.start(); tb.start()
    ta.join(); tb.join()
    con = conectar()
    with con.cursor() as cur:
        print(f"RESULTADO: {ocupadas(cur)} matriculas ativas na turma de 8 vagas\n")
        cur.execute("DELETE FROM matricula WHERE id_turma=%s AND id_aluno IN (%s,%s)",
                    (TURMA, ALUNO_A, ALUNO_B))
    con.commit()
    con.close()


if __name__ == "__main__":
    con = conectar()
    with con.cursor() as cur:
        cur.execute("SELECT @@transaction_isolation, @@innodb_lock_wait_timeout")
        iso, timeout = cur.fetchone()
    con.close()
    print(f"Nivel de isolamento: {iso}   innodb_lock_wait_timeout: {timeout} s\n")
    print("=== CASO 3a - SEM trava (SELECT COUNT simples) ===")
    rodar(com_trava=False)
    T0 = time.perf_counter()
    print("=== CASO 3b - COM trava (SELECT ... FOR UPDATE na turma) ===")
    rodar(com_trava=True)
