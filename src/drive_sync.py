import streamlit as st
import pandas as pd
import hashlib
import io
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

def get_drive_service():
    """Autentica usando as credenciais do secrets.toml"""
    creds_dict = dict(st.secrets["gcp_service_account"])
    creds = service_account.Credentials.from_service_account_info(creds_dict)
    return build('drive', 'v3', credentials=creds)

def listar_planilhas_drive():
    """Lista arquivos Excel na pasta configurada (Protegido para Superadmin)"""
    from src.configuracoes_storage import obter_configuracao
    from src.auth import carregar_usuarios
    
    # 1. BLINDAGEM DE SEGURANÇA
    usuario_logado = st.session_state.get("usuario_logado")
    USUARIOS = carregar_usuarios()
    perfil = USUARIOS.get(usuario_logado, {}).get("perfil", "corretor")
    
    if perfil != "superadmin":
        raise Exception("Acesso negado. Apenas o Superadmin pode sincronizar o Google Drive.")
    
    # 2. Busca o ID da pasta (banco de dados ou fallback para o secrets)
    folder_id = obter_configuracao("drive_folder_id", "")
    if not folder_id:
        folder_id = st.secrets.get("google_drive", {}).get("folder_id", "")
        
    if not folder_id:
        raise Exception("Pasta do Google Drive não configurada.")

    service = get_drive_service()
    
    query = f"'{folder_id}' in parents and (mimeType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' or mimeType='application/vnd.google-apps.spreadsheet') and trashed=false"
    
    results = service.files().list(q=query, fields="files(id, name, mimeType, md5Checksum, modifiedTime)").execute()
    return results.get('files', [])

def baixar_planilha_bruta(file_id, mime_type):
    """Baixa o arquivo e retorna o DataFrame CRU (sem cabeçalho definido)."""
    service = get_drive_service()
    
    if mime_type == 'application/vnd.google-apps.spreadsheet':
        request = service.files().export_media(fileId=file_id, mimeType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    else:
        request = service.files().get_media(fileId=file_id)
        
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while done is False:
        status, done = downloader.next_chunk()
        
    fh.seek(0)
    df_bruto = pd.read_excel(fh, header=None, nrows=15)
    return df_bruto

def verificar_hash_arquivo(file_hash):
    """Verifica no Supabase se esse arquivo já foi processado"""
    from src.db import get_client
    client = get_client()
    try:
        res = client.table("historico_importacoes").select("id").eq("hash_arquivo", file_hash).execute()
        return len(res.data) > 0
    except Exception:
        return False

def registrar_importacao(file_hash, nome_arquivo, status):
    """Salva o histórico para evitar duplicidade"""
    from src.db import get_client
    client = get_client()
    try:
        client.table("historico_importacoes").insert({
            "hash_arquivo": file_hash,
            "nome_arquivo": nome_arquivo,
            "status": status
        }).execute()
    except Exception as e:
        print(f"Erro ao registrar: {e}")