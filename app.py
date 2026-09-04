import json

import streamlit as st

from database import salvar_ensaio, atualizar_ensaio, listar_ensaios, excluir_ensaio
from pdf import gerar_pdf

st.set_page_config(page_title="Culto de Jovens — Ensaio Local", page_icon="🎵", layout="centered")

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

CORES_CATEGORIA = {
    "Cordas": "#5C7A63",
    "Madeiras": "#B8860B",
    "Metais": "#B5551A",
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
                st.session_state.editando_id = id_
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

if st.session_state.get("editando_id"):
    c1, c2 = st.columns([4, 1])
    c1.info(f"Editando um ensaio salvo (id {st.session_state.editando_id}). Salvar vai atualizar esse mesmo registro.")
    if c2.button("Novo", use_container_width=True):
        del st.session_state.editando_id
        st.session_state.form_data = {}
        st.rerun()

dados_salvos = st.session_state.get("form_data", {})

titulo = st.text_input("Título do programa", value=dados_salvos.get("titulo", "Culto de Jovens — Ensaio Local"))

aba_culto, aba_ensaio = st.tabs(["Culto de Jovens", "Ensaio"])

with aba_culto:
    st.header("Músicos e Organistas")
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
    st.header("Encarregados")
    st.caption("Quem vai reger e a localidade de cada um.")
    encarregados_nomes = []
    encarregados_locais = []
    for i in (1, 2, 3):
        c1, c2 = st.columns(2)
        nome = c1.text_input(f"Nome {i}", value=dados_salvos.get(f"encarregado{i}_nome", ""), key=f"encarregado{i}_nome", placeholder="Nome do encarregado")
        local = c2.text_input(f"Localidade {i}", value=dados_salvos.get(f"encarregado{i}_local", ""), key=f"encarregado{i}_local", placeholder="Localidade")
        encarregados_nomes.append(nome)
        encarregados_locais.append(local)

    st.header("Músicos")
    instrumento_valores = {}
    totais_categoria = {}
    for categoria, lista in INSTRUMENTOS.items():
        cor = CORES_CATEGORIA[categoria]
        st.markdown(
            f"<div style='background:{cor};color:white;padding:6px 12px;"
            f"border-radius:4px;font-weight:600;margin:10px 0 6px;'>{categoria}</div>",
            unsafe_allow_html=True,
        )
        cols = st.columns(len(lista))
        soma = 0
        for col, nome in zip(cols, lista):
            chave = f"i_{nome}"
            v = col.number_input(nome, min_value=0, value=dados_salvos.get(chave, 0), key=chave)
            instrumento_valores[nome] = v
            soma += v
        totais_categoria[categoria] = soma
        st.markdown(
            f"<span style='color:{cor};font-weight:600;'>Total {categoria.lower()}: {soma}</span>",
            unsafe_allow_html=True,
        )

    st.header("Organistas e Irmandade")
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
    **{f"encarregado{i}_nome": n for i, n in enumerate(encarregados_nomes, start=1)},
    **{f"encarregado{i}_local": l for i, l in enumerate(encarregados_locais, start=1)},
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


def salvar_ou_atualizar():
    editando_id = st.session_state.get("editando_id")
    if editando_id:
        atualizar_ensaio(editando_id, titulo, dados, total_geral)
        st.success("Atualizado!")
    else:
        novo_id = salvar_ensaio(titulo, dados, total_geral)
        st.session_state.editando_id = novo_id
        st.success("Salvo!")


rotulo_botao = "Atualizar" if st.session_state.get("editando_id") else "Salvar"

with culto_actions.container():
    if st.button(f"{rotulo_botao} Culto de Jovens", type="primary", use_container_width=True, key="salvar_culto"):
        salvar_ou_atualizar()
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
    if st.button(f"{rotulo_botao} Ensaio", type="primary", use_container_width=True, key="salvar_ensaio"):
        salvar_ou_atualizar()
        st.rerun()
    st.download_button(
        "Salvar em PDF",
        data=pdf_bytes_ensaio,
        file_name=f"{titulo} - Ensaio.pdf",
        mime="application/pdf",
        use_container_width=True,

        key="pdf_ensaio",
    )
