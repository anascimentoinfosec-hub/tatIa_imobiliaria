import streamlit as st

from src.construtoras_storage import carregar_cidades
from src.construtoras_listar import renderizar_aba_listar
from src.construtoras_adicionar import renderizar_aba_adicionar
from src.construtoras_produtos import renderizar_aba_produtos
from src.construtoras_cidades import renderizar_aba_cidades


def pagina_gestao_construtoras(CONSTRUTORAS):
    st.title("🏗️ Gestão de Construtoras e Produtos")

    cidades = carregar_cidades()
    tabs = st.tabs([
        "📋 Listar",
        "➕ Adicionar Construtora",
        "📦 Gerenciar Produtos",
        "📍 Gerenciar Cidades",
    ])

    with tabs[0]:
        renderizar_aba_listar(CONSTRUTORAS)

    with tabs[1]:
        renderizar_aba_adicionar(CONSTRUTORAS, cidades)

    with tabs[2]:
        renderizar_aba_produtos(cidades)

    with tabs[3]:
        renderizar_aba_cidades()