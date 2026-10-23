from src.db import get_client

def obter_configuracao(chave, padrao=""):
    client = get_client()
    try:
        response = client.table("configuracoes").select("valor").eq("chave", chave).execute()
        if response.data:
            return response.data[0]["valor"]
    except Exception:
        pass
    return padrao

def salvar_configuracao(chave, valor):
    client = get_client()
    try:
        client.table("configuracoes").upsert({
            "chave": chave,
            "valor": valor
        }).execute()
        return True
    except Exception as e:
        import streamlit as st
        st.error(f"❌ Erro ao salvar configuração: {str(e)}")
        return False