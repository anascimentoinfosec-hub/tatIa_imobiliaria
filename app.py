import streamlit as st
import pandas as pd
import io
import pdfplumber
import re
import json
import os

# CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Simulador de Crédito", layout="wide")
st.title("🏢 Simulador de Crédito")
st.markdown("---")

# --- SENHA DO GERENTE (altere aqui) ---
SENHA_GERENTE = "gerente2026"

# --- ARQUIVO DE CONFIGURAÇÃO ---
ARQUIVO_CONFIG = "construtoras.json"

# --- FUNÇÃO PARA CARREGAR CONFIGURAÇÕES ---
def carregar_construtoras():
    """Carrega as construtoras do arquivo JSON ou usa o padrão"""
    try:
        if os.path.exists(ARQUIVO_CONFIG):
            with open(ARQUIVO_CONFIG, 'r', encoding='utf-8') as f:
                return json.load(f)
    except:
        pass
    
    # Configuração padrão (Oásis II)
    return {
        "Oásis II": {
            "skiprows": 2,
            "mapeamento": {
                "0": "UNIDADE", "1": "PAVTO", "2": "COLUNA", "3": "M²",
                "4": "TIPOLOGIA", "5": "VAGA", "6": "SOL",
                "8": "1ª AVALIAÇÃO OÁSIS II", "10": "DESCONTO", "12": "PREÇO", "13": "DISPONIBILIDADE"
            },
            "colunas_ordem": ["UNIDADE", "PAVTO", "COLUNA", "M²", "TIPOLOGIA", "VAGA", "SOL", "1ª AVALIAÇÃO OÁSIS II", "DESCONTO", "PREÇO", "DISPONIBILIDADE"],
            "colunas_para_converter": ["PREÇO", "1ª AVALIAÇÃO OÁSIS II", "DESCONTO", "M²", "PAVTO"]
        }
    }

# --- FUNÇÃO PARA SALVAR CONFIGURAÇÕES ---
def salvar_construtoras(construtoras):
    """Salva as construtoras no arquivo JSON"""
    with open(ARQUIVO_CONFIG, 'w', encoding='utf-8') as f:
        json.dump(construtoras, f, indent=2, ensure_ascii=False)

# --- FUNÇÃO DE CONVERSÃO ---
def converter_para_float(valor):
    if valor is None or pd.isna(valor):
        return 0.0
    if isinstance(valor, (int, float)):
        return float(valor)
    
    valor_str = str(valor).strip()
    valor_str = re.sub(r'R\$\s*', '', valor_str)
    
    if '.' in valor_str and ',' in valor_str:
        valor_str = valor_str.replace('.', '').replace(',', '.')
    elif ',' in valor_str:
        partes = valor_str.split(',')
        if len(partes) == 2 and len(partes[1]) <= 2:
            valor_str = valor_str.replace(',', '.')
        else:
            valor_str = valor_str.replace(',', '')
    
    valor_str = re.sub(r'[^0-9.]', '', valor_str)
    
    try:
        return float(valor_str)
    except:
        return 0.0

