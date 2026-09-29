import streamlit as st
from src.utils import formatar_valor_br


def renderizar_seletor_proposta(top_recomendacoes):
    """Radio para escolher UMA unidade como proposta. Retorna o index ou None."""
    if top_recomendacoes is None or top_recomendacoes.empty:
        return None

    st.markdown("### 🎯 Escolha a unidade para a proposta")
    st.caption("Selecione UMA unidade para gerar o PDF e a proposta. Os cards mostram a escolhida com ⭐.")

    opcoes = ["(Mostrar todas)"]
    indices = [None]

    for idx, row in top_recomendacoes.iterrows():
        unidade = row.get("UNIDADE", "N/A")
        tipologia = row.get("TIPOLOGIA", "")
        valor = row.get("valor_base", 0)
        label = f"🏢 Unidade {unidade}"
        if tipologia:
            label += f" — {tipologia}"
        if valor:
            label += f" — {formatar_valor_br(valor)}"
        opcoes.append(label)
        indices.append(idx)

    escolha = st.radio(
        "Selecione uma opção:",
        range(len(opcoes)),
        format_func=lambda i: opcoes[i],
        key="seletor_proposta_radio",
        label_visibility="collapsed",
    )

    return indices[escolha]


def renderizar_cards(top_recomendacoes, desconto_acordado, tipo_desconto,
                     coluna_base, preco_col, nome_cliente):
    """Renderiza os cards das recomendações."""
    if top_recomendacoes is None or top_recomendacoes.empty:
        st.warning(f"⚠️ Nenhuma oportunidade encontrada para {nome_cliente}.")
        return

    st.success(f"✅ {len(top_recomendacoes)} oportunidades encontradas para {nome_cliente}!")

    escolhida_idx = st.session_state.get("unidade_escolhida_idx")

    for idx, row in top_recomendacoes.iterrows():
        _renderizar_card_imovel(
            idx=idx,
            row=row,
            desconto_acordado=desconto_acordado,
            tipo_desconto=tipo_desconto,
            coluna_base=coluna_base,
            preco_col=preco_col,
            destacado=(idx == escolhida_idx),
        )


def _renderizar_card_imovel(idx, row, desconto_acordado, tipo_desconto,
                            coluna_base, preco_col, destacado=False):
    with st.container():
        st.markdown("---")
        col_a, col_b = st.columns([3, 2])

        with col_a:
            _renderizar_info_imovel(row, desconto_acordado, tipo_desconto,
                                     coluna_base, preco_col, destacado)

        with col_b:
            _renderizar_entrada_disponivel(row)


def _renderizar_info_imovel(row, desconto_acordado, tipo_desconto, coluna_base,
                             preco_col, destacado=False):
    unidade = row.get("UNIDADE", "N/A")

    if destacado:
        st.markdown(f"**🏢 Unidade {unidade}** ⭐ **_(proposta escolhida)_**")
    else:
        st.markdown(f"**🏢 Unidade {unidade}**")

    st.caption(f"💡 Desconto sobre: {tipo_desconto}")

    bloco = row.get("BLOCO", "")
    pavto = row.get("PAVTO", row.get("ANDAR", ""))
    if bloco or pavto:
        partes = []
        if bloco:
            partes.append(f"Bloco: {bloco}")
        if pavto:
            partes.append(f"Andar: {pavto}")
        st.write(f"📍 **{' | '.join(partes)}**")

    if "AVALIAÇÃO" in row:
        st.write(f"📊 **Avaliação:** {formatar_valor_br(row['AVALIAÇÃO'])}")

    if coluna_base == "PREÇO" and preco_col in row:
        st.write(f"💵 **Preço original:** {formatar_valor_br(row[preco_col])}")

    st.write(f"💸 **Desconto:** {formatar_valor_br(desconto_acordado)}")
    st.write(f"💰 **Valor base:** {formatar_valor_br(row['valor_base'])}")

    if "TIPOLOGIA" in row:
        st.write(f"🏠 **Tipo:** {row['TIPOLOGIA']}")
    if "M²" in row:
        try:
            st.write(f"📐 **Área:** {float(row['M²']):.2f} m²")
        except (ValueError, TypeError):
            pass
    if "VAGA" in row:
        st.write(f"🚗 **Vagas:** {row['VAGA']}")


def _renderizar_entrada_disponivel(row):
    """Coluna direita: mostra o valor base e informações úteis para a entrada."""
    valor_base = row.get("valor_base", 0)

    st.markdown("##### 💰 Resumo da unidade")

    st.write(f"💰 **Valor base:** {formatar_valor_br(valor_base)}")

    # Simulação simples: entrada total = valor base (sem banco por enquanto)
    st.caption("💡 O cálculo de financiamento será adicionado após a implementação das regras de entrada por construtora.")


def renderizar_ajuste_global(df, preco_col):
    st.markdown("---")
    st.markdown("### 💰 Ajuste de Entrada")
    st.caption("Ajuste o percentual de entrada para simular diferentes cenários.")

    entrada_percentual_global = st.slider(
        "Percentual de entrada (%)",
        min_value=20, max_value=50, value=20, step=5,
        key="entrada_global",
        help="Percentual do valor do imóvel que será pago como entrada.",
    )

    if preco_col not in df.columns or df.empty:
        return

    valor_medio = df[preco_col].mean()
    entrada_media = valor_medio * (entrada_percentual_global / 100)

    st.markdown("**📊 Simulação média com base nos imóveis disponíveis:**")
    col_s1, col_s2 = st.columns(2)
    col_s1.metric("💰 Valor médio", formatar_valor_br(valor_medio))
    col_s2.metric(f"💵 Entrada ({entrada_percentual_global}%)", formatar_valor_br(entrada_media))