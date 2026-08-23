import streamlit as st
import pandas as pd
import io
import pdfplumber
import re

# CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="ImobFlux IA", layout="wide")
st.title("🏢 ImobFlux IA")
st.markdown("---")

# --- FUNÇÕES AUXILIARES DE CONVERSÃO ---
def converter_moeda_br_para_float(valor):
    """Converte strings de moeda BR (R$ 1.234,56 ou 1.234,56) para float."""
    if isinstance(valor, (int, float)):
        return float(valor)
    if pd.isna(valor):
        return 0.0
    # Converte para string e limpa
    valor_str = str(valor).strip()
    # Remove "R$" e espaços
    valor_str = re.sub(r'R\$\s*', '', valor_str)
    # Remove pontos de milhar e substitui vírgula por ponto decimal
    valor_str = valor_str.replace('.', '').replace(',', '.')
    # Remove qualquer coisa que não seja número ou ponto
    valor_str = re.sub(r'[^0-9.]', '', valor_str)
    try:
        return float(valor_str)
    except ValueError:
        return 0.0

def converter_numero_br_para_float(valor):
    """Converte strings de número BR (1.234,56 ou 1,234.56) para float."""
    if isinstance(valor, (int, float)):
        return float(valor)
    if pd.isna(valor):
        return 0.0
    valor_str = str(valor).strip()
    # Se tiver vírgula e ponto, tenta identificar o padrão BR
    if ',' in valor_str and '.' in valor_str:
        # Ex: 1.234,56 -> 1234.56
        valor_str = valor_str.replace('.', '').replace(',', '.')
    elif ',' in valor_str:
        # Ex: 1,234 -> 1.234 ou 1234? Assumimos que é decimal (1,23 -> 1.23)
        # Vamos verificar se a vírgula parece ser decimal (ex: 59,49)
        partes = valor_str.split(',')
        if len(partes) == 2 and len(partes[1]) in [1, 2]:
            valor_str = valor_str.replace(',', '.')
        else:
            # Se não for decimal, remove a vírgula (ex: 1,234 -> 1234)
            valor_str = valor_str.replace(',', '')
    try:
        return float(valor_str)
    except ValueError:
        return 0.0

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Configurações")
    uploaded_file = st.file_uploader(
        "📤 Envie a planilha da construtora",
        type=['xlsx', 'xls', 'csv', 'pdf']
    )
    st.markdown("---")
    st.caption("Versão 1.0 - Desenvolvido com IA")

