import streamlit as st
from src.construtoras_storage import carregar_cidades
from src.compartilhar import gerar_resumo


def renderizar_area_cliente(resultado, tipo_desconto, preco_col, usuario_logado, USUARIOS):
    """
    Renderiza a área do cliente (inputs + botão Analisar).
    Se o botão for clicado, roda a análise e salva em st.session_state.simulacao_ativa.
    """
    st.subheader("🧑 Área do Cliente")
    st.markdown("Preencha os dados abaixo para receber recomendações personalizadas.")

    with st.container():
        col1, col2 = st.columns(2)

        with col1:
            nome_cliente = st.text_input("Nome do Cliente", placeholder="Ex: João Silva", key="cliente_nome")
            renda_cliente = st.number_input(
                "💰 Renda líquida mensal (R$)",
                min_value=0.0, value=5000.0, step=500.0, format="%.2f",
                key="cliente_renda",
            )
            entrada_cliente = st.number_input(
                "🏦 Valor disponível para entrada (R$)",
                min_value=0.0, value=100000.0, step=10000.0, format="%.2f",
                key="cliente_entrada",
            )

        with col2:
            cidades_disponiveis = carregar_cidades()
            bairro_preferencia = st.selectbox(
                "📍 Bairro de preferência", [""] + cidades_disponiveis, key="cliente_bairro"
            )
            quartos_preferencia = st.selectbox(
                "🛏️ Quantos quartos?", ["Indiferente", "1", "2", "3", "4+"], key="cliente_quartos"
            )
            tipo_preferencia = st.selectbox(
                "🏠 Tipo de imóvel", ["Indiferente", "Apartamento", "Cobertura", "Garden"], key="cliente_tipo"
            )
            desconto_acordado = st.number_input(
                "💸 Desconto acordado (R$)",
                min_value=0.0, value=0.0, step=1000.0, format="%.2f",
                help=f"Desconto será aplicado sobre: {tipo_desconto}",
                key="cliente_desconto",
            )

        if st.button("🔍 Analisar Oportunidades", use_container_width=True):
            if not nome_cliente:
                st.warning("⚠️ Por favor, informe o nome do cliente.")
                return

            with st.spinner("Analisando oportunidades..."):
                try:
                    dados_simulacao = _analisar(
                        resultado=resultado,
                        nome_cliente=nome_cliente,
                        renda_cliente=renda_cliente,
                        entrada_cliente=entrada_cliente,
                        bairro_preferencia=bairro_preferencia,
                        quartos_preferencia=quartos_preferencia,
                        tipo_preferencia=tipo_preferencia,
                        desconto_acordado=desconto_acordado,
                        tipo_desconto=tipo_desconto,
                        preco_col=preco_col,
                        usuario_logado=usuario_logado,
                        USUARIOS=USUARIOS,
                    )
                    st.session_state.simulacao_ativa = dados_simulacao
                except Exception as e:
                    st.error(f"❌ Erro ao analisar oportunidades: {str(e)}")


def _analisar(resultado, nome_cliente, renda_cliente, entrada_cliente,
              bairro_preferencia, quartos_preferencia, tipo_preferencia,
              desconto_acordado, tipo_desconto, preco_col, usuario_logado, USUARIOS):
    """Lógica pura de análise. Retorna dict pronto para o session_state."""
    df_filtrado = resultado.copy()

    # Filtro por quartos
    if quartos_preferencia != "Indiferente":
        qtd = int(quartos_preferencia.replace("+", ""))
        col_quartos = None
        for c in ["QUARTOS", "DORMITÓRIOS", "TIPO"]:
            if c in df_filtrado.columns:
                col_quartos = c
                break
        if col_quartos:
            df_filtrado = df_filtrado[df_filtrado[col_quartos].astype(str).str.contains(str(qtd))]

    # Filtro por tipologia
    if tipo_preferencia != "Indiferente" and "TIPOLOGIA" in df_filtrado.columns:
        df_filtrado = df_filtrado[
            df_filtrado["TIPOLOGIA"].astype(str).str.contains(tipo_preferencia, case=False, na=False)
        ]

    # Define coluna base do desconto
    coluna_base = "AVALIAÇÃO" if tipo_desconto == "AVALIAÇÃO" else "PREÇO"

    # Aplica desconto
    if coluna_base in df_filtrado.columns:
        df_filtrado["valor_base"] = df_filtrado[coluna_base] - desconto_acordado
        df_filtrado["valor_base"] = df_filtrado["valor_base"].clip(lower=0)
    else:
        df_filtrado["valor_base"] = df_filtrado["PREÇO"]

    # Filtro por parcela máxima (30% da renda)
    parcela_maxima = renda_cliente * 0.3
    if preco_col in df_filtrado.columns:
        df_filtrado["parcela_estimada"] = df_filtrado["valor_base"] * 0.005
        df_filtrado = df_filtrado[df_filtrado["parcela_estimada"] <= parcela_maxima]
        if "R$/m²" in df_filtrado.columns:
            df_filtrado = df_filtrado.sort_values("R$/m²")

    top_recomendacoes = df_filtrado.head(5)

    # Gera resumo para compartilhar
    resumo = gerar_resumo(
        nome_cliente,
        renda_cliente,
        entrada_cliente,
        bairro_preferencia,
        top_recomendacoes,
        nome_gerente=USUARIOS[usuario_logado]["nome"] if usuario_logado in USUARIOS else "",
        desconto=desconto_acordado,
        tipo_desconto=tipo_desconto,
    )

    return {
        "top_recomendacoes": top_recomendacoes,
        "desconto_acordado": desconto_acordado,
        "tipo_desconto": tipo_desconto,
        "coluna_base": coluna_base,
        "preco_col": preco_col,
        "nome_cliente": nome_cliente,
        "resumo": resumo,
    }