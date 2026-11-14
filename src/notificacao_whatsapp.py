import streamlit as st
import requests

def enviar_alerta_novo_lead(nome_cliente, renda, origem, telefone):
    """Envia uma mensagem no WhatsApp e retorna 'sucesso' ou a mensagem de erro."""
    try:
        instance_id = st.secrets["ZAPI_INSTANCE_ID"]
        token = st.secrets["ZAPI_TOKEN"]
        client_token = st.secrets["ZAPI_CLIENT_TOKEN"]
        telefone_gerente = st.secrets["WHATSAPP_GERENTE"]
    except KeyError as e:
        return f"Chave faltando no secrets: {str(e)}"

    mensagem = f"""🚀 *NOVO LEAD RECEBIDO!*

👤 *Nome:* {nome_cliente}
💰 *Renda:* R$ {renda:,.2f}
🎯 *Origem:* {origem}
📱 *Telefone:* {telefone}"""

    url = f"https://api.z-api.io/instances/{instance_id}/token/{token}/send-text"
    
    payload = {
        "phone": telefone_gerente,
        "message": mensagem
    }

    headers = {
        "Content-Type": "application/json",
        "Client-Token": client_token
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        if response.status_code == 200:
            return "sucesso"
        else:
            return f"Status {response.status_code}: {response.text}"
    except Exception as e:
        return f"Falha na conexão: {str(e)}"