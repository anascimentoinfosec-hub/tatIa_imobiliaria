from src.db import get_client
from datetime import datetime

def bater_ponto(corretor, local):
    """Corretor entra na fila."""
    client = get_client()
    try:
        # 1. Desativa check-ins antigos desse corretor
        client.table("checkins_corretores").update({"ativo": False, "data_saida": datetime.now().isoformat()}).eq("corretor", corretor).eq("ativo", True).execute()
        
        # 2. Cria o novo check-in
        client.table("checkins_corretores").insert({
            "id": f"{corretor}_{datetime.now().timestamp()}",
            "corretor": corretor,
            "local": local,
            "ativo": True
        }).execute()
        
        # 3. Adiciona/Atualiza na fila da roleta
        client.table("roleta_fila").upsert({"corretor": corretor}).execute()
        return True
    except Exception as e:
        print(f"Erro ao bater ponto: {e}")
        return False

def sair_do_ponto(corretor):
    """Corretor sai da fila."""
    client = get_client()
    try:
        client.table("checkins_corretores").update({"ativo": False, "data_saida": datetime.now().isoformat()}).eq("corretor", corretor).eq("ativo", True).execute()
        # Remove da fila
        client.table("roleta_fila").delete().eq("corretor", corretor).execute()
        return True
    except Exception:
        return False

def proximo_corretor_disponivel():
    """Acha o próximo corretor da fila que está no Stand (ou online)."""
    client = get_client()
    try:
        # Pega quem fez check-in e está ativo (prioriza Stand, depois Home/Escritório)
        checkins = client.table("checkins_corretores").select("corretor, local").eq("ativo", True).execute().data
        
        if not checkins:
            return None
            
        # Separa quem tá no stand
        no_stand = [c["corretor"] for c in checkins if c["local"] == "stand"]
        
        # Pega a fila da roleta ordenada por quem recebeu lead há mais tempo
        fila = client.table("roleta_fila").select("corretor").order("ultimo_lead_recebido").execute().data
        
        for item in fila:
            if item["corretor"] in no_stand:
                return item["corretor"] # Retorna o primeiro que está no stand
                
        # Se ninguém estiver no stand, retorna o primeiro da fila geral
        if fila:
            return fila[0]["corretor"]
            
        return None
    except Exception as e:
        print(f"Erro na roleta: {e}")
        return None

def distribuir_lead(lead_id):
    """Atribui o lead para um corretor."""
    corretor = proximo_corretor_disponivel()
    if corretor:
        client = get_client()
        # Atualiza o lead
        client.table("crm_leads").update({"corretor": corretor}).eq("id", lead_id).execute()
        # Atualiza a hora que ele recebeu o lead na fila
        client.table("roleta_fila").update({"ultimo_lead_recebido": datetime.now().isoformat()}).eq("corretor", corretor).execute()
        return corretor
    return None