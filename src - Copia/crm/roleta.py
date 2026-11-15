import streamlit as st
from src.db import get_client
from datetime import datetime, timezone, timedelta

# Usado apenas para exibição em telas, mas o cálculo é sempre UTC
FUSO_BR = timezone(timedelta(hours=-3))

def bater_ponto(corretor, local):
    """Corretor entra na fila."""
    client = get_client()
    try:
        # Desativa check-ins antigos
        client.table("checkins_corretores").update({"ativo": False, "data_saida": datetime.now(timezone.utc).isoformat()}).eq("corretor", corretor).eq("ativo", True).execute()
        
        # Cria o novo check-in
        client.table("checkins_corretores").insert({
            "id": f"{corretor}_{datetime.now().timestamp()}",
            "corretor": corretor,
            "local": local,
            "ativo": True
        }).execute()
        
        # Limpa a fila e força uma data no passado (Ano 2000) para ele ficar 100% disponível!
        client.table("roleta_fila").delete().eq("corretor", corretor).execute()
        client.table("roleta_fila").insert({
            "corretor": corretor,
            "ultimo_lead_recebido": "2000-01-01T00:00:00+00:00"
        }).execute()
        
        return True
    except Exception as e:
        st.error(f"❌ Erro ao bater ponto: {str(e)}")
        return False

def sair_do_ponto(corretor):
    """Corretor sai da fila."""
    client = get_client()
    try:
        client.table("checkins_corretores").update({"ativo": False, "data_saida": datetime.now(timezone.utc).isoformat()}).eq("corretor", corretor).eq("ativo", True).execute()
        client.table("roleta_fila").delete().eq("corretor", corretor).execute()
        return True
    except Exception as e:
        st.error(f"❌ Erro ao sair do ponto: {str(e)}")
        return False

def verificar_se_esta_na_roleta(corretor):
    """Verifica se o corretor tem um check-in ativo."""
    client = get_client()
    try:
        res = client.table("checkins_corretores").select("id").eq("corretor", corretor).eq("ativo", True).execute()
        return len(res.data) > 0
    except Exception:
        return False

def proximo_corretor_disponivel():
    """Acha o próximo corretor no Stand que não recebeu lead nos últimos 10 min."""
    client = get_client()
    try:
        checkins = client.table("checkins_corretores").select("corretor, local").eq("ativo", True).execute().data
        if not checkins:
            return None
            
        no_stand = [c["corretor"] for c in checkins if c["local"] == "stand"]
        fila = client.table("roleta_fila").select("corretor, ultimo_lead_recebido").order("ultimo_lead_recebido").execute().data
        
        agora_ts = datetime.now(timezone.utc).timestamp()
        
        for item in fila:
            corretor = item["corretor"]
            ultimo_recebido = item.get("ultimo_lead_recebido")
            
            if ultimo_recebido:
                try:
                    if isinstance(ultimo_recebido, str):
                        ultimo_dt = datetime.fromisoformat(ultimo_recebido.replace("Z", "+00:00"))
                        ultimo_ts = ultimo_dt.timestamp()
                    else:
                        ultimo_ts = ultimo_recebido.timestamp()
                    
                    diferenca_segundos = agora_ts - ultimo_ts
                    
                    if diferenca_segundos < 600:
                        continue
                except Exception:
                    pass
            
            if (no_stand and corretor in no_stand) or (not no_stand):
                return corretor
                
        return None 
    except Exception as e:
        # Não exibe o erro na tela (evita erro pro cliente)
        print(f"Erro na roleta: {e}")
        return None

def distribuir_lead(lead_id):
    """Atribui o lead para um corretor."""
    corretor = proximo_corretor_disponivel()
    if corretor:
        client = get_client()
        try:
            client.table("crm_leads").update({"corretor": corretor}).eq("id", lead_id).execute()
            agora_iso = datetime.now(timezone.utc).isoformat()
            client.table("roleta_fila").update({"ultimo_lead_recebido": agora_iso}).eq("corretor", corretor).execute()
            return corretor
        except Exception:
            return None
    return None

def puxar_lead_orfao(corretor):
    """Busca um lead 'Novo' e 'Não atribuído', respeitando a regra de 10 min."""
    client = get_client()
    try:
        res_fila = client.table("roleta_fila").select("ultimo_lead_recebido").eq("corretor", corretor).execute()
        if res_fila.data and res_fila.data[0].get("ultimo_lead_recebido"):
            ultimo_recebido = res_fila.data[0]["ultimo_lead_recebido"]
            
            if isinstance(ultimo_recebido, str):
                ultimo_dt = datetime.fromisoformat(ultimo_recebido.replace("Z", "+00:00"))
                ultimo_ts = ultimo_dt.timestamp()
            else:
                ultimo_ts = ultimo_recebido.timestamp()
                
            agora_ts = datetime.now(timezone.utc).timestamp()
            diferenca_segundos = agora_ts - ultimo_ts
            
            if diferenca_segundos < 600:
                st.warning(f"⏳ Calma aí! Você só pode puxar um novo lead em {int((600 - diferenca_segundos)/60)} minutos.")
                return False

        res = client.table("crm_leads").select("id").eq("corretor", "Não atribuído").eq("status", "novo").order("criado_em").limit(1).execute()
        
        if res.data:
            lead_id = res.data[0]["id"]
            client.table("crm_leads").update({"corretor": corretor}).eq("id", lead_id).execute()
            
            agora_iso = datetime.now(timezone.utc).isoformat()
            client.table("roleta_fila").update({"ultimo_lead_recebido": agora_iso}).eq("corretor", corretor).execute()
            return True
        return False
    except Exception as e:
        st.error(f"❌ Erro ao puxar lead: {str(e)}")
        return False

def zerar_roleta():
    """Limpa a fila e tira todos os corretores do ponto (Ação de Admin)."""
    client = get_client()
    try:
        client.table("roleta_fila").delete().neq("corretor", "x").execute()
        client.table("checkins_corretores").update({"ativo": False}).eq("ativo", True).execute()
        return True
    except Exception as e:
        st.error(f"❌ Erro ao zerar roleta: {str(e)}")
        return False