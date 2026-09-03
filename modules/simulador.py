import streamlit as st
import pandas as pd
from modules.planilha import ler_planilha
from modules.utils import converter_para_float
from modules.planilha_cache import salvar_planilha_cache, carregar_planilha_cache, tem_planilha_cache, excluir_planilha_cache
from modules.recomendacoes import recomendar_imoveis
from modules.construtoras import carregar_cidades

def formatar_valor_br(valor):
    """Formata um float no padrão BR: R$ 1.234,56"""
    if valor is None or pd.isna(valor):
        return "R$ 0,00"
    us = f"{valor:,.2f}"
    br = us.replace(',', 'X').replace('.', ',').replace('X', '.')
    return f"R$ {br}"

def pagina_simulador(CONSTRUTORAS, USUARIOS):
    # Exibe mensagem persistente se houver (após rerun)
    if 'mensagem' in st.session_state:
        tipo, texto = st.session_state['mensagem']
        if tipo == 'success':
            st.success(texto)
        elif tipo == 'error':
            st.error(texto)
        elif tipo == 'warning':
            st.warning(texto)
        del st.session_state['mensagem']

    st.title("📊 Simulador de Crédito")
    
    usuario_logado = st.session_state.get("usuario_logado")
    if usuario_logado and usuario_logado in USUARIOS:
        perfil_usuario = USUARIOS[usuario_logado].get("perfil", "corretor")
    else:
        perfil_usuario = "corretor"
    
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
        
        if perfil_usuario in ["gerente", "superadmin"]:
            if produto_selecionado:
                st.markdown("### 📤 Upload")
                uploaded_file = st.file_uploader(
                    f"Planilha para {construtora_selecionada} - {produto_selecionado}",
                    type=['xlsx', 'xls', 'csv', 'pdf'],
                    key=f"upload_{construtora_selecionada}_{produto_selecionado}"
                )
                
                if st.button("📥 Carregar", use_container_width=True):
                    if uploaded_file is None:
                        st.session_state['mensagem'] = ("warning", "⚠️ Selecione um arquivo primeiro!")
                        st.rerun()
                    else:
                        try:
                            config = produtos[produto_selecionado]
                            df = ler_planilha(uploaded_file, config)
                            
                            if df is None:
                                st.session_state['mensagem'] = ("error", "❌ Erro ao ler a planilha. Verifique o formato e o mapeamento.")
                                st.rerun()
                            else:
                                # Converte colunas monetárias
                                colunas_monetarias = ['AVALIAÇÃO', 'PREÇO', 'VALOR', 'DESCONTO', '1ª AVALIAÇÃO OÁSIS II']
                                for col in colunas_monetarias:
                                    if col in df.columns:
                                        df[col] = df[col].astype(str).str.replace('RS', '', regex=False)
                                        df[col] = df[col].str.replace('R$', '', regex=False)
                                        df[col] = df[col].str.replace('R', '', regex=False)
                                        df[col] = df[col].str.strip()
                                        
                                        if col == 'PREÇO':
                                            df[col] = df[col].str.replace('.', '', regex=False)
                                            df[col] = df[col].str.replace(',', '.', regex=False)
                                            df[col] = df[col].str.extract(r'(\d+\.?\d*)')
                                            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
                                        else:
                                            df[col] = df[col].str.replace('.', '', regex=False)
                                            df[col] = df[col].str.replace(',', '.', regex=False)
                                            df[col] = df[col].str.extract(r'(\d+\.?\d*)')
                                            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
                                
                                for col in config.get("colunas_para_converter", []):
                                    if col in df.columns and col not in colunas_monetarias:
                                        df[col] = df[col].apply(converter_para_float)
                                
                                salvar_planilha_cache(construtora_selecionada, df, produto_selecionado)
                                st.session_state['mensagem'] = ("success", f"✅ Planilha '{produto_selecionado}' carregada com sucesso!")
                                st.rerun()
                        except Exception as e:
                            st.session_state['mensagem'] = ("error", f"❌ Erro ao carregar a planilha: {str(e)}")
                            st.rerun()
                
                st.markdown("---")
                
                if st.button("🗑️ Limpar cache", use_container_width=True):
                    excluir_planilha_cache(construtora_selecionada, produto_selecionado)
                    st.session_state['mensagem'] = ("success", f"✅ Cache de '{produto_selecionado}' removido!")
                    st.rerun()
        else:
            st.info("🔒 As planilhas são gerenciadas pelo gerente. Você está visualizando a versão mais recente disponível.")
        
        st.markdown("---")
        st.caption("Versão 4.3 - Formatação BR")
    
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
    
    colunas_monetarias = ['AVALIAÇÃO', 'PREÇO', 'VALOR', 'DESCONTO', '1ª AVALIAÇÃO OÁSIS II']
    for col in colunas_monetarias:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    st.info(f"📂 Planilha carregada do cache: {construtora_selecionada} - {produto_selecionado}")
    
    if "df_imoveis_cache" not in st.session_state:
        st.session_state.df_imoveis_cache = {}
    
    chave_cache = f"{construtora_selecionada}_{produto_selecionado}"
    st.session_state.df_imoveis_cache[chave_cache] = df
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
        
        df_exibicao = resultado_ordenado.copy()
        
        colunas_monetarias_exibicao = ['PREÇO', 'VALOR', 'AVALIAÇÃO', 'DESCONTO', '1ª AVALIAÇÃO OÁSIS II', 'R$/m²']
        for col in colunas_monetarias_exibicao:
            if col in df_exibicao.columns:
                df_exibicao[col] = df_exibicao[col].apply(formatar_valor_br)
        
        if "M²" in df_exibicao.columns:
            df_exibicao["M²"] = df_exibicao["M²"].apply(lambda x: f"{x:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.') if not pd.isna(x) else "")
        
        st.dataframe(
            df_exibicao[colunas_ordem],
            use_container_width=True,
            height=400
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
                format="%.2f",
                help="Informe a renda líquida mensal do cliente."
            )
            entrada_cliente = st.number_input(
                "🏦 Valor disponível para entrada (R$)",
                min_value=0.0,
                value=100000.0,
                step=10000.0,
                format="%.2f",
                help="Valor que o cliente pode dar de entrada."
            )
        
        with col_cliente2:
            cidades_disponiveis = carregar_cidades()
            opcoes_bairro = [""] + cidades_disponiveis
            bairro_preferencia = st.selectbox("📍 Bairro de preferência", opcoes_bairro)
            
            quartos_preferencia = st.selectbox("🛏️ Quantos quartos?", ["Indiferente", "1", "2", "3", "4+"])
            tipo_preferencia = st.selectbox("🏠 Tipo de imóvel", ["Indiferente", "Apartamento", "Cobertura", "Garden"])
        
        if st.button("🔍 Analisar Oportunidades", use_container_width=True):
            if not nome_cliente:
                st.session_state['mensagem'] = ("warning", "⚠️ Por favor, informe o nome do cliente.")
                st.rerun()
            else:
                with st.spinner("Analisando oportunidades para o cliente..."):
                    try:
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
                            df_filtrado = df_filtrado[df_filtrado["TIPOLOGIA"].astype(str).str.contains(tipo_preferencia, case=False, na=False)]
                        
                        parcela_maxima = renda_cliente * 0.3
                        
                        if preco_col in df_filtrado.columns:
                            df_filtrado["parcela_estimada"] = df_filtrado[preco_col] * 0.005
                            df_filtrado = df_filtrado[df_filtrado["parcela_estimada"] <= parcela_maxima]
                            
                            if 'R$/m²' in df_filtrado.columns:
                                df_filtrado = df_filtrado.sort_values('R$/m²')
                        
                        top_recomendacoes = df_filtrado.head(5)
                        
                        if not top_recomendacoes.empty:
                            st.session_state['mensagem'] = ("success", f"✅ {len(top_recomendacoes)} oportunidades encontradas para {nome_cliente}!")
                            st.rerun()
                        else:
                            st.session_state['mensagem'] = ("warning", f"⚠️ Nenhuma oportunidade encontrada para {nome_cliente} com os critérios informados.")
                            st.rerun()
                    except Exception as e:
                        st.session_state['mensagem'] = ("error", f"❌ Erro ao analisar oportunidades: {str(e)}")
                        st.rerun()
        
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
                st.metric("💰 Valor médio", formatar_valor_br(valor_medio))
            with col_s2:
                st.metric(f"💵 Entrada ({entrada_percentual_global}%)", formatar_valor_br(entrada_media))
            with col_s3:
                st.metric("📆 Parcela média", formatar_valor_br(parcela_media_global))
        
        st.markdown("---")
        if st.button("💬 Perguntar à BIA (IA Imobiliária)", use_container_width=True):
            st.session_state.pagina = "ChatIA"
            st.rerun()