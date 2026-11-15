import streamlit as st
import requests
import json
from datetime import datetime
import os

ARQUIVO_INDICADORES = "dados/indicadores.json"

def buscar_indicadores_bc():
    """Busca indicadores econômicos da API do Banco Central"""
    
    # Mapeamento dos códigos SGS
    codigos = {
        "selic": 4390,           # Taxa Selic
        "ipca": 433,             # IPCA
        "tjlp": 4389,            # TJLP
        "poupanca": 12,          # Poupança
    }
    
    indicadores = {}
    
    for nome, codigo in codigos.items():
        try:
            # Busca o último valor disponível
            url = f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo}/dados/ultimos/1"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                dados = response.json()
                if dados and len(dados) > 0:
                    valor = dados[0]['valor']
                    # Formata o valor
                    if isinstance(valor, (int, float)):
                        if nome == "selic":
                            indicadores[nome] = f"{valor:.2f}%"
                        elif nome == "ipca":
                            indicadores[nome] = f"{valor:.2f}%"
                        elif nome == "tjlp":
                            indicadores[nome] = f"{valor:.2f}%"
                        elif nome == "poupanca":
                            indicadores[nome] = f"{valor:.2f}%"
                    else:
                        indicadores[nome] = str(valor)
            else:
                # Se falhar, usa fallback
                indicadores[nome] = None
        except:
            indicadores[nome] = None
    
    return indicadores

def carregar_indicadores():
    """Carrega indicadores do cache ou busca novos"""
    
    # Tenta carregar do cache local
    try:
        if os.path.exists(ARQUIVO_INDICADORES):
            with open(ARQUIVO_INDICADORES, 'r', encoding='utf-8') as f:
                dados = json.load(f)
                # Verifica se o cache é recente (menos de 1 hora)
                cache_time = datetime.fromisoformat(dados.get("cache_time", "2000-01-01"))
                if (datetime.now() - cache_time).seconds < 3600:  # 1 hora
                    return dados["indicadores"]
    except:
        pass
    
    # Busca novos dados
    indicadores = buscar_indicadores_bc()
    
    # Preenche com fallback se algum não veio
    fallback = {
        "selic": "10,50%",
        "ipca": "4,50%",
        "tjlp": "6,00%",
        "poupanca": "6,17%"
    }
    
    for key, value in fallback.items():
        if key not in indicadores or indicadores[key] is None:
            indicadores[key] = value
    
    # Salva no cache
    try:
        with open(ARQUIVO_INDICADORES, 'w', encoding='utf-8') as f:
            json.dump({
                "indicadores": indicadores,
                "cache_time": datetime.now().isoformat()
            }, f, ensure_ascii=False)
    except:
        pass
    
    return indicadores

def mostrar_indicadores():
    """Exibe os indicadores na página"""
    
    indicadores = carregar_indicadores()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(
            label="🏦 Taxa Selic",
            value=indicadores.get("selic", "10,50%"),
            delta="Atualizado hoje"
        )
        st.metric(
            label="📈 IPCA",
            value=indicadores.get("ipca", "4,50%"),
            delta="Últimos 12 meses"
        )
    with col2:
        st.metric(
            label="🏛️ TJLP",
            value=indicadores.get("tjlp", "6,00%"),
            delta="Trimestral"
        )
        st.metric(
            label="💰 Poupança",
            value=indicadores.get("poupanca", "6,17%"),
            delta="Referência"
        )
    with col3:
        st.metric(
            label="🏠 Valor m² (RJ)",
            value="R$ 12.800",
            delta="Média da região"
        )
        st.metric(
            label="📋 Prazo máximo",
            value="420 meses",
            delta="35 anos"
        )