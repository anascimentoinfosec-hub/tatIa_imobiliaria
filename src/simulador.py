import streamlit as st

from src.simulador_upload import renderizar_sidebar, carregar_dataframe
from src.simulador_filtros import (
    renderizar_filtros,
    aplicar_filtros,
    calcular_preco_m2,
    renderizar_tabela,
)
from src.simulador_cliente import renderizar_area_cliente
from src.simulador_cards import renderizar_cards, renderizar_ajuste_global
from src.compartilhar import botoes_compartilhar


def pagina_simulador(CONSTRUTORAS, USUARIOS):
    if not CONSTRUTORAS:
        st.warning("⚠️ Nenhuma construtora cadastrada. Cadastre uma construtora primeiro.")
        return

    st.title("📊 Simulador de Crédito")

    usuario_logado = st.session_state.get("usuario_logado")

    # ---------- 1. Sidebar ----------
    sidebar = renderizar_sidebar(CONSTRUTORAS, USUARIOS)
    if sidebar is None:
        st.warning("⚠️ Selecione um produto para visualizar os dados.")
        return

    construtora = sidebar["construtora"]
    produto = sidebar["produto"]
    tipo_desconto = sidebar["tipo_desconto"]
    config = sidebar["config"]

    # ---------- 2. Dataframe ----------
    df = carregar_dataframe(construtora, produto)
    if df is None:
        st.warning(f"⚠️ Nenhuma planilha disponível para '{produto}'. Faça o upload.")
        return

    st.info(f"📂 Planilha carregada do cache: {construtora} - {produto}")
    st.session_state.df_imoveis = df

    st.markdown("---")

    # ---------- 3. Filtros + Tabela ----------
    filtros = renderizar_filtros(df)
    if filtros is None:
        return

    preco_col = filtros["preco_col"]
    resultado = aplicar_filtros(df, filtros)
    resultado = calcular_preco_m2(resultado, preco_col)
    renderizar_tabela(resultado, config, construtora, produto, tipo_desconto, preco_col)

    st.markdown("---")

    # ---------- 4. Área do Cliente ----------
    renderizar_area_cliente(resultado, tipo_desconto, preco_col, usuario_logado, USUARIOS)

    # ---------- 5. Resultados persistentes ----------
    if st.session_state.get("simulacao_ativa"):
        sim = st.session_state.simulacao_ativa
        st.markdown("---")
        st.markdown("### 📤 Compartilhar Simulação")
        botoes_compartilhar(sim["resumo"], sim["nome_cliente"])
        st.markdown("---")
        renderizar_cards(
            sim["top_recomendacoes"],
            sim["desconto_acordado"],
            sim["tipo_desconto"],
            sim["coluna_base"],
            sim["preco_col"],
            sim["nome_cliente"],
        )

    # ---------- 6. Ajuste global ----------
    renderizar_ajuste_global(df, preco_col)

    st.markdown("---")
    if st.button("💬 Perguntar à BIA (IA Imobiliária)", use_container_width=True):
        st.session_state.pagina = "ChatIA"
        st.rerun()