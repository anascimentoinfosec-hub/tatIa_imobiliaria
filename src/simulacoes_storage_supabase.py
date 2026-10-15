"""Camada Supabase para simulações."""
from src.db import get_client
from datetime import datetime


def _client():
    c = get_client()
    if not c:
        raise Exception("Supabase não configurado.")
    return c


def carregar_simulacoes():
    """Retorna todas as simulações (mais recentes primeiro)."""
    client = _client()
    try:
        response = client.table("simulacoes").select("*").order("criado_em", desc=True).execute()
        resultado = []
        for r in response.data or []:
            dados = r.get("dados") or {}
            dados["id"] = r.get("id")
            resultado.append(dados)
        return resultado
    except Exception as e:
        import streamlit as st
        st.error(f"❌ Erro ao carregar simulações: {str(e)}")
        return []


def salvar_simulacao_sb(registro):
    """Insere/atualiza uma simulação pelo ID."""
    from src.db import limpar_nan
    client = _client()
    try:
        client.table("simulacoes").upsert({
            "id": registro["id"],
            "dados": limpar_nan(registro),
        }).execute()
        return True
    except Exception as e:
        import streamlit as st
        st.error(f"❌ Erro ao salvar simulação: {str(e)}")
        return False


def atualizar_simulacao_sb(sim_id, registro):
    return salvar_simulacao_sb(registro)


def excluir_simulacao_sb(sim_id):
    client = _client()
    try:
        client.table("simulacoes").delete().eq("id", sim_id).execute()
        return True
    except Exception as e:
        import streamlit as st
        st.error(f"❌ Erro ao excluir simulação: {str(e)}")
        return False


def migrar_do_json(caminho_json="dados/simulacoes.json"):
    import json
    import os
    if not os.path.exists(caminho_json):
        return 0, "JSON não encontrado"
    try:
        with open(caminho_json, "r", encoding="utf-8") as f:
            sims = json.load(f)
    except Exception as e:
        return 0, f"Erro: {str(e)}"

    count = 0
    for sim in sims:
        sim_id = sim.get("id")
        if not sim_id:
            continue
        if salvar_simulacao_sb(sim):
            count += 1
    return count, "OK"