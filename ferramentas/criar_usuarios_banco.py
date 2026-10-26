"""
Cria os usuarios do MySQL usados pela aplicacao e liga cada um ao seu papel
(os papeis sao criados em sql/04_seguranca.sql).

Por que isto e um script Python e nao SQL: o usuario do banco tem senha, e
senha nao pode ficar no repositorio (item B2). As senhas vem do arquivo .env,
que esta no .gitignore. O modelo do arquivo e o .env.example.

Uso (depois de rodar 01, 02, 04 e 05):
    python ferramentas/criar_usuarios_banco.py
O script pede a senha do root do MySQL (deixe em branco se nao tiver).
"""

import getpass
import os
from pathlib import Path

import pymysql
from dotenv import load_dotenv

RAIZ = Path(__file__).resolve().parent.parent
load_dotenv(RAIZ / ".env")

# usuario do MySQL -> (variavel do .env com a senha, papel)
USUARIOS = {
    "app_login":      ("DB_SENHA_LOGIN",      "r_login"),
    "app_admin":      ("DB_SENHA_ADMIN",      "r_admin"),
    "app_secretaria": ("DB_SENHA_SECRETARIA", "r_secretaria"),
    "app_professor":  ("DB_SENHA_PROFESSOR",  "r_professor"),
}


def main():
    host = os.getenv("DB_HOST", "localhost")
    port = int(os.getenv("DB_PORT", "3306"))
    senha_root = os.getenv("DB_ROOT_PASSWORD")
    if senha_root is None:
        senha_root = getpass.getpass("Senha do root do MySQL (Enter se vazia): ")

    con = pymysql.connect(host=host, port=port, user="root", password=senha_root)
    with con.cursor() as cur:
        for usuario, (var, papel) in USUARIOS.items():
            senha = os.getenv(var)
            if not senha:
                raise SystemExit(f"Falta {var} no arquivo .env (veja .env.example)")
            # O nome do usuario vem da lista fixa acima, nunca do usuario final;
            # a senha vai como parametro, sem concatenar no SQL.
            cur.execute(f"DROP USER IF EXISTS '{usuario}'@'%'")
            # '%%' vira '%' quando o comando recebe parametros
            cur.execute(f"CREATE USER '{usuario}'@'%%' IDENTIFIED BY %s", (senha,))
            cur.execute(f"GRANT {papel} TO '{usuario}'@'%'")
            cur.execute(f"SET DEFAULT ROLE {papel} TO '{usuario}'@'%'")
            print(f"ok  {usuario:15} -> {papel}")
    con.commit()
    con.close()


if __name__ == "__main__":
    main()
