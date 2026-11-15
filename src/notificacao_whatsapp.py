import requests
import streamlit as st
from src.configuracoes_storage import obter_configuracao

def enviar_alerta_novo_lead(nome_cliente, renda, origem, telefone="", corretor=""):
    """
    Envia um alerta de novo lead para o WhatsApp do gerente via Evolution API.
    Retorna 'sucesso' ou a mensagem de erro.
    """
    # 1. Busca o número do gerente no banco (já configurado na tela de Configurações)
    numero_gerente = obter_configuracao("whatsapp_gerente", "")
    if not numero_gerente:
        return "Número do gerente não configurado no sistema."

    # 2. Puxa as credenciais do secrets.toml
    try:
        EVOLUTION_URL = st.secrets["evolution"]["url"]
        EVOLUTION_APIKEY = st.secrets["evolution"]["apikey"]
        EVOLUTION_INSTANCE = st.secrets["evolution"]["instance"]
    except KeyError:
        return "Credenciais da Evolution API não encontradas no secrets.toml."

    # 3. Monta a mensagem
    mensagem = f"🚨 *NOVO LEAD RECEBIDO!*\n\n"
    mensagem += f"👤 *Cliente:* {nome_cliente}\n"
    mensagem += f"💰 *Renda:* R$ {renda:,.2f}\n"
    mensagem += f"🎯 *Origem:* {origem}\n"
    if telefone:
        mensagem += f"📞 *Telefone:* {telefone}\n"
    if corretor:
        mensagem += f"🏃 *Corretor:* {corretor}\n"
    mensagem += "\n_Acesse o CRM para mais detalhes._"

    # 4. Dispara para a Evolution API
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