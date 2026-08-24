import streamlit as st
import pandas as pd
import io
import pdfplumber
import re

# CONFIGURAÇÃO
st.set_page_config(page_title="ImobFlux IA", layout="wide")
st.title("🏢 ImobFlux IA - Modo de Inspeção")
st.markdown("---")

# --- FUNÇÃO DE CONVERSÃO ---
def converter_para_float(valor):
    """Converte strings de moeda BR para float."""
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
    st.caption("Versão 1.0 - Modo de Inspeção")

# CORPO PRINCIPAL
if uploaded_file is not None:
    try:
        st.subheader("📄 Arquivo Carregado")
        st.write(f"Nome: {uploaded_file.name}")

        # --- 1. LEITURA DO ARQUIVO ---
        if uploaded_file.name.endswith('.pdf'):
            # (Leitura de PDF - sem alterações)
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
            # (Leitura de CSV)
            df = pd.read_csv(uploaded_file)
        else:
            # --- LEITURA XLSX - MODO DE INSPEÇÃO (NENHUM skiprows ou header) ---
            # Lê o arquivo sem nenhum parâmetro especial, para ver os dados brutos
            df_raw = pd.read_excel(uploaded_file, header=None)
            
            # === EXPANSOR DE INSPEÇÃO VISUAL ===
            with st.expander("🔍 Modo de Inspeção do XLSX (veja os dados brutos)", expanded=True):
                st.markdown("*Essa é a visualização do arquivo XLSX que você enviou, SEM pular nenhuma linha:*")
                st.dataframe(df_raw)
                
                st.markdown("---")
                st.markdown("*Aqui estão os primeiros registros que encontramos, para que você possa ver os cabeçalhos e os números:*")
                
                # Procura automaticamente a linha com 'UNIDADE' para sugerir o cabeçalho
                linha_cabecalho_sugerida = None
                for i, row in df_raw.iterrows():
                    if 'UNIDADE' in ' '.join([str(cell) for cell in row if pd.notna(cell)]).upper():
                        linha_cabecalho_sugerida = i
                        break
                
                if linha_cabecalho_sugerida is not None:
                    st.success(f"✅ Encontramos uma possível linha de cabeçalho na linha {linha_cabecalho_sugerida} (contém 'UNIDADE').")
                    st.dataframe(df_raw.iloc[linha_cabecalho_sugerida:linha_cabecalho_sugerida+5])
                    
                    # Adiciona um aviso para você verificar
                    st.warning("Verifique se a linha destacada contém os cabeçalhos corretos: UNIDADE, PAVTO, M², etc.")
                else:
                    st.warning("⚠️ Não encontramos nenhuma linha com 'UNIDADE' neste arquivo. Verifique se você selecionou o arquivo correto.")
                
                st.info("*Agora, envie uma imagem (print) desta tela no chat para podermos ajustar o código manualmente!*")

            # --- APLICA O PROCESSAMENTO (usando o método antigo, para mostrar o resultado) ---
            # Pula as 2 primeiras linhas para tentar ler a tabela principal
            try:
                df = pd.read_excel(io.BytesIO(uploaded_file.getvalue()), skiprows=2)
                df = df.dropna(how='all')
                df = df.dropna(axis=1, how='all')
                
                if 'UNIDADE' in df.columns:
                    df = df[df['UNIDADE'].notna() & (df['UNIDADE'].astype(str).str.strip() != '')]
            except Exception as e:
                st.error(f"Não foi possível processar o arquivo com skiprows=2: {e}")
                st.stop()

        # --- CONVERSÃO E EXIBIÇÃO (para você ver o resultado do processamento) ---
        colunas_para_converter = ['PREÇO', '1ª AVALIAÇÃO OÁSIS II', 'DESCONTO', 'M²', 'PAVTO.']
        for col in colunas_para_converter:
            if col in df.columns:
                df[col] = df[col].apply(converter_para_float)
        
        st.markdown("---")
        st.subheader("📊 Resultado do Processamento Atual")
        st.dataframe(df.head(10))
        
        st.warning("Se os valores de 'PREÇO', '1ª AVALIAÇÃO OÁSIS II' ou 'DESCONTO' estão zerados, o problema é que o cabeçalho do XLSX não foi reconhecido. O print da inspeção acima vai nos ajudar a corrigir isso.")
        
    except Exception as e:
        st.error(f"❌ Erro ao processar o arquivo: {str(e)}")
        st.info("Verifique o formato do arquivo.")
else:
    st.info("👈 Envie a planilha da construtora no menu lateral para começar a inspeção.")
