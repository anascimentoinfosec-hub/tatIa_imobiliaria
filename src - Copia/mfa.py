import pyotp
import qrcode
import io
import streamlit as st
from src.db import get_client
from datetime import datetime, timedelta
import hmac
import hashlib
import base64
from streamlit_cookies_controller import CookieController

def gerar_segredo_mfa():
    """Gera um segredo TOTP único para o usuário."""
    return pyotp.random_base32()


def gerar_qr_code(nome_usuario, segredo, nome_app="TatIA Imobiliaria"):
    """Gera a imagem do QR Code para o usuário escanear."""
    totp = pyotp.TOTP(segredo)
    # O formato 'otpauth://' é reconhecido por todos os apps de autenticação
    uri = totp.provisioning_uri(name=nome_usuario, issuer_name=nome_app)
    qr = qrcode.make(uri)
    buf = io.BytesIO()
    qr.save(buf, format="PNG")
    return buf.getvalue()


def verificar_codigo(segredo, codigo_digitado):
    """Verifica se o código de 6 dígitos é válido."""
    totp = pyotp.TOTP(segredo)
    # valid_window=1 permite uma pequena tolerância de relógio (30s antes/depois)
    return totp.verify(codigo_digitado, valid_window=1)


def salvar_segredo_mfa(login, segredo):
    """Salva o segredo e ativa o MFA do usuário no Supabase."""
    client = get_client()
    client.table("usuarios").update({
        "mfa_secret": segredo,
        "mfa_ativo": True
    }).eq("login", login).execute()


def desativar_mfa(login):
    """Remove o MFA do usuário."""
    client = get_client()
    client.table("usuarios").update({
        "mfa_secret": None,
        "mfa_ativo": False
    }).eq("login", login).execute()


def obter_status_mfa(login, usuarios_dict):
    """Retorna (mfa_ativo, mfa_secret) do usuário."""
    dados = usuarios_dict.get(login, {})
    return dados.get("mfa_ativo", False), dados.get("mfa_secret")

# Chave secreta para assinar o cookie (Em produção, coloque isso no secrets.toml)
SECRET_KEY = "tatia_imobiliaria_mfa_secret_key_2026"

def gerar_token_confianca(login):
    """Gera um token com o login e a data de expiração."""
    expira_em = (datetime.now() + timedelta(hours=10)).timestamp()
    dados = f"{login}|{expira_em}"
    
    # Assina os dados para evitar fraude
    assinatura = hmac.new(
        SECRET_KEY.encode(), dados.encode(), hashlib.sha256
    ).hexdigest()
    
    token = f"{dados}|{assinatura}"
    return base64.b64encode(token.encode()).decode()

def validar_token_confianca(token_b64, login_esperado):
    """Valida se o token é autêntico e se não expirou."""
    try:
        token = base64.b64decode(token_b64.encode()).decode()
        login, expira_em, assinatura = token.split("|")
        
        # 1. Verifica se o token é daquele usuário
        if login != login_esperado:
            return False
            
        # 2. Verifica a assinatura
        dados = f"{login}|{expira_em}"
        assinatura_esperada = hmac.new(
            SECRET_KEY.encode(), dados.encode(), hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(assinatura, assinatura_esperada):
            return False
            
        # 3. Verifica se expirou (10 horas)
        if datetime.now().timestamp() > float(expira_em):
            return False
            
        return True
    except Exception:
        return False