# --- FUNÇÃO PARA LER PLANILHA ---
def ler_planilha(uploaded_file, config):
    """Lê a planilha com a configuração da construtora"""
    try:
        if uploaded_file.name.endswith('.pdf'):
            with pdfplumber.open(io.BytesIO(uploaded_file.read())) as pdf:
                all_tables = []
                for page in pdf.pages:
                    tables = page.extract_tables()
                    for table in tables:
                        if table and len(table) > 1:
                            all_tables.append(table)
                if all_tables:
                    table_data = all_tables[0]
                    header_row = None
                    for i, row in enumerate(table_data):
                        if row:
                            row_text = ' '.join([str(cell).upper() for cell in row if cell])
                            if 'UNIDADE' in row_text:
                                header_row = i
                                break
                    if header_row is not None:
                        columns = [str(col).strip() if col else f'col_{i}' for i, col in enumerate(table_data[header_row])]
                        df = pd.DataFrame(table_data[header_row + 1:], columns=columns)
                        df = df.dropna(how='all')
                        df = df[~df.iloc[:, 0].astype(str).str.strip().eq('')]
                        return df
                    else:
                        return None
                else:
                    return None
        elif uploaded_file.name.endswith('.csv'):
            return pd.read_csv(uploaded_file)
        else:
            df_raw = pd.read_excel(uploaded_file, header=None)
            
            # Encontra a linha do cabeçalho
            linha_cabecalho = None
            for i, row in df_raw.iterrows():
                row_text = ' '.join([str(cell).upper() for cell in row if pd.notna(cell)])
                if 'UNIDADE' in row_text:
                    linha_cabecalho = i
                    break
            
            if linha_cabecalho is None:
                return None
            
            dados = df_raw.iloc[linha_cabecalho + 1:].reset_index(drop=True)
            
            # Aplica o mapeamento
            mapeamento = config.get("mapeamento", {})
            df = pd.DataFrame()
            for idx_str, nome_novo in mapeamento.items():
                idx = int(idx_str)
                if idx < len(dados.columns):
                    df[nome_novo] = dados.iloc[:, idx]
            
            # Remove linhas vazias
            df = df.dropna(how='all')
            if 'UNIDADE' in df.columns:
                df = df[df['UNIDADE'].notna() & (df['UNIDADE'].astype(str).str.strip() != '')]
            
            return df
    except:
        return None

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Configurações")
    
    # --- VERIFICA SE É GERENTE ---
    is_gerente = False
    if st.checkbox("🔧 Painel do Gerente"):
        senha_digitada = st.text_input("Senha do Gerente:", type="password")
        if senha_digitada == SENHA_GERENTE:
            is_gerente = True
            st.success("✅ Acesso liberado!")
        elif senha_digitada:
            st.error("❌ Senha incorreta!")
    
    st.markdown("---")
    
    # Carrega as construtoras
    CONSTRUTORAS = carregar_construtoras()
    
    # Se for gerente, mostra o painel de gestão
    if is_gerente:
        with st.expander("🔧 Gerenciar Construtoras", expanded=True):
            st.markdown("#### Adicionar Nova Construtora")
            
            # Formulário para adicionar
            with st.form("form_nova_construtora"):
                nome = st.text_input("Nome da Construtora")
                skiprows = st.number_input("Linhas para pular (skiprows)", min_value=0, value=0, step=1)
                
                st.markdown("*Mapeamento de colunas (índice: nome)*")
                st.caption("Ex: 0:UNIDADE, 1:PAVTO, 2:PREÇO")
                mapeamento_str = st.text_area(
                    "Digite o mapeamento",
                    placeholder='{"0": "UNIDADE", "1": "PAVTO", "2": "PREÇO"}',
                    height=100
                )
                
                st.markdown("*Colunas para exibir*")
                st.caption("Ex: UNIDADE, PAVTO, PREÇO")
                colunas_ordem_str = st.text_input(
                    "Colunas (separadas por vírgula)",
                    placeholder="UNIDADE, PAVTO, PREÇO"
                )
                
                st.markdown("*Colunas numéricas*")
                st.caption("Ex: PREÇO, M², ANDAR")
                colunas_numericas_str = st.text_input(
                    "Colunas numéricas (separadas por vírgula)",
                    placeholder="PREÇO, M², ANDAR"
                )
                
                submitted = st.form_submit_button("➕ Adicionar Construtora")
                
                if submitted and nome:
                    try:
                        # Converte o mapeamento
                        if mapeamento_str:
                            mapeamento = json.loads(mapeamento_str)
                        else:
                            mapeamento = {}
                        
                        # Converte listas
                        colunas_ordem = [c.strip() for c in colunas_ordem_str.split(',') if c.strip()]
                        colunas_numericas = [c.strip() for c in colunas_numericas_str.split(',') if c.strip()]
                        
                        # Adiciona a nova construtora
                        CONSTRUTORAS[nome] = {
                            "skiprows": skiprows,
                            "mapeamento": {str(k): v for k, v in mapeamento.items()},
                            "colunas_ordem": colunas_ordem,
                            "colunas_para_converter": colunas_numericas
                        }
                        
                        salvar_construtoras(CONSTRUTORAS)
                        st.success(f"✅ Construtora '{nome}' adicionada com sucesso!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Erro ao adicionar: {str(e)}")
            
            st.markdown("---")
            
            # Lista as construtoras existentes
            st.markdown("#### Construtoras Cadastradas")
            for nome, config in CONSTRUTORAS.items():
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.write(f"*{nome}*")
                with col2:
                    if st.button(f"🗑️ Excluir", key=f"del_{nome}"):
                        del CONSTRUTORAS[nome]
                        salvar_construtoras(CONSTRUTORAS)
                        st.rerun()
                with col3:
                    if st.button(f"📋 Editar", key=f"edit_{nome}"):
                        st.session_state['editando'] = nome
                
                # Edição inline
                if st.session_state.get('editando') == nome:
                    with st.form(f"form_edit_{nome}"):
                        novo_nome = st.text_input("Novo nome", value=nome)
                        novo_skiprows = st.number_input("Skiprows", value=config.get("skiprows", 0), step=1)
                        
                        novo_mapeamento = st.text_area(
                            "Mapeamento",
                            value=json.dumps(config.get("mapeamento", {}), indent=2, ensure_ascii=False),
                            height=100
                        )
                        
                        novo_colunas_ordem = st.text_input(
                            "Colunas para exibir",
                            value=", ".join(config.get("colunas_ordem", []))
                        )
                        
                        novo_colunas_numericas = st.text_input(
                            "Colunas numéricas",
                            value=", ".join(config.get("colunas_para_converter", []))
                        )
                        
                        col_edit1, col_edit2 = st.columns(2)
                        with col_edit1:
                            if st.form_submit_button("💾 Salvar"):
                                try:
                                    # Remove a antiga
                                    del CONSTRUTORAS[nome]
                                    
                                    # Adiciona a nova
                                    CONSTRUTORAS[novo_nome] = {
                                        "skiprows": novo_skiprows,
                                        "mapeamento": json.loads(novo_mapeamento),
                                        "colunas_ordem": [c.strip() for c in novo_colunas_ordem.split(',') if c.strip()],
                                        "colunas_para_converter": [c.strip() for c in novo_colunas_numericas.split(',') if c.strip()]
                                    }
                                    
                                    salvar_construtoras(CONSTRUTORAS)
                                    st.session_state['editando'] = None
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"❌ Erro: {str(e)}")
                        
                        with col_edit2:
                            if st.form_submit_button("❌ Cancelar"):
                                st.session_state['editando'] = None
                                st.rerun()
        
        st.markdown("---")
    
    # --- SELEÇÃO DA CONSTRUTORA (para todos) ---
    construtora_selecionada = st.selectbox(
        "🏗️ Selecione a construtora",
        options=list(CONSTRUTORAS.keys())
    )
    
    st.markdown("---")
    
    # Upload do arquivo
    uploaded_file = st.file_uploader(
        "📤 Envie a planilha",
        type=['xlsx', 'xls', 'csv', 'pdf']
    )
    
    st.markdown("---")
    st.caption("Versão 2.0 - Multi Construtoras")

