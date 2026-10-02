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


def carregar_todas_planilhas(CONSTRUTORAS):
    """
    Percorre todas as construtoras/produtos com planilha em cache
    e retorna um DataFrame unificado com colunas extras:
    _construtora, _produto, _tipo_desconto
    """
    dfs = []
    resumo = []

    for construtora, dados in CONSTRUTORAS.items():
        tipo_desc = dados.get("tipo_desconto", "AVALIAÇÃO")
        produtos = dados.get("produtos", {})

        for produto, config in produtos.items():
            if not tem_planilha_cache(construtora, produto):
                continue

            df = carregar_planilha_cache(construtora, produto)
            if df is None or df.empty:
                continue

            df = df.copy()
            df["_construtora"] = construtora
            df["_produto"] = produto
            df["_tipo_desconto"] = tipo_desc
            dfs.append(df)
            resumo.append((construtora, produto, len(df)))

    if not dfs:
        return None, []

    df_total = pd.concat(dfs, ignore_index=True)
    return df_total, resumo


def renderizar_sidebar_resumo(CONSTRUTORAS):
    """Mostra na sidebar um resumo das planilhas em cache."""
    df, resumo = carregar_todas_planilhas(CONSTRUTORAS)

    with st.sidebar:
        st.header("📦 Planilhas em cache")

        if not resumo:
            st.warning("⚠️ Nenhuma planilha disponível.")
            st.caption(
                "Vá em **⚙️ Gestão → 🏗️ Construtoras → 📦 Gerenciar Produtos** "
                "para subir planilhas."
            )
        else:
            st.success(f"✅ {len(resumo)} produto(s) • {sum(r[2] for r in resumo)} unidades")

            for construtora, produto, qtd in resumo:
                st.caption(f"• **{construtora}** → {produto} ({qtd})")

    return df, resumo