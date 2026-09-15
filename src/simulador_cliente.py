import streamlit as st
from src.construtoras_storage import carregar_cidades
from src.compartilhar import gerar_resumo
from src.origens_storage import carregar_origens
from src.simulacoes_storage import salvar_simulacao


def renderizar_area_cliente(resultado, tipo_desconto, preco_col, usuario_logado, USUARIOS):
    """Renderiza a área do cliente (inputs + botão Analisar)."""
    st.subheader("🧑 Área do Cliente")
    st.markdown("Preencha os dados abaixo para receber recomendações personalizadas.")

    with st.container():
        col1, col2 = st.columns(2)

        with col1:
            nome_cliente = st.text_input(
                "Nome do Cliente",
                placeholder="Ex: João Silva",
                key="cliente_nome",
                help="Nome completo do cliente. Aparecerá no resumo compartilhado.",
            )
            renda_cliente = st.number_input(
                "💰 Renda líquida mensal (R$)",
                min_value=0.0, value=5000.0, step=500.0, format="%.2f",
                key="cliente_renda",
                help="Renda líquida mensal do cliente (após impostos). Usada para calcular a parcela máxima (30% da renda).",
            )
            entrada_cliente = st.number_input(
                "🏦 Valor disponível para entrada (R$)",
                min_value=0.0, value=100000.0, step=10000.0, format="%.2f",
                key="cliente_entrada",
                help="Quanto o cliente tem disponível para dar de entrada no imóvel.",
            )
            origem_cliente = _renderizar_origem_cliente()

        with col2:
            cidades_disponiveis = carregar_cidades()
            bairro_preferencia = st.selectbox(
                "📍 Bairro de preferência", [""] + cidades_disponiveis, key="cliente_bairro",
                help="Filtra os imóveis pelo bairro de interesse do cliente.",
            )
            quartos_preferencia = st.selectbox(
                "🛏️ Quantos quartos?", ["Indiferente", "1", "2", "3", "4+"], key="cliente_quartos",
                help="Filtra os imóveis pela quantidade de quartos. Escolha 'Indiferente' para não filtrar.",
            )
            tipo_preferencia = st.selectbox(
                "🏠 Tipo de imóvel", ["Indiferente", "Apartamento", "Cobertura", "Garden"], key="cliente_tipo",
                help="Filtra os imóveis pelo tipo (apartamento, cobertura, garden, etc.).",
            )
            desconto_acordado = st.number_input(
                "💸 Desconto acordado (R$)",
                min_value=0.0, value=0.0, step=1000.0, format="%.2f",
                help=f"Desconto a ser subtraído do {tipo_desconto} do imóvel. O resultado é o 'Valor base'.",
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
                        origem_cliente=origem_cliente,
                    )
                    st.session_state.simulacao_ativa = dados_simulacao

                    # === SALVA NO HISTÓRICO ===
                    nome_gerente = USUARIOS[usuario_logado]["nome"] if usuario_logado in USUARIOS else ""
                    sim_id = salvar_simulacao(
                        nome_cliente=nome_cliente,
                        renda=renda_cliente,
                        entrada=entrada_cliente,
                        bairro=bairro_preferencia,
                        origem=origem_cliente if origem_cliente != "(Não informado)" else "",
                        desconto=desconto_acordado,
                        tipo_desconto=tipo_desconto,
                        gerente=nome_gerente,
                        top_recomendacoes=dados_simulacao["top_recomendacoes"],
                    )
                    st.session_state.ultima_simulacao_id = sim_id
                    st.toast(f"💾 Simulação salva no histórico (ID: {sim_id[-6:]})")

                except Exception as e:
                    st.error(f"❌ Erro ao analisar oportunidades: {str(e)}")


def _renderizar_origem_cliente():
    """Renderiza o combo de origem do cliente."""
    origens = carregar_origens()
    opcoes = ["(Não informado)"] + origens
    return st.selectbox(
        "🎯 Origem do Cliente",
        opcoes,
        key="cliente_origem",
        help="Como esse cliente chegou até nós? Ajuda a medir a eficácia dos canais de captação.",
    )


def _analisar(resultado, nome_cliente, renda_cliente, entrada_cliente,
              bairro_preferencia, quartos_preferencia, tipo_preferencia,
              desconto_acordado, tipo_desconto, preco_col, usuario_logado,
              USUARIOS, origem_cliente):
    """Lógica pura de análise. Retorna dict pronto para o session_state."""
    df_filtrado = resultado.copy()

    if quartos_preferencia != "Indiferente":
        qtd = int(quartos_preferencia.replace("+", ""))
        col_quartos = None
        for c in ["QUARTOS", "DORMITÓRIOS", "TIPO"]:
            if c in df_filtrado.columns:
                col_quartos = c
                break
        if col_quartos:
            df_filtrado = df_filtrado[df_filtrado[col_quartos].astype(str).str.contains(str(qtd))]

    if tipo_preferencia != "Indiferente" and "TIPOLOGIA" in df_filtrado.columns:
        df_filtrado = df_filtrado[
            df_filtrado["TIPOLOGIA"].astype(str).str.contains(tipo_preferencia, case=False, na=False)
        ]

    coluna_base = "AVALIAÇÃO" if tipo_desconto == "AVALIAÇÃO" else "PREÇO"

    if coluna_base in df_filtrado.columns:
        df_filtrado["valor_base"] = df_filtrado[coluna_base] - desconto_acordado
        df_filtrado["valor_base"] = df_filtrado["valor_base"].clip(lower=0)
    else:
        df_filtrado["valor_base"] = df_filtrado["PREÇO"]

    parcela_maxima = renda_cliente * 0.3
    if preco_col in df_filtrado.columns:
        df_filtrado["parcela_estimada"] = df_filtrado["valor_base"] * 0.005
        df_filtrado = df_filtrado[df_filtrado["parcela_estimada"] <= parcela_maxima]
        if "R$/m²" in df_filtrado.columns:
            df_filtrado = df_filtrado.sort_values("R$/m²")

    top_recomendacoes = df_filtrado.head(5)

    resumo = gerar_resumo(
        nome_cliente,
        renda_cliente,
        entrada_cliente,
        bairro_preferencia,
        top_recomendacoes,
        nome_gerente=USUARIOS[usuario_logado]["nome"] if usuario_logado in USUARIOS else "",
        desconto=desconto_acordado,
        tipo_desconto=tipo_desconto,
        origem=origem_cliente,
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