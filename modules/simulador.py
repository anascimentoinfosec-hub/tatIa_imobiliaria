import streamlit as st
import pandas as pd
from modules.planilha import ler_planilha
from modules.utils import converter_para_float
from modules.planilha_cache import salvar_planilha_cache, carregar_planilha_cache, tem_planilha_cache, excluir_planilha_cache
from modules.recomendacoes import recomendar_imoveis

def pagina_simulador(CONSTRUTORAS):
    st.title("📊 Simulador de Crédito")
    
    with st.sidebar:
        st.header("⚙️ Configurações")
        
        construtora_selecionada = st.selectbox(
            "🏗️ Selecione a construtora",
            options=list(CONSTRUTORAS.keys())
        )
        
        produtos = CONSTRUTORAS[construtora_selecionada].get("produtos", {})
        produtos_lista = list(produtos.keys())
        
        if produtos_lista:
            produto_selecionado = st.selectbox(
                "📦 Selecione o produto",
                options=produtos_lista
            )
        else:
            st.warning("⚠️ Nenhum produto cadastrado para esta construtora.")
            produto_selecionado = None
        
        st.markdown("---")
        
        if produto_selecionado:
            st.markdown("### 📤 Upload")
            uploaded_file = st.file_uploader(
                f"Planilha para {construtora_selecionada} - {produto_selecionado}",
                type=['xlsx', 'xls', 'csv', 'pdf'],
                key=f"upload_{construtora_selecionada}_{produto_selecionado}"
            )
            
            if st.button("📥 Carregar", use_container_width=True):
                if uploaded_file is not None:
                    config = produtos[produto_selecionado]
                    df = ler_planilha(uploaded_file, config)
                    if df is not None:
                        for col in config.get("colunas_para_converter", []):
                            if col in df.columns:
                                df[col] = df[col].apply(converter_para_float)
                        
                        if "AVALIAÇÃO" in df.columns:
                            df["AVALIAÇÃO"] = df["AVALIAÇÃO"].astype(str).str.replace('RS', '').str.replace('R$', '').str.replace('R', '').str.strip()
                            df["AVALIAÇÃO"] = df["AVALIAÇÃO"].str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
                            df["AVALIAÇÃO"] = df["AVALIAÇÃO"].str.extract(r'(\d+\.?\d*)')
                            df["AVALIAÇÃO"] = pd.to_numeric(df["AVALIAÇÃO"], errors='coerce').fillna(0)
                        
                        salvar_planilha_cache(construtora_selecionada, df, produto_selecionado)
                        st.success(f"✅ Planilha '{produto_selecionado}' carregada!")
                        st.rerun()
                    else:
                        st.error("❌ Erro ao ler a planilha")
                else:
                    st.warning("⚠️ Selecione uma planilha primeiro!")
            
            st.markdown("---")
            
            if st.button("🗑️ Limpar cache", use_container_width=True):
                excluir_planilha_cache(construtora_selecionada, produto_selecionado)
                st.success(f"✅ Cache de '{produto_selecionado}' removido!")
                st.rerun()
        
        st.markdown("---")
        st.caption("Versão 4.1 - Formatação de valores")
    
    # --- CORPO PRINCIPAL ---
    if not produto_selecionado:
        st.warning("⚠️ Selecione um produto para visualizar os dados.")
        return
    
    config = produtos[produto_selecionado]
    df = None
    
    if tem_planilha_cache(construtora_selecionada, produto_selecionado):
        df = carregar_planilha_cache(construtora_selecionada, produto_selecionado)
    
    if df is None:
        st.warning(f"⚠️ Nenhuma planilha disponível para '{produto_selecionado}'. Faça o upload.")
        return
    
    # --- FORÇA CONVERSÃO PARA FLOAT DAS COLUNAS MONETÁRIAS ---
    colunas_para_converter = ['PREÇO', 'VALOR', 'AVALIAÇÃO', 'DESCONTO', '1ª AVALIAÇÃO OÁSIS II']
    for col in colunas_para_converter:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    st.info(f"📂 Planilha carregada do cache: {construtora_selecionada} - {produto_selecionado}")
    
    # Guarda na sessão para o chat
    if "df_imoveis_cache" not in st.session_state:
        st.session_state.df_imoveis_cache = {}
    
    chave_cache = f"{construtora_selecionada}_{produto_selecionado}"
    st.session_state.df_imoveis_cache[chave_cache] = df
    st.session_state.df_imoveis = df
    
    st.markdown("---")
    
    # --- FILTROS ---
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
            tipo_selecionado = st.selectbox("🏠 Tipo", tipos)
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
            andar_min = st.number_input("📌 Andar mínimo", min_value=0, value=0, step=1)
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
                "💰 Preço máximo (R$)",
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
            status_selecionado = st.selectbox("🔑 Disponibilidade", status_opcoes)
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
    
    st.subheader(f"🔍 Resultados: {len(resultado)} imóveis encontrados")
    st.caption(f"📌 {construtora_selecionada} - {produto_selecionado}")
    
    if not resultado.empty:
        if 'R$/m²' in resultado.columns:
            resultado_ordenado = resultado.sort_values('R$/m²')
        else:
            resultado_ordenado = resultado
        
        # =========================================================
        # FORMATAÇÃO DAS COLUNAS MONETÁRIAS (FORÇADA)
        # =========================================================
        # Converte colunas para float (garantia)
        for col in resultado_ordenado.select_dtypes(include=['object']).columns:
            try:
                resultado_ordenado[col] = pd.to_numeric(resultado_ordenado[col], errors='coerce')
            except:
                pass
        
        column_config = {}
        
        # Lista de colunas monetárias
        colunas_monetarias = ['PREÇO', 'VALOR', 'AVALIAÇÃO', 'DESCONTO', '1ª AVALIAÇÃO OÁSIS II']
        for col in colunas_monetarias:
            if col in resultado_ordenado.columns:
                column_config[col] = st.column_config.NumberColumn(
                    col,
                    format="R$ %,.2f"
                )
        
        # Formata R$/m²
        if "R$/m²" in resultado_ordenado.columns:
            column_config["R$/m²"] = st.column_config.NumberColumn(
                "R$/m²",
                format="R$ %,.2f"
            )
        
        # Formata M² (se for numérico)
        if "M²" in resultado_ordenado.columns:
            column_config["M²"] = st.column_config.NumberColumn(
                "M²",
                format="%.2f"
            )
        
        st.dataframe(
            resultado_ordenado[colunas_ordem],
            use_container_width=True,
            height=400,
            column_config=column_config
        )
    
    st.markdown("---")
    
    # =========================================================
    # ÁREA DO CLIENTE
    # =========================================================
    st.subheader("🧑 Área do Cliente")
    st.markdown("Preencha os dados abaixo para receber recomendações personalizadas.")
    
    with st.container():
        col_cliente1, col_cliente2 = st.columns(2)
        
        with col_cliente1:
            nome_cliente = st.text_input("Nome do Cliente", placeholder="Ex: João Silva")
            renda_cliente = st.number_input(
                "💰 Renda líquida mensal (R$)",
                min_value=0.0,
                value=5000.0,
                step=500.0,
                format="%.2f"
            )
            entrada_cliente = st.number_input(
                "🏦 Valor disponível para entrada (R$)",
                min_value=0.0,
                value=100000.0,
                step=10000.0,
                format="%.2f"
            )
        
        with col_cliente2:
            bairro_preferencia = st.text_input("📍 Bairro de preferência", placeholder="Ex: Barra da Tijuca")
            quartos_preferencia = st.selectbox("🛏️ Quantos quartos?", ["Indiferente", "1", "2", "3", "4+"])
            tipo_preferencia = st.selectbox("🏠 Tipo de imóvel", ["Indiferente", "Apartamento", "Cobertura", "Garden"])
        
        if st.button("🔍 Analisar Oportunidades", use_container_width=True):
            if nome_cliente:
                with st.spinner("Analisando oportunidades para o cliente..."):
                    df_filtrado = resultado.copy()
                    
                    if quartos_preferencia != "Indiferente":
                        qtd = int(quartos_preferencia.replace("+", ""))
                        col_quartos = None
                        for c in ['QUARTOS', 'DORMITÓRIOS', 'TIPO']:
                            if c in df_filtrado.columns:
                                col_quartos = c
                                break
                        if col_quartos:
                            df_filtrado = df_filtrado[df_filtrado[col_quartos].astype(str).str.contains(str(qtd))]
                    
                    if tipo_preferencia != "Indiferente" and "TIPOLOGIA" in df_filtrado.columns:
                        df_filtrado = df_filtrado[df_filtrado["TIPOLOGIA"].str.contains(tipo_preferencia, case=False, na=False)]
                    
                    parcela_maxima = renda_cliente * 0.3
                    
                    if preco_col in df_filtrado.columns:
                        df_filtrado["parcela_estimada"] = df_filtrado[preco_col] * 0.005
                        df_filtrado = df_filtrado[df_filtrado["parcela_estimada"] <= parcela_maxima]
                        
                        if 'R$/m²' in df_filtrado.columns:
                            df_filtrado = df_filtrado.sort_values('R$/m²')
                    
                    top_recomendacoes = df_filtrado.head(5)
                    
                    if not top_recomendacoes.empty:
                        st.success(f"✅ *{len(top_recomendacoes)} oportunidades encontradas para {nome_cliente}:*")
                        
                        for idx, row in top_recomendacoes.iterrows():
                            with st.container():
                                st.markdown("---")
                                col_a, col_b = st.columns([3, 2])
                                
                                with col_a:
                                    st.markdown(f"*🏢 Unidade {row['UNIDADE']}*")
                                    if preco_col in row:
                                        st.write(f"💰 *Preço:* R$ {row[preco_col]:,.2f}")
                                    if 'R$/m²' in row:
                                        st.write(f"📊 *R$/m²:* R$ {row['R$/m²']:.2f}")
                                    if 'parcela_estimada' in row:
                                        st.write(f"📆 *Parcela estimada:* R$ {row['parcela_estimada']:,.2f}")
                                    if 'TIPOLOGIA' in row:
                                        st.write(f"🏠 *Tipo:* {row['TIPOLOGIA']}")
                                
                                with col_b:
                                    entrada_percentual = st.slider(
                                        f"Entrada (%) - Unidade {row['UNIDADE']}",
                                        min_value=20,
                                        max_value=50,
                                        value=30,
                                        step=5,
                                        key=f"entrada_{idx}"
                                    )
                                    valor_imovel = row[preco_col] if preco_col in row else 0
                                    entrada_valor = valor_imovel * (entrada_percentual / 100)
                                    financiado = valor_imovel - entrada_valor
                                    parcela_media = financiado * (1 + 0.10/12) / 420
                                    
                                    st.write(f"💵 *Entrada:* R$ {entrada_valor:,.2f}")
                                    st.write(f"🏦 *Financiado:* R$ {financiado:,.2f}")
                                    st.write(f"📆 *Parcela:* R$ {parcela_media:,.2f}")
                                    
                                    if st.button(f"💬 Perguntar sobre esta unidade", key=f"perguntar_{idx}"):
                                        st.session_state['pergunta_imovel'] = row['UNIDADE']
                                        st.session_state['pergunta_valor'] = row[preco_col] if preco_col in row else 0
                                        st.info("💬 Vá até o chat da BIA para perguntar sobre este imóvel!")
                    else:
                        st.warning(f"⚠️ Nenhuma oportunidade encontrada para {nome_cliente} com os critérios informados.")
            else:
                st.warning("⚠️ Por favor, informe o nome do cliente.")
        
        st.markdown("---")
        st.markdown("### 💰 Ajuste de Entrada")
        st.caption("Ajuste o percentual de entrada para simular diferentes cenários de financiamento.")
        
        entrada_percentual_global = st.slider(
            "Percentual de entrada (%)",
            min_value=20,
            max_value=50,
            value=30,
            step=5,
            key="entrada_global"
        )
        
        if preco_col in df.columns and not df.empty:
            valor_medio = df[preco_col].mean()
            entrada_media = valor_medio * (entrada_percentual_global / 100)
            financiado_medio = valor_medio - entrada_media
            parcela_media_global = financiado_medio * (1 + 0.10/12) / 420
            
            st.markdown("*📊 Simulação média com base nos imóveis disponíveis:*")
            col_s1, col_s2, col_s3 = st.columns(3)
            with col_s1:
                st.metric("💰 Valor médio", f"R$ {valor_medio:,.0f}")
            with col_s2:
                st.metric(f"💵 Entrada ({entrada_percentual_global}%)", f"R$ {entrada_media:,.0f}")
            with col_s3:
                st.metric("📆 Parcela média", f"R$ {parcela_media_global:,.0f}")
        
        st.markdown("---")
        if st.button("💬 Perguntar à BIA (IA Imobiliária)", use_container_width=True):
            st.session_state.pagina = "ChatIA"
            st.rerun()