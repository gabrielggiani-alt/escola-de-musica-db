"""
Monta docs/relatorio-final.pdf, o relatorio consolidado para entrega (item B8):

    capa + sumario  ->  relatorio da Etapa 1  ->  relatorio da Etapa 2

e carimba no canto superior direito de cada pagina a numeracao GERAL do
arquivo ("pag. 12/32"), que e a usada no sumario. As paginas de cada etapa
continuam com o rodape proprio ("Pagina 3 de 20"), porque sao os mesmos
PDFs entregues em cada etapa.

Uso (depois de gerar docs/relatorio-etapa2.pdf):
    pip install reportlab pypdf
    python ferramentas/montar_relatorio_final.py
"""

import io
from pathlib import Path

from pypdf import PdfReader, PdfWriter
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas

from gerar_relatorio_etapa2 import FONTE, NEGRITO  # mesma fonte do relatorio

DOCS = Path(__file__).resolve().parent.parent / "docs"
ETAPA1, ETAPA2 = DOCS / "relatorio-etapa1.pdf", DOCS / "relatorio-etapa2.pdf"
DESTINO = DOCS / "relatorio-final.pdf"

GRUPO = "Group 8"
# mesmos dados da capa da Etapa 1
INTEGRANTES = [
    "Gabriel Gomes Giani — UC21200531",
    "Paulo Henrique Barreto da Rocha Dantas — UC25200677",
    "Letícia Paolino — matrícula não informada",
    "Artur Henrique Caetano — UC25200566",
    "Lucas de Oliveira Faustino — UC25200756",
]

# (titulo, pagina dentro do PDF da propria etapa). Se um relatorio mudar de
# tamanho, conferir estas paginas.
SECOES_ETAPA1 = [
    ("1. Requisitos mínimos de complexidade", 2),
    ("2. A1 — Escopo e regras de negócio", 3),
    ("3. A2 — Modelo Entidade-Relacionamento conceitual", 6),
    ("4. A3 — Dicionário de dados conceitual", 7),
    ("5. A4 — Modelo lógico relacional", 12),
    ("6. A5 — Verificação de normalização", 15),
    ("7. Implementação física, carga e consultas (A6 a A8)", 18),
    ("8. Declaração de uso de inteligência artificial", 20),
]
SECOES_ETAPA2 = [
    ("1. Como reproduzir tudo do zero", 1),
    ("2. B1 — Aplicação com interface", 1),
    ("3. B2 — Camada de acesso a dados", 2),
    ("4. B3 — Transações e controle de concorrência", 2),
    ("5. B4 — Otimização de consultas", 4),
    ("6. B5 — Segurança e controle de acesso", 4),
    ("7. B6 — Gatilhos e auditoria", 6),
    ("8. B7 — Projeto físico e armazenamento", 6),
    ("9. Alterações no modelo desde a Etapa 1", 8),
    ("10. Roteiro da demonstração", 9),
    ("11. Declaração de uso de inteligência artificial", 10),
]
PAGINAS_INICIAIS = 2  # capa + sumario
# A pagina 1 do relatorio da Etapa 1 e a capa dela; a capa geral ja traz os
# mesmos dados, entao ela e omitida no consolidado.
PULAR_ETAPA1 = 1


