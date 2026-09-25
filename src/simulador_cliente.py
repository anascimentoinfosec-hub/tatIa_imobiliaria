import streamlit as st
from src.construtoras_storage import carregar_cidades
from src.compartilhar import gerar_resumo
from src.origens_storage import carregar_origens
from src.simulacoes_storage import salvar_simulacao
from src.regras_storage import carregar_regras_ativas


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
                help="Renda líquida mensal do cliente (após impostos). Usada para calcular a parcela máxima.",
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
                help="Filtra os imóveis pela quantidade de quartos.",
            )
            tipo_preferencia = st.selectbox(
                "🏠 Tipo de imóvel", ["Indiferente", "Apartamento", "Cobertura", "Garden"], key="cliente_tipo",
                help="Filtra os imóveis pelo tipo.",
            )
            desconto_acordado = st.number_input(
                "💸 Desconto acordado (R$)",
                min_value=0.0, value=0.0, step=1000.0, format="%.2f",
                help=f"Desconto a ser subtraído do {tipo_desconto} do imóvel. O resultado é o 'Valor base'.",
                key="cliente_desconto",
            )

            # === Escolha da regra de financiamento ===
            regra_id, regra = _renderizar_seletor_regra()

        if st.button("🔍 Analisar Oportunidades", use_container_width=True):
            if not nome_cliente:
                st.warning("⚠️ Por favor, informe o nome do cliente.")
                return

            if regra is None:
                st.warning("⚠️ Nenhuma regra de financiamento ativa. Cadastre em Gestão → Regras Financiamento.")
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
                        regra_id=regra_id,
                        regra=regra,
                    )
                    st.session_state.simulacao_ativa = dados_simulacao

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
    origens = carregar_origens()
    opcoes = ["(Não informado)"] + origens
    return st.selectbox(
        "🎯 Origem do Cliente",
        opcoes,
        key="cliente_origem",
        help="Como esse cliente chegou até nós?",
    )


def _renderizar_seletor_regra():
    """Combo com as regras de financiamento ativas. Retorna (regra_id, dados_regra)."""
    regras = carregar_regras_ativas()

    if not regras:
        return None, None

    opcoes = list(regras.keys())
    labels = {rid: f"{r['nome']} ({r['taxa_anual']*100:.2f}% a.a. • {r['prazo_max_meses']}m)" for rid, r in regras.items()}

    regra_id = st.selectbox(
        "🏦 Regra de financiamento",
        opcoes,
        format_func=lambda rid: labels[rid],
        key="cliente_regra",
        help="Escolha o banco/sistema. Taxa, prazo e sistema são aplicados nas parcelas.",
    )

    return regra_id, regras[regra_id]


def _analisar(resultado, nome_cliente, renda_cliente, entrada_cliente,
              bairro_preferencia, quartos_preferencia, tipo_preferencia,
              desconto_acordado, tipo_desconto, preco_col, usuario_logado,
              USUARIOS, origem_cliente, regra_id, regra):
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

    # Usa comprometimento da regra
    comprometimento = regra.get("comprometimento_max_pct", 30) / 100
    parcela_maxima = renda_cliente * comprometimento

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
        "regra_id": regra_id,
        "regra": regra,
        "renda": renda_cliente,
        "entrada": entrada_cliente,
    }