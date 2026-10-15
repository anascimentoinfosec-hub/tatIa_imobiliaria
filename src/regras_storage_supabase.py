"""Camada Supabase para regras de financiamento."""
from src.db import get_client


def _client():
    c = get_client()
    if not c:
        raise Exception("Supabase não configurado.")
    return c


def carregar_regras_sb():
    client = _client()
    try:
        response = client.table("regras_financiamento").select("*").execute()
        regras = {}
        for r in response.data or []:
            regras[r["id"]] = r.get("dados") or {}
        return regras
    except Exception as e:
        import streamlit as st
        st.error(f"❌ Erro ao carregar regras: {str(e)}")
        return {}


def salvar_regras_sb(regras_dict):
    client = _client()
    try:
        response = client.table("regras_financiamento").select("id").execute()
        ids_banco = {r["id"] for r in (response.data or [])}
        ids_dict = set(regras_dict.keys())

        for rid, dados in regras_dict.items():
            client.table("regras_financiamento").upsert({
                "id": rid,
                "dados": dados,
            }).execute()

        for rid in ids_banco - ids_dict:
            client.table("regras_financiamento").delete().eq("id", rid).execute()
    except Exception as e:
        import streamlit as st
        st.error(f"❌ Erro ao salvar regras: {str(e)}")


def migrar_regras_do_json(caminho_json="dados/regras_financiamento.json"):
    import json
    import os
    if not os.path.exists(caminho_json):
        return 0, "JSON não encontrado"
    try:
        with open(caminho_json, "r", encoding="utf-8") as f:
            regras = json.load(f)
    except Exception as e:
        return 0, f"Erro: {str(e)}"

    salvar_regras_sb(regras)
    return len(regras), "OK"