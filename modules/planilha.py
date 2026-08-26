import pandas as pd
import io
import pdfplumber
import re

def ler_planilha(uploaded_file, config):
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
        elif uploaded_file.name.endswith('.csv'):
            return pd.read_csv(uploaded_file)
        else:
            df_raw = pd.read_excel(uploaded_file, header=None)
            linha_cabecalho = None
            for i, row in df_raw.iterrows():
                row_text = ' '.join([str(cell).upper() for cell in row if pd.notna(cell)])
                if 'UNIDADE' in row_text:
                    linha_cabecalho = i
                    break
            if linha_cabecalho is None:
                return None
            dados = df_raw.iloc[linha_cabecalho + 1:].reset_index(drop=True)
            mapeamento = config.get("mapeamento", {})
            df = pd.DataFrame()
            for idx_str, nome_novo in mapeamento.items():
                idx = int(idx_str)
                if idx < len(dados.columns):
                    df[nome_novo] = dados.iloc[:, idx]
            df = df.dropna(how='all')
            if 'UNIDADE' in df.columns:
                df = df[df['UNIDADE'].notna() & (df['UNIDADE'].astype(str).str.strip() != '')]
            return df
    except:
        return None
