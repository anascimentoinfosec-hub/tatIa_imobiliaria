"""Camada Supabase para regras de entrada por construtora."""
from src.db import get_client


def _client():
    c = get_client()
    if not c:
        raise Exception("Supabase não configurado.")
    return c


def carregar_regras_entrada_sb():
    client = _client()
    try:
        response = client.table("regras_entrada").select("*").execute()
        regras = {}
        for r in response.data or []:
            regras[r["construtora"]] = r.get("dados") or {}
        return regras
    except Exception as e:
        import streamlit as st
        st.error(f"❌ Erro ao carregar regras de entrada: {str(e)}")
        return {}


def salvar_regras_entrada_sb(regras_dict):
    client = _client()
    try:
        response = client.table("regras_entrada").select("construtora").execute()
        nomes_banco = {r["construtora"] for r in (response.data or [])}
        nomes_dict = set(regras_dict.keys())

        for nome, dados in regras_dict.items():
            client.table("regras_entrada").upsert({
                "construtora": nome,
                "dados": dados,
            }).execute()

        for nome in nomes_banco - nomes_dict:
            client.table("regras_entrada").delete().eq("construtora", nome).execute()
    except Exception as e:
        import streamlit as st
        st.error(f"❌ Erro ao salvar regras de entrada: {str(e)}")


def migrar_regras_entrada_do_json(caminho_json="dados/regras_entrada.json"):
    import json
    import os
    if not os.path.exists(caminho_json):
        return 0, "JSON não encontrado"
    try:
        with open(caminho_json, "r", encoding="utf-8") as f:
            regras = json.load(f)
    except Exception as e:
        return 0, f"Erro: {str(e)}"

    salvar_regras_entrada_sb(regras)
    return len(regras), "OK"