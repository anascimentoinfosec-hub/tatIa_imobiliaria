import requests
import streamlit as st
from src.configuracoes_storage import obter_configuracao
from src.db import get_client # <-- Importante para buscar o nome da campanha

def traduzir_origem(origem):
    """Se a origem for um ID de campanha (ex: 55fccc8a), busca o nome real no Supabase."""
    if not origem or len(origem) > 20: # Se já for um nome grande, ignora
        return origem
        
    client = get_client()
    try:
        # Busca o nome da campanha pelo ID. Ajuste o nome da tabela e coluna se necessário!
        res = client.table("crm_campanhas").select("nome").eq("id", origem).execute()
        if res.data and len(res.data) > 0:
            return res.data[0]["nome"]
    except Exception:
        pass # Se der erro na busca, apenas ignora e mostra o ID original
    
    return origem # Retorna o original se não achar

def enviar_alerta_novo_lead(nome_cliente, renda, origem, telefone="", corretor=""):
    """
    Envia um alerta de novo lead para o WhatsApp do gerente via Evolution API.
    Retorna 'sucesso' ou a mensagem de erro.
    """
    numero_gerente = obter_configuracao("whatsapp_gerente", "")
    if not numero_gerente:
        return "Número do gerente não configurado no sistema."

    try:
        EVOLUTION_URL = st.secrets["evolution"]["url"]
        EVOLUTION_APIKEY = st.secrets["evolution"]["apikey"]
        EVOLUTION_INSTANCE = st.secrets["evolution"]["instance"]
    except KeyError:
        return "Credenciais da Evolution API não encontradas no secrets.toml."

    # NOVO: Traduz o ID da campanha para o nome antes de mandar
    origem_amigavel = traduzir_origem(origem)

    mensagem = f"🚨 *NOVO LEAD RECEBIDO!*\n\n"
    mensagem += f"👤 *Cliente:* {nome_cliente}\n"
    mensagem += f"💰 *Renda:* R$ {renda:,.2f}\n"
    mensagem += f"🎯 *Origem:* {origem_amigavel}\n" # <-- Usa a origem traduzida aqui
    if telefone:
        mensagem += f"📞 *Telefone:* {telefone}\n"
    if corretor:
        mensagem += f"🏃 *Corretor:* {corretor}\n"
    mensagem += "\n_Acesse o CRM para mais detalhes._"

    url = f"{EVOLUTION_URL}/message/sendText/{EVOLUTION_INSTANCE}"
    headers = {
        "apikey": EVOLUTION_APIKEY,
        "Content-Type": "application/json"
    }
    payload = {
        "number": numero_gerente,
        "text": mensagem
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        if response.status_code in [200, 201]:
            return "sucesso"
        else:
            return f"Erro API ({response.status_code}): {response.text}"
    except Exception as e:
        return f"Erro de conexão: {str(e)}"