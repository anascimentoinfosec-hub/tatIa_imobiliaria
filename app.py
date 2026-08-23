import streamlit as st
import pandas as pd
import io
import pdfplumber
import re

# CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="IA Imobiliária", layout="wide")
st.title("🏢 ImobFlux IA")
st.markdown("---")

# FUNÇÃO PARA CONVERTER VALORES MONETÁRIOS
def converter_para_float(valor):
    """Converte strings como 'R$ 399.440,00' ou 'R 440.000,00' para float"""
    if isinstance(valor, (int, float)):
        return float(valor)
    if not isinstance(valor, str):
        return 0.0
    
    # Remove R$, R, espaços e substitui vírgula por ponto
    valor_limpo = re.sub(r'[R$]', '', str(valor)).strip()
    valor_limpo = valor_limpo.replace('.', '').replace(',', '.')
    
    # Remove qualquer outro caractere não numérico (exceto ponto)
    valor_limpo = re.sub(r'[^0-9.]', '', valor_limpo)
    
    try:
        return float(valor_limpo)
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
    st.caption("Versão 1.0 - Desenvolvido com IA")

# CORPO PRINCIPAL
if uploaded_file is not None:
    try:
        # Lê o arquivo conforme o tipo
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
                    
                    # Procura onde está o cabeçalho
                    header_row = None
                    for i, row in enumerate(table_data):
                        if row:
                            row_text = ' '.join([str(cell).upper() for cell in row if cell])
                            if 'UNIDADE' in row_text or 'PAVTO' in row_text or 'M²' in row_text:
                                header_row = i
                                break
                    
                    if header_row is not None:
                        columns = []
                        for col in table_data[header_row]:
                            if col:
                                columns.append(str(col).strip())
                            else:
                                columns.append('')
                        
                        # Preenche colunas vazias
                        for i, col in enumerate(columns):
                            if not col or col == '':
                                columns[i] = f'col_{i}'
                        
                        df = pd.DataFrame(table_data[header_row + 1:], columns=columns)
                        df = df.dropna(how='all')
                        df = df[~df.iloc[:, 0].astype(str).str.strip().eq('')]
                    else:
                        st.error("❌ Cabeçalho da tabela não encontrado.")
                        st.stop()
                else:
                    st.error("❌ Nenhuma tabela encontrada no PDF.")
                    st.stop()
        elif uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file, skiprows=2)
        
        # Limpeza
        df = df.dropna(subset=['UNIDADE'])
        
        # Converte PREÇO usando a função universal
        if 'PREÇO' in df.columns:
            df['PREÇO'] = df['PREÇO'].apply(converter_para_float)
        
        # Converte 1ª AVALIAÇÃO
        if '1ª AVALIAÇÃO OÁSIS II' in df.columns:
            df['1ª AVALIAÇÃO OÁSIS II'] = df['1ª AVALIAÇÃO OÁSIS II'].apply(converter_para_float)
        
        # Converte DESCONTO (se existir)
        if 'DESCONTO' in df.columns:
            df['DESCONTO'] = df['DESCONTO'].apply(converter_para_float)
        
        with st.expander("📊 Visualizar dados da planilha"):
            st.dataframe(df)
        
        st.markdown("---")
        
        # FILTROS
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if 'TIPOLOGIA' in df.columns:
                tipologias = ['Todas'] + sorted(df['TIPOLOGIA'].unique().tolist())
                tipo_selecionado = st.selectbox("🏠 Tipologia", tipologias)
            else:
                tipo_selecionado = 'Todas'
        
        with col2:
            andar_min = st.number_input("📌 Andar mínimo", min_value=0, value=0)
        
        with col3:
            if 'PREÇO' in df.columns:
                preco_max = st.number_input(
                    "💰 Preço máximo (R$)",
                    min_value=100000,
                    value=int(df['PREÇO'].max()),
                    step=50000,
                    format="%d"
                )
            else:
                preco_max = 1000000
        
        with col4:
            if 'DISPONIBILIDADE' in df.columns:
                disponibilidade = st.selectbox(
                    "🔑 Disponibilidade",
                    ['Todas'] + sorted(df['DISPONIBILIDADE'].unique().tolist())
                )
            else:
                disponibilidade = 'Todas'
        
        # APLICA FILTROS
        resultado = df.copy()
        
        if tipo_selecionado != 'Todas' and 'TIPOLOGIA' in df.columns:
            resultado = resultado[resultado['TIPOLOGIA'] == tipo_selecionado]
        
        if andar_min > 0 and 'PAVTO.' in df.columns:
            resultado = resultado[resultado['PAVTO.'] >= andar_min]
        
        if 'PREÇO' in df.columns:
            resultado = resultado[resultado['PREÇO'] <= preco_max]
        
        if disponibilidade != 'Todas' and 'DISPONIBILIDADE' in df.columns:
            resultado = resultado[resultado['DISPONIBILIDADE'] == disponibilidade]
        
        # CALCULA INDICADORES
        if not resultado.empty:
            if 'PREÇO' in df.columns and 'M²' in df.columns:
                resultado['R$/m²'] = (resultado['PREÇO'] / resultado['M²']).round(2)
            
            if '1ª AVALIAÇÃO OÁSIS II' in df.columns and 'PREÇO' in df.columns:
                resultado['% DESCONTO'] = ((resultado['1ª AVALIAÇÃO OÁSIS II'] - resultado['PREÇO']) / resultado['1ª AVALIAÇÃO OÁSIS II'] * 100).round(1)
        
        # EXIBE RESULTADOS
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
                if 'PREÇO' in melhor:
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
            st.warning("⚠️ Nenhum imóvel encontrado com os filtros atuais. Tente ajustar.")
    
    except Exception as e:
        st.error(f"❌ Erro ao ler a planilha: {str(e)}")
        st.info("Verifique se o arquivo está no formato correto (XLSX, CSV ou PDF)")

else:
    st.info("👈 Envie a planilha da construtora no menu lateral para começar")
    st.markdown("""
    ### Como usar:
    1. Clique em *"Browse files"* no menu lateral
    2. Selecione a planilha (XLSX, CSV ou PDF) da construtora
    3. Ajuste os filtros
    4. A IA recomenda o melhor imóvel
    """)
