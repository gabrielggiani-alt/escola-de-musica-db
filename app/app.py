"""
Aplicacao web da Escola de Musica (Etapa 2, item B1).

Rodar:  python app/app.py   e abrir http://127.0.0.1:5000

O que esta disciplina avalia aqui nao e a beleza da tela, e sim o que a
aplicacao mostra sobre o banco: transacoes, consultas parametrizadas,
erros de restricao tratados e acesso por perfil.
"""

import os
from datetime import date
from functools import wraps

from flask import Flask, flash, redirect, render_template, request, session, url_for

import repositorio as repo
from db import conectar
from erros import traduzir

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")
if not app.secret_key:
    raise SystemExit("Falta FLASK_SECRET_KEY no .env (veja .env.example)")

# o que cada perfil ve no menu (o BANCO e quem garante; o menu so organiza)
MENU = {
    "ADMIN": ["alunos", "turma", "instrumento", "sala", "matricula", "mensalidades",
              "desempenho", "inadimplencia", "relatorio", "auditoria"],
    "SECRETARIA": ["alunos", "turma", "instrumento", "sala", "matricula", "mensalidades",
                   "desempenho", "inadimplencia", "relatorio"],
    "PROFESSOR": ["turma", "desempenho", "relatorio"],
}


def requer_login(f):
    @wraps(f)
    def envolvida(*args, **kwargs):
        if "perfil" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return envolvida


def banco():
    """Conexao com o usuario do MySQL do perfil logado."""
    return conectar(session["perfil"], session["login"])


@app.context_processor
def menu():
    return {"menu": MENU.get(session.get("perfil"), [])}


# ------------------------------------------------------------------ login
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        con = conectar("LOGIN")
        try:
            u = repo.autenticar(con, request.form["login"], request.form["senha"])
        finally:
            con.close()
        if u:
            session.clear()
            session.update(login=u["login"], perfil=u["perfil"])
            return redirect(url_for("inicio"))
        # mesma mensagem para login inexistente e senha errada: nao revela
        # quais logins existem
        flash("Login ou senha invalidos.", "erro")
    return render_template("login.html")


@app.route("/sair")
def sair():
    session.clear()
    return redirect(url_for("login"))


@app.route("/")
@requer_login
def inicio():
    return render_template("inicio.html")


# ------------------------------------------- CRUD generico: instrumento, sala, turma
@app.route("/cad/<ent>")
@requer_login
def cad_lista(ent):
    if ent not in repo.ENTIDADES:
        return redirect(url_for("inicio"))
    con = banco()
    try:
        if ent == "turma" and session["perfil"] == "PROFESSOR":
            # professor nao tem acesso a PESSOA; ve as turmas pela visao
            linhas, editavel = repo.ocupacao_turmas(con), False
        else:
            linhas, editavel = repo.listar(con, ent), True
    except Exception as e:
        flash(traduzir(e), "erro")
        linhas, editavel = [], False
    finally:
        con.close()
    return render_template("cad_lista.html", ent=ent, e=repo.ENTIDADES[ent],
                           linhas=linhas, editavel=editavel)


@app.route("/cad/<ent>/novo", methods=["GET", "POST"])
@app.route("/cad/<ent>/<int:pk>", methods=["GET", "POST"])
@requer_login
def cad_form(ent, pk=None):
    if ent not in repo.ENTIDADES:
        return redirect(url_for("inicio"))
    e = repo.ENTIDADES[ent]
    con = banco()
    try:
        if request.method == "POST":
            try:
                repo.salvar(con, ent, request.form, pk)
                flash("Registro salvo.", "ok")
                return redirect(url_for("cad_lista", ent=ent))
            except Exception as erro:
                con.rollback()
                flash(traduzir(erro), "erro")
                registro = request.form
        else:
            registro = repo.obter(con, ent, pk) if pk else {}
        # opcoes dos campos de escolha
        opc = {}
        for campo, (_, tipo, origem) in e["campos"].items():
            if tipo == "select":
                if isinstance(origem, str):
                    opc[campo] = repo.opcoes(con, origem)
                else:
                    opc[campo] = [o if isinstance(o, tuple) else (o, o) for o in origem]
    finally:
        con.close()
    return render_template("cad_form.html", ent=ent, e=e, pk=pk,
                           r={k: ("" if v is None else str(v)) for k, v in (registro or {}).items()},
                           opc=opc)


@app.route("/cad/<ent>/<int:pk>/excluir", methods=["POST"])
@requer_login
def cad_excluir(ent, pk):
    con = banco()
    try:
        repo.excluir(con, ent, pk)
        flash("Registro excluido.", "ok")
    except Exception as e:
        con.rollback()
        flash(traduzir(e), "erro")
    finally:
        con.close()
    return redirect(url_for("cad_lista", ent=ent))


