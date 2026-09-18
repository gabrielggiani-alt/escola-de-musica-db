"""
Gera docs/mer-conceitual.drawio (arquivo-fonte do MER, editavel no draw.io).

Notacao: Engenharia da Informacao (pe de galinha), usada do inicio ao fim.
Convencoes do diagrama (repetidas na legenda):
  # atributo    identificador        (U) valor unico (chave alternativa)
  ? atributo    opcional             /atributo  derivado (calculado, nao armazenado)
  {atributo}    multivalorado        atributo ( ... ) composto
  borda dupla   entidade fraca       linha grossa  relacionamento identificador

Depois de gerar, exportar com o draw.io desktop:
  DrawIO.exe -x -f pdf -o docs/mer-conceitual.pdf docs/mer-conceitual.drawio
"""

from html import escape
from pathlib import Path

SAIDA = Path(__file__).resolve().parent.parent / "docs" / "mer-conceitual.drawio"

# nome: (x, y, largura, [atributos], subtitulo, fraca)
ENTIDADES = {
    "PESSOA": (620, 40, 330, [
        "# id_pessoa", "cpf (U)", "nome", "data_nascimento", "/idade",
        "? email (U)",
        "? endereco (logradouro, numero, bairro, cidade, uf, cep)",
        "{telefone (numero, tipo)}", "data_cadastro"], None, False),
    "ALUNO": (300, 470, 250, ["data_ingresso", "? nome_responsavel"], None, False),
    "PROFESSOR": (1020, 470, 250, ["data_admissao", "valor_hora", "? formacao"], None, False),
    "HABILITACAO": (1360, 470, 250, ["nivel_proficiencia", "data_certificacao"], "associativa", False),
    "INSTRUMENTO": (1700, 470, 230, ["# id_instrumento", "nome (U)", "familia"], None, False),
    "MATRICULA": (300, 780, 250, ["# id_matricula", "data_matricula", "situacao",
                                   "/media_final", "/percentual_frequencia"], "associativa", False),
    "TURMA": (1020, 780, 250, ["# id_turma", "codigo (U)", "dia_semana", "horario_inicio",
                               "data_inicio", "data_fim", "vagas", "/qtd_matriculados"], None, False),
    "NIVEL": (1700, 780, 230, ["# id_nivel", "nome", "ordem", "carga_horaria"], None, False),
    "HISTORICO_SITUACAO": (0, 1160, 250, ["# id_historico", "situacao", "data_alteracao",
                                          "? motivo"], None, False),
    "AVALIACAO": (290, 1160, 230, ["# numero_avaliacao (discriminador)", "tipo",
                                   "data_avaliacao", "nota"], "entidade fraca", True),
    "MENSALIDADE": (560, 1160, 240, ["# id_mensalidade", "competencia", "valor",
                                     "data_vencimento", "? data_pagamento",
                                     "? forma_pagamento"], None, False),
    "FREQUENCIA": (840, 1160, 220, ["presente", "? justificativa"], "associativa", False),
    "AULA": (1120, 1160, 230, ["# id_aula", "numero_aula", "data_aula", "? conteudo",
                               "status"], None, False),
    "SALA": (1420, 1160, 220, ["# id_sala", "nome (U)", "capacidade", "possui_piano"], None, False),
}

