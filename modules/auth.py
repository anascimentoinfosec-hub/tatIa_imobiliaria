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

# =============================================
# USUÁRIOS FIXOS (DIRETO NO CÓDIGO - PARA TESTE)
# =============================================
USUARIOS_FIXOS = {
    "superadmin": {
        "nome": "Administrador do Sistema",
        "hash": hash_senha("admin2026"),
        "perfil": "superadmin",
        "ativo": True,
        "email": "admin@email.com"
    },
    "gerente": {
        "nome": "Gerente Geral",
        "hash": hash_senha("gerente2026"),
        "perfil": "gerente",
        "ativo": True,
        "email": "gerente@email.com"
    }
}

def carregar_usuarios():
    """Carrega usuários - PRIORIDADE: usuários fixos"""
    # SEMPRE usa os usuários fixos primeiro
    return USUARIOS_FIXOS.copy()

def salvar_usuarios(usuarios):
    """Salva os usuários (mantém os fixos como base)"""
    # Atualiza os fixos com as alterações
    for login, dados in usuarios.items():
        if login in USUARIOS_FIXOS:
            USUARIOS_FIXOS[login].update(dados)
        else:
            USUARIOS_FIXOS[login] = dados
    
    # Tenta salvar no JSON também (opcional)
    try:
        with open(ARQUIVO_USUARIOS, 'w', encoding='utf-8') as f:
            json.dump(USUARIOS_FIXOS, f, indent=2, ensure_ascii=False)
    except:
        pass
    
    return USUARIOS_FIXOS

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

def exibir_login_sidebar(USUARIOS):
    """Exibe o formulário de login e recuperação de senha na sidebar"""
    
    st.markdown("### Login")
    usuario = st.text_input("Usuário", key="login_usuario")
    senha = st.text_input("Senha", type="password", key="login_senha")
          
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("Entrar", use_container_width=True):
            if verificar_login(usuario, senha, USUARIOS):
                st.session_state.usuario_logado = usuario
                st.success(f"✅ Bem-vindo, {USUARIOS[usuario]['nome']}!")
                st.rerun()
            else:
                st.error("❌ Usuário ou senha inválidos!")
    
    with col2:
        if st.button("🔑 Esqueci a senha", use_container_width=True):
            st.session_state['recuperando_senha'] = True
            st.rerun()
    
    # --- RECUPERAÇÃO DE SENHA ---
    if st.session_state.get('recuperando_senha', False):
        st.markdown("---")
        st.markdown("### 🔐 Recuperar senha")
        
        email = st.text_input("E-mail cadastrado", key="email_recuperacao")
        
        if st.button("📧 Enviar código", use_container_width=True):
            if email:
                email_existe = False
                for user, dados in USUARIOS.items():
                    if dados.get("email") == email:
                        email_existe = True
                        break
                
                if not email_existe:
                    st.warning("⚠️ E-mail não encontrado. Verifique ou contate o administrador.")
                else:
                    token = gerar_token_recuperacao()
                    salvar_token_recuperacao(email, token)
                    
                    if enviar_email_recuperacao(email, token):
                        st.success("✅ Código enviado para seu e-mail!")
                        st.session_state['token_enviado'] = True
                    else:
                        st.error("❌ Erro ao enviar e-mail")
            else:
                st.warning("⚠️ Digite seu e-mail cadastrado.")
        
        if st.session_state.get('token_enviado', False):
            codigo = st.text_input("Código de verificação", key="codigo_recuperacao")
            nova_senha = st.text_input("Nova senha", type="password", key="nova_senha")
            confirmar_senha = st.text_input("Confirmar nova senha", type="password", key="confirmar_senha")
            
            if st.button("✅ Alterar senha", use_container_width=True):
                if codigo and nova_senha and confirmar_senha:
                    if nova_senha != confirmar_senha:
                        st.error("❌ As senhas não coincidem!")
                    elif len(nova_senha) < 6:
                        st.error("❌ A senha deve ter pelo menos 6 caracteres!")
                    else:
                        if validar_token_recuperacao(email, codigo):
                            for user, dados in USUARIOS.items():
                                if dados.get("email") == email:
                                    dados["hash"] = hash_senha(nova_senha)
                                    salvar_usuarios(USUARIOS)
                                    remover_token_recuperacao(email)
                                    st.success("✅ Senha alterada com sucesso!")
                                    st.session_state['recuperando_senha'] = False
                                    st.session_state['token_enviado'] = False
                                    st.rerun()
                                    break
                        else:
                            st.error("❌ Código inválido ou expirado!")
                else:
                    st.error("❌ Preencha todos os campos!")
        
        if st.button("🔙 Voltar ao login"):
            st.session_state['recuperando_senha'] = False
            st.session_state['token_enviado'] = False
            st.rerun()

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