import streamlit as st
import pandas as pd
import re
from src.planilha_cache import tem_planilha_cache, carregar_planilha_cache
from src.dashboard_graficos import (
    grafico_tipologia, grafico_faixa_preco, grafico_disponibilidade, grafico_preco_por_produto,
)

def pagina_dashboard(CONSTRUTORAS, USUARIOS):
    st.title("📊 Dashboard do Gerente (Estoque)")
    
    if not CONSTRUTORAS:
        st.warning("Nenhuma construtora cadastrada.")
        return
        
    # === FILTRO NO TOPO ===
    lista_construtoras = ["(Todas as Construtoras)"] + list(CONSTRUTORAS.keys())
    filtro_construtora = st.selectbox("🏗️ Selecione a Construtora", lista_construtoras)
    
    if filtro_construtora != "(Todas as Construtoras)":
        construtoras_filtradas = {filtro_construtora: CONSTRUTORAS[filtro_construtora]}
    else:
        construtoras_filtradas = CONSTRUTORAS

    st.markdown("---")

    metricas = _coletar_metricas(construtoras_filtradas)
    _renderizar_cards(metricas)

    st.markdown("---")

    df_total = metricas["df_total"]
    if df_total.empty:
        st.info("📭 Nenhum dado disponível para gerar gráficos com os filtros atuais.")
    else:
        st.subheader("📈 Análise Visual")
        
        col1, col2 = st.columns(2)
        with col1:
            fig = grafico_tipologia(df_total)
            if fig: st.plotly_chart(fig, use_container_width=True)
            else: st.info("Sem dados de tipologia.")
        with col2:
            preco_col = _detectar_coluna_valor(df_total)
            fig = grafico_faixa_preco(df_total, preco_col) if preco_col else None
            if fig: st.plotly_chart(fig, use_container_width=True)
            else: st.info("Sem dados de preço.")

        col3, col4 = st.columns(2)
        with col3:
            fig = grafico_disponibilidade(df_total)
            if fig: st.plotly_chart(fig, use_container_width=True)
            else: st.info("Sem dados de disponibilidade.")
        with col4:
            fig = grafico_preco_por_produto(metricas["preco_por_produto"])
            if fig: st.plotly_chart(fig, use_container_width=True)
            else: st.info("Sem dados de preço por produto.")

    st.markdown("---")
    st.subheader("🏗️ Produtos Cadastrados")
    
    for construtora, dados in construtoras_filtradas.items():
        with st.expander(f"🏢 {construtora}"):
            produtos = dados.get("produtos", {})
            if produtos:
                for produto, config in produtos.items():
                    cidade = config.get("cidade", "Não definida")
                    st.write(f"  📄 **{produto}** – 📍 {cidade}")
            else:
                st.caption("  ⚠️ Nenhum produto cadastrado")

def _coletar_metricas(CONSTRUTORAS):
    total_imoveis, total_disponiveis, total_reservados, total_vendidos = 0, 0, 0, 0
    dfs, preco_por_produto = [], {}

    for construtora, dados in CONSTRUTORAS.items():
        for produto, config in dados.get("produtos", {}).items():
            try:
                if not tem_planilha_cache(construtora, produto):
                    continue
                df = carregar_planilha_cache(construtora, produto)
                if df is None or df.empty:
                    continue

                df = df.copy()
                df["_produto"] = produto
                df["_construtora"] = construtora
                dfs.append(df)
                total_imoveis += len(df)

                status_col = None
                for c in ["DISPONIBILIDADE", "STATUS", "SITUAÇÃO", "SITUACAO"]:
                    if c in df.columns:
                        status_col = c
                        break

                if status_col:
                    status_upper = df[status_col].astype(str).str.upper()
                    total_disponiveis += len(df[status_upper.isin(["LIVRE", "DISPONÍVEL", "DISPONIVEL"])])
                    total_reservados += len(df[status_upper.isin(["RESERVADA", "RESERVADO"])])
                    total_vendidos += len(df[status_upper.isin(["VENDIDA", "VENDIDO"])])
                else:
                    total_disponiveis += len(df)

                # === A MÁGICA DA LIMPEZA DO PREÇO AQUI ===
                preco_col = _detectar_coluna_valor(df)
                if preco_col:
                    try:
                        # Converte para string, tira R$, tira pontos, troca vírgula por ponto
                        serie_limpa = df[preco_col].astype(str).str.replace('R$', '', regex=False)
                        serie_limpa = serie_limpa.str.replace('.', '', regex=False)
                        serie_limpa = serie_limpa.str.replace(',', '.', regex=False)
                        serie_limpa = pd.to_numeric(serie_limpa, errors="coerce")
                        
                        media = serie_limpa.mean()
                        if pd.notna(media) and media > 0:
                            preco_por_produto[f"{construtora} - {produto}"] = round(media, 2)
                    except Exception:
                        pass
            except Exception:
                pass

    df_total = pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()
    return {
        "total_imoveis": total_imoveis, "total_disponiveis": total_disponiveis,
        "total_reservados": total_reservados, "total_vendidos": total_vendidos,
        "df_total": df_total, "preco_por_produto": preco_por_produto,
    }

def _detectar_coluna_valor(df):
    for k in ["AVALIA", "VALOR_DA_AVALIA"]:
        for c in df.columns:
            if k in str(c).upper():
                return c
    for k in ["PREÇO", "PRECO", "VALOR_DO_IMOVEL", "VALOR"]:
        for c in df.columns:
            if k in str(c).upper():
                return c
    return None

def _renderizar_cards(metricas):
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"<div class='card-moderno' style='text-align:center;'><h3 style='font-size:32px; margin:0; color:#1a73e8;'>{metricas['total_imoveis']}</h3><p style='margin:0; color:#5f6368;'>Total de Imóveis</p></div>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<div class='card-moderno' style='text-align:center;'><h3 style='font-size:32px; margin:0; color:#28a745;'>{metricas['total_disponiveis']}</h3><p style='margin:0; color:#5f6368;'>Disponíveis</p></div>", unsafe_allow_html=True)
    with col3:
        st.markdown(f"<div class='card-moderno' style='text-align:center;'><h3 style='font-size:32px; margin:0; color:#ffc107;'>{metricas['total_reservados']}</h3><p style='margin:0; color:#5f6368;'>Reservados</p></div>", unsafe_allow_html=True)
    with col4:
        st.markdown(f"<div class='card-moderno' style='text-align:center;'><h3 style='font-size:32px; margin:0; color:#dc3545;'>{metricas['total_vendidos']}</h3><p style='margin:0; color:#5f6368;'>Vendidos</p></div>", unsafe_allow_html=True)