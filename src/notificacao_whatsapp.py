import streamlit as st
import requests

def enviar_alerta_novo_lead(nome_cliente, renda, origem, telefone):
    """Envia uma mensagem no WhatsApp da gerente avisando do novo lead."""
    try:
        instance_id = st.secrets["ZAPI_INSTANCE_ID"]
        token = st.secrets["ZAPI_TOKEN"]
        client_token = st.secrets["ZAPI_CLIENT_TOKEN"]
        telefone_gerente = st.secrets["WHATSAPP_GERENTE"]
    except KeyError:
        print("Chaves da Z-API não configuradas nos secrets.")
        return

    # Formata a mensagem
    mensagem = f"""🚀 *NOVO LEAD RECEBIDO!*

👤 *Nome:* {nome_cliente}
💰 *Renda:* R$ {renda:,.2f}
🎯 *Origem:* {origem}
📱 *Telefone:* {telefone}

_O lead já foi distribuído automaticamente para a equipe!_"""

    # URL da API da Z-API (formato padrão)
    url = f"https://api.z-api.io/instances/{instance_id}/token/{token}/send-text"
    
    payload = {
        "phone": telefone_gerente,
        "message": mensagem
    }

    headers = {
        "Content-Type": "application/json",
        "Client-Token": "SEU_CLIENT_TOKEN_AQUI" # A Z-API fornece um Client-Token de segurança no painel
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        if response.status_code == 200:
            print("✅ Alerta enviado para o WhatsApp da gerente.")
        else:
            print(f"❌ Erro ao enviar WhatsApp: {response.text}")
    except Exception as e:
        print(f"❌ Falha na conexão com Z-API: {str(e)}")