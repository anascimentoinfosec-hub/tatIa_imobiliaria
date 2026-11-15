import streamlit as st
import pandas as pd
import re
from src.planilha_cache import carregar_planilha_cache, salvar_planilha_cache, tem_planilha_cache
from src.construtoras_storage import carregar_construtoras


def _br_to_float(valor):
    """Converte 'R$ 337.035,63' ou '337035,63' ou '337035.63' em float."""
    if pd.isna(valor):
        return None
    s = str(valor).strip()
    s = re.sub(r"R\$?\s*", "", s, flags=re.IGNORECASE)
    s = s.replace(" ", "").strip()
    if not s:
        return None

    tem_virgula = "," in s
    tem_ponto = "." in s

    if tem_virgula and tem_ponto:
        s = s.replace(".", "").replace(",", ".")
    elif tem_virgula:
        s = s.replace(",", ".")
    elif tem_ponto:
        partes = s.split(".")
        if len(partes) > 1 and all(len(p) == 3 for p in partes[1:]):
            s = s.replace(".", "")

    match = re.search(r"\d+(\.\d+)?", s)
    if not match:
        return None
    try:
        return float(match.group())
    except (ValueError, TypeError):
        return None


def renderizar_ajuste_valores():
    st.subheader("🔧 Ajustar valores de uma planilha em cache")
    st.caption(
        "Se os valores importados ficaram errados (multiplicados ou divididos por 10/100/1000), "
        "ajuste aqui. Selecione a coluna e o fator de correção."
    )

    construtoras = carregar_construtoras()
    if not construtoras:
        st.info("Cadastre uma construtora primeiro.")
        return

    col1, col2 = st.columns(2)
    with col1:
        construtora = st.selectbox("🏗️ Construtora", list(construtoras.keys()), key="aj_construtora")

    produtos = list(construtoras[construtora].get("produtos", {}).keys())
    with col2:
        if produtos:
            produto = st.selectbox("📦 Produto", produtos, key="aj_produto")
        else:
            st.warning("Sem produtos cadastrados.")
            return

    if not tem_planilha_cache(construtora, produto):
        st.warning(f"⚠️ Nenhuma planilha em cache para **{construtora} - {produto}**.")
        return

    df = carregar_planilha_cache(construtora, produto)
    if df is None or df.empty:
        st.warning("Planilha vazia.")
        return

    # Detecção robusta de colunas numéricas
    colunas_numericas = []
    for c in df.columns:
        valores_convertidos = df[c].apply(_br_to_float)
        qtd_validos = valores_convertidos.notna().sum()
        if qtd_validos >= len(df) * 0.5:
            colunas_numericas.append(c)

    if not colunas_numericas:
        st.warning("Nenhuma coluna numérica detectada.")
        st.caption(f"Colunas disponíveis: {list(df.columns)}")
        return

    coluna = st.selectbox(
        "📊 Coluna para ajustar",
        colunas_numericas,
        key="aj_coluna",
    )

    # Amostra real com conversão
    valores_originais = df[coluna].head(5).tolist()
    valores_convertidos = [(_br_to_float(v), v) for v in valores_originais]

    st.markdown("**🔍 Amostra atual (original → convertido):**")
    for conv, orig in valores_convertidos:
        if conv is not None:
            st.caption(f"• `{orig}` → {conv:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        else:
            st.caption(f"• `{orig}` → (não numérico)")

    st.markdown("---")

    col_f1, col_f2 = st.columns(2)
    with col_f1:
        operacao = st.radio("Operação", ["÷ (dividir)", "× (multiplicar)"],
                             key="aj_operacao", horizontal=True)
    with col_f2:
        fator = st.selectbox("Fator", [10, 100, 1000, 10000], key="aj_fator")

    divisor = fator if "÷" in operacao else (1 / fator)

    st.info(f"➡️ Vou {'dividir' if '÷' in operacao else 'multiplicar'} os valores por **{fator}**.")

    # Preview
    st.markdown("**👀 Preview DEPOIS do ajuste:**")
    for conv, _ in valores_convertidos:
        if conv is not None:
            novo = round(conv / divisor, 2)
            st.caption(f"• {novo:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

    st.markdown("---")

    if st.button("✅ Aplicar ajuste", type="primary", use_container_width=True, key="aj_aplicar"):
        try:
            df[coluna] = df[coluna].apply(
                lambda v: round(_br_to_float(v) / divisor, 2) if _br_to_float(v) is not None else v
            )
            salvar_planilha_cache(construtora, df, produto)
            st.success(f"✅ Coluna **{coluna}** ajustada! Recarregue o simulador (F5).")
            st.rerun()
        except Exception as e:
            st.error(f"❌ Erro ao ajustar: {str(e)}")