# (origem, destino, simbolo junto a origem, simbolo junto ao destino, rotulo, identificador, extra)
# Simbolos pe de galinha: 1 = (1,1)  01 = (0,1)  0N = (0,N)  1N = (1,N)
RELACOES = [
    ("ALUNO", "MATRICULA", "1", "0N", "realiza", False, ""),
    ("TURMA", "MATRICULA", "1", "0N", "recebe", False, "exitX=0;exitY=0.25;entryX=1;entryY=0.25;"),
    ("PROFESSOR", "HABILITACAO", "1", "1N", "possui", False, ""),
    ("INSTRUMENTO", "HABILITACAO", "1", "0N", "habilita", False, ""),
    ("INSTRUMENTO", "NIVEL", "1", "0N", "organiza-se em", False, ""),
    ("NIVEL", "TURMA", "1", "0N", "e ofertado em", False, ""),
    ("PROFESSOR", "TURMA", "1", "0N", "leciona", False, ""),
    ("SALA", "TURMA", "1", "0N", "abriga", False, "exitX=0.5;exitY=0;entryX=1;entryY=0.8;"),
    ("TURMA", "AULA", "1", "0N", "tem", False, ""),
    ("MATRICULA", "HISTORICO_SITUACAO", "1", "1N", "registra", False, "exitX=0;exitY=0.5;entryX=0.5;entryY=0;"),
    ("MATRICULA", "AVALIACAO", "1", "0N", "compoe (identificador)", True, "exitX=0.45;exitY=1;entryX=0.5;entryY=0;"),
    ("MATRICULA", "MENSALIDADE", "1", "0N", "gera", False, "exitX=0.85;exitY=1;entryX=0.5;entryY=0;"),
    ("MATRICULA", "FREQUENCIA", "1", "0N", "", False, "exitX=1;exitY=0.85;entryX=0.5;entryY=0;"),
    ("AULA", "FREQUENCIA", "1", "0N", "registra presenca", False, ""),
]

SIMBOLO = {"1": "ERmandOne", "01": "ERzeroToOne", "0N": "ERzeroToMany", "1N": "ERoneToMany"}

cells = []
ids = {}


def altura(attrs):
    return 30 + 14 * len(attrs) + 8


for i, (nome, (x, y, w, attrs, sub, fraca)) in enumerate(ENTIDADES.items(), start=2):
    ids[nome] = f"e{i}"
    titulo = f"<b>{nome}</b>" + (f"<br><i style='font-size:10px'>({sub})</i>" if sub else "")
    corpo = "<br>".join(escape(a).replace("# ", "<u>#</u> ") for a in attrs)
    label = (f"<div style='text-align:center;border-bottom:1px solid #333;padding-bottom:3px;"
             f"margin-bottom:3px'>{titulo}</div><div style='text-align:left'>{corpo}</div>")
    h = altura(attrs) + (14 if sub else 0)
    estilo = ("rounded=0;whiteSpace=wrap;html=1;verticalAlign=top;align=left;spacingLeft=6;"
              "spacingTop=4;fontSize=11;fillColor=#FFFFFF;strokeColor=#333333;")
    if fraca:
        estilo += "shape=ext;double=1;strokeWidth=1;"
    if sub == "associativa":
        estilo += "fillColor=#F5F5F5;"
    cells.append(f'<mxCell id="{ids[nome]}" value="{escape(label)}" style="{estilo}" '
                 f'vertex="1" parent="1"><mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" '
                 f'as="geometry"/></mxCell>')

# especializacao: PESSOA -> (triangulo t,s) -> ALUNO / PROFESSOR
cells.append('<mxCell id="esp" value="t, s" style="triangle;direction=south;whiteSpace=wrap;html=1;'
             'fontSize=11;fontStyle=1;verticalAlign=top;spacingTop=-2;fillColor=#FFFFFF;" vertex="1" parent="1">'
             '<mxGeometry x="755" y="330" width="60" height="50" as="geometry"/></mxCell>')
cells.append('<mxCell id="esp_lbl" value="especializacao TOTAL (t) e SOBREPOSTA (s):&lt;br&gt;'
             'toda pessoa e aluno, professor ou ambos" style="text;html=1;fontSize=10;align=left;" '
             'vertex="1" parent="1"><mxGeometry x="830" y="270" width="280" height="40" as="geometry"/></mxCell>')
linha = "endArrow=none;html=1;rounded=0;edgeStyle=orthogonalEdgeStyle;"
cells.append(f'<mxCell id="esp0" style="{linha}" edge="1" parent="1" source="{ids["PESSOA"]}" target="esp">'
             '<mxGeometry relative="1" as="geometry"/></mxCell>')
for k, alvo in enumerate(["ALUNO", "PROFESSOR"]):
    cells.append(f'<mxCell id="esp{k+1}" style="{linha}exitX=0.5;exitY=1;entryX=0.5;entryY=0;" edge="1" '
                 f'parent="1" source="esp" target="{ids[alvo]}"><mxGeometry relative="1" as="geometry"/></mxCell>')

