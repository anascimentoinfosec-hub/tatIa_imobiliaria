import streamlit as st
from src.utils import formatar_valor_br
from src.regras.financeiro import (
    calcular_parcela_price,
    calcular_entrada_e_financiado,
)


def renderizar_cards(top_recomendacoes, desconto_acordado, tipo_desconto,
                     coluna_base, preco_col, nome_cliente):
    """
    Renderiza os cards das recomendações com sliders individuais de entrada.
    Persiste o estado via st.session_state (chaves por índice).
    """
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

        # --- Coluna esquerda: informações ---
        with col_a:
            unidade = row.get("UNIDADE", "N/A")
            st.markdown(f"**🏢 Unidade {unidade}**")
            st.caption(f"💡 Desconto sobre: {tipo_desconto}")

            # SEMPRE mostra AVALIAÇÃO primeiro
            if "AVALIAÇÃO" in row:
                st.write(f"📊 **Avaliação:** {formatar_valor_br(row['AVALIAÇÃO'])}")

            # Se o desconto for sobre PREÇO, mostra o preço original em seguida
            if coluna_base == "PREÇO" and preco_col in row:
                st.write(f"💵 **Preço original:** {formatar_valor_br(row[preco_col])}")

            st.write(f"💸 **Desconto:** {formatar_valor_br(desconto_acordado)}")
            st.write(f"💰 **Valor base:** {formatar_valor_br(row['valor_base'])}")

            if "parcela_estimada" in row:
                st.write(f"📆 **Parcela estimada:** {formatar_valor_br(row['parcela_estimada'])}")
            if "TIPOLOGIA" in row:
                st.write(f"🏠 **Tipo:** {row['TIPOLOGIA']}")

        # --- Coluna direita: slider de entrada ---
        with col_b:
            _renderizar_slider_entrada(idx, row)


def _renderizar_slider_entrada(idx, row):
    """Renderiza o slider + os valores calculados de entrada/financiado/parcela."""
    entrada_percentual = st.slider(
        f"Entrada (%) - Unidade {row.get('UNIDADE', idx)}",
        min_value=20,
        max_value=50,
        value=20,
        step=5,
        key=f"entrada_{idx}",
    )

    valor_base = row["valor_base"]
    entrada_fin = calcular_entrada_e_financiado(valor_base, entrada_percentual)
    entrada_valor = entrada_fin["entrada"]
    financiado = entrada_fin["financiado"]
    parcela_media = calcular_parcela_price(financiado, 0.10, 420)

    st.write(f"💵 **Entrada:** {formatar_valor_br(entrada_valor)}")
    st.write(f"🏦 **Financiado:** {formatar_valor_br(financiado)}")
    st.write(f"📆 **Parcela:** {formatar_valor_br(parcela_media)}")


def renderizar_ajuste_global(df, preco_col):
    """
    Renderiza a seção de ajuste de entrada global + métricas médias.
    """
    st.markdown("---")
    st.markdown("### 💰 Ajuste de Entrada")
    st.caption("Ajuste o percentual de entrada para simular diferentes cenários.")

    entrada_percentual_global = st.slider(
        "Percentual de entrada (%)",
        min_value=20,
        max_value=50,
        value=20,
        step=5,
        key="entrada_global",
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