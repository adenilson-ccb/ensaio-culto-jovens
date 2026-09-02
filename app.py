import hashlib
import io
import json
from datetime import datetime

import streamlit as st
import libsql_client

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

st.set_page_config(page_title="Culto de Jovens — Ensaio Local", page_icon="🎵", layout="centered")

# ---------------------------------------------------------------------------
# Conexão com o Turso
# ---------------------------------------------------------------------------

@st.cache_resource
def get_client():
    client = libsql_client.create_client_sync(
        url=st.secrets["TURSO_DATABASE_URL"],
        auth_token=st.secrets["TURSO_AUTH_TOKEN"],
    )
    client.execute(
        """
        CREATE TABLE IF NOT EXISTS ensaios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            criado_em TEXT NOT NULL,
            titulo TEXT NOT NULL,
            dados TEXT NOT NULL,
            total_geral INTEGER NOT NULL
        )
        """
    )
    return client


def salvar_ensaio(titulo: str, dados: dict, total_geral: int):
    client = get_client()
    client.execute(
        "INSERT INTO ensaios (criado_em, titulo, dados, total_geral) VALUES (?, ?, ?, ?)",
        [datetime.now().isoformat(timespec="seconds"), titulo, json.dumps(dados), total_geral],
    )


def listar_ensaios(limite: int = 15):
    client = get_client()
    rs = client.execute(
        "SELECT id, criado_em, titulo, dados, total_geral FROM ensaios ORDER BY id DESC LIMIT ?",
        [limite],
    )
    return rs.rows


def excluir_ensaio(id_: int):
    client = get_client()
    client.execute("DELETE FROM ensaios WHERE id = ?", [id_])


# ---------------------------------------------------------------------------
# Login por senha única
# ---------------------------------------------------------------------------

def tela_login():
    st.title("🎵 Culto de Jovens — Ensaio Local")
    st.caption("Acesso restrito aos responsáveis pelo ensaio.")
    with st.form("login_form"):
        senha = st.text_input("Senha", type="password")
        entrar = st.form_submit_button("Entrar", use_container_width=True)
    if entrar:
        if senha == st.secrets["APP_PASSWORD"]:
            st.session_state.autenticado = True
            st.rerun()
        else:
            st.error("Senha incorreta.")


if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    tela_login()
    st.stop()

# ---------------------------------------------------------------------------
# Geração do PDF
# ---------------------------------------------------------------------------

def gerar_pdf(dados: dict, secao: str = "completo") -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=1.5 * cm, bottomMargin=1.5 * cm)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph(dados["titulo"], styles["Title"]))
    elements.append(Spacer(1, 10))

    if secao in ("completo", "culto"):
        elements.append(Paragraph("Culto de Jovens", styles["Heading2"]))
        elements.append(Paragraph("Cadastro geral", styles["Heading3"]))
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

    if secao in ("completo", "ensaio"):
        elements.append(Paragraph("Ensaio", styles["Heading2"]))
        elements.append(Paragraph("Instrumentistas", styles["Heading3"]))
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

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()


# ---------------------------------------------------------------------------
# App principal
# ---------------------------------------------------------------------------

INSTRUMENTOS = {
    "Cordas": ["Violino", "Viola", "Violoncelo"],
    "Madeiras": ["Flauta", "Clarinete", "Clarone", "Sax Soprano", "Sax Alto", "Sax Tenor", "Sax Barítono"],
    "Metais": ["Trompete", "Trombone", "Flugelhorn", "Euphonium", "Tuba"],
}

with st.sidebar:
    st.subheader("Ensaios salvos")
    for row in listar_ensaios():
        id_, criado_em, titulo_salvo, dados_json, total_geral_salvo = row
        with st.expander(f"{titulo_salvo} — {total_geral_salvo} pessoas"):
            st.caption(criado_em)
            c1, c2 = st.columns(2)
            if c1.button("Carregar", key=f"load_{id_}", use_container_width=True):
                st.session_state.form_data = json.loads(dados_json)
                st.rerun()
            if c2.button("Excluir", key=f"del_{id_}", use_container_width=True):
                st.session_state[f"confirmar_exclusao_{id_}"] = True
            if st.session_state.get(f"confirmar_exclusao_{id_}"):
                st.warning("Excluir esse registro? Não tem como desfazer.")
                cc1, cc2 = st.columns(2)
                if cc1.button("Sim, excluir", key=f"confirma_del_{id_}", use_container_width=True):
                    excluir_ensaio(id_)
                    del st.session_state[f"confirmar_exclusao_{id_}"]
                    st.rerun()
                if cc2.button("Cancelar", key=f"cancela_del_{id_}", use_container_width=True):
                    del st.session_state[f"confirmar_exclusao_{id_}"]
                    st.rerun()
    st.divider()
    if st.button("Sair"):
        st.session_state.autenticado = False
        st.rerun()

