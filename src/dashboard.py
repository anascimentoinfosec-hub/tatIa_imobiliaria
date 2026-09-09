import streamlit as st
import pandas as pd

def pagina_dashboard(CONSTRUTORAS, USUARIOS):
    st.title("📊 Dashboard do Gerente")
    st.markdown("---")
    
    # =========================================================
    # MÉTRICAS RÁPIDAS
    # =========================================================
    total_imoveis = 0
    total_disponiveis = 0
    total_reservados = 0
    total_vendidos = 0
    produtos_count = 0
    
    for construtora, dados in CONSTRUTORAS.items():
        for produto, config in dados.get("produtos", {}).items():
            produtos_count += 1
            # Tenta carregar planilha do cache
            try:
                from modules.planilha_cache import tem_planilha_cache, carregar_planilha_cache
                if tem_planilha_cache(construtora, produto):
                    df = carregar_planilha_cache(construtora, produto)
                    if df is not None:
                        total_imoveis += len(df)
                        if "DISPONIBILIDADE" in df.columns:
                            total_disponiveis += len(df[df["DISPONIBILIDADE"] == "LIVRE"])
                            total_reservados += len(df[df["DISPONIBILIDADE"] == "RESERVADA"])
                            total_vendidos += len(df[df["DISPONIBILIDADE"] == "VENDIDA"])
            except:
                pass
    
    # =========================================================
    # CARDS
    # =========================================================
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="card-moderno" style="text-align:center;">
            <h3 style="font-size:32px; margin:0; color:#1a73e8;">{}</h3>
            <p style="margin:0; color:#5f6368;">Total de Imóveis</p>
        </div>
        """.format(total_imoveis), unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="card-moderno" style="text-align:center;">
            <h3 style="font-size:32px; margin:0; color:#28a745;">{}</h3>
            <p style="margin:0; color:#5f6368;">Disponíveis</p>
        </div>
        """.format(total_disponiveis), unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="card-moderno" style="text-align:center;">
            <h3 style="font-size:32px; margin:0; color:#ffc107;">{}</h3>
            <p style="margin:0; color:#5f6368;">Reservados</p>
        </div>
        """.format(total_reservados), unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class="card-moderno" style="text-align:center;">
            <h3 style="font-size:32px; margin:0; color:#dc3545;">{}</h3>
            <p style="margin:0; color:#5f6368;">Vendidos</p>
        </div>
        """.format(total_vendidos), unsafe_allow_html=True)
    
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