import streamlit as st
from src.db import get_client
from datetime import datetime
import uuid

def _client():
    c = get_client()
    if not c:
        raise Exception("Supabase não configurado.")
    return c

def criar_campanha(nome, investimento, data_fim):
    client = _client()
    campanha_id = str(uuid.uuid4())[:8] # ID curto para o link
    try:
        client.table("crm_campanhas").insert({
            "id": campanha_id,
            "nome": nome,
            "investimento": float(investimento),
            "data_inicio": datetime.now().strftime("%Y-%m-%d"),
            "data_fim": data_fim.strftime("%Y-%m-%d"),
            "ativo": True
        }).execute()
        return True, campanha_id
    except Exception as e:
        st.error(f"❌ Erro ao criar campanha: {str(e)}")
        return False, None

def carregar_campanhas():
    client = _client()
    try:
        response = client.table("crm_campanhas").select("*").order("criado_em", desc=True).execute()
        return response.data or []
    except Exception as e:
        st.error(f"❌ Erro ao carregar campanhas: {str(e)}")
        return []