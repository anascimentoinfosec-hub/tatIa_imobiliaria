import streamlit as st
import pandas as pd
import json
import os
import re
from datetime import datetime

PASTA_PLANILHAS = "dados/planilhas"

def _get_arquivo_cache(construtora: str, produto: str = None):
    """Retorna o caminho do arquivo de cache com nome seguro"""
    construtora_limpa = re.sub(r'[\\/*?:"<>|]', '_', construtora)
    if produto:
        produto_limpo = re.sub(r'[\\/*?:"<>|]', '_', produto)
        nome_arquivo = f"{construtora_limpa}_{produto_limpo}.json"
    else:
        nome_arquivo = f"{construtora_limpa}.json"
    return os.path.join(PASTA_PLANILHAS, nome_arquivo)

def salvar_planilha_cache(construtora: str, df: pd.DataFrame, produto: str = None):
    try:
        if not os.path.exists(PASTA_PLANILHAS):
            os.makedirs(PASTA_PLANILHAS)
        arquivo = _get_arquivo_cache(construtora, produto)
        dados = {
            "construtora": construtora,
            "produto": produto,
            "data_upload": datetime.now().isoformat(),
            "colunas": df.columns.tolist(),
            "dados": df.to_dict(orient="records")
        }
        with open(arquivo, 'w', encoding='utf-8') as f:
            json.dump(dados, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        st.error(f"❌ Erro ao salvar cache: {str(e)}")
        return False

def carregar_planilha_cache(construtora: str, produto: str = None):
    try:
        arquivo = _get_arquivo_cache(construtora, produto)
        if not os.path.exists(arquivo):
            return None
        with open(arquivo, 'r', encoding='utf-8') as f:
            dados = json.load(f)
        df = pd.DataFrame(dados["dados"])
        df.columns = dados["colunas"]
        return df
    except Exception as e:
        return None

def tem_planilha_cache(construtora: str, produto: str = None) -> bool:
    arquivo = _get_arquivo_cache(construtora, produto)
    return os.path.exists(arquivo)

def excluir_planilha_cache(construtora: str, produto: str = None):
    try:
        arquivo = _get_arquivo_cache(construtora, produto)
        if os.path.exists(arquivo):
            os.remove(arquivo)
            return True
    except:
        pass
    return False