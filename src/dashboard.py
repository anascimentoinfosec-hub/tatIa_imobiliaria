import streamlit as st
import pandas as pd
from src.planilha_cache import tem_planilha_cache, carregar_planilha_cache
from src.dashboard_graficos import (
    grafico_tipologia,
    grafico_faixa_preco,
    grafico_disponibilidade,
    grafico_preco_por_produto,
)


def pagina_dashboard(CONSTRUTORAS, USUARIOS):
    st.title("📊 Dashboard do Gerente")
    st.markdown("---")

    # =========================================================
    # COLETA DE DADOS DE TODOS OS PRODUTOS
    # =========================================================
    metricas = _coletar_metricas(CONSTRUTORAS)

    # =========================================================
    # CARDS DE MÉTRICAS
    # =========================================================
    _renderizar_cards(metricas)

    st.markdown("---")

    # =========================================================
    # GRÁFICOS
    # =========================================================
    df_total = metricas["df_total"]

    if df_total.empty:
        st.info("📭 Nenhum dado disponível para gerar gráficos. Faça upload de planilhas primeiro.")
    else:
        st.subheader("📈 Análise Visual")

        col1, col2 = st.columns(2)
        with col1:
            fig = grafico_tipologia(df_total)
            if fig:
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Sem dados de tipologia.")
        with col2:
            preco_col = _detectar_preco_col(df_total)
            fig = grafico_faixa_preco(df_total, preco_col) if preco_col else None
            if fig:
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Sem dados de preço.")

        col3, col4 = st.columns(2)
        with col3:
            fig = grafico_disponibilidade(df_total)
            if fig:
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Sem dados de disponibilidade.")
        with col4:
            dados_produto = metricas["preco_por_produto"]
            fig = grafico_preco_por_produto(dados_produto) if dados_produto else None
            if fig:
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Sem dados de preço por produto.")

    st.markdown("---")

    # =========================================================
    # LISTA DE CONSTRUTORAS E PRODUTOS
    # =========================================================
    st.subheader("🏗️ Construtoras e Produtos")

    for construtora, dados in CONSTRUTORAS.items():
        with st.expander(f"🏢 {construtora}"):
            produtos = dados.get("produtos", {})
            if produtos:
                for produto, config in produtos.items():
                    cidade = config.get("cidade", "Não definida")
                    colunas = len(config.get("colunas_ordem", []))
                    st.write(f"  📄 **{produto}** – 📍 {cidade} – {colunas} colunas")
            else:
                st.caption("  ⚠️ Nenhum produto cadastrado")

    st.markdown("---")
    st.caption("📊 Dashboard atualizado automaticamente com os dados do cache.")


# =========================================================
# HELPERS
# =========================================================
def _coletar_metricas(CONSTRUTORAS):
    """Percorre todas as construtoras/produtos, coleta dados e calcula métricas."""
    total_imoveis = 0
    total_disponiveis = 0
    total_reservados = 0
    total_vendidos = 0
    produtos_count = 0
    dfs = []
    preco_por_produto = {}

    for construtora, dados in CONSTRUTORAS.items():
        for produto, config in dados.get("produtos", {}).items():
            produtos_count += 1
            try:
                if not tem_planilha_cache(construtora, produto):
                    continue

                df = carregar_planilha_cache(construtora, produto)
                if df is None or df.empty:
                    continue

                # Adiciona coluna identificadora
                df = df.copy()
                df["_produto"] = produto
                df["_construtora"] = construtora
                dfs.append(df)

                total_imoveis += len(df)

                # Detectar coluna de status
                status_col = None
                for c in ["DISPONIBILIDADE", "STATUS", "SITUAÇÃO"]:
                    if c in df.columns:
                        status_col = c
                        break

                if status_col:
                    total_disponiveis += len(df[df[status_col].astype(str).str.upper().isin(["LIVRE", "DISPONÍVEL"])])
                    total_reservados += len(df[df[status_col].astype(str).str.upper().isin(["RESERVADA", "RESERVADO"])])
                    total_vendidos += len(df[df[status_col].astype(str).str.upper().isin(["VENDIDA", "VENDIDO"])])

                # Preço médio por produto
                preco_col = _detectar_preco_col(df)
                if preco_col:
                    df[preco_col] = pd.to_numeric(df[preco_col], errors="coerce")
                    media = df[preco_col].mean()
                    if pd.notna(media) and media > 0:
                        preco_por_produto[f"{construtora} - {produto}"] = round(media, 2)
            except Exception:
                pass

    df_total = pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()

    return {
        "total_imoveis": total_imoveis,
        "total_disponiveis": total_disponiveis,
        "total_reservados": total_reservados,
        "total_vendidos": total_vendidos,
        "produtos_count": produtos_count,
        "df_total": df_total,
        "preco_por_produto": preco_por_produto,
    }


def _detectar_preco_col(df):
    """Retorna o nome da coluna de preço encontrada, ou None."""
    for c in ["PREÇO", "VALOR", "AVALIAÇÃO"]:
        if c in df.columns:
            return c
    return None


def _renderizar_cards(metricas):
    """Renderiza os 4 cards de métricas."""
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(f"""
        <div class="card-moderno" style="text-align:center;">
            <h3 style="font-size:32px; margin:0; color:#1a73e8;">{metricas['total_imoveis']}</h3>
            <p style="margin:0; color:#5f6368;">Total de Imóveis</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="card-moderno" style="text-align:center;">
            <h3 style="font-size:32px; margin:0; color:#28a745;">{metricas['total_disponiveis']}</h3>
            <p style="margin:0; color:#5f6368;">Disponíveis</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="card-moderno" style="text-align:center;">
            <h3 style="font-size:32px; margin:0; color:#ffc107;">{metricas['total_reservados']}</h3>
            <p style="margin:0; color:#5f6368;">Reservados</p>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div class="card-moderno" style="text-align:center;">
            <h3 style="font-size:32px; margin:0; color:#dc3545;">{metricas['total_vendidos']}</h3>
            <p style="margin:0; color:#5f6368;">Vendidos</p>
        </div>
        """, unsafe_allow_html=True)