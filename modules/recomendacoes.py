import streamlit as st
import pandas as pd

def recomendar_imoveis(df_imoveis, renda=None, preferencias=None):
    """
    Recomenda imóveis com base no perfil do cliente
    """
    if df_imoveis is None or df_imoveis.empty:
        return None
    
    df = df_imoveis.copy()
    if "DISPONIBILIDADE" in df.columns:
        df = df[df["DISPONIBILIDADE"] == "LIVRE"]
    
    if renda:
        parcela_maxima = renda * 0.4
        df = df[df["PREÇO"] * 0.005 <= parcela_maxima]
    
    if preferencias:
        if "TIPOLOGIA" in preferencias and preferencias["TIPOLOGIA"]:
            df = df[df["TIPOLOGIA"] == preferencias["TIPOLOGIA"]]
        if "SOL" in preferencias and preferencias["SOL"]:
            df = df[df["SOL"] == preferencias["SOL"]]
    
    if "R$/m²" in df.columns:
        df = df.sort_values("R$/m²")
    
    return df.head(10) if len(df) > 10 else df