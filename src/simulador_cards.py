import streamlit as st
import pandas as pd
import re
from src.utils import formatar_valor_br


# =========================================================
# REFINAMENTO
# =========================================================
def renderizar_refinamento():
    """Filtros de refinamento pós-análise, incluindo Construtora/Produto."""
    sim = st.session_state.get("simulacao_ativa", {})
    df_completo = sim.get("df_filtrado_completo")

    if df_completo is None or df_completo.empty:
        return sim.get("top_recomendacoes")

    with st.expander("🔧 Refinar oportunidades (ajuste rápido)", expanded=False):
        st.caption(
            f"📊 **{len(df_completo)} unidades** disponíveis após os filtros iniciais. "
            "Ajuste abaixo — os cards atualizam automaticamente."
        )

        # Linha 1: Construtora + Produto + Cidade
        col1, col2, col3 = st.columns(3)

        with col1:
            if "_construtora" in df_completo.columns:
                construtoras = ["Todas"] + sorted(df_completo["_construtora"].dropna().unique().tolist())
                filtro_construtora = st.selectbox("🏗️ Construtora", construtoras, key="ref_construtora")
            else:
                filtro_construtora = "Todas"

        with col2:
            if filtro_construtora != "Todas" and "_produto" in df_completo.columns:
                produtos = ["Todos"] + sorted(
                    df_completo[df_completo["_construtora"] == filtro_construtora]["_produto"].dropna().unique().tolist()
                )
            elif "_produto" in df_completo.columns:
                produtos = ["Todos"] + sorted(df_completo["_produto"].dropna().unique().tolist())
            else:
                produtos = ["Todos"]
            filtro_produto = st.selectbox("📦 Produto", produtos, key="ref_produto")

        with col3:
            col_cidade = None
            for col in df_completo.columns:
                col_up = str(col).upper()
                if any(k in col_up for k in ["CIDADE", "BAIRRO", "LOCALIZ", "MUNICIPIO"]):
                    col_cidade = col
                    break
            if col_cidade:
                cidades = ["Todas"] + sorted(df_completo[col_cidade].dropna().unique().tolist())
                filtro_cidade = st.selectbox("📍 Cidade", cidades, key="ref_cidade")
            else:
                filtro_cidade = "Todas"

        # Linha 2: Tipologia + Preço + Vagas + Andar + Qtd
        col4, col5, col6 = st.columns(3)

        with col4:
            if "TIPOLOGIA" in df_completo.columns:
                tipos = ["Todas"] + sorted(df_completo["TIPOLOGIA"].dropna().unique().tolist())
                filtro_tipo = st.selectbox("🏠 Tipologia", tipos, key="ref_tipo")
            else:
                filtro_tipo = "Todas"

        with col5:
            col_preco = _detectar_coluna_preco(df_completo)
            if col_preco:
                try:
                    valores = pd.to_numeric(df_completo[col_preco], errors="coerce").fillna(0)
                    max_preco = int(valores.max()) if valores.max() > 0 else 1000000
                    filtro_preco = st.slider(
                        "💰 Valor máximo (R$)",
                        min_value=0, max_value=max_preco, value=max_preco,
                        step=10000, key="ref_preco", format="R$ %d",
                    )
                except Exception:
                    filtro_preco = None
            else:
                filtro_preco = None

        with col6:
            col_vaga = None
            for c in ["VAGA", "VAGAS", "VAGAS_GARAGEM"]:
                if c in df_completo.columns:
                    col_vaga = c
                    break
            if col_vaga:
                filtro_vagas = st.number_input(
                    "🚗 Vagas mínimas", min_value=0, value=0, step=1, key="ref_vagas",
                )
            else:
                filtro_vagas = 0

        col7, col8, _ = st.columns(3)
        with col7:
            col_andar = None
            for c in ["PAVTO", "ANDAR"]:
                if c in df_completo.columns:
                    col_andar = c
                    break
            if col_andar:
                filtro_andar = st.number_input(
                    "📌 Andar mínimo", min_value=0, value=0, step=1, key="ref_andar",
                )
            else:
                filtro_andar = 0

        with col8:
            qtd_exibir = st.number_input(
                "📋 Cards a exibir", min_value=1, max_value=30, value=5, step=1,
                key="ref_qtd",
            )

        # === APLICA FILTROS ===
        df = df_completo.copy()

        if filtro_construtora != "Todas" and "_construtora" in df.columns:
            df = df[df["_construtora"] == filtro_construtora]

        if filtro_produto != "Todos" and "_produto" in df.columns:
            df = df[df["_produto"] == filtro_produto]

        if filtro_cidade != "Todas" and col_cidade:
            df = df[df[col_cidade] == filtro_cidade]

        if filtro_tipo != "Todas" and "TIPOLOGIA" in df.columns:
            df = df[df["TIPOLOGIA"] == filtro_tipo]

        if filtro_preco is not None and col_preco:
            df[col_preco] = pd.to_numeric(df[col_preco], errors="coerce").fillna(0)
            df = df[df[col_preco] <= filtro_preco]

        if filtro_vagas > 0 and col_vaga:
            def tem_vagas(s):
                try:
                    nums = re.findall(r"\d+", str(s))
                    return any(int(n) >= filtro_vagas for n in nums)
                except Exception:
                    return False
            df = df[df[col_vaga].apply(tem_vagas)]

        if filtro_andar > 0 and col_andar:
            df[col_andar] = pd.to_numeric(df[col_andar], errors="coerce").fillna(0)
            df = df[df[col_andar] >= filtro_andar]

        st.caption(f"🎯 **{len(df)} unidades** após refinamento")

        return df.head(int(qtd_exibir))


