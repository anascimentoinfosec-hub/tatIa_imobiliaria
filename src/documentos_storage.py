import streamlit as st
from src.db import get_client
from datetime import datetime
import uuid
import secrets

BUCKET = "documentos-clientes"

def upload_documento(arquivo, cliente_nome, tipo_doc="doc"):
    client = get_client()
    try:
        nome_limpo = cliente_nome.strip().replace(" ", "_").lower()
        extensao = arquivo.name.split('.')[-1]
        nome_unico = f"{nome_limpo}_{uuid.uuid4().hex[:6]}.{extensao}"
        path = nome_unico

        bytes_data = arquivo.getvalue()
        # Tenta fazer o upload
        client.storage.from_(BUCKET).upload(
            path=path,
            file=bytes_data,
            file_options={"content-type": arquivo.type}
        )
        return path
    except Exception as e:
        # AQUI ESTÁ O SEGREDO: Mostra o erro na tela!
        st.error(f"❌ Erro ao enviar arquivo para o Supabase Storage: {str(e)}")
        return None

def gerar_link_temporario(path, expira_em_segundos=3600):
    client = get_client()
    try:
        response = client.storage.from_(BUCKET).create_signed_url(
            path=path, expires_in=expira_em_segundos
        )
        return response.get("signedURL") or response.get("signed_url")
    except Exception as e:
        st.warning(f"⚠️ Erro ao gerar link de download: {str(e)}")
        return None

def criar_token_consentimento(cliente_nome):
    client = get_client()
    try:
        token = secrets.token_urlsafe(16)
        client.table("consentimentos_lgpd").insert({
            "id": secrets.token_hex(8),
            "cliente_nome": cliente_nome,
            "token": token,
            "status": "pendente"
        }).execute()
        return token
    except Exception as e:
        print(f"Erro ao criar token: {e}")
        return None

def verificar_consentimento(token):
    client = get_client()
    try:
        res = client.table("consentimentos_lgpd").select("status").eq("token", token).execute()
        if res.data:
            return res.data[0]["status"]
    except Exception:
        pass
    return "nao_encontrado"

def autorizar_consentimento(token):
    client = get_client()
    try:
        client.table("consentimentos_lgpd").update({
            "status": "autorizado",
            "data_autorizacao": datetime.now().isoformat()
        }).eq("token", token).execute()
        return True
    except Exception as e:
        print(f"Erro ao autorizar: {e}")
        return False

def obter_data_consentimento(token):
    client = get_client()
    try:
        res = client.table("consentimentos_lgpd").select("data_autorizacao").eq("token", token).execute()
        if res.data and res.data[0]["data_autorizacao"]:
            data_iso = res.data[0]["data_autorizacao"]
            dt = datetime.fromisoformat(data_iso.replace("Z", "+00:00"))
            return dt.strftime("%d/%m/%Y às %H:%M")
    except Exception:
        pass
    return ""