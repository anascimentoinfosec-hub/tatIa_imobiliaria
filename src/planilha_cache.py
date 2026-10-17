"""
Cache de planilhas. Usa Supabase se disponível, cai para JSON local.
"""
import json
import os
import re
from datetime import datetime
import pandas as pd
import streamlit as st
from src.db import supabase_disponivel

PASTA_PLANILHAS = "dados/planilhas"


# =========================================================
# HELPERS (nome de arquivo local)
# =========================================================
def _get_arquivo_cache(construtora: str, produto: str = None):
    construtora_limpa = re.sub(r'[\\/*?:"<>|]', '_', construtora)
    if produto:
        produto_limpo = re.sub(r'[\\/*?:"<>|]', '_', produto)
        nome_arquivo = f"{construtora_limpa}_{produto_limpo}.json"
    else:
        nome_arquivo = f"{construtora_limpa}.json"
    return os.path.join(PASTA_PLANILHAS, nome_arquivo)


# =========================================================
# SALVAR
# =========================================================
def salvar_planilha_cache(construtora: str, df: pd.DataFrame, produto: str = None):
    if supabase_disponivel():
        try:
            from src.planilha_cache_supabase import salvar_planilha_sb
            return salvar_planilha_sb(construtora, df, produto)
        except Exception as e:
            st.error(f"❌ Erro ao salvar no Supabase: {str(e)}")
            return False

    # Fallback JSON
    try:
        if not os.path.exists(PASTA_PLANILHAS):
            os.makedirs(PASTA_PLANILHAS)
        arquivo = _get_arquivo_cache(construtora, produto)
        dados = {
            "construtora": construtora,
            "produto": produto,
            "data_upload": datetime.now().isoformat(),
            "colunas": df.columns.tolist(),
            "dados": df.to_dict(orient="records"),
        }
        with open(arquivo, 'w', encoding='utf-8') as f:
            json.dump(dados, f, indent=2, ensure_ascii=False, default=str)
        return True
    except Exception as e:
        st.error(f"❌ Erro ao salvar cache: {str(e)}")
        return False


# =========================================================
# CARREGAR
# =========================================================
def carregar_planilha_cache(construtora: str, produto: str = None):
    if supabase_disponivel():
        try:
            from src.planilha_cache_supabase import carregar_planilha_sb
            return carregar_planilha_sb(construtora, produto)
        except Exception as e:
            st.error(f"❌ Erro ao carregar do Supabase: {str(e)}")
            return None

    # Fallback JSON
    try:
        arquivo = _get_arquivo_cache(construtora, produto)
        if not os.path.exists(arquivo):
            return None
        with open(arquivo, 'r', encoding='utf-8') as f:
            dados = json.load(f)
        df = pd.DataFrame(dados["dados"])
        df.columns = dados["colunas"]
        return df
    except Exception:
        return None


# =========================================================
# TEM CACHE?
# =========================================================
def tem_planilha_cache(construtora: str, produto: str = None) -> bool:
    if supabase_disponivel():
        try:
            from src.planilha_cache_supabase import tem_planilha_sb
            return tem_planilha_sb(construtora, produto)
        except Exception:
            return False

    arquivo = _get_arquivo_cache(construtora, produto)
    return os.path.exists(arquivo)


# =========================================================
# EXCLUIR
# =========================================================
def excluir_planilha_cache(construtora: str, produto: str = None):
    if supabase_disponivel():
        try:
            from src.planilha_cache_supabase import excluir_planilha_sb
            return excluir_planilha_sb(construtora, produto)
        except Exception:
            return False

    try:
        arquivo = _get_arquivo_cache(construtora, produto)
        if os.path.exists(arquivo):
            os.remove(arquivo)
            return True
    except Exception:
        pass
    return False