for k, (a, b, sa, sb, rot, ident, extra) in enumerate(RELACOES):
    estilo = (f"edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;fontSize=10;startArrow={SIMBOLO[sa]};"
              f"endArrow={SIMBOLO[sb]};startFill=0;endFill=0;startSize=14;endSize=14;"
              f"strokeWidth={3 if ident else 1};labelBackgroundColor=#FFFFFF;{extra}")
    cells.append(f'<mxCell id="r{k}" value="{escape(rot)}" style="{estilo}" edge="1" parent="1" '
                 f'source="{ids[a]}" target="{ids[b]}"><mxGeometry relative="1" as="geometry"/></mxCell>')

# autorrelacionamento NIVEL (pre-requisito): 0..1 pre-requisito, 0..N dependentes
nx, ny, nw = ENTIDADES["NIVEL"][0], ENTIDADES["NIVEL"][1], ENTIDADES["NIVEL"][2]
cells.append('<mxCell id="auto" value="e pre-requisito de" style="edgeStyle=orthogonalEdgeStyle;rounded=0;'
             'html=1;fontSize=10;startArrow=ERzeroToOne;endArrow=ERzeroToMany;startFill=0;endFill=0;'
             'startSize=14;endSize=14;exitX=1;exitY=0.25;entryX=1;entryY=0.75;labelBackgroundColor=#FFFFFF;" '
             f'edge="1" parent="1" source="{ids["NIVEL"]}" target="{ids["NIVEL"]}">'
             f'<mxGeometry relative="1" as="geometry"><Array as="points">'
             f'<mxPoint x="{nx + nw + 70}" y="{ny + 30}"/><mxPoint x="{nx + nw + 70}" y="{ny + 110}"/>'
             f'</Array></mxGeometry></mxCell>')

legenda = ("<b>Legenda — notacao Engenharia da Informacao (pe de galinha)</b><br>"
           "<u>#</u> identificador &nbsp;&nbsp; (U) valor unico &nbsp;&nbsp; ? opcional<br>"
           "/atributo derivado &nbsp;&nbsp; {atributo} multivalorado &nbsp;&nbsp; atributo ( ... ) composto<br>"
           "Cardinalidades: ||  (1,1) &nbsp; o|  (0,1) &nbsp; o&lt; (0,N) &nbsp; |&lt; (1,N)<br>"
           "Borda dupla: entidade fraca &nbsp;&nbsp; Linha grossa: relacionamento identificador<br>"
           "Fundo cinza: entidade associativa (relacionamento N:N com atributos)<br>"
           "Triangulo t,s: especializacao total e sobreposta")
cells.append(f'<mxCell id="leg" value="{escape(legenda)}" style="rounded=0;whiteSpace=wrap;html=1;align=left;'
             'verticalAlign=top;spacing=8;fontSize=10;fillColor=#FFFDE7;strokeColor=#999999;" vertex="1" parent="1">'
             '<mxGeometry x="1680" y="1160" width="330" height="140" as="geometry"/></mxCell>')
titulo = "Escola de Música — MER conceitual&lt;br&gt;notação Engenharia da Informação (pé de galinha)"
cells.append(f'<mxCell id="tit" value="{titulo}" style="text;html=1;fontSize=16;fontStyle=1;" vertex="1" '
             'parent="1"><mxGeometry x="0" y="40" width="520" height="50" as="geometry"/></mxCell>')

xml = ('<mxfile host="drawio"><diagram id="mer" name="MER conceitual"><mxGraphModel dx="1600" dy="900" '
       'grid="1" gridSize="10" page="1" pageScale="1" pageWidth="2100" pageHeight="1400" math="0" '
       'shadow="0"><root><mxCell id="0"/><mxCell id="1" parent="0"/>'
       + "".join(cells) + "</root></mxGraphModel></diagram></mxfile>")
SAIDA.write_text(xml, encoding="utf-8")
print("gerado:", SAIDA)
