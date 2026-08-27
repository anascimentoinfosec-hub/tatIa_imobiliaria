import streamlit as st
import pandas as pd
from modules.planilha import ler_planilha
from modules.utils import converter_para_float
#from modules.planilha_cache import salvar_planilha_cache, carregar_planilha_cache, tem_planilha_cache

def pagina_simulador(CONSTRUTORAS):
    st.title(" Simulador de Crédito")
    
    with st.sidebar:
        st.header(" Configurações")
        
        construtora_selecionada = st.selectbox(
            " Selecione a construtora",
            options=list(CONSTRUTORAS.keys())
        )
        
        st.markdown("---")
        
        uploaded_file = st.file_uploader(
            " Envie a planilha",
            type=['xlsx', 'xls', 'csv', 'pdf']
        )
        
        st.markdown("---")
        st.caption("Versão 2.0 - Multi Construtoras")
        
    # --- CORPO PRINCIPAL ---
    if uploaded_file is None:
        st.info(" Selecione a construtora e envie uma planilha para começar")
        
        st.markdown("### Mercado Imobiliário")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Taxa Selic", "10,50%")
            st.metric("TR", "1,50% a.a.")
        with col2:
            st.metric("Taxa SFH", "9,50% a.a.")
            st.metric("Entrada média", "20-30%")
        with col3:
            st.metric("Valor m² (RJ)", "R$ 12.800")
            st.metric("Prazo máximo", "420 meses")
        
        st.markdown("---")
        st.markdown("### Empreendimento em Destaque")
        st.success("**Oásis II** \n Barra da Tijuca - Rio de Janeiro \n 18 andares • 115 unidades • 2 e 3 quartos \n Preços a partir de R$ 384.950")
        
        return
        
    # --- PROCESSAMENTO DA PLANILHA ---
    try:
        config = CONSTRUTORAS[construtora_selecionada]
        
        # --- VERIFICA SE JÁ EXISTE PLANILHA EM CACHE ---
        planilha_carregada = False
        df = None
        
        # Se o usuário fez upload, processa e salva em cache
        if uploaded_file is not None:
            df = ler_planilha(uploaded_file, config)
            if df is not None:
                # Converte colunas numéricas
                for col in config.get("colunas_para_converter", []):
                    if col in df.columns:
                        df[col] = df[col].apply(converter_para_float)
                
                # --- CORREÇÃO PARA COLUNA AVALIAÇÃO ---
                if "AVALIAÇÃO" in df.columns:
                    df["AVALIAÇÃO"] = df["AVALIAÇÃO"].astype(str).str.replace('RS', '').str.replace('R$', '').str.replace('R', '').str.strip()
                    df["AVALIAÇÃO"] = df["AVALIAÇÃO"].str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
                    df["AVALIAÇÃO"] = df["AVALIAÇÃO"].str.extract(r'(\d+\.?\d*)')
                    df["AVALIAÇÃO"] = pd.to_numeric(df["AVALIAÇÃO"], errors='coerce').fillna(0)
                
                # Salva em cache
                salvar_planilha_cache(construtora_selecionada, df)
                st.success(f" Planilha '{construtora_selecionada}' carregada e salva em cache!")
                planilha_carregada = True
                
        # Se não fez upload, tenta carregar do cache
        elif tem_planilha_cache(construtora_selecionada):
            df = carregar_planilha_cache(construtora_selecionada)
            if df is not None:
                st.info(f" Planilha carregada do cache: {construtora_selecionada} (atualize com novo upload)")
                planilha_carregada = True
                
        # Se não tem cache, mostra mensagem
        if not planilha_carregada or df is None:
            st.warning(f" Nenhuma planilha disponível para '{construtora_selecionada}'. Faça o upload.")
            return
            
        # =============================================
        # GUARDA O DATAFRAME NA SESSÃO PARA O CHAT
        # =============================================
        st.session_state.df_imoveis = df
        
        st.markdown("---")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            colunas_tipo = ['TIPOLOGIA', 'QUARTOS', 'DORMITÓRIOS', 'TIPO']
            tipo_col = None
            for c in colunas_tipo:
                if c in df.columns:
                    tipo_col = c
                    break
                    
            if tipo_col:
                tipos = ['Todas'] + sorted(df[tipo_col].dropna().unique().tolist())
                tipo_selecionado = st.selectbox(" Tipo", tipos)
            else:
                tipo_selecionado = 'Todas'
                
        with col2:
            colunas_andar = ['PAVTO', 'ANDAR']
            andar_col = None
            for c in colunas_andar:
                if c in df.columns:
                    andar_col = c
                    break
                    
            if andar_col:
                andar_min = st.number_input(" Andar mínimo", min_value=0, value=0, step=1)
            else:
                andar_min = 0
                
        with col3:
            colunas_preco = ['PREÇO', 'VALOR']
            preco_col = None
            for c in colunas_preco:
                if c in df.columns:
                    preco_col = c
                    break
                    
            if preco_col and not df[preco_col].isna().all():
                preco_max = st.number_input(
                    " Preço máximo (R$)",
                    min_value=0,
                    value=int(df[preco_col].max()) if df[preco_col].max() > 0 else 1000000,
                    step=50000,
                    format="%d"
                )
            else:
                preco_max = 1000000
                
        with col4:
            colunas_status = ['DISPONIBILIDADE', 'STATUS', 'SITUAÇÃO']
            status_col = None
            for c in colunas_status:
                if c in df.columns:
                    status_col = c
                    break
                    
            if status_col:
                status_opcoes = ['Todas'] + sorted(df[status_col].dropna().unique().tolist())
                status_selecionado = st.selectbox(" Disponibilidade", status_opcoes)
            else:
                status_selecionado = 'Todas'
                
        resultado = df.copy()
        
        if tipo_selecionado != 'Todas' and tipo_col:
            resultado = resultado[resultado[tipo_col] == tipo_selecionado]
            
        if andar_min > 0 and andar_col:
            resultado = resultado[resultado[andar_col] >= andar_min]
            
        if preco_col and preco_col in df.columns:
            resultado = resultado[resultado[preco_col] <= preco_max]
            
        if status_selecionado != 'Todas' and status_col:
            resultado = resultado[resultado[status_col] == status_selecionado]
            
        if not resultado.empty:
            colunas_area = ['M²', 'AREA_M2', 'AREA']
            area_col = None
            for c in colunas_area:
                if c in resultado.columns:
                    area_col = c
                    break
                    
            if preco_col and area_col:
                resultado['R$/m²'] = (resultado[preco_col] / resultado[area_col]).round(2)
                
            colunas_ordem = config.get("colunas_ordem", list(df.columns)).copy()
            if 'R$/m²' in resultado.columns:
                colunas_ordem.append('R$/m²')
                
            colunas_ordem = [c for c in colunas_ordem if c in resultado.columns]
            
            st.subheader(f" Resultados: {len(resultado)} imóveis encontrados - {construtora_selecionada}")
            
            if 'R$/m²' in resultado.columns:
                resultado_ordenado = resultado.sort_values('R$/m²')
            else:
                resultado_ordenado = resultado
                
            st.dataframe(
                resultado_ordenado[colunas_ordem],
                use_container_width=True,
                height=400
            )
            
            st.markdown("---")
            st.subheader(" Recomendação da IA")
            
            melhor = resultado_ordenado.iloc[0]
            
            col_a, col_b = st.columns([2, 1])
            
            with col_a:
                st.success(f"**Melhor custo-benefício:** Unidade {melhor['UNIDADE']}")
                if preco_col and preco_col in melhor:
                    st.write(f"- **Preço:** R$ {melhor[preco_col]:,.2f}")
                if 'R$/m²' in melhor:
                    st.write(f"- **R$/m²:** R$ {melhor['R$/m²']:.2f}")
                if 'AVALIAÇÃO' in melhor:
                    st.write(f"- **Avaliação:** R$ {melhor['AVALIAÇÃO']:,.2f}")
                if '1ª AVALIAÇÃO OÁSIS II' in melhor:
                    st.write(f"- **Avaliação:** R$ {melhor['1ª AVALIAÇÃO OÁSIS II']:,.2f}")
                if 'DESCONTO' in melhor:
                    st.write(f"- **Desconto:** R$ {melhor['DESCONTO']:,.2f}")
                if tipo_col and tipo_col in melhor:
                    st.write(f"- **Tipo:** {melhor[tipo_col]}")
                    
            with col_b:
                if preco_col and preco_col in melhor and melhor[preco_col] > 0:
                    valor = melhor[preco_col]
                    entrada_percentual = st.slider("Entrada (%)", 20, 50, 30)
                    entrada = valor * (entrada_percentual / 100)
                    financiado = valor - entrada
                    juros = 0.10
                    prazo_meses = 420
                    parcela_media = financiado * (1 + juros/12) / prazo_meses
                    
                    st.info(f"**Simulação - Unidade {melhor['UNIDADE']}**")
                    st.write(f"Valor total: R$ {valor:,.2f}")
                    st.write(f"Entrada ({entrada_percentual}%): R$ {entrada:,.2f}")
                    st.write(f"Financiado: R$ {financiado:,.2f}")
                    st.write(f"Parcela estimada: R$ {parcela_media:,.2f}")
