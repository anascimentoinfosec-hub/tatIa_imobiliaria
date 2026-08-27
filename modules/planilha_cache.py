import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime

PASTA_PLANILHAS = "dados/planilhas"

def salvar_planilha_cache(construtora: str, df: pd.DataFrame):
 """Salva a planilha em cache para acesso futuro"""
 try:
 if not os.path.exists(PASTA_PLANILHAS):
 os.makedirs(PASTA_PLANILHAS)
 
 # Converte DataFrame para JSON
 arquivo = os.path.join(PASTA_PLANILHAS, f"{construtora}.json")
 dados = {
 "construtora": construtora,
 "data_upload": datetime.now().isoformat(),
 "colunas": df.columns.tolist(),
 "dados": df.to_dict(orient="records")
 }
 
 with open(arquivo, 'w', encoding='utf-8') as f:
 json.dump(dados, f, indent=2, ensure_ascii=False)
 
 return True
 except Exception as e:
 st.error(f" Erro ao salvar cache: {str(e)}")
 return False

def carregar_planilha_cache(construtora: str):
 """Carrega a planilha do cache"""
 try:
 arquivo = os.path.join(PASTA_PLANILHAS, f"{construtora}.json")
 if not os.path.exists(arquivo):
 return None
 
 with open(arquivo, 'r', encoding='utf-8') as f:
 dados = json.load(f)
 
 df = pd.DataFrame(dados["dados"])
 df.columns = dados["colunas"]
 
 return df
 except Exception as e:
 return None

def tem_planilha_cache(construtora: str) -> bool:
 """Verifica se existe planilha em cache para a construtora"""
 arquivo = os.path.join(PASTA_PLANILHAS, f"{construtora}.json")
 return os.path.exists(arquivo)

def excluir_planilha_cache(construtora: str):
 """Exclui a planilha em cache"""
 try:
 arquivo = os.path.join(PASTA_PLANILHAS, f"{construtora}.json")
 if os.path.exists(arquivo):
 os.remove(arquivo)
 return True
 except:
 pass
 return False