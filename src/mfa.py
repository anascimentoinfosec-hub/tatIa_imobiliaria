import pyotp
import qrcode
import io
import streamlit as st
from src.db import get_client


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