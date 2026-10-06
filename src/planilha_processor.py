import pandas as pd
import io
from src.planilha import ler_planilha
from src.planilha_cache import salvar_planilha_cache
from src.utils import converter_para_float


def _tratar_colunas_monetarias(df, config):
    """Converte colunas monetárias do formato BR para float (corrigido)."""
    import re as _re

    def _br_to_float(valor):
        if pd.isna(valor):
            return 0.0
        s = str(valor).strip()
        # Remove símbolos
        s = _re.sub(r"R\$?\s*", "", s, flags=_re.IGNORECASE)
        s = s.replace(" ", "").strip()
        if not s:
            return 0.0

        tem_virgula = "," in s
        tem_ponto = "." in s

        if tem_virgula and tem_ponto:
            # Formato BR: 1.234.567,89 → remove TODOS os pontos, troca vírgula por ponto
            s = s.replace(".", "").replace(",", ".")
        elif tem_virgula:
            # Só vírgula: 1234,89 → troca por ponto
            s = s.replace(",", ".")
        elif tem_ponto:
            # Só ponto: pode ser "1.234" (milhar BR) ou "1234.89" (decimal US)
            partes = s.split(".")
            if len(partes) > 1 and all(len(p) == 3 for p in partes[1:]):
                # É formato de milhar: 1.234.567 → remove pontos
                s = s.replace(".", "")
            # senão, mantém como está (decimal US)

        # Extrai apenas números e ponto
        match = _re.search(r"\d+(\.\d+)?", s)
        if not match:
            return 0.0
        try:
            return float(match.group())
        except (ValueError, TypeError):
            return 0.0

    for col in df.columns:
        col_up = str(col).upper()
        if any(m in col_up for m in ["VALOR", "PREÇO", "PRECO", "AVALIA", "DESCONTO"]):
            df[col] = df[col].apply(_br_to_float)

    for col in config.get("colunas_para_converter", []):
        if col in df.columns:
            # Guarda valor original como string para debug
            df[f"_{col}_original"] = df[col].astype(str)
            df[col] = df[col].apply(_br_to_float)


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