def capa_e_sumario(ini1, ini2):
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    larg, alt = A4
    azul = colors.HexColor("#26314f")

    # ---- capa
    y = alt - 4 * cm
    for texto, fonte, tam in [
        ("UNIVERSIDADE CATÓLICA DE BRASÍLIA", NEGRITO, 13),
        ("Laboratório de Banco de Dados — GPE17M40083", FONTE, 11),
        ("Prof. Samuel Novais Moura Júnior", FONTE, 11),
    ]:
        c.setFont(fonte, tam); c.drawCentredString(larg / 2, y, texto); y -= 0.7 * cm
    y -= 3 * cm
    c.setFillColor(azul)
    c.setFont(NEGRITO, 22); c.drawCentredString(larg / 2, y, "Projeto Final — Relatório Consolidado"); y -= 1.1 * cm
    c.setFont(FONTE, 14); c.drawCentredString(larg / 2, y, "Escola de Música: do modelo conceitual à aplicação"); y -= 0.8 * cm
    c.setFont(FONTE, 11); c.drawCentredString(larg / 2, y, "Etapa 1 (projeto e construção) + Etapa 2 (operação, interface e desempenho)")
    c.setFillColor(colors.black)
    y -= 3 * cm
    c.setFont(NEGRITO, 12); c.drawCentredString(larg / 2, y, f"Grupo: {GRUPO}"); y -= 1 * cm
    c.setFont(NEGRITO, 11); c.drawCentredString(larg / 2, y, "Integrantes"); y -= 0.6 * cm
    c.setFont(FONTE, 11)
    for nome in INTEGRANTES:
        c.drawCentredString(larg / 2, y, nome); y -= 0.55 * cm
    c.setFont(FONTE, 10)
    c.drawCentredString(larg / 2, 4.5 * cm, "SGBD: MySQL 8 · Aplicação: Python + Flask")
    c.drawCentredString(larg / 2, 3.8 * cm, "Repositório: github.com/gabrielggiani-alt/escola-de-musica-db")
    c.drawCentredString(larg / 2, 2.5 * cm, "Brasília, outubro de 2026")
    c.showPage()

    # ---- sumario
    y = alt - 3 * cm
    c.setFillColor(azul); c.setFont(NEGRITO, 18); c.drawString(2 * cm, y, "Sumário")
    c.setFillColor(colors.black); y -= 1.2 * cm

    def linha(texto, pagina, fonte=FONTE, recuo=0):
        nonlocal y
        c.setFont(fonte, 10.5)
        c.drawString(2 * cm + recuo, y, texto)
        c.drawRightString(larg - 2 * cm, y, str(pagina))
        w = c.stringWidth(texto, fonte, 10.5)
        c.setDash(1, 2); c.setStrokeColor(colors.grey)
        c.line(2 * cm + recuo + w + 4, y + 2, larg - 2 * cm - 18, y + 2)
        c.setDash(); y -= 0.6 * cm

    linha("Parte I — Etapa 1: projeto e construção do banco", ini1, NEGRITO)
    for t, p in SECOES_ETAPA1:
        linha(t, ini1 + p - 1 - PULAR_ETAPA1, recuo=0.6 * cm)
    y -= 0.4 * cm
    linha("Parte II — Etapa 2: operação, interface e desempenho", ini2, NEGRITO)
    for t, p in SECOES_ETAPA2:
        linha(t, ini2 + p - 1, recuo=0.6 * cm)
    y -= 0.6 * cm
    c.setFont(FONTE, 8.5); c.setFillColor(colors.grey)
    c.drawString(2 * cm, y, "Os números deste sumário são a numeração geral do arquivo, carimbada no canto superior direito")
    c.drawString(2 * cm, y - 0.4 * cm, "de cada página. O rodapé de cada parte mantém a numeração do relatório original da etapa.")
    c.save()
    return PdfReader(io.BytesIO(buf.getvalue()))


def carimbo(n, total):
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    c.setFont(FONTE, 8); c.setFillColor(colors.grey)
    c.drawRightString(A4[0] - 1.2 * cm, A4[1] - 0.9 * cm, f"Relatório consolidado — pág. {n}/{total}")
    c.save()
    return PdfReader(io.BytesIO(buf.getvalue())).pages[0]


def main():
    e1, e2 = PdfReader(ETAPA1), PdfReader(ETAPA2)
    ini1 = PAGINAS_INICIAIS + 1
    paginas_e1 = list(e1.pages)[PULAR_ETAPA1:]
    ini2 = ini1 + len(paginas_e1)
    paginas = list(capa_e_sumario(ini1, ini2).pages) + paginas_e1 + list(e2.pages)
    total = len(paginas)
    saida = PdfWriter()
    for n, pagina in enumerate(paginas, start=1):
        if n > 1:  # capa sem numero
            pagina.merge_page(carimbo(n, total))
        saida.add_page(pagina)
    saida.add_metadata({"/Title": "Projeto Final — Relatório Consolidado — Escola de Música"})
    with open(DESTINO, "wb") as f:
        saida.write(f)
    print(f"gerado: {DESTINO} ({total} páginas)")


if __name__ == "__main__":
    main()
