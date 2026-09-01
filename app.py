import json
from datetime import datetime

import streamlit as st
import libsql_client

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
# App principal
# ---------------------------------------------------------------------------

INSTRUMENTOS = {
    "Cordas": ["Violino", "Viola", "Violoncelo"],
    "Madeiras": ["Flauta", "Clarinete", "Clarone", "Sax Soprano", "Sax Alto", "Sax Tenor", "Sax Barítono"],
    "Metais": ["Trompete", "Trombone", "Flugelhorn", "Euphonium", "Tuba"],
}

with st.sidebar:
    st.subheader("Registros salvos")
    for row in listar_ensaios():
        _, criado_em, titulo, dados_json, total_geral = row
        with st.expander(f"{titulo} — {total_geral} pessoas"):
            st.caption(criado_em)
            if st.button("Carregar", key=f"load_{row[0]}"):
                st.session_state.form_data = json.loads(dados_json)
                st.rerun()
    st.divider()
    if st.button("Sair"):
        st.session_state.autenticado = False
        st.rerun()

st.title("🎵 Culto de Jovens — Ensaio Local")

dados_salvos = st.session_state.get("form_data", {})

titulo = st.text_input("Título do registro", value=dados_salvos.get("titulo", "Culto de Jovens — Ensaio Local"))

tab_culto, tab_ensaio = st.tabs(["🙏 Culto de Jovens", "🎻 Ensaio"])

# ---------------------------------------------------------------------------
# ABA 1 — CULTO DE JOVENS
# ---------------------------------------------------------------------------
with tab_culto:
    st.header("Cadastro geral")
    c1, c2 = st.columns(2)
    mus_rjm = c1.number_input("Músicos RJM", min_value=0, value=dados_salvos.get("mus_rjm", 0), key="mus_rjm")
    org_rjm = c2.number_input("Organistas RJM", min_value=0, value=dados_salvos.get("org_rjm", 0), key="org_rjm")
    mus_casados = c1.number_input("Músicos Casados", min_value=0, value=dados_salvos.get("mus_casados", 0), key="mus_casados")
    org_casadas = c2.number_input("Organistas Casadas", min_value=0, value=dados_salvos.get("org_casadas", 0), key="org_casadas")

    st.header("Recitativos")
    st.markdown("**Irmãs**")
    c1, c2, c3 = st.columns(3)
    irmas1 = c1.number_input("1ª Fileira", min_value=0, value=dados_salvos.get("irmas1", 0), key="irmas1")
    irmas2 = c2.number_input("2ª Fileira", min_value=0, value=dados_salvos.get("irmas2", 0), key="irmas2")
    irmas3 = c3.number_input("3ª Fileira", min_value=0, value=dados_salvos.get("irmas3", 0), key="irmas3")
    st.markdown("**Irmãos**")
    c1, c2, c3 = st.columns(3)
    irmaos1 = c1.number_input("1ª Fileira", min_value=0, value=dados_salvos.get("irmaos1", 0), key="irmaos1")
    irmaos2 = c2.number_input("2ª Fileira", min_value=0, value=dados_salvos.get("irmaos2", 0), key="irmaos2")
    irmaos3 = c3.number_input("3ª Fileira", min_value=0, value=dados_salvos.get("irmaos3", 0), key="irmaos3")

    # --- Cálculos do balanço do culto ---
    total_musicos_culto = mus_rjm + mus_casados
    total_organistas_culto = org_rjm + org_casadas
    total_recitativo_irmas = irmas1 + irmas2 + irmas3
    total_recitativo_irmaos = irmaos1 + irmaos2 + irmaos3
    total_recitativo = total_recitativo_irmas + total_recitativo_irmaos
    total_geral_culto = total_musicos_culto + total_organistas_culto + total_recitativo

    st.header("Balanço geral — Culto de Jovens")
    c1, c2 = st.columns(2)
    c1.metric("Total de músicos", total_musicos_culto)
    c2.metric("Total de organistas", total_organistas_culto)

    c1, c2, c3 = st.columns(3)
    c1.metric("Recitativo — Irmãs", total_recitativo_irmas)
    c2.metric("Recitativo — Irmãos", total_recitativo_irmaos)
    c3.metric("Total Recitativo", total_recitativo)

    st.metric("Total geral do culto", total_geral_culto)
    st.caption(
        f"{total_musicos_culto} músicos + {total_organistas_culto} organistas + {total_recitativo} recitativos"
    )

