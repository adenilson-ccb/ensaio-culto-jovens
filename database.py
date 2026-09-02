"""Conexão com o Turso e operações de leitura/escrita dos ensaios salvos."""
import json
from datetime import datetime

import streamlit as st
import libsql_client


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
