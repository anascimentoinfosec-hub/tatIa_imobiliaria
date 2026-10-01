import pandas as pd
import io
from src.planilha import ler_planilha
from src.planilha_cache import salvar_planilha_cache
from src.utils import converter_para_float


def _tratar_colunas_monetarias(df, config):
    """Converte colunas monetárias do formato BR para float."""
    for col in df.columns:
        col_up = str(col).upper()
        if any(m in col_up for m in ["VALOR", "PREÇO", "PRECO", "AVALIA", "DESCONTO"]):
            try:
                df[col] = df[col].astype(str).str.replace("RS", "", regex=False)
                df[col] = df[col].str.replace("R$", "", regex=False)
                df[col] = df[col].str.replace("R", "", regex=False)
                df[col] = df[col].str.strip()
                df[col] = df[col].str.replace(".", "", regex=False)
                df[col] = df[col].str.replace(",", ".", regex=False)
                df[col] = df[col].str.extract(r"(\d+\.?\d*)")
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
            except Exception:
                pass

    for col in config.get("colunas_para_converter", []):
        if col in df.columns:
            df[col] = df[col].apply(converter_para_float)


class _FakeUpload(io.BytesIO):
    """Emula o file_uploader do Streamlit: tem .name e é um BytesIO (com seek/read)."""
    def __init__(self, name, data):
        super().__init__(data)
        self.name = name


def processar_planilha_e_salvar_cache(file_bytes, file_name, config, construtora, produto):
    """
    Processa uma planilha (bytes) com o mapeamento config e salva no cache.
    Retorna (sucesso: bool, mensagem: str).
    """
    if not file_bytes:
        return False, "Nenhum arquivo para processar."

    try:
        fake = _FakeUpload(file_name, file_bytes)

        df = ler_planilha(fake, config)
        if df is None or df.empty:
            return False, "A planilha não pôde ser lida ou está vazia."

        _tratar_colunas_monetarias(df, config)
        salvar_planilha_cache(construtora, df, produto)
        return True, f"✅ {len(df)} unidades salvas no cache."

    except Exception as e:
        return False, f"Erro ao processar planilha: {str(e)}"