def _detectar_coluna_preco(df):
    """Procura a melhor coluna de valor (prioridade: AVALIAÇÃO > PREÇO > VALOR)."""
    for k in ["AVALIA", "VALOR_DA_AVALIA"]:
        for c in df.columns:
            if k in str(c).upper():
                return c
    for k in ["PREÇO", "PRECO", "VALOR_DO_IMOVEL", "VALOR"]:
        for c in df.columns:
            if k in str(c).upper():
                return c
    return None


# =========================================================
# SELETOR DE PROPOSTA
# =========================================================
def renderizar_seletor_proposta(top_recomendacoes):
    if top_recomendacoes is None or top_recomendacoes.empty:
        return None

    st.markdown("### 🎯 Escolha a unidade para a proposta")
    st.caption("Selecione UMA unidade para gerar o PDF e a proposta.")

    opcoes = ["(Mostrar todas)"]
    indices = [None]

    for idx, row in top_recomendacoes.iterrows():
        unidade = row.get("UNIDADE", "N/A")
        construtora = row.get("_construtora", "")
        produto = row.get("_produto", "")
        valor = row.get("valor_base", 0)

        label = f"🏢 {unidade}"
        if construtora:
            label += f" — {construtora}"
        if produto:
            label += f" / {produto}"
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