st.title("🎵 Culto de Jovens — Ensaio Local")

dados_salvos = st.session_state.get("form_data", {})

titulo = st.text_input("Título do programa", value=dados_salvos.get("titulo", "Culto de Jovens — Ensaio Local"))

aba_culto, aba_ensaio = st.tabs(["Culto de Jovens", "Ensaio"])

with aba_culto:
    st.header("Cadastro geral")
    c1, c2 = st.columns(2)
    mus_rjm = c1.number_input("Músicos RJM", min_value=0, value=dados_salvos.get("mus_rjm", 0))
    org_rjm = c2.number_input("Organistas RJM", min_value=0, value=dados_salvos.get("org_rjm", 0))
    mus_casados = c1.number_input("Músicos Casados", min_value=0, value=dados_salvos.get("mus_casados", 0))
    org_casadas = c2.number_input("Organistas Casadas", min_value=0, value=dados_salvos.get("org_casadas", 0))
    st.caption(f"Total no cadastro: {mus_rjm + org_rjm + mus_casados + org_casadas}")

    st.header("Recitativos")
    st.caption("Quantidade por fileira e o recitativo previsto para o próximo domingo.")

    st.markdown("**Irmãs**")
    c1, c2 = st.columns([1, 2])
    irmas1 = c1.number_input("1ª Fileira", min_value=0, value=dados_salvos.get("irmas1", 0), key="irmas1")
    irmas1_texto = c2.text_input("Recitativo", value=dados_salvos.get("irmas1_texto", ""), key="irmas1_texto", placeholder="Ex: Provérbios cap. 10")
    c1, c2 = st.columns([1, 2])
    irmas2 = c1.number_input("2ª Fileira", min_value=0, value=dados_salvos.get("irmas2", 0), key="irmas2")
    irmas2_texto = c2.text_input("Recitativo", value=dados_salvos.get("irmas2_texto", ""), key="irmas2_texto", placeholder="Ex: Provérbios cap. 10")
    c1, c2 = st.columns([1, 2])
    irmas3 = c1.number_input("3ª Fileira", min_value=0, value=dados_salvos.get("irmas3", 0), key="irmas3")
    irmas3_texto = c2.text_input("Recitativo", value=dados_salvos.get("irmas3_texto", ""), key="irmas3_texto", placeholder="Ex: Provérbios cap. 10")

    st.markdown("**Irmãos**")
    c1, c2 = st.columns([1, 2])
    irmaos1 = c1.number_input("1ª Fileira", min_value=0, value=dados_salvos.get("irmaos1", 0), key="irmaos1")
    irmaos1_texto = c2.text_input("Recitativo", value=dados_salvos.get("irmaos1_texto", ""), key="irmaos1_texto", placeholder="Ex: Provérbios cap. 10")
    c1, c2 = st.columns([1, 2])
    irmaos2 = c1.number_input("2ª Fileira", min_value=0, value=dados_salvos.get("irmaos2", 0), key="irmaos2")
    irmaos2_texto = c2.text_input("Recitativo", value=dados_salvos.get("irmaos2_texto", ""), key="irmaos2_texto", placeholder="Ex: Provérbios cap. 10")
    c1, c2 = st.columns([1, 2])
    irmaos3 = c1.number_input("3ª Fileira", min_value=0, value=dados_salvos.get("irmaos3", 0), key="irmaos3")
    irmaos3_texto = c2.text_input("Recitativo", value=dados_salvos.get("irmaos3_texto", ""), key="irmaos3_texto", placeholder="Ex: Provérbios cap. 10")

    st.caption(f"Total de recitativos: {irmas1 + irmas2 + irmas3 + irmaos1 + irmaos2 + irmaos3}")

    st.markdown("**Recitativos Avulsos**")
    avulsos_ativo = st.checkbox("Adicionar recitativos avulsos", value=dados_salvos.get("avulsos_ativo", False))
    if avulsos_ativo:
        qtd_avulsos = st.number_input(
            "Quantidade de recitativos avulsos", min_value=0,
            value=dados_salvos.get("qtd_avulsos", 1), key="qtd_avulsos",
        )
    else:
        qtd_avulsos = 0

    st.divider()
    culto_actions = st.empty()

