"""
Gera docs/relatorio-etapa2.pdf a partir de docs/relatorio-etapa2.md.

O texto do relatorio fica em Markdown (facil de editar e de ler no GitHub);
este script so converte para PDF paginado. Para mudar o relatorio, edite o
.md e rode de novo:

    pip install reportlab
    python ferramentas/gerar_relatorio_etapa2.py

Suporta o subconjunto de Markdown usado no relatorio: titulos (#, ##, ###),
paragrafos, **negrito**, *italico*, `codigo`, listas (- e 1.), tabelas,
blocos de codigo (```) e linha horizontal (---).
"""

import re
from html import escape
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (HRFlowable, ListFlowable, ListItem, Paragraph, Preformatted,
                                SimpleDocTemplate, Spacer, Table, TableStyle)

RAIZ = Path(__file__).resolve().parent.parent
ORIGEM = RAIZ / "docs" / "relatorio-etapa2.md"
DESTINO = RAIZ / "docs" / "relatorio-etapa2.pdf"

# Fonte com acentos e simbolos (setas, etc.): DejaVu no Linux, Arial no Windows.
CANDIDATAS = [
    ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
     "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
     "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"),
    (r"C:\Windows\Fonts\arial.ttf", r"C:\Windows\Fonts\arialbd.ttf", r"C:\Windows\Fonts\consola.ttf"),
]
FONTE, NEGRITO, MONO = "Helvetica", "Helvetica-Bold", "Courier"
for normal, bold, mono in CANDIDATAS:
    if Path(normal).exists() and Path(bold).exists() and Path(mono).exists():
        pdfmetrics.registerFont(TTFont("Texto", normal))
        pdfmetrics.registerFont(TTFont("Texto-Bold", bold))
        pdfmetrics.registerFont(TTFont("Mono", mono))
        pdfmetrics.registerFontFamily("Texto", normal="Texto", bold="Texto-Bold",
                                      italic="Texto", boldItalic="Texto-Bold")
        FONTE, NEGRITO, MONO = "Texto", "Texto-Bold", "Mono"
        break

base = getSampleStyleSheet()
EST = {
    "p": ParagraphStyle("p", parent=base["Normal"], fontName=FONTE, fontSize=9.5, leading=13,
                        spaceAfter=5, alignment=TA_LEFT),
    "h1": ParagraphStyle("h1", parent=base["Heading1"], fontName=NEGRITO, fontSize=16,
                         textColor=colors.HexColor("#26314f"), spaceAfter=8),
    "h2": ParagraphStyle("h2", parent=base["Heading2"], fontName=NEGRITO, fontSize=13,
                         textColor=colors.HexColor("#26314f"), spaceBefore=10, spaceAfter=6),
    "h3": ParagraphStyle("h3", parent=base["Heading3"], fontName=NEGRITO, fontSize=11,
                         spaceBefore=6, spaceAfter=4),
    "cel": ParagraphStyle("cel", fontName=FONTE, fontSize=8, leading=10),
    "celh": ParagraphStyle("celh", fontName=NEGRITO, fontSize=8, leading=10),
    "code": ParagraphStyle("code", fontName=MONO, fontSize=7.5, leading=9.5,
                           backColor=colors.HexColor("#f1f2f6"), borderPadding=5,
                           spaceBefore=4, spaceAfter=8),
}


def inline(texto):
    t = escape(texto, quote=False)
    t = re.sub(r"`([^`]+)`", rf'<font face="{MONO}">\1</font>', t)
    t = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"(?<![\w*])\*([^*]+)\*(?![\w*])", r"<i>\1</i>", t)
    return t


def tabela(linhas, largura):
    celulas = [[c.strip() for c in l.strip().strip("|").split("|")] for l in linhas]
    celulas = [c for c in celulas if not all(re.fullmatch(r":?-{2,}:?", x) for x in c)]
    dados = [[Paragraph(inline(c), EST["celh" if i == 0 else "cel"]) for c in linha]
             for i, linha in enumerate(celulas)]
    n = len(celulas[0])
    t = Table(dados, colWidths=[largura / n] * n, repeatRows=1)
    t.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#c5c9d3")),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e6e9f1")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]))
    return t


def converter(md, largura):
    historia, i = [], 0
    linhas = md.splitlines()
    while i < len(linhas):
        l = linhas[i]
        if l.startswith("```"):
            bloco = []
            i += 1
            while i < len(linhas) and not linhas[i].startswith("```"):
                bloco.append(linhas[i]); i += 1
            historia.append(Preformatted("\n".join(bloco), EST["code"]))
        elif l.startswith("|"):
            bloco = []
            while i < len(linhas) and linhas[i].startswith("|"):
                bloco.append(linhas[i]); i += 1
            historia += [tabela(bloco, largura), Spacer(1, 6)]
            continue
        elif l.startswith("### "):
            historia.append(Paragraph(inline(l[4:]), EST["h3"]))
        elif l.startswith("## "):
            historia.append(Paragraph(inline(l[3:]), EST["h2"]))
        elif l.startswith("# "):
            historia.append(Paragraph(inline(l[2:]), EST["h1"]))
        elif l.strip() == "---":
            historia.append(HRFlowable(width="100%", color=colors.HexColor("#c5c9d3"),
                                       spaceBefore=4, spaceAfter=4))
        elif re.match(r"^\s*(- |\d+\. )", l):
            itens, numerada = [], bool(re.match(r"^\s*\d+\. ", l))
            while i < len(linhas) and re.match(r"^\s*(- |\d+\. )", linhas[i]):
                texto = re.sub(r"^\s*(- |\d+\. )", "", linhas[i])
                recuo = len(linhas[i]) - len(linhas[i].lstrip())
                itens.append(ListItem(Paragraph(inline(texto), EST["p"]), leftIndent=12 + recuo * 4))
                i += 1
            historia.append(ListFlowable(itens, bulletType="1" if numerada else "bullet",
                                         bulletFontName=FONTE, bulletFontSize=8, leftIndent=14))
            continue
        elif l.strip():
            paragrafo = [l]
            while (i + 1 < len(linhas) and linhas[i + 1].strip()
                   and not re.match(r"^(#|\||```|---|\s*- |\s*\d+\. )", linhas[i + 1])):
                i += 1; paragrafo.append(linhas[i])
            historia.append(Paragraph(inline(" ".join(paragrafo)), EST["p"]))
        i += 1
    return historia


def rodape(canvas, doc):
    canvas.saveState()
    canvas.setFont(FONTE, 8)
    canvas.setFillColor(colors.grey)
    canvas.drawString(2 * cm, 1.2 * cm, "Escola de Música — Relatório da Etapa 2 — Lab. de Banco de Dados UCB 2026/2")
    canvas.drawRightString(A4[0] - 2 * cm, 1.2 * cm, f"Página {doc.page}")
    canvas.restoreState()


def main():
    doc = SimpleDocTemplate(str(DESTINO), pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm,
                            topMargin=1.8 * cm, bottomMargin=2 * cm,
                            title="Relatório da Etapa 2 — Escola de Música")
    historia = converter(ORIGEM.read_text(encoding="utf-8"), A4[0] - 4 * cm)
    doc.build(historia, onFirstPage=rodape, onLaterPages=rodape)
    print(f"gerado: {DESTINO}")


if __name__ == "__main__":
    main()