# ---------------------------------------------------------------------------
# ABA 2 — ENSAIO
# ---------------------------------------------------------------------------
with tab_ensaio:
    st.header("Instrumentistas")
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
    ens_organistas = c1.number_input("Organistas", min_value=0, value=dados_salvos.get("ens_organistas", 0), key="ens_organistas")
    ens_irmas = c2.number_input("Irmãs", min_value=0, value=dados_salvos.get("ens_irmas", 0), key="ens_irmas")
    ens_irmaos = c3.number_input("Irmãos", min_value=0, value=dados_salvos.get("ens_irmaos", 0), key="ens_irmaos")

    st.header("Percentual de presença esperada")
    pct_musicos = st.slider("Músicos", 0, 100, value=dados_salvos.get("pct_musicos", 100), key="pct_musicos")
    pct_organistas = st.slider("Organistas", 0, 100, value=dados_salvos.get("pct_organistas", 100), key="pct_organistas")

    # --- Cálculos do balanço do ensaio ---
    previa_categoria = {
        cat: round(totais_categoria[cat] * pct_musicos / 100) for cat in INSTRUMENTOS
    }
    total_instrumentistas = sum(totais_categoria.values())
    previa_musicos = sum(previa_categoria.values())
    previa_organistas = round(ens_organistas * pct_organistas / 100)
    total_irmandade_ensaio = ens_irmas + ens_irmaos
    total_geral_ensaio = previa_musicos + previa_organistas + total_irmandade_ensaio

    st.header("Balanço geral — Ensaio")
    st.subheader("Por categoria de instrumento")
    c1, c2, c3 = st.columns(3)
    c1.metric("Cordas", f"{previa_categoria['Cordas']} / {totais_categoria['Cordas']}")
    c2.metric("Madeiras", f"{previa_categoria['Madeiras']} / {totais_categoria['Madeiras']}")
    c3.metric("Metais", f"{previa_categoria['Metais']} / {totais_categoria['Metais']}")
    st.caption("Estimado (com % de presença) / Cadastrado")

    st.subheader("Totais individuais")
    c1, c2, c3 = st.columns(3)
    c1.metric("Total de músicos (estimado)", previa_musicos)
    c2.metric("Total de organistas (estimado)", previa_organistas)
    c3.metric("Irmandade (irmãs + irmãos)", total_irmandade_ensaio)

    st.subheader("Total geral do ensaio")
    st.metric("Músicos + Organistas + Irmandade", total_geral_ensaio)
    st.caption(
        f"{previa_musicos} músicos + {previa_organistas} organistas + {ens_irmas} irmãs + {ens_irmaos} irmãos"
    )

# ---------------------------------------------------------------------------
# Salvar
# ---------------------------------------------------------------------------
st.divider()
if st.button("💾 Salvar este registro", type="primary", use_container_width=True):
    dados = {
        "titulo": titulo,
        # Culto de Jovens
        "mus_rjm": mus_rjm, "org_rjm": org_rjm, "mus_casados": mus_casados, "org_casadas": org_casadas,
        "irmas1": irmas1, "irmas2": irmas2, "irmas3": irmas3,
        "irmaos1": irmaos1, "irmaos2": irmaos2, "irmaos3": irmaos3,
        "total_musicos_culto": total_musicos_culto,
        "total_organistas_culto": total_organistas_culto,
        "total_recitativo": total_recitativo,
        "total_geral_culto": total_geral_culto,
        # Ensaio
        **{f"i_{nome}": v for nome, v in instrumento_valores.items()},
        "ens_organistas": ens_organistas, "ens_irmas": ens_irmas, "ens_irmaos": ens_irmaos,
        "pct_musicos": pct_musicos, "pct_organistas": pct_organistas,
        "previa": previa_categoria,
        "previa_musicos": previa_musicos,
        "previa_organistas": previa_organistas,
        "total_geral_ensaio": total_geral_ensaio,
        # Combinado
        "total_geral": total_geral_culto + total_geral_ensaio,
    }
    salvar_ensaio(titulo, dados, total_geral_culto + total_geral_ensaio)
    st.success("Registro salvo!")
    st.rerun()
