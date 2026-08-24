import streamlit as st
import pandas as pd
import io
import pdfplumber
import re

# CONFIGURAÇÃO
st.set_page_config(page_title="ImobFlux IA - DEBUG", layout="wide")
st.title("🐞 ImobFlux IA - Modo Debug")
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
    st.caption("Modo Debug - Versão 1.0")

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
            # --- LEITURA XLSX COM DEBUG COMPLETO ---
            st.subheader("📊 DEBUG: Arquivo XLSX Lido")
            
            # Lê o arquivo SEM cabeçalho
            df_raw = pd.read_excel(uploaded_file, header=None)
            
            # ================================================
            # DEBUG 1: Mostrar TODAS as colunas e linhas
            # ================================================
            st.markdown("### 🔍 1. Dados BRUTOS (sem tratamento)")
            st.write(f"*Formato:* {df_raw.shape[0]} linhas × {df_raw.shape[1]} colunas")
            st.dataframe(df_raw)
            
            # ================================================
            # DEBUG 2: Mostrar as primeiras linhas detalhadamente
            # ================================================
            st.markdown("### 🔍 2. Primeiras 5 linhas (detalhadas)")
            for i in range(min(5, len(df_raw))):
                st.write(f"*Linha {i}:*")
                for j, valor in enumerate(df_raw.iloc[i]):
                    if pd.notna(valor):
                        st.write(f"  Coluna {j}: {valor}")
            
            # ================================================
            # DEBUG 3: Tentar encontrar o cabeçalho
            # ================================================
            st.markdown("### 🔍 3. Busca por cabeçalho 'UNIDADE'")
            linha_cabecalho = None
            for i, row in df_raw.iterrows():
                row_text = ' '.join([str(cell).upper() for cell in row if pd.notna(cell)])
                st.write(f"Linha {i}: {row_text[:100]}...")
                if 'UNIDADE' in row_text:
                    linha_cabecalho = i
                    st.success(f"✅ Encontrado na linha {i}!")
                    break
            
            if linha_cabecalho is None:
                st.warning("⚠️ Nenhuma linha com 'UNIDADE' encontrada.")
                st.stop()
            
            # ================================================
            # DEBUG 4: Extrair cabeçalho e dados
            # ================================================
            st.markdown("### 🔍 4. Cabeçalho extraído")
            cabecalho = []
            for col in df_raw.iloc[linha_cabecalho]:
                if pd.isna(col):
                    cabecalho.append('')
                else:
                    cabecalho.append(str(col).strip())
            
            st.write("Cabeçalho (como foi lido):")
            st.write(cabecalho)
            
            # ================================================
            # DEBUG 5: Mostrar dados após o cabeçalho
            # ================================================
            st.markdown("### 🔍 5. Dados após o cabeçalho (linhas abaixo)")
            dados = df_raw.iloc[linha_cabecalho + 1:].reset_index(drop=True)
            st.dataframe(dados.head(10))
            
            # ================================================
            # DEBUG 6: Verificar colunas específicas
            # ================================================
            st.markdown("### 🔍 6. Verificação de colunas específicas")
            
            # Tenta encontrar colunas com "PREÇO", "AVALIAÇÃO", "DESCONTO"
            colunas_preco = []
            colunas_avaliacao = []
            colunas_desconto = []
            
            for i, h in enumerate(cabecalho):
                if 'PREÇO' in h.upper() or 'PRECO' in h.upper():
                    colunas_preco.append(i)
                if 'AVAL' in h.upper():
                    colunas_avaliacao.append(i)
                if 'DESCONTO' in h.upper() or 'DESCO' in h.upper():
                    colunas_desconto.append(i)
            
            st.write(f"Colunas com 'PREÇO': {colunas_preco}")
            st.write(f"Colunas com 'AVALIAÇÃO': {colunas_avaliacao}")
            st.write(f"Colunas com 'DESCONTO': {colunas_desconto}")
            
            # Mostra os valores dessas colunas
            if colunas_preco:
                for idx in colunas_preco:
                    st.write(f"*Coluna {idx} (PREÇO):*")
                    st.write(dados.iloc[:5, idx].tolist())
            
            if colunas_avaliacao:
                for idx in colunas_avaliacao:
                    st.write(f"*Coluna {idx} (AVALIAÇÃO):*")
                    st.write(dados.iloc[:5, idx].tolist())
            
            if colunas_desconto:
                for idx in colunas_desconto:
                    st.write(f"*Coluna {idx} (DESCONTO):*")
                    st.write(dados.iloc[:5, idx].tolist())
            
            # ================================================
            # DEBUG 7: Criar DataFrame final (como o app faria)
            # ================================================
            st.markdown("### 🔍 7. Processamento atual")
            
            # Pula as 2 primeiras linhas (como antes)
            try:
                df = pd.read_excel(io.BytesIO(uploaded_file.getvalue()), skiprows=2)
                st.write("DataFrame após skiprows=2:")
                st.dataframe(df.head(10))
                st.write("Colunas:", df.columns.tolist())
            except Exception as e:
                st.error(f"Erro com skiprows=2: {e}")
            
            st.markdown("---")
            st.warning("*📸 Por favor, tire um print DESTA TELA INTEIRA e me envie!*")
            st.stop()  # Para aqui para não processar mais nada
        
        # (O código só chega aqui para PDF/CSV)
        st.success("✅ Arquivo processado com sucesso!")
    
    except Exception as e:
        st.error(f"❌ Erro ao ler a planilha: {str(e)}")
        st.info("Verifique o formato do arquivo (XLSX, CSV ou PDF).")

else:
    st.info("👈 Envie a planilha da construtora no menu lateral para começar o debug.")
    st.markdown("""
    ### Como usar:
    1. Clique em *"Browse files"* no menu lateral
    2. Selecione a planilha XLSX
    3. O app vai mostrar *TODOS* os dados brutos
    4. Tire um *print da tela inteira*
    5. Me envie a imagem
    """)
