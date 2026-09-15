import streamlit as st
from src.utils import formatar_valor_br
from src.regras.financeiro import (
    calcular_parcela_price,
    calcular_entrada_e_financiado,
)


def renderizar_cards(top_recomendacoes, desconto_acordado, tipo_desconto,
                     coluna_base, preco_col, nome_cliente):
    """Renderiza os cards das recomendações."""
    if top_recomendacoes is None or top_recomendacoes.empty:
        st.warning(f"⚠️ Nenhuma oportunidade encontrada para {nome_cliente}.")
        return

    st.success(f"✅ {len(top_recomendacoes)} oportunidades encontradas para {nome_cliente}!")

    for idx, row in top_recomendacoes.iterrows():
        _renderizar_card_imovel(
            idx=idx,
            row=row,
            desconto_acordado=desconto_acordado,
            tipo_desconto=tipo_desconto,
            coluna_base=coluna_base,
            preco_col=preco_col,
        )


def _renderizar_card_imovel(idx, row, desconto_acordado, tipo_desconto,
                            coluna_base, preco_col):
    """Renderiza um único card de imóvel."""
    with st.container():
        st.markdown("---")
        col_a, col_b = st.columns([3, 2])

        with col_a:
            _renderizar_info_imovel(row, desconto_acordado, tipo_desconto,
                                     coluna_base, preco_col)

        with col_b:
            _renderizar_simulacao_imovel(idx, row)


def _renderizar_info_imovel(row, desconto_acordado, tipo_desconto, coluna_base, preco_col):
    """Coluna esquerda: informações do imóvel (Bloco, Andar, valores)."""
    unidade = row.get("UNIDADE", "N/A")
    st.markdown(f"**🏢 Unidade {unidade}**")
    st.caption(f"💡 Desconto sobre: {tipo_desconto}")

    # Bloco e Andar
    bloco = row.get("BLOCO", "")
    pavto = row.get("PAVTO", row.get("ANDAR", ""))
    if bloco or pavto:
        partes = []
        if bloco:
            partes.append(f"Bloco: {bloco}")
        if pavto:
            partes.append(f"Andar: {pavto}")
        st.write(f"📍 **{' | '.join(partes)}**")

    # Avaliação sempre primeiro
    if "AVALIAÇÃO" in row:
        st.write(f"📊 **Avaliação:** {formatar_valor_br(row['AVALIAÇÃO'])}")

    if coluna_base == "PREÇO" and preco_col in row:
        st.write(f"💵 **Preço original:** {formatar_valor_br(row[preco_col])}")

    st.write(f"💸 **Desconto:** {formatar_valor_br(desconto_acordado)}")
    st.write(f"💰 **Valor base:** {formatar_valor_br(row['valor_base'])}")

    if "parcela_estimada" in row:
        st.write(f"📆 **Parcela estimada:** {formatar_valor_br(row['parcela_estimada'])}")
    if "TIPOLOGIA" in row:
        st.write(f"🏠 **Tipo:** {row['TIPOLOGIA']}")


def _renderizar_simulacao_imovel(idx, row):
    """Coluna direita: number_input de financiado + entrada e parcela calculadas."""
    valor_base = row["valor_base"]
    unidade = row.get("UNIDADE", idx)

    financiado_padrao = round(valor_base * 0.8, 2)

    st.markdown(f"##### 💰 Simulação — Unidade {unidade}")

    financiado = st.number_input(
        "🏦 Valor financiado (R$)",
        min_value=0.0,
        max_value=float(valor_base),
        value=float(financiado_padrao),
        step=5000.0,
        format="%.2f",
        key=f"financiado_{idx}",
        help="Valor que o cliente vai financiar no banco. A entrada é calculada como (Valor base − Financiado).",
    )

    entrada_valor = valor_base - financiado
    percentual_entrada = (entrada_valor / valor_base * 100) if valor_base > 0 else 0

    parcela_media = calcular_parcela_price(financiado, 0.10, 420)

    st.write(f"💵 **Entrada ({percentual_entrada:.1f}%):** {formatar_valor_br(entrada_valor)}")
    st.write(f"🏦 **Financiado:** {formatar_valor_br(financiado)}")
    st.write(f"📆 **Parcela (Price 10% a.a. / 420m):** {formatar_valor_br(parcela_media)}")
    st.caption("💡 Tabela Price • Taxa 10% a.a. • Prazo 420 meses (35 anos) • Parcela fixa.")


def renderizar_ajuste_global(df, preco_col):
    """Seção de ajuste de entrada global + métricas médias."""
    st.markdown("---")
    st.markdown("### 💰 Ajuste de Entrada")
    st.caption("Ajuste o percentual de entrada para simular diferentes cenários.")

    entrada_percentual_global = st.slider(
        "Percentual de entrada (%)",
        min_value=20, max_value=50, value=20, step=5,
        key="entrada_global",
        help="Percentual do valor do imóvel que será pago como entrada. O restante é financiado.",
    )

    if preco_col not in df.columns or df.empty:
        return

    valor_medio = df[preco_col].mean()
    entrada_fin_g = calcular_entrada_e_financiado(valor_medio, entrada_percentual_global)
    entrada_media = entrada_fin_g["entrada"]
    financiado_medio = entrada_fin_g["financiado"]
    parcela_media_global = calcular_parcela_price(financiado_medio, 0.10, 420)

    st.markdown("**📊 Simulação média com base nos imóveis disponíveis:**")
    col_s1, col_s2, col_s3 = st.columns(3)
    col_s1.metric("💰 Valor médio", formatar_valor_br(valor_medio))
    col_s2.metric(f"💵 Entrada ({entrada_percentual_global}%)", formatar_valor_br(entrada_media))
    col_s3.metric("📆 Parcela média", formatar_valor_br(parcela_media_global))