with aba_ensaio:
    st.header("Ensaio — instrumentistas")
    instrumento_valores = {}
    totais_categoria = {}
    for categoria, lista in INSTRUMENTOS.items():
        st.markdown(f"**{categoria}**")
        cols = st.columns(len(lista))
        soma = 0
        for col, nome in zip(cols, lista):
            chave = f"i_{nome}"
            v = col.number_input(nome, min_value=0, value=dados_salvos.get(chave, 0), key=chave)
            instrumento_valores[nome] = v
            soma += v
        totais_categoria[categoria] = soma
        st.caption(f"Total {categoria.lower()}: {soma}")

    st.header("Organistas e congregação no ensaio")
    c1, c2, c3 = st.columns(3)
    ens_organistas = c1.number_input("Organistas", min_value=0, value=dados_salvos.get("ens_organistas", 0))
    ens_irmas = c2.number_input("Irmãs", min_value=0, value=dados_salvos.get("ens_irmas", 0))
    ens_irmaos = c3.number_input("Irmãos", min_value=0, value=dados_salvos.get("ens_irmaos", 0))

    st.header("Percentual de presença esperada")
    pct_musicos = st.slider("Músicos", 0, 100, value=dados_salvos.get("pct_musicos", 100))
    pct_organistas = st.slider("Organistas", 0, 100, value=dados_salvos.get("pct_organistas", 100))

    previa_categoria = {
        cat: round(totais_categoria[cat] * pct_musicos / 100) for cat in INSTRUMENTOS
    }
    previa_musicos = sum(previa_categoria.values())
    previa_organistas = round(ens_organistas * pct_organistas / 100)
    total_geral = previa_musicos + previa_organistas + ens_irmas + ens_irmaos

    st.header("Prévia do ensaio")
    c1, c2, c3 = st.columns(3)
    c1.metric("Cordas", previa_categoria["Cordas"])
    c2.metric("Madeiras", previa_categoria["Madeiras"])
    c3.metric("Metais", previa_categoria["Metais"])

    c1, c2 = st.columns(2)
    c1.metric("Total de músicos (estimado)", previa_musicos)
    c2.metric("Total de organistas (estimado)", previa_organistas)

    st.metric("Total geral do ensaio", total_geral)
    st.caption(
        f"{previa_musicos} músicos + {previa_organistas} organistas + {ens_irmas} irmãs + {ens_irmaos} irmãos"
    )

    st.divider()
    ensaio_actions = st.empty()

# ---------------------------------------------------------------------------
# Ações — salvar no Turso e exportar PDF
# ---------------------------------------------------------------------------

dados = {
    "titulo": titulo,
    "mus_rjm": mus_rjm, "org_rjm": org_rjm, "mus_casados": mus_casados, "org_casadas": org_casadas,
    "irmas1": irmas1, "irmas2": irmas2, "irmas3": irmas3,
    "irmas1_texto": irmas1_texto, "irmas2_texto": irmas2_texto, "irmas3_texto": irmas3_texto,
    "irmaos1": irmaos1, "irmaos2": irmaos2, "irmaos3": irmaos3,
    "irmaos1_texto": irmaos1_texto, "irmaos2_texto": irmaos2_texto, "irmaos3_texto": irmaos3_texto,
    "avulsos_ativo": avulsos_ativo, "qtd_avulsos": int(qtd_avulsos),
    "ens_organistas": ens_organistas, "ens_irmas": ens_irmas, "ens_irmaos": ens_irmaos,
    "pct_musicos": pct_musicos, "pct_organistas": pct_organistas,
    **{f"i_{nome}": v for nome, v in instrumento_valores.items()},
    "totais_categoria": totais_categoria,
    "previa": previa_categoria,
    "previa_musicos": previa_musicos,
    "previa_organistas": previa_organistas,
    "total_geral": total_geral,
}

pdf_bytes_culto = gerar_pdf(dados, secao="culto")
pdf_bytes_ensaio = gerar_pdf(dados, secao="ensaio")

with culto_actions.container():
    if st.button("Salvar Culto de Jovens", type="primary", use_container_width=True, key="salvar_culto"):
        salvar_ensaio(titulo, dados, total_geral)
        st.success("Salvo!")
        st.rerun()
    st.download_button(
        "Salvar em PDF",
        data=pdf_bytes_culto,
        file_name=f"{titulo} - Culto de Jovens.pdf",
        mime="application/pdf",
        use_container_width=True,
        key="pdf_culto",
    )

with ensaio_actions.container():
    if st.button("Salvar Ensaio", type="primary", use_container_width=True, key="salvar_ensaio"):
        salvar_ensaio(titulo, dados, total_geral)
        st.success("Salvo!")
        st.rerun()
    st.download_button(
        "Salvar em PDF",
        data=pdf_bytes_ensaio,
        file_name=f"{titulo} - Ensaio.pdf",
        mime="application/pdf",
        use_container_width=True,
        key="pdf_ensaio",
    )
