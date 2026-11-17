import requests
import streamlit as st
from src.configuracoes_storage import obter_configuracao
from src.db import get_client

def traduzir_origem(origem):
    if not origem or len(origem) > 20:
        return origem
    client = get_client()
    try:
        res = client.table("crm_campanhas").select("nome").eq("id", origem).execute()
        if res.data and len(res.data) > 0:
            return res.data[0]["nome"]
    except Exception:
        pass
    return origem

def enviar_alerta_novo_lead(nome_cliente, renda, origem, telefone="", corretor=""):
    numero_gerente = obter_configuracao("whatsapp_gerente", "")
    if not numero_gerente:
        return "Número do gerente não configurado no sistema."

    try:
        EVOLUTION_URL = st.secrets["evolution"]["url"]
        EVOLUTION_APIKEY = st.secrets["evolution"]["apikey"]
        EVOLUTION_INSTANCE = st.secrets["evolution"]["instance"]
    except KeyError:
        return "Credenciais da Evolution API não encontradas no secrets.toml."

    origem_amigavel = traduzir_origem(origem)

    mensagem = f"🚨 *NOVO LEAD RECEBIDO!*\n\n"
    mensagem += f"👤 *Cliente:* {nome_cliente}\n"
    mensagem += f"💰 *Renda:* R$ {renda:,.2f}\n"
    mensagem += f"🎯 *Origem:* {origem_amigavel}\n"
    if telefone:
        mensagem += f"📞 *Telefone:* {telefone}\n"
    if corretor:
        mensagem += f"🏃 *Corretor:* {corretor}\n"
    mensagem += "\n_Acesse o CRM para mais detalhes._"

    url = f"{EVOLUTION_URL}/message/sendText/{EVOLUTION_INSTANCE}"
    headers = {"apikey": EVOLUTION_APIKEY, "Content-Type": "application/json"}
    payload = {"number": numero_gerente, "text": mensagem}

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        if response.status_code in [200, 201]:
            return "sucesso"
        else:
            return f"Erro API ({response.status_code}): {response.text}"
    except Exception as e:
        return f"Erro de conexão: {str(e)}"

def enviar_otp_lgpd(telefone_cliente, codigo_otp):
    try:
        EVOLUTION_URL = st.secrets["evolution"]["url"]
        EVOLUTION_APIKEY = st.secrets["evolution"]["apikey"]
        EVOLUTION_INSTANCE = st.secrets["evolution"]["instance"]
    except KeyError:
        return "Credenciais da Evolution API não encontradas."

    mensagem = f"🔒 *Código de Segurança - LGPD*\n\n"
    mensagem += f"Seu código para autorizar o uso dos documentos é:\n\n"
    mensagem += f"*{codigo_otp}*\n\n"
    mensagem += "_Se você não solicitou este código, por favor ignore esta mensagem._"

    url = f"{EVOLUTION_URL}/message/sendText/{EVOLUTION_INSTANCE}"
    headers = {"apikey": EVOLUTION_APIKEY, "Content-Type": "application/json"}
    payload = {"number": telefone_cliente, "text": mensagem}

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        return "sucesso" if response.status_code in [200, 201] else f"Erro API: {response.text}"
    except Exception as e:
        return f"Erro de conexão: {str(e)}"