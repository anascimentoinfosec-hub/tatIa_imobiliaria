import streamlit as st
import requests
from src.configuracoes_storage import obter_configuracao

def enviar_alerta_novo_lead(nome_cliente, renda, origem, telefone):
    """Envia uma mensagem no WhatsApp via Omni Z-API."""
    try:
        # Credenciais da Z-API continuam no secrets (são fixas e seguras)
        secret_key = st.secrets["ZAPI_SECRET_KEY"]
        channel_id = st.secrets["ZAPI_CHANNEL_ID"]
    except KeyError as e:
        return f"Chave faltando no secrets: {str(e)}"
    
    # O número do gerente agora vem do BANCO DE DADOS (editável na tela)
    telefone_gerente = obter_configuracao("whatsapp_gerente", "")
    
    if not telefone_gerente:
        return "Número do gerente não configurado no painel de Configurações."

    mensagem = f"""🚀 *NOVO LEAD RECEBIDO!*

👤 *Nome:* {nome_cliente}
💰 *Renda:* R$ {renda:,.2f}
🎯 *Origem:* {origem}
📱 *Telefone:* {telefone}"""

    url = f"https://api.omni.z-api.io/v1/channels/{channel_id}/messages"
    
    payload = {
        "phone": telefone_gerente,
        "message": mensagem
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {secret_key}"
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        print("DEBUG ZAPI:", response.status_code, response.text)
        if response.status_code in [200, 201]:
            return "sucesso"
        else:
            return f"Status {response.status_code}: {response.text}"
    except Exception as e:
        return f"Falha na conexão: {str(e)}"
