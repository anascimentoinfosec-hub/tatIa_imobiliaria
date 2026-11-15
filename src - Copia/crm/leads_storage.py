"""
Storage do CRM - Módulo 100% isolado.
"""
from src.db import get_client, limpar_nan
from datetime import datetime
import uuid

def _client():
    c = get_client()
    if not c:
        raise Exception("Supabase não configurado.")
    return c

def _gerar_id():
    return str(uuid.uuid4())

# =========================================================
# LEADS
# =========================================================
def criar_lead(nome, telefone, email, renda, origem, corretor, campanha_id=None):
    client = _client()
    lead_id = _gerar_id()
    try:
        client.table("crm_leads").insert({
            "id": lead_id,
            "nome": nome,
            "telefone": telefone,
            "email": email,
            "renda": float(renda) if renda else 0.0,
            "origem": origem,
            "corretor": corretor,
            "campanha_id": campanha_id,
            "status": "novo",
            "ultima_interacao": datetime.now().isoformat(),
        }).execute()
        return True, lead_id
    except Exception as e:
        import streamlit as st
        st.error(f"❌ Erro ao criar lead: {str(e)}")
        return False, None

def carregar_leads(corretor=None):
    client = _client()
    try:
        query = client.table("crm_leads").select("*").order("criado_em", desc=True)
        # Se for corretor, ele só vê os leads dele
        if corretor:
            query = query.eq("corretor", corretor)
        response = query.execute()
        return response.data or []
    except Exception as e:
        import streamlit as st
        st.error(f"❌ Erro ao carregar leads: {str(e)}")
        return []

def atualizar_status_lead(lead_id, novo_status):
    client = _client()
    try:
        client.table("crm_leads").update({
            "status": novo_status,
            "atualizado_em": datetime.now().isoformat(),
            "ultima_interacao": datetime.now().isoformat(),
        }).eq("id", lead_id).execute()
        return True
    except Exception as e:
        import streamlit as st
        st.error(f"❌ Erro ao atualizar lead: {str(e)}")
        return False

def excluir_lead(lead_id):
    client = _client()
    try:
        client.table("crm_leads").delete().eq("id", lead_id).execute()
        return True
    except Exception as e:
        import streamlit as st
        st.error(f"❌ Erro ao excluir lead: {str(e)}")
        return False