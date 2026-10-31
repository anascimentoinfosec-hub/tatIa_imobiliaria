import streamlit as st
from src.db import get_client
from datetime import datetime, timezone, timedelta

FUSO_BR = timezone(timedelta(hours=-3))

def bater_ponto(corretor, local):
    """Corretor entra na fila (reseta o tempo)."""
    client = get_client()
    try:
        # 1. Desativa check-ins antigos
        client.table("checkins_corretores").update({"ativo": False, "data_saida": datetime.now(FUSO_BR).isoformat()}).eq("corretor", corretor).eq("ativo", True).execute()
        
        # 2. Cria o novo check-in
        client.table("checkins_corretores").insert({
            "id": f"{corretor}_{datetime.now().timestamp()}",
            "corretor": corretor,
            "local": local,
            "ativo": True
        }).execute()
        
        # 3. A MÁGICA: Deleta o registro antigo da fila e insere um novo (com tempo zerado)
        client.table("roleta_fila").delete().eq("corretor", corretor).execute()
        client.table("roleta_fila").insert({
            "corretor": corretor
            # ultimo_lead_recebido fica vazio, então ele está livre!
        }).execute()
        
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
        fila = client.table("roleta_fila").select("corretor, ultimo_lead_recebido").order("ultimo_lead_recebido").execute().data
        
        agora = datetime.now(FUSO_BR)
        
        for item in fila:
            corretor = item["corretor"]
            ultimo_recebido = item.get("ultimo_lead_recebido")
            
            # REGRA DOS 10 MINUTOS BLINDADA
            if ultimo_recebido:
                try:
                    # Se o Supabase mandou como texto, converte.
                    if isinstance(ultimo_recebido, str):
                        ultimo_dt = datetime.fromisoformat(ultimo_recebido.replace("Z", "+00:00"))
                    else:
                        # Se já mandou como datetime (o que estava causando o erro)
                        ultimo_dt = ultimo_recebido
                    
                    # Garante que tem fuso horário
                    if ultimo_dt.tzinfo is None:
                        ultimo_dt = ultimo_dt.replace(tzinfo=FUSO_BR)
                        
                    diferenca_minutos = (agora - ultimo_dt).total_seconds() / 60
                    
                    if diferenca_minutos < 10:
                        continue  # Pula o corretor (descanso)
                except Exception:
                    pass # Se der erro na data, ignora e deixa o corretor passar
            
            # Se está no stand (ou não tem ninguém no stand), retorna ele!
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
            # Atualiza a hora atual em formato ISO
            agora_iso = datetime.now(FUSO_BR).isoformat()
            client.table("roleta_fila").update({"ultimo_lead_recebido": agora_iso}).eq("corretor", corretor).execute()
            return corretor
        except Exception as e:
            st.error(f"❌ Erro ao distribuir lead: {str(e)}")
            return None
    return None

def zerar_roleta():
    """Limpa a fila e tira todos os corretores do ponto (Ação de Admin)."""
    client = get_client()
    try:
        # Deleta todos da fila
        client.table("roleta_fila").delete().neq("corretor", "x").execute()
        # Desativa todos os check-ins
        client.table("checkins_corretores").update({"ativo": False}).eq("ativo", True).execute()
        return True
    except Exception as e:
        st.error(f"❌ Erro ao zerar roleta: {str(e)}")
        return False