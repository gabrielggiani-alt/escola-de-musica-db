"""
PREPARA TUDO PARA A DEMONSTRACAO COM UM COMANDO SO.

    python ferramentas/preparar_banco.py

O que faz, nesta ordem:
  1. roda sql/01_ddl.sql, 02_carga.sql, 04_seguranca.sql, 05_auditoria.sql
     e 06_otimizacao.sql (cria o banco do zero, carrega os dados, cria
     perfis, auditoria e indices)
  2. cria os usuarios do MySQL da aplicacao (mesmo que criar_usuarios_banco.py)

Nao precisa do programa "mysql" no terminal: executa os scripts pelo Python.
Pode rodar quantas vezes quiser. Cada vez o banco VOLTA AO ESTADO INICIAL
(tudo o que foi cadastrado em ensaios e apagado). Rode de novo pouco antes
da apresentacao.

O 07_transacoes.sql fica de fora de proposito: ele tem um erro PROPOSITAL e
e para ser mostrado na apresentacao, nao para preparar o banco.
"""

import getpass
import os
import re
import sys
from pathlib import Path

import pymysql
from dotenv import load_dotenv

RAIZ = Path(__file__).resolve().parent.parent
load_dotenv(RAIZ / ".env")
SCRIPTS = ["01_ddl.sql", "02_carga.sql", "04_seguranca.sql", "05_auditoria.sql", "06_otimizacao.sql"]


def comandos(texto):
    """Separa um script SQL em comandos, respeitando DELIMITER (usado nos gatilhos)."""
    delimitador, atual = ";", []
    for linha in texto.splitlines():
        limpa = linha.strip()
        if not atual and (not limpa or limpa.startswith("--")):
            continue
        if limpa.upper().startswith("DELIMITER "):
            delimitador = limpa.split()[1]
            continue
        atual.append(linha)
        # o fim do comando e decidido sem o comentario do fim da linha
        # ("... ;  -- comentario") e ignorando linhas que sao so comentario
        codigo = "" if limpa.startswith("--") else re.sub(r"\s--\s.*$", "", limpa).rstrip()
        if codigo.endswith(delimitador):
            atual[-1] = atual[-1][: atual[-1].rindex(delimitador)]
            yield "\n".join(atual)
            atual = []
    if "".join(atual).strip():
        yield "\n".join(atual)


def main():
    senha_root = os.getenv("DB_ROOT_PASSWORD")
    if senha_root is None:
        senha_root = getpass.getpass("Senha do root do MySQL (Enter se vazia): ")
    try:
        con = pymysql.connect(host=os.getenv("DB_HOST", "localhost"),
                              port=int(os.getenv("DB_PORT", "3306")),
                              user="root", password=senha_root, charset="utf8mb4",
                              autocommit=True)
    except pymysql.MySQLError as e:
        sys.exit(f"Nao consegui conectar no MySQL como root: {e}\n"
                 "Confira se o MySQL esta ligado e se a senha do root esta certa no .env.")

    for nome in SCRIPTS:
        texto = (RAIZ / "sql" / nome).read_text(encoding="utf-8")
        with con.cursor() as cur:
            for sql in comandos(texto):
                try:
                    cur.execute(sql)
                    while cur.nextset():
                        pass
                except pymysql.MySQLError as e:
                    sys.exit(f"ERRO em {nome}: {e}\nComando:\n{sql[:300]}")
        print(f"ok  {nome}")
    con.close()

    # usuarios do MySQL da aplicacao (senhas do .env)
    sys.path.insert(0, str(RAIZ / "ferramentas"))
    import criar_usuarios_banco
    criar_usuarios_banco.main()
    print("\nPRONTO. Agora rode:  python app/app.py   e abra http://127.0.0.1:5000")


if __name__ == "__main__":
    main()
