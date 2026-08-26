import streamlit as st
import pandas as pd
from modules.planilha import ler_planilha
from modules.utils import converter_para_float

def pagina_simulador(CONSTRUTORAS):
    st.title("📊 Simulador de Crédito")
    
    with st.sidebar:
        st.header("⚙️ Configurações")
        construtora = st.selectbox("🏗️ Selecione", list(CONSTRUTORAS.keys()))
        uploaded_file = st.file_uploader("📤 Envie a planilha", type=['xlsx', 'xls', 'csv', 'pdf'])
    
    if uploaded_file is None:
        st.info("👈 Selecione a construtora e envie uma planilha")
        return
    
    try:
        config = CONSTRUTORAS[construtora]
        df = ler_planilha(uploaded_file, config)
        if df is None:
            st.error("❌ Não foi possível ler a planilha.")
            return
        
        for col in config.get("colunas_para_converter", []):
            if col in df.columns:
                df[col] = df[col].apply(converter_para_float)
        
        st.markdown("---")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            tipo_col = None
            for c in ['TIPOLOGIA', 'QUARTOS', 'TIPO']:
                if c in df.columns:
                    tipo_col = c
                    break
            if tipo_col:
                tipos = ['Todas'] + sorted(df[tipo_col].dropna().unique().tolist())
                tipo = st.selectbox("🏠 Tipo", tipos)
            else:
                tipo = 'Todas'
        
        with col2:
            andar_col = None
            for c in ['PAVTO', 'ANDAR']:
                if c in df.columns:
                    andar_col = c
                    break
            if andar_col:
                andar_min = st.number_input("📌 Andar mínimo", min_value=0, value=0, step=1)
            else:
                andar_min = 0
        
        with col3:
            preco_col = None
            for c in ['PREÇO', 'VALOR']:
                if c in df.columns:
                    preco_col = c
                    break
            if preco_col and not df[preco_col].isna().all():
                preco_max = st.number_input("💰 Preço máximo", min_value=0, value=int(df[preco_col].max()), step=50000)
            else:
                preco_max = 1000000
        
        with col4:
            status_col = None
            for c in ['DISPONIBILIDADE', 'STATUS']:
                if c in df.columns:
                    status_col = c
                    break
            if status_col:
                status_opcoes = ['Todas'] + sorted(df[status_col].dropna().unique().tolist())
                status = st.selectbox("🔑 Disponibilidade", status_opcoes)
            else:
                status = 'Todas'
        
        resultado = df.copy()
        if tipo != 'Todas' and tipo_col:
            resultado = resultado[resultado[tipo_col] == tipo]
        if andar_min > 0 and andar_col:
            resultado = resultado[resultado[andar_col] >= andar_min]
        if preco_col:
            resultado = resultado[resultado[preco_col] <= preco_max]
        if status != 'Todas' and status_col:
            resultado = resultado[resultado[status_col] == status]
        
        if not resultado.empty:
            area_col = None
            for c in ['M²', 'AREA']:
                if c in resultado.columns:
                    area_col = c
                    break
            if preco_col and area_col:
                resultado['R$/m²'] = (resultado[preco_col] / resultado[area_col]).round(2)
        
        colunas = config.get("colunas_ordem", list(df.columns)).copy()
        if 'R$/m²' in resultado.columns:
            colunas.append('R$/m²')
        colunas = [c for c in colunas if c in resultado.columns]
        
        st.subheader(f"🔍 {len(resultado)} imóveis encontrados")
        if not resultado.empty:
            resultado_ordenado = resultado.sort_values('R$/m²') if 'R$/m²' in resultado.columns else resultado
            st.dataframe(resultado_ordenado[colunas], use_container_width=True, height=400)
            
            st.markdown("---")
            st.subheader("🤖 Recomendação da IA")
            melhor = resultado_ordenado.iloc[0]
            st.success(f"*Melhor custo-benefício:* Unidade {melhor['UNIDADE']}")
            if preco_col:
                st.write(f"💰 Preço: R$ {melhor[preco_col]:,.2f}")
            if 'R$/m²' in melhor:
                st.write(f"📊 R$/m²: R$ {melhor['R$/m²']:.2f}")
        else:
            st.warning("⚠️ Nenhum imóvel encontrado.")
    except Exception as e:
        st.error(f"❌ Erro: {str(e)}")
