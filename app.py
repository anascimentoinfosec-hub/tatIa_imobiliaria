import streamlit as st
import pandas as pd
import io
import pdfplumber
import re

# CONFIGURAÇÃO
st.set_page_config(page_title="ImobFlux IA", layout="wide")
st.title("🏢 ImobFlux IA")
st.markdown("---")

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

# SIDEBAR
with st.sidebar:
    st.header("⚙️ Configurações")
    uploaded_file = st.file_uploader(
        "📤 Envie a planilha da construtora",
        type=['xlsx', 'xls', 'csv', 'pdf']
    )
    st.markdown("---")
    st.caption("Versão 1.0")

# CORPO PRINCIPAL
if uploaded_file is not None:
    try:
        # --- LEITURA ---
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
                    else:
                        st.error("❌ Cabeçalho não encontrado no PDF.")
                        st.stop()
                else:
                    st.error("❌ Nenhuma tabela encontrada no PDF.")
                    st.stop()
        elif uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df_raw = pd.read_excel(uploaded_file, header=None)
            
            header_row = None
            for i, row in df_raw.iterrows():
                row_text = ' '.join([str(cell).upper() for cell in row if pd.notna(cell)])
                if 'UNIDADE' in row_text:
                    header_row = i
                    break
            
            if header_row is None:
                st.error("❌ Cabeçalho 'UNIDADE' não encontrado.")
                st.stop()
            
            headers = df_raw.iloc[header_row].fillna('').astype(str).str.strip().tolist()
            dados = df_raw.iloc[header_row + 1:].reset_index(drop=True)
            
            colunas_validas = [(i, h) for i, h in enumerate(headers) if h and h != '']
            
            df = pd.DataFrame()
            for i, h in colunas_validas:
                df[h] = dados.iloc[:, i]
            
            df = df.dropna(how='all')
            if 'UNIDADE' in df.columns:
                df = df[df['UNIDADE'].notna() & (df['UNIDADE'].astype(str).str.strip() != '')]
        
        # --- CONVERSÃO ---
        colunas_para_converter = ['PREÇO', '1ª AVALIAÇÃO OÁSIS II', 'DESCONTO', 'M²', 'PAVTO.', 'PAVTO']
        for col in colunas_para_converter:
            if col in df.columns:
                df[col] = df[col].apply(converter_para_float)
        
        st.markdown("---")
        
        # --- FILTROS ---
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if 'TIPOLOGIA' in df.columns:
                tipologias = ['Todas'] + sorted(df['TIPOLOGIA'].dropna().unique().tolist())
                tipo_selecionado = st.selectbox("🏠 Tipologia", tipologias)
            else:
                tipo_selecionado = 'Todas'
        
        with col2:
            andar_min = st.number_input("📌 Andar mínimo", min_value=0, value=0, step=1)
        
        with col3:
            if 'PREÇO' in df.columns and not df['PREÇO'].isna().all():
                preco_max = st.number_input(
                    "💰 Preço máximo (R$)",
                    min_value=0,
                    value=int(df['PREÇO'].max()) if df['PREÇO'].max() > 0 else 1000000,
                    step=50000,
                    format="%d"
                )
            else:
                preco_max = 1000000
        
        with col4:
            if 'DISPONIBILIDADE' in df.columns:
                disp_opcoes = ['Todas'] + sorted(df['DISPONIBILIDADE'].dropna().unique().tolist())
                disponibilidade = st.selectbox("🔑 Disponibilidade", disp_opcoes)
            else:
                disponibilidade = 'Todas'
        
        # --- APLICA FILTROS ---
        resultado = df.copy()
        
        if tipo_selecionado != 'Todas' and 'TIPOLOGIA' in df.columns:
            resultado = resultado[resultado['TIPOLOGIA'] == tipo_selecionado]
        
        if andar_min > 0:
            col_pavto = 'PAVTO.' if 'PAVTO.' in df.columns else ('PAVTO' if 'PAVTO' in df.columns else None)
            if col_pavto:
                resultado = resultado[resultado[col_pavto] >= andar_min]
        
        if 'PREÇO' in df.columns:
            resultado = resultado[resultado['PREÇO'] <= preco_max]
        
        if disponibilidade != 'Todas' and 'DISPONIBILIDADE' in df.columns:
            resultado = resultado[resultado['DISPONIBILIDADE'] == disponibilidade]
        
        # --- INDICADORES ---
        if not resultado.empty:
            if 'PREÇO' in resultado.columns and 'M²' in resultado.columns:
                resultado['R$/m²'] = (resultado['PREÇO'] / resultado['M²']).round(2)
            
            if '1ª AVALIAÇÃO OÁSIS II' in resultado.columns and 'PREÇO' in resultado.columns:
                resultado['% DESCONTO'] = ((resultado['1ª AVALIAÇÃO OÁSIS II'] - resultado['PREÇO']) / resultado['1ª AVALIAÇÃO OÁSIS II'] * 100).round(1)
        
        # --- EXIBE ---
        st.subheader(f"🔍 Resultados: {len(resultado)} imóveis encontrados")
        
        if not resultado.empty:
            if 'R$/m²' in resultado.columns:
                resultado_ordenado = resultado.sort_values('R$/m²')
            else:
                resultado_ordenado = resultado
            
            colunas_base = ['UNIDADE', 'PAVTO.', 'COLUNA', 'M²', 'TIPOLOGIA', 'VAGA', 'SOL', 'PREÇO']
            colunas_extras = ['R$/m²', '% DESCONTO', 'DISPONIBILIDADE']
            colunas_exibir = [c for c in colunas_base + colunas_extras if c in resultado_ordenado.columns]
            
            st.dataframe(
                resultado_ordenado[colunas_exibir],
                use_container_width=True,
                height=400
            )
            
            st.markdown("---")
            st.subheader("🤖 Recomendação da IA")
            
            melhor = resultado_ordenado.iloc[0]
            
            col_a, col_b = st.columns([2, 1])
            
            with col_a:
                st.success(f"*Melhor custo-benefício:* Unidade {melhor['UNIDADE']}")
                if 'PREÇO' in melhor:
                    st.write(f"- *Preço:* R$ {melhor['PREÇO']:,.2f}")
                if 'R$/m²' in melhor:
                    st.write(f"- *R$/m²:* R$ {melhor['R$/m²']:.2f}")
                if '% DESCONTO' in melhor:
                    st.write(f"- *Desconto:* {melhor['% DESCONTO']}%")
                if 'TIPOLOGIA' in melhor:
                    st.write(f"- *Tipologia:* {melhor['TIPOLOGIA']}")
            
            with col_b:
                if 'PREÇO' in melhor and melhor['PREÇO'] > 0:
                    valor = melhor['PREÇO']
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
    st.info("👈 Envie a planilha da construtora no menu lateral para começar")
    st.markdown("""
    ### Como usar:
    1. Clique em *"Browse files"* no menu lateral
    2. Selecione a planilha (XLSX, CSV ou PDF) da construtora
    3. Ajuste os filtros
    4. A IA recomenda o melhor imóvel
    """)