# --------------------------------------------------------- CRUD de alunos
@app.route("/alunos")
@requer_login
def alunos():
    busca = request.args.get("busca", "")
    con = banco()
    try:
        linhas = repo.listar_alunos(con, busca)
    except Exception as e:
        flash(traduzir(e), "erro")
        linhas = []
    finally:
        con.close()
    return render_template("alunos.html", linhas=linhas, busca=busca)


@app.route("/alunos/novo", methods=["GET", "POST"])
@app.route("/alunos/<int:pk>", methods=["GET", "POST"])
@requer_login
def aluno_form(pk=None):
    con = banco()
    try:
        if request.method == "POST":
            try:
                repo.salvar_aluno(con, request.form, pk)
                flash("Aluno salvo.", "ok")
                return redirect(url_for("alunos"))
            except Exception as e:
                flash(traduzir(e), "erro")
                r = dict(request.form)
        else:
            r = repo.obter_aluno(con, pk) if pk else {"data_ingresso": date.today()}
    finally:
        con.close()
    r = {k: ("" if v is None else str(v)) for k, v in (r or {}).items()}
    return render_template("aluno_form.html", r=r, pk=pk)


@app.route("/alunos/<int:pk>/excluir", methods=["POST"])
@requer_login
def aluno_excluir(pk):
    con = banco()
    try:
        repo.excluir_aluno(con, pk)
        flash("Aluno excluido.", "ok")
    except Exception as e:
        flash(traduzir(e), "erro")
    finally:
        con.close()
    return redirect(url_for("alunos"))


# ------------------------------------------- operacao transacional: matricula
@app.route("/matricula", methods=["GET", "POST"])
@requer_login
def matricula():
    con = banco()
    try:
        if request.method == "POST":
            try:
                valor = request.form.get("valor") or "0"
                n = repo.matricular(con, int(request.form["id_aluno"]),
                                    int(request.form["id_turma"]), valor)
                flash(f"Matricula {n} criada: matricula + historico + 1a mensalidade "
                      f"gravados na mesma transacao (COMMIT).", "ok")
            except Exception as e:
                flash(traduzir(e), "erro")
        alunos_opc = repo.opcoes(con, "alunos")
        turmas_opc = repo.opcoes(con, "turmas")
    finally:
        con.close()
    return render_template("matricula.html", alunos=alunos_opc, turmas=turmas_opc,
                           f=request.form)


# --------------------------------------------------- mensalidades (auditadas)
@app.route("/mensalidades", methods=["GET", "POST"])
@requer_login
def mensalidades():
    con = banco()
    try:
        if request.method == "POST":
            try:
                repo.registrar_pagamento(con, int(request.form["id_mensalidade"]),
                                         request.form["forma"])
                flash("Pagamento registrado (alteracao gravada na auditoria).", "ok")
            except Exception as e:
                con.rollback()
                flash(traduzir(e), "erro")
        linhas = repo.mensalidades_em_aberto(con)
    except Exception as e:
        flash(traduzir(e), "erro")
        linhas = []
    finally:
        con.close()
    return render_template("mensalidades.html", linhas=linhas)


# ----------------------------------------------- consultas parametrizadas
@app.route("/desempenho")
@requer_login
def desempenho():
    con = banco()
    linhas = None
    try:
        instrumentos = repo.opcoes(con, "instrumentos")
        if request.args.get("id_instrumento"):
            linhas = repo.consulta_desempenho(con, request.args["id_instrumento"],
                                              request.args.get("media_minima") or 0)
    except Exception as e:
        flash(traduzir(e), "erro")
        instrumentos = []
    finally:
        con.close()
    return render_template("desempenho.html", instrumentos=instrumentos,
                           linhas=linhas, f=request.args)


@app.route("/inadimplencia")
@requer_login
def inadimplencia():
    con = banco()
    linhas = None
    try:
        if request.args.get("venc_de"):
            linhas = repo.consulta_inadimplencia(con, request.args["venc_de"],
                                                 request.args["venc_ate"],
                                                 request.args.get("valor_minimo") or 0)
    except Exception as e:
        flash(traduzir(e), "erro")
    finally:
        con.close()
    return render_template("inadimplencia.html", linhas=linhas, f=request.args)


# ------------------------------------------------------------ relatorios
@app.route("/relatorio")
@requer_login
def relatorio():
    con = banco()
    financeiro = ocupacao = None
    try:
        ocupacao = repo.ocupacao_turmas(con)
        if session["perfil"] != "PROFESSOR":
            financeiro = repo.relatorio_financeiro(con)
    except Exception as e:
        flash(traduzir(e), "erro")
    finally:
        con.close()
    return render_template("relatorio.html", financeiro=financeiro, ocupacao=ocupacao)


@app.route("/auditoria")
@requer_login
def auditoria():
    con = banco()
    try:
        linhas = repo.auditoria(con)
    except Exception as e:
        flash(traduzir(e), "erro")
        linhas = []
    finally:
        con.close()
    return render_template("auditoria.html", linhas=linhas)


if __name__ == "__main__":
    app.run(debug=False)
