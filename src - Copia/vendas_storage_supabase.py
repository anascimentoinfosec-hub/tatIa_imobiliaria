"""Camada Supabase para vendas, status e campos extras."""
from src.db import get_client
from datetime import datetime


def _client():
    c = get_client()
    if not c:
        raise Exception("Supabase não configurado.")
    return c


# =========================================================
# VENDAS
# =========================================================
def carregar_vendas():
    client = _client()
    try:
        response = client.table("vendas").select("*").order("criado_em", desc=True).execute()
        resultado = []
        for r in response.data or []:
            dados = r.get("dados") or {}
            dados["id"] = r.get("id")
            resultado.append(dados)
        return resultado
    except Exception as e:
        import streamlit as st
        st.error(f"❌ Erro ao carregar vendas: {str(e)}")
        return []


def salvar_venda_sb(venda_id, dados):
    from src.db import limpar_nan
    client = _client()
    try:
        client.table("vendas").upsert({
            "id": venda_id,
            "dados": limpar_nan(dados),
        }).execute()
        return True
    except Exception as e:
        import streamlit as st
        st.error(f"❌ Erro ao salvar venda: {str(e)}")
        return False


def excluir_venda_sb(venda_id):
    client = _client()
    try:
        client.table("vendas").delete().eq("id", venda_id).execute()
        return True
    except Exception as e:
        import streamlit as st
        st.error(f"❌ Erro ao excluir venda: {str(e)}")
        return False


def migrar_vendas_do_json(caminho_json="dados/vendas.json"):
    import json
    import os
    if not os.path.exists(caminho_json):
        return 0, "JSON não encontrado"
    try:
        with open(caminho_json, "r", encoding="utf-8") as f:
            vendas = json.load(f)
    except Exception as e:
        return 0, f"Erro: {str(e)}"

    count = 0
    for v in vendas:
        v_id = v.get("id")
        if not v_id:
            continue
        if salvar_venda_sb(v_id, v):
            count += 1
    return count, "OK"


# =========================================================
# STATUS
# =========================================================
def carregar_status_sb():
    client = _client()
    try:
        response = client.table("vendas_status").select("*").order("ordem").execute()
        return response.data or []
    except Exception:
        return []


def salvar_status_sb(lista_status):
    client = _client()
    try:
        response = client.table("vendas_status").select("id").execute()
        ids_banco = {r["id"] for r in (response.data or [])}
        ids_lista = {s["id"] for s in lista_status}

        for s in lista_status:
            client.table("vendas_status").upsert({
                "id": s["id"],
                "nome": s.get("nome", ""),
                "cor": s.get("cor", "#94a3b8"),
                "ordem": int(s.get("ordem", 0)),
            }).execute()

        for id_remover in ids_banco - ids_lista:
            client.table("vendas_status").delete().eq("id", id_remover).execute()
    except Exception as e:
        import streamlit as st
        st.error(f"❌ Erro ao salvar status: {str(e)}")


# =========================================================
# CAMPOS EXTRAS
# =========================================================
def carregar_campos_extras_sb():
    client = _client()
    try:
        response = client.table("vendas_campos_extras").select("*").order("criado_em").execute()
        return response.data or []
    except Exception:
        return []


def salvar_campos_extras_sb(lista_campos):
    client = _client()
    try:
        response = client.table("vendas_campos_extras").select("id").execute()
        ids_banco = {r["id"] for r in (response.data or [])}
        ids_lista = {c["id"] for c in lista_campos}

        for c in lista_campos:
            client.table("vendas_campos_extras").upsert({
                "id": c["id"],
                "nome": c.get("nome", ""),
                "tipo": c.get("tipo", "texto"),
            }).execute()

        for id_remover in ids_banco - ids_lista:
            client.table("vendas_campos_extras").delete().eq("id", id_remover).execute()
    except Exception as e:
        import streamlit as st
        st.error(f"❌ Erro ao salvar campos extras: {str(e)}")