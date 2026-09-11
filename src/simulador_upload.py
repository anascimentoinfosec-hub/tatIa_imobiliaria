import streamlit as st
import pandas as pd
import json
import os
from src.planilha import ler_planilha
from src.utils import converter_para_float
from src.planilha_cache import (
    salvar_planilha_cache,
    carregar_planilha_cache,
    tem_planilha_cache,
    excluir_planilha_cache,
)

ARQUIVO_CONFIG = "dados/construtoras.json"


def obter_tipo_desconto(construtora, CONSTRUTORAS):
    """Sempre busca o tipo_desconto mais atualizado do JSON."""
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
    """
    Renderiza a sidebar de configuração + upload.
    Retorna dict com:
    {
        "construtora": str,
        "produto": str,
        "tipo_desconto": str,
        "config": dict,
        "preco_col": str | None
    }
    ou None se nada foi selecionado.
    """
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

        if perfil in ["gerente", "superadmin"]:
            _renderizar_upload(construtora, produto, produtos)
        else:
            st.info("🔒 As planilhas são gerenciadas pelo gerente.")

        st.markdown("---")
        st.caption(f"Versão 6.3 - Desconto sobre: {tipo_desconto}")

    return {
        "construtora": construtora,
        "produto": produto,
        "tipo_desconto": tipo_desconto,
        "config": produtos[produto],
    }


def _renderizar_upload(construtora, produto, produtos):
    """Bloco de upload da sidebar."""
    st.markdown("### 📤 Upload")
    uploaded_file = st.file_uploader(
        f"Planilha para {construtora} - {produto}",
        type=["xlsx", "xls", "csv"],
        key=f"upload_{construtora}_{produto}",
    )

    if st.button("📥 Carregar", use_container_width=True):
        if uploaded_file is None:
            st.warning("⚠️ Selecione um arquivo primeiro!")
        else:
            try:
                config = produtos[produto]
                df = ler_planilha(uploaded_file, config)
                if df is None:
                    st.error("❌ Erro ao ler a planilha. Verifique o formato e o mapeamento.")
                else:
                    _tratar_colunas_monetarias(df, config)
                    salvar_planilha_cache(construtora, df, produto)
                    st.success(f"✅ Planilha '{produto}' carregada com sucesso!")
            except Exception as e:
                st.error(f"❌ Erro ao carregar a planilha: {str(e)}")

    st.markdown("---")
    if st.button("🗑️ Limpar cache", use_container_width=True):
        excluir_planilha_cache(construtora, produto)
        st.success(f"✅ Cache de '{produto}' removido!")


def _tratar_colunas_monetarias(df, config):
    """Converte colunas monetárias do formato BR para float."""
    colunas_monetarias = ["AVALIAÇÃO", "PREÇO", "VALOR", "DESCONTO", "1ª AVALIAÇÃO OÁSIS II"]
    for col in colunas_monetarias:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace("RS", "", regex=False)
            df[col] = df[col].str.replace("R$", "", regex=False)
            df[col] = df[col].str.replace("R", "", regex=False)
            df[col] = df[col].str.strip()
            df[col] = df[col].str.replace(".", "", regex=False)
            df[col] = df[col].str.replace(",", ".", regex=False)
            df[col] = df[col].str.extract(r"(\d+\.?\d*)")
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    for col in config.get("colunas_para_converter", []):
        if col in df.columns and col not in colunas_monetarias:
            df[col] = df[col].apply(converter_para_float)


def carregar_dataframe(construtora, produto):
    """Carrega o DataFrame do cache ou retorna None."""
    if not tem_planilha_cache(construtora, produto):
        return None
    df = carregar_planilha_cache(construtora, produto)
    if df is None:
        return None
    colunas_monetarias = ["AVALIAÇÃO", "PREÇO", "VALOR", "DESCONTO", "1ª AVALIAÇÃO OÁSIS II"]
    for col in colunas_monetarias:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    return df