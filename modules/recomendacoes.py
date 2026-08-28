import streamlit as st
import pandas as pd

def recomendar_imoveis(df_imoveis, perfil_cliente):
    """
    Recomenda imóveis com base no perfil do cliente
    """
    if df_imoveis is None or df_imoveis.empty:
        return None
    
    df = df_imoveis.copy()
    
    # Filtra apenas disponíveis
    if "DISPONIBILIDADE" in df.columns:
        df = df[df["DISPONIBILIDADE"].str.upper() == "LIVRE"]
    
    # Filtra por tipo
    if "TIPOLOGIA" in df.columns and perfil_cliente.get("tipo"):
        df = df[df["TIPOLOGIA"].str.contains(perfil_cliente["tipo"], case=False, na=False)]
    
    # Filtra por quartos
    if "QUARTOS" in df.columns and perfil_cliente.get("quartos"):
        try:
            qtd = int(perfil_cliente["quartos"])
            df = df[df["QUARTOS"].astype(str).str.contains(str(qtd))]
        except:
            pass
    
    # Filtra por preço máximo baseado na renda
    if "PREÇO" in df.columns and perfil_cliente.get("renda"):
        parcela_maxima = perfil_cliente["renda"] * 0.3
        df["parcela_estimada"] = df["PREÇO"] * 0.005
        df = df[df["parcela_estimada"] <= parcela_maxima]
    
    # Ordena por R$/m²
    if "R$/m²" in df.columns:
        df = df.sort_values("R$/m²")
    
    return df.head(10)