"""Geração do PDF do programa (Culto de Jovens e/ou Ensaio)."""
import hashlib
import io

# Corrige incompatibilidade do reportlab com hashlib.md5 em alguns Windows/Python
_md5_original = hashlib.md5
try:
    _md5_original(usedforsecurity=False)
except TypeError:
    def _md5_compativel(*args, **kwargs):
        kwargs.pop("usedforsecurity", None)
        return _md5_original(*args, **kwargs)
    hashlib.md5 = _md5_compativel

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle


def _tabela_culto(dados, elements, styles):
    elements.append(Paragraph("Culto de Jovens", styles["Heading2"]))
    elements.append(Paragraph("Músicos e Organistas", styles["Heading3"]))
    total_cadastro = dados["mus_rjm"] + dados["org_rjm"] + dados["mus_casados"] + dados["org_casadas"]
    tabela_cadastro = [
        ["Músicos RJM", dados["mus_rjm"], "Organistas RJM", dados["org_rjm"]],
        ["Músicos Casados", dados["mus_casados"], "Organistas Casadas", dados["org_casadas"]],
        ["Total", "", "", total_cadastro],
    ]
    t = Table(tabela_cadastro, colWidths=[4.5 * cm, 2 * cm, 4.5 * cm, 2 * cm])
    t.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 10))

    elements.append(Paragraph("Recitativos", styles["Heading3"]))
    total_recitativos = 0
    tabela_recitativos = [["Fileira", "Qtd.", "Recitativo"]]
    for label, prefixo in [("Irmãs", "irmas"), ("Irmãos", "irmaos")]:
        for i in (1, 2, 3):
            qtd = dados.get(f"{prefixo}{i}", 0)
            total_recitativos += qtd
            tabela_recitativos.append([
                f"{label} — {i}ª Fileira",
                qtd,
                dados.get(f"{prefixo}{i}_texto", "") or "—",
            ])
    if dados.get("avulsos_ativo") and dados.get("qtd_avulsos", 0) > 0:
        tabela_recitativos.append(["Recitativos Avulsos", dados.get("qtd_avulsos", 0), ""])
    tabela_recitativos.append(["Total", total_recitativos, ""])
    t = Table(tabela_recitativos, colWidths=[4.5 * cm, 1.5 * cm, 7 * cm])
    t.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BACKGROUND", (0, 0), (-1, 0), colors.whitesmoke),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 16))


def _tabela_ensaio(dados, elements, styles):
    elements.append(Paragraph("Ensaio", styles["Heading2"]))
    elements.append(Paragraph("Músicos", styles["Heading3"]))
    tabela_instrumentos = [["Categoria", "Cadastrados", "Prévia estimada"]]
    for cat in ["Cordas", "Madeiras", "Metais"]:
        tabela_instrumentos.append([cat, dados["totais_categoria"][cat], dados["previa"][cat]])
    t = Table(tabela_instrumentos, colWidths=[4.5 * cm, 4.5 * cm, 4.5 * cm])
    t.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BACKGROUND", (0, 0), (-1, 0), colors.whitesmoke),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 10))

    elements.append(Paragraph("Prévia geral", styles["Heading3"]))
    tabela_previa = [
        ["Total de músicos (estimado)", dados["previa_musicos"]],
        ["Total de organistas (estimado)", dados["previa_organistas"]],
        ["Irmãs no ensaio", dados["ens_irmas"]],
        ["Irmãos no ensaio", dados["ens_irmaos"]],
        ["Total geral do ensaio", dados["total_geral"]],
    ]
    t = Table(tabela_previa, colWidths=[9 * cm, 4 * cm])
    t.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
    ]))
    elements.append(t)


def gerar_pdf(dados: dict, secao: str = "completo") -> bytes:
    """Gera o PDF do programa. secao: 'completo', 'culto' ou 'ensaio'."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=1.5 * cm, bottomMargin=1.5 * cm)
    styles = getSampleStyleSheet()
    elements = [Paragraph(dados["titulo"], styles["Title"]), Spacer(1, 10)]

    if secao in ("completo", "culto"):
        _tabela_culto(dados, elements, styles)
    if secao in ("completo", "ensaio"):
        _tabela_ensaio(dados, elements, styles)

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()