# --- CORPO PRINCIPAL ---
if uploaded_file is not None:
    try:
        # Pega a configuração da construtora selecionada
        config = CONSTRUTORAS[construtora_selecionada]
        
        # Lê a planilha
        df = ler_planilha(uploaded_file, config)
        
        if df is None:
            st.error("❌ Não foi possível ler a planilha. Verifique o formato e o mapeamento.")
            st.stop()
        
        # --- CONVERSÃO DE COLUNAS NUMÉRICAS ---
        for col in config.get("colunas_para_converter", []):
            if col in df.columns:
                df[col] = df[col].apply(converter_para_float)
        
        st.markdown("---")
        
        # --- FILTROS DINÂMICOS ---
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
        
        # --- APLICA FILTROS ---
        resultado = df.copy()
        
        if tipo_selecionado != 'Todas' and tipo_col:
            resultado = resultado[resultado[tipo_col] == tipo_selecionado]
        
        if andar_min > 0 and andar_col:
            resultado = resultado[resultado[andar_col] >= andar_min]
        
        if preco_col and preco_col in df.columns:
            resultado = resultado[resultado[preco_col] <= preco_max]
        
        if status_selecionado != 'Todas' and status_col:
            resultado = resultado[resultado[status_col] == status_selecionado]
        
        # --- INDICADORES ---
        if not resultado.empty:
            colunas_area = ['M²', 'AREA_M2', 'AREA']
            area_col = None
            for c in colunas_area:
                if c in resultado.columns:
                    area_col = c
                    break
            
            if preco_col and area_col:
                resultado['R$/m²'] = (resultado[preco_col] / resultado[area_col]).round(2)
        
        # --- ORDEM DAS COLUNAS ---
        colunas_ordem = config.get("colunas_ordem", list(df.columns)).copy()
        if 'R$/m²' in resultado.columns:
            colunas_ordem.append('R$/m²')
        
        colunas_ordem = [c for c in colunas_ordem if c in resultado.columns]
        
        # --- EXIBE ---
        st.subheader(f"🔍 Resultados: {len(resultado)} imóveis encontrados - {construtora_selecionada}")
        
        if not resultado.empty:
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
            st.subheader("🤖 Recomendação da IA")
            
            melhor = resultado_ordenado.iloc[0]
            
            col_a, col_b = st.columns([2, 1])
            
            with col_a:
                st.success(f"*Melhor custo-benefício:* Unidade {melhor['UNIDADE']}")
                if preco_col and preco_col in melhor:
                    st.write(f"- *Preço:* R$ {melhor[preco_col]:,.2f}")
                if 'R$/m²' in melhor:
                    st.write(f"- *R$/m²:* R$ {melhor['R$/m²']:.2f}")
                if '1ª AVALIAÇÃO OÁSIS II' in melhor:
                    st.write(f"- *Avaliação:* R$ {melhor['1ª AVALIAÇÃO OÁSIS II']:,.2f}")
                if 'DESCONTO' in melhor:
                    st.write(f"- *Desconto:* R$ {melhor['DESCONTO']:,.2f}")
                if tipo_col and tipo_col in melhor:
                    st.write(f"- *Tipo:* {melhor[tipo_col]}")
            
            with col_b:
                if preco_col and preco_col in melhor and melhor[preco_col] > 0:
                    valor = melhor[preco_col]
                    entrada_percentual = st.slider("Entrada (%)", 20, 50, 30)
                    entrada = valor * (entrada_percentual / 100)
                    financiado = valor - entrada
                    juros = 0.10
                    prazo_meses = 420
                    parcela_media = financiado * (1 + juros/12) / prazo_meses
                    
                    st.info(f"*Simulação - Unidade {melhor['UNIDADE']}*")
                    st.write(f"Valor total: R$ {valor:,.2f}")
                    st.write(f"Entrada ({entrada_percentual}%): R$ {entrada:,.2f}")
                    st.write(f"Financiado: R$ {financiado:,.2f}")
                    st.write(f"Parcela estimada: R$ {parcela_media:,.2f}")
                    st.caption(f"Prazo: {prazo_meses} meses (35 anos), juros: {juros*100}% a.a. (SAC)")
                else:
                    st.warning("⚠️ Valor do imóvel não disponível para simulação.")
        else:
            st.warning("⚠️ Nenhum imóvel encontrado com os filtros atuais.")
    
    except Exception as e:
        st.error(f"❌ Erro ao ler a planilha: {str(e)}")
        st.info("Verifique o formato do arquivo (XLSX, CSV ou PDF).")

else:
    st.info("👈 Selecione a construtora e envie a planilha no menu lateral para começar")
    st.markdown("""
    ### Como usar:
    1. Selecione a *construtora* no menu lateral
    2. Envie a planilha da construtora (XLSX, CSV ou PDF)
    3. Ajuste os filtros disponíveis
    4. A IA recomenda o melhor imóvel
    """)