# =========================================================
# CARDS
# =========================================================
def renderizar_cards(top_recomendacoes, desconto_acordado, tipo_desconto,
                     coluna_base, preco_col, nome_cliente):
    if top_recomendacoes is None or top_recomendacoes.empty:
        st.warning(f"⚠️ Nenhuma oportunidade encontrada para {nome_cliente}.")
        return

    st.success(f"✅ {len(top_recomendacoes)} oportunidades encontradas para {nome_cliente}!")

    escolhida_idx = st.session_state.get("unidade_escolhida_idx")

    for idx, row in top_recomendacoes.iterrows():
        _renderizar_card_imovel(
            idx=idx, row=row, desconto_acordado=desconto_acordado,
            tipo_desconto=tipo_desconto, coluna_base=coluna_base,
            preco_col=preco_col, destacado=(idx == escolhida_idx),
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
            _renderizar_resumo_unidade(row)


def _renderizar_info_imovel(row, desconto_acordado, tipo_desconto, coluna_base,
                             preco_col, destacado=False):
    unidade = row.get("UNIDADE", "N/A")

    if destacado:
        st.markdown(f"**🏢 Unidade {unidade}** ⭐ **_(proposta escolhida)_**")
    else:
        st.markdown(f"**🏢 Unidade {unidade}**")

    # Construtora + Produto (sempre mostrar no novo fluxo)
    construtora = row.get("_construtora", "")
    produto = row.get("_produto", "")
    if construtora or produto:
        linha = []
        if construtora:
            linha.append(f"🏗️ {construtora}")
        if produto:
            linha.append(f"📦 {produto}")
        st.caption(" • ".join(linha))

    # Tipo de desconto DESTA linha (não mais global)
    tipo_linha = row.get("_tipo_desconto", tipo_desconto)
    st.caption(f"💡 Desconto sobre: {tipo_linha}")

    bloco = row.get("BLOCO", "")
    pavto = row.get("PAVTO", row.get("ANDAR", ""))
    if bloco or pavto:
        partes = []
        if bloco:
            partes.append(f"Bloco: {bloco}")
        if pavto:
            partes.append(f"Andar: {pavto}")
        st.write(f"📍 **{' | '.join(partes)}**")

    # Mostra avaliação e/ou preço original quando existirem
    for col in ["AVALIAÇÃO", "AVALIACAO", "VALOR_DA_AVALIACAO", "VALOR_DE_AVALIACAO"]:
        if col in row.index and pd.notna(row[col]):
            try:
                st.write(f"📊 **Avaliação:** {formatar_valor_br(float(row[col]))}")
                break
            except (ValueError, TypeError):
                pass

    for col in ["PREÇO", "PRECO", "VALOR_DO_IMOVEL"]:
        if col in row.index and pd.notna(row[col]):
            try:
                st.write(f"💵 **Valor:** {formatar_valor_br(float(row[col]))}")
                break
            except (ValueError, TypeError):
                pass

    st.write(f"💸 **Desconto:** {formatar_valor_br(desconto_acordado)}")
    st.write(f"💰 **Valor base:** {formatar_valor_br(row['valor_base'])}")

    if "TIPOLOGIA" in row:
        st.write(f"🏠 **Tipo:** {row['TIPOLOGIA']}")
    if "VAGA" in row:
        st.write(f"🚗 **Vagas:** {row['VAGA']}")


def _renderizar_resumo_unidade(row):
    valor_base = row.get("valor_base", 0)
    st.markdown("##### 💰 Resumo da unidade")
    st.write(f"💰 **Valor base:** {formatar_valor_br(valor_base)}")
    st.caption("💡 Financiamento será calculado após regras de entrada por construtora (#014).")


# =========================================================
# AJUSTE GLOBAL
# =========================================================
def renderizar_ajuste_global(df, preco_col):
    st.markdown("---")
    st.markdown("### 💰 Ajuste de Entrada (média geral)")
    st.caption("Média de todos os imóveis em cache.")

    entrada_percentual_global = st.slider(
        "Percentual de entrada (%)",
        min_value=20, max_value=50, value=20, step=5,
        key="entrada_global",
    )

    col_valor = _detectar_coluna_preco(df)
    if col_valor is None or df.empty:
        return

    valores = pd.to_numeric(df[col_valor], errors="coerce")
    valor_medio = valores.mean()
    if pd.isna(valor_medio):
        return

    entrada_media = valor_medio * (entrada_percentual_global / 100)

    st.markdown("**📊 Simulação média:**")
    col_s1, col_s2 = st.columns(2)
    col_s1.metric("💰 Valor médio", formatar_valor_br(valor_medio))
    col_s2.metric(f"💵 Entrada ({entrada_percentual_global}%)", formatar_valor_br(entrada_media))