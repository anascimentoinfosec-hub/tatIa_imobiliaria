import streamlit as st
import json
import os
import secrets
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from modules.utils import hash_senha

ARQUIVO_USUARIOS = "dados/usuarios.json"
ARQUIVO_RECUPERACAO = "dados/recuperacao.json"

def carregar_usuarios():
    try:
        if os.path.exists(ARQUIVO_USUARIOS):
            with open(ARQUIVO_USUARIOS, 'r', encoding='utf-8') as f:
                return json.load(f)
    except:
        pass
    return {
        "gerente": {
            "nome": "Gerente Geral",
            "hash": hash_senha("gerente2026"),
            "perfil": "gerente",
            "ativo": True,
            "email": "gerente@email.com",
            "criado_em": datetime.now().isoformat()
        }
    }

def salvar_usuarios(usuarios):
    with open(ARQUIVO_USUARIOS, 'w', encoding='utf-8') as f:
        json.dump(usuarios, f, indent=2, ensure_ascii=False)

def verificar_login(usuario: str, senha: str, usuarios: dict) -> bool:
    if usuario not in usuarios:
        return False
    return usuarios[usuario]["hash"] == hash_senha(senha) and usuarios[usuario]["ativo"]

def gerar_token_recuperacao():
    return ''.join(secrets.choice('0123456789') for _ in range(6))

def salvar_token_recuperacao(email, token):
    recuperacao = {}
    try:
        if os.path.exists(ARQUIVO_RECUPERACAO):
            with open(ARQUIVO_RECUPERACAO, 'r', encoding='utf-8') as f:
                recuperacao = json.load(f)
    except:
        pass
    
    recuperacao[email] = {
        "token": token,
        "criado_em": datetime.now().isoformat()
    }
    
    with open(ARQUIVO_RECUPERACAO, 'w', encoding='utf-8') as f:
        json.dump(recuperacao, f, indent=2, ensure_ascii=False)

def validar_token_recuperacao(email, token):
    try:
        if not os.path.exists(ARQUIVO_RECUPERACAO):
            return False
        
        with open(ARQUIVO_RECUPERACAO, 'r', encoding='utf-8') as f:
            recuperacao = json.load(f)
        
        if email not in recuperacao:
            return False
        
        dados = recuperacao[email]
        if dados["token"] != token:
            return False
        
        criado_em = datetime.fromisoformat(dados["criado_em"])
        if datetime.now() - criado_em > timedelta(minutes=15):
            return False
        
        return True
    except:
        return False

def remover_token_recuperacao(email):
    try:
        if os.path.exists(ARQUIVO_RECUPERACAO):
            with open(ARQUIVO_RECUPERACAO, 'r', encoding='utf-8') as f:
                recuperacao = json.load(f)
            
            if email in recuperacao:
                del recuperacao[email]
            
            with open(ARQUIVO_RECUPERACAO, 'w', encoding='utf-8') as f:
                json.dump(recuperacao, f, indent=2, ensure_ascii=False)
    except:
        pass

def enviar_email_recuperacao(email, token):
    try:
        if "EMAIL_SENDER" not in st.secrets or "EMAIL_PASSWORD" not in st.secrets:
            st.warning(f"⚠️ Configure EMAIL_SENDER e EMAIL_PASSWORD nos Secrets do Streamlit")
            st.info(f"💡 Token gerado: *{token}* (copie e cole)")
            return True
        
        remetente = st.secrets["EMAIL_SENDER"]
        senha = st.secrets["EMAIL_PASSWORD"]
        
        msg = MIMEMultipart()
        msg['From'] = remetente
        msg['To'] = email
        msg['Subject'] = "🔐 Código de recuperação - Simulador de Crédito"
        
        corpo = f"""
        Olá!
        
        Você solicitou a recuperação de senha do Simulador de Crédito.
        
        Seu código de verificação é: *{token}*
        
        Digite este código no app para criar uma nova senha.
        
        Este código é válido por 15 minutos.
        
        Se você não solicitou esta recuperação, ignore este e-mail.
        
        Atenciosamente,
        Equipe Simulador de Crédito
        """
        
        msg.attach(MIMEText(corpo, 'plain'))
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(remetente, senha)
        server.send_message(msg)
        server.quit()
        
        return True
    except Exception as e:
        st.error(f"❌ Erro ao enviar e-mail: {str(e)}")
        return False

def pagina_login():
    st.markdown("""
    <style>
    .login-hero {
        background: linear-gradient(135deg, #1a237e, #0d47a1, #1565c0);
        padding: 40px 30px;
        border-radius: 16px;
        color: white;
        text-shadow: 2px 2px 8px rgba(0,0,0,0.8);
        margin-bottom: 30px;
        text-align: center;
    }
    .login-hero h1 { font-size: 36px; margin: 0; }
    .login-hero p { font-size: 18px; margin: 8px 0 0 0; opacity: 0.9; }
    </style>
    <div class="login-hero">
        <h1>🏢 Simulador de Crédito Imobiliário</h1>
        <p>Rio de Janeiro • Oásis II e outras construtoras</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### 📊 Mercado Imobiliário")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Taxa Selic", "10,50%")
        st.metric("TR", "1,50% a.a.")
    with col2:
        st.metric("Taxa SFH", "9,50% a.a.")
        st.metric("Entrada média", "20-30%")
    with col3:
        st.metric("Valor m² (RJ)", "R$ 12.800")
        st.metric("Prazo máximo", "420 meses")
    
    st.markdown("---")
    st.markdown("### 🏗️ Empreendimento em Destaque")
    st.success("*Oásis II*  \n📍 Barra da Tijuca - Rio de Janeiro  \n🏢 18 andares • 115 unidades • 2 e 3 quartos  \n💰 Preços a partir de R$ 384.950")
