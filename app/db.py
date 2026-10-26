"""
Conexao com o MySQL.

Cada perfil da aplicacao conecta com um usuario DIFERENTE do MySQL
(criados por ferramentas/criar_usuarios_banco.py). Assim, quem garante o
que cada perfil pode fazer e o PROPRIO BANCO (GRANT/REVOKE em
sql/04_seguranca.sql), e nao so os menus da aplicacao: mesmo que alguem
burle a tela, o banco recusa.

As senhas vem do .env (fora do Git). Nenhuma credencial fica no codigo.
"""

import os
from pathlib import Path

import pymysql
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

# perfil da aplicacao -> (usuario do MySQL, variavel do .env com a senha)
USUARIO_POR_PERFIL = {
    "LOGIN":      ("app_login",      "DB_SENHA_LOGIN"),
    "ADMIN":      ("app_admin",      "DB_SENHA_ADMIN"),
    "SECRETARIA": ("app_secretaria", "DB_SENHA_SECRETARIA"),
    "PROFESSOR":  ("app_professor",  "DB_SENHA_PROFESSOR"),
}


def conectar(perfil, login_app=None):
    usuario, var_senha = USUARIO_POR_PERFIL[perfil]
    con = pymysql.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=usuario,
        password=os.getenv(var_senha),
        database=os.getenv("DB_NAME", "escola_musica"),
        charset="utf8mb4",
        autocommit=False,                      # transacoes sempre explicitas
        cursorclass=pymysql.cursors.DictCursor,
    )
    if login_app:
        # Os gatilhos de auditoria (sql/05_auditoria.sql) leem esta variavel
        # para registrar QUEM fez a alteracao. Vai como parametro.
        with con.cursor() as cur:
            cur.execute("SET @usuario_app = %s", (login_app,))
    return con
