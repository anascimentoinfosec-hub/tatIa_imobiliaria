import streamlit as st
import pandas as pd
import json
import os
from src.planilha_cache import carregar_planilha_cache, tem_planilha_cache

ARQUIVO_CONFIG = "dados/construtoras.json"


def obter_tipo_desconto(construtora, CONSTRUTORAS):
    try:
        if os.path.exists(ARQUIVO_CONFIG):
            with open(ARQUIVO_CONFIG, "r", encoding="utf-8") as f:
                dados = json.load(f)
                if construtora in dados:
                    return dados[construtora].get("tipo_desconto", "AVALIAÇÃO")
    except Exception:
        pass
    return CONSTRUTORAS.get(construtora, {}).get("tipo_desconto", "AVALIAÇÃO")


def renderizar_sidebar(CONSTRUTORAS, USUARIOS):
    """Sidebar simplificada: só seleção de construtora + produto."""
    usuario_logado = st.session_state.get("usuario_logado")
    perfil = "corretor"
    if usuario_logado and usuario_logado in USUARIOS:
        perfil = USUARIOS[usuario_logado].get("perfil", "corretor")

    with st.sidebar:
        st.header("⚙️ Configurações")
        construtora = st.selectbox("🏗️ Selecione a construtora", options=list(CONSTRUTORAS.keys()))
        tipo_desconto = obter_tipo_desconto(construtora, CONSTRUTORAS)

        produtos = CONSTRUTORAS[construtora].get("produtos", {})
        produtos_lista = list(produtos.keys())
        if produtos_lista:
            produto = st.selectbox("📦 Selecione o produto", options=produtos_lista)
        else:
            st.warning("⚠️ Nenhum produto cadastrado para esta construtora.")
            return None

        st.markdown("---")
        st.caption(f"Versão 6.4 - Desconto sobre: {tipo_desconto}")

        # Verifica se há planilha no cache
        if tem_planilha_cache(construtora, produto):
            st.success("✅ Planilha disponível")
        else:
            st.warning("⚠️ Sem planilha no cache")
            if perfil in ["gerente", "superadmin"]:
                st.caption(
                    "Vá em **⚙️ Gestão → 🏗️ Construtoras → 📦 Gerenciar Produtos** "
                    "para subir a planilha."
                )
            else:
                st.caption("Peça ao gerente para subir a planilha.")

    return {
        "construtora": construtora,
        "produto": produto,
        "tipo_desconto": tipo_desconto,
        "config": produtos[produto],
    }


def carregar_dataframe(construtora, produto):
    if not tem_planilha_cache(construtora, produto):
        return None
    df = carregar_planilha_cache(construtora, produto)
    if df is None:
        return None
    colunas_monetarias = ["AVALIAÇÃO", "PREÇO", "VALOR", "DESCONTO"]
    for col in colunas_monetarias:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    return df