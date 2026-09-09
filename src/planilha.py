import pandas as pd

def ler_planilha(uploaded_file, config):
    try:
        if uploaded_file.name.endswith('.csv'):
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