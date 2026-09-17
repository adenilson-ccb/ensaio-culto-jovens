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

    tem_encarregado = any(dados.get(f"encarregado{i}_nome") for i in (1, 2, 3))
    if tem_encarregado:
        elements.append(Paragraph("Encarregados", styles["Heading3"]))
        tabela_encarregados = [["Nome", "Localidade"]]
        for i in (1, 2, 3):
            nome = dados.get(f"encarregado{i}_nome", "")
            if nome:
                tabela_encarregados.append([nome, dados.get(f"encarregado{i}_local", "") or "—"])
        t = Table(tabela_encarregados, colWidths=[6.5 * cm, 6.5 * cm])
        t.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("BACKGROUND", (0, 0), (-1, 0), colors.whitesmoke),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
        ]))
        elements.append(t)
        elements.append(Spacer(1, 12))

    elements.append(Paragraph("Músicos e Organistas", styles["Heading3"]))
    instrumentos = sorted(
        ((chave[2:], valor) for chave, valor in dados.items() if chave.startswith("i_") and valor > 0),
        key=lambda item: item[0],
    )
    total_musicos = sum(valor for _, valor in instrumentos)
    total_organistas = dados.get("ens_organistas", 0)
    total_geral_musicos_organistas = total_musicos + total_organistas

    tabela_instrumentos = [["Instrumento", "Quantidade"]]
    for nome, valor in instrumentos:
        tabela_instrumentos.append([nome, valor])
    tabela_instrumentos.append(["Sub Total (músicos)", total_musicos])
    tabela_instrumentos.append(["Organistas (Órgão)", total_organistas])
    tabela_instrumentos.append(["TOTAL GERAL", total_geral_musicos_organistas])

    n_linhas = len(tabela_instrumentos)
    t = Table(tabela_instrumentos, colWidths=[9 * cm, 4 * cm])
    t.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BACKGROUND", (0, 0), (-1, 0), colors.whitesmoke),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("FONTNAME", (0, n_linhas - 3), (-1, -1), "Helvetica-Bold"),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 14))

    elements.append(Paragraph("Composição dos participantes", styles["Heading3"]))
    metas = {"Cordas": 50, "Madeiras": 25, "Metais": 25}
    tabela_composicao = [["Categoria", "Cadastrados", "% atual", "Meta CCB"]]
    for cat in ["Cordas", "Madeiras", "Metais"]:
        qtd_cat = dados["totais_categoria"].get(cat, 0)
        pct_atual = round(qtd_cat / total_musicos * 100) if total_musicos else 0
        tabela_composicao.append([cat, qtd_cat, f"{pct_atual}%", f"{metas[cat]}%"])
    t = Table(tabela_composicao, colWidths=[4 * cm, 3 * cm, 3 * cm, 3 * cm])
    t.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BACKGROUND", (0, 0), (-1, 0), colors.whitesmoke),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 14))

    if dados.get("hinos_ensaiados"):
        elements.append(Paragraph("Hinos ensaiados", styles["Heading3"]))
        for linha in dados["hinos_ensaiados"].splitlines():
            if linha.strip():
                elements.append(Paragraph(linha.strip(), styles["Normal"]))
        elements.append(Spacer(1, 14))

    elements.append(Paragraph("Resumo geral", styles["Heading3"]))
    total_irmandade = dados.get("ens_irmaos", 0) + dados.get("ens_irmas", 0)
    tabela_resumo = [
        ["Quant. Músicos", total_musicos],
        ["Quant. Organistas", total_organistas],
        ["TOTAL GERAL", total_geral_musicos_organistas],
        ["Irmãos", dados.get("ens_irmaos", 0)],
        ["Irmãs", dados.get("ens_irmas", 0)],
        ["TOTAL irmandade", total_irmandade],
        ["Total geral", total_geral_musicos_organistas + total_irmandade],
    ]
    t = Table(tabela_resumo, colWidths=[9 * cm, 4 * cm])
    t.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("FONTNAME", (0, 2), (-1, 2), "Helvetica-Bold"),
        ("FONTNAME", (0, 5), (-1, 6), "Helvetica-Bold"),
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
