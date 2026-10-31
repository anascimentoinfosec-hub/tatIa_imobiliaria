import streamlit as st
from src.db import get_client
from datetime import datetime, timezone, timedelta

FUSO_BR = timezone(timedelta(hours=-3))

def bater_ponto(corretor, local):
    """Corretor entra na fila."""
    client = get_client()
    try:
        client.table("checkins_corretores").update({"ativo": False, "data_saida": datetime.now(FUSO_BR).isoformat()}).eq("corretor", corretor).eq("ativo", True).execute()
        
        client.table("checkins_corretores").insert({
            "id": f"{corretor}_{datetime.now().timestamp()}",
            "corretor": corretor,
            "local": local,
            "ativo": True
        }).execute()
        
        # Salva o timestamp atual (segundos) como string
        agora_ts = str(datetime.now(FUSO_BR).timestamp())
        
        client.table("roleta_fila").upsert({
            "corretor": corretor, 
            "ultimo_lead_recebido": agora_ts
        }, on_conflict="corretor").execute()
        
        return True
    except Exception as e:
        st.error(f"❌ Erro ao bater ponto: {str(e)}")
        return False

def sair_do_ponto(corretor):
    """Corretor sai da fila."""
    client = get_client()
    try:
        client.table("checkins_corretores").update({"ativo": False, "data_saida": datetime.now(FUSO_BR).isoformat()}).eq("corretor", corretor).eq("ativo", True).execute()
        client.table("roleta_fila").delete().eq("corretor", corretor).execute()
        return True
    except Exception as e:
        st.error(f"❌ Erro ao sair do ponto: {str(e)}")
        return False

def proximo_corretor_disponivel():
    """Acha o próximo corretor no Stand que não recebeu lead nos últimos 10 min."""
    client = get_client()
    try:
        checkins = client.table("checkins_corretores").select("corretor, local").eq("ativo", True).execute().data
        if not checkins:
            return None
            
        no_stand = [c["corretor"] for c in checkins if c["local"] == "stand"]
        
        # Pega a fila ordenada por quem recebeu lead há mais tempo
        fila = client.table("roleta_fila").select("corretor, ultimo_lead_recebido").order("ultimo_lead_recebido").execute().data
        
        agora_ts = datetime.now(FUSO_BR).timestamp()
        
        for item in fila:
            corretor = item["corretor"]
            ultimo_ts_str = item.get("ultimo_lead_recebido")
            
            # REGRA DOS 10 MINUTOS (600 SEGUNDOS)
            if ultimo_ts_str:
                try:
                    ultimo_ts = float(ultimo_ts_str)
                    diferenca_segundos = agora_ts - ultimo_ts
                    
                    if diferenca_segundos < 600:  # Se passaram menos de 10 min (600s)
                        continue # Pula esse corretor (está em descanso)
                except ValueError:
                    pass # Se não for um número (ex: é uma data ISO antiga), ignora
            
            # Se passou pelo descanso, e está no stand, retorna ele!
            if (no_stand and corretor in no_stand) or (not no_stand):
                return corretor
                
        return None 
    except Exception as e:
        st.error(f"❌ Erro na roleta: {str(e)}")
        return None

def distribuir_lead(lead_id):
    """Atribui o lead para um corretor."""
    corretor = proximo_corretor_disponivel()
    if corretor:
        client = get_client()
        try:
            client.table("crm_leads").update({"corretor": corretor}).eq("id", lead_id).execute()
            # Atualiza a hora atual em Timestamp
            agora_ts = str(datetime.now(FUSO_BR).timestamp())
            client.table("roleta_fila").update({"ultimo_lead_recebido": agora_ts}).eq("corretor", corretor).execute()
            return corretor
        except Exception as e:
            st.error(f"❌ Erro ao distribuir lead: {str(e)}")
            return None
    return None