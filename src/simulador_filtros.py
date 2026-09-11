import streamlit as st
import pandas as pd
from src.utils import formatar_valor_br


def renderizar_filtros(df):
    """
    Renderiza os 4 filtros (tipo, andar, preço, disponibilidade).
    Retorna dict com os valores selecionados e os nomes das colunas detectadas.
    """
    col1, col2, col3, col4 = st.columns(4)

    # --- Tipo ---
    with col1:
        tipo_col = None
        for c in ["TIPOLOGIA", "QUARTOS", "DORMITÓRIOS", "TIPO"]:
            if c in df.columns:
                tipo_col = c
                break
        if tipo_col:
            tipos = ["Todas"] + sorted(df[tipo_col].dropna().unique().tolist())
            tipo_selecionado = st.selectbox("🏠 Tipo", tipos)
        else:
            tipo_selecionado = "Todas"

    # --- Andar ---
    with col2:
        andar_col = None
        for c in ["PAVTO", "ANDAR"]:
            if c in df.columns:
                andar_col = c
                break
        if andar_col:
            andar_min = st.number_input("📌 Andar mínimo", min_value=0, value=0, step=1)
        else:
            andar_min = 0

    # --- Preço ---
    with col3:
        preco_col = None
        for c in ["PREÇO", "VALOR"]:
            if c in df.columns:
                preco_col = c
                break
        if preco_col is None:
            st.error("❌ Nenhuma coluna de preço encontrada.")
            return None
        if not df[preco_col].isna().all():
            preco_max = st.number_input(
                "💰 Preço máximo (R$)",
                min_value=0,
                value=int(df[preco_col].max()) if df[preco_col].max() > 0 else 1000000,
                step=50000,
                format="%d",
            )
        else:
            preco_max = 1000000

    # --- Disponibilidade ---
    with col4:
        status_col = None
        for c in ["DISPONIBILIDADE", "STATUS", "SITUAÇÃO"]:
            if c in df.columns:
                status_col = c
                break
        if status_col:
            status_opcoes = ["Todas"] + sorted(df[status_col].dropna().unique().tolist())
            status_selecionado = st.selectbox("🔑 Disponibilidade", status_opcoes)
        else:
            status_selecionado = "Todas"

    return {
        "tipo_col": tipo_col,
        "tipo_selecionado": tipo_selecionado,
        "andar_col": andar_col,
        "andar_min": andar_min,
        "preco_col": preco_col,
        "preco_max": preco_max,
        "status_col": status_col,
        "status_selecionado": status_selecionado,
    }


def aplicar_filtros(df, filtros):
    """Aplica os filtros no DataFrame e retorna o resultado."""
    resultado = df.copy()

    if filtros["tipo_selecionado"] != "Todas" and filtros["tipo_col"]:
        resultado = resultado[resultado[filtros["tipo_col"]] == filtros["tipo_selecionado"]]

    if filtros["andar_min"] > 0 and filtros["andar_col"]:
        resultado = resultado[resultado[filtros["andar_col"]] >= filtros["andar_min"]]

    if filtros["preco_col"] and filtros["preco_col"] in df.columns:
        resultado = resultado[resultado[filtros["preco_col"]] <= filtros["preco_max"]]

    if filtros["status_selecionado"] != "Todas" and filtros["status_col"]:
        resultado = resultado[resultado[filtros["status_col"]] == filtros["status_selecionado"]]

    return resultado


def calcular_preco_m2(resultado, preco_col):
    """Adiciona coluna R$/m² se possível."""
    if resultado.empty:
        return resultado
    area_col = None
    for c in ["M²", "AREA_M2", "AREA"]:
        if c in resultado.columns:
            area_col = c
            break
    if preco_col and area_col:
        resultado["R$/m²"] = (resultado[preco_col] / resultado[area_col]).round(2)
    return resultado


def renderizar_tabela(resultado, config, construtora, produto, tipo_desconto, preco_col):
    """Renderiza o cabeçalho + tabela de resultados."""
    colunas_ordem = config.get("colunas_ordem", list(resultado.columns)).copy()
    if "R$/m²" in resultado.columns:
        colunas_ordem.append("R$/m²")
    colunas_ordem = [c for c in colunas_ordem if c in resultado.columns]

    st.subheader(f"🔍 Resultados: {len(resultado)} imóveis encontrados")
    st.caption(f"📌 {construtora} - {produto}  |  💡 Desconto sobre: {tipo_desconto}")

    if resultado.empty:
        return

    if "R$/m²" in resultado.columns:
        resultado_ordenado = resultado.sort_values("R$/m²")
    else:
        resultado_ordenado = resultado

    df_exibicao = resultado_ordenado.copy()
    for col in ["PREÇO", "VALOR", "AVALIAÇÃO", "DESCONTO", "1ª AVALIAÇÃO OÁSIS II", "R$/m²"]:
        if col in df_exibicao.columns:
            df_exibicao[col] = df_exibicao[col].apply(formatar_valor_br)
    if "M²" in df_exibicao.columns:
        df_exibicao["M²"] = df_exibicao["M²"].apply(
            lambda x: f"{x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") if not pd.isna(x) else ""
        )

    st.dataframe(df_exibicao[colunas_ordem], use_container_width=True, height=400)