# --- CORPO PRINCIPAL ---
if uploaded_file is not None:
    try:
        # --- 1. LEITURA DO ARQUIVO ---
        if uploaded_file.name.endswith('.pdf'):
            # Leitura de PDF (já estava funcionando)
            with pdfplumber.open(io.BytesIO(uploaded_file.read())) as pdf:
                all_tables = []
                for page in pdf.pages:
                    tables = page.extract_tables()
                    for table in tables:
                        if table and len(table) > 1:
                            all_tables.append(table)
                if all_tables:
                    table_data = all_tables[0]
                    # Encontra o cabeçalho
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
                        st.error("❌ Cabeçalho da tabela não encontrado no PDF.")
                        st.stop()
                else:
                    st.error("❌ Nenhuma tabela encontrada no PDF.")
                    st.stop()
        elif uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            # --- LEITURA DO XLSX (CORRIGIDA) ---
            # Lê o arquivo sem cabeçalho para processar manualmente
            df_raw = pd.read_excel(uploaded_file, header=None)
            # Encontra a linha com os cabeçalhos
            header_row_idx = None
            for i, row in df_raw.iterrows():
                # Verifica se a linha contém a palavra 'UNIDADE' em alguma célula
                if row.astype(str).str.contains('UNIDADE', case=False, na=False).any():
                    header_row_idx = i
                    break

            if header_row_idx is None:
                st.error("❌ Cabeçalho 'UNIDADE' não encontrado no arquivo XLSX.")
                st.stop()

            # Define a linha do cabeçalho e os dados
            raw_headers = df_raw.iloc[header_row_idx].fillna('').astype(str).str.strip()
            data = df_raw.iloc[header_row_idx + 1:].reset_index(drop=True)
            
            # Limpa os cabeçalhos: remove colunas com cabeçalho vazio e renomeia
            valid_headers = []
            for i, header in enumerate(raw_headers):
                if header != '':
                    valid_headers.append((i, header))
            
            # Cria um novo DataFrame com apenas as colunas válidas
            df = pd.DataFrame()
            for original_idx, new_header in valid_headers:
                df[new_header] = data.iloc[:, original_idx]
            
            # Remove linhas que estão completamente vazias
            df = df.dropna(how='all')
            
            # Remove linhas onde a coluna 'UNIDADE' está vazia
            if 'UNIDADE' in df.columns:
                df = df[df['UNIDADE'].notna() & (df['UNIDADE'].astype(str).str.strip() != '')]
            else:
                st.error("❌ Coluna 'UNIDADE' não encontrada após limpeza.")
                st.stop()

        # --- 2. PRÉ-PROCESSAMENTO E CONVERSÃO ---
        # Garante que as colunas numéricas estão em float
        if 'PREÇO' in df.columns:
            df['PREÇO'] = df['PREÇO'].apply(converter_moeda_br_para_float)
        
        if '1ª AVALIAÇÃO OÁSIS II' in df.columns:
            df['1ª AVALIAÇÃO OÁSIS II'] = df['1ª AVALIAÇÃO OÁSIS II'].apply(converter_moeda_br_para_float)
        
        if 'DESCONTO' in df.columns:
            df['DESCONTO'] = df['DESCONTO'].apply(converter_moeda_br_para_float)
        
        if 'M²' in df.columns:
            df['M²'] = df['M²'].apply(converter_numero_br_para_float)
        
        # PAVTO pode vir como 'PAVTO' ou 'PAVTO.'
        coluna_pavto = None
        for col in ['PAVTO.', 'PAVTO']:
            if col in df.columns:
                coluna_pavto = col
                break
        if coluna_pavto:
            df[coluna_pavto] = df[coluna_pavto].apply(converter_numero_br_para_float)

        # Verifica se a conversão foi bem-sucedida (debug)
        with st.expander("📊 Dados após conversão (verifique os tipos)"):
            st.write(df.dtypes)
            st.dataframe(df)

        # --- 3. FILTROS E EXIBIÇÃO ---
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
            andar_min = st.number_input("📌 Andar mínimo", min_value=0, value=0, step=1)
        
        with col3:
            if 'PREÇO' in df.columns and not df['PREÇO'].isna().all():
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
        
        if andar_min > 0:
            if coluna_pavto and coluna_pavto in df.columns:
                resultado = resultado[resultado[coluna_pavto] >= andar_min]
        
        if 'PREÇO' in df.columns:
            resultado = resultado[resultado['PREÇO'] <= preco_max]
        
        if disponibilidade != 'Todas' and 'DISPONIBILIDADE' in df.columns:
            resultado = resultado[resultado['DISPONIBILIDADE'] == disponibilidade]
        
        # CALCULA INDICADORES
        if not resultado.empty:
            if 'PREÇO' in resultado.columns and 'M²' in resultado.columns:
                resultado['R$/m²'] = (resultado['PREÇO'] / resultado['M²']).round(2)
            
            if '1ª AVALIAÇÃO OÁSIS II' in resultado.columns and 'PREÇO' in resultado.columns:
                resultado['% DESCONTO'] = ((resultado['1ª AVALIAÇÃO OÁSIS II'] - resultado['PREÇO']) / resultado['1ª AVALIAÇÃO OÁSIS II'] * 100).round(1)
        
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
