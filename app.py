import streamlit as st
from src.auth import carregar_usuarios
from src.construtoras_storage import carregar_construtoras

# === CONFIGURAÇÃO DA PÁGINA ===
st.set_page_config(
    page_title="Everest ERP Imobiliário",  # Nome novo aqui
    page_icon="🏔️",                       # Favicon de montanha
    layout="wide",
    initial_sidebar_state="expanded",
)

# === CSS GLOBAL ===
# (Mantive o CSS exatamente como estava, para não perder o estilo)
st.markdown("""
<style>
    .stApp { background-color: #eef2f7 !important; }
    .css-1d391kg, .st-emotion-cache-1d391kg {
        background-color: #ffffff !important;
        border-right: 1px solid #d0d7de !important;
    }
    .card-moderno {
        background-color: #ffffff !important;
        border-radius: 12px !important;
        padding: 20px !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06) !important;
        border: 1px solid #e2e8f0 !important;
        margin-bottom: 16px !important;
    }
    .card-moderno:hover { box-shadow: 0 4px 16px rgba(0,0,0,0.10) !important; }
    .stButton button[kind="primary"] {
        background-color: #1a73e8 !important;
        color: white !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        padding: 8px 24px !important;
        border: none !important;
        box-shadow: 0 2px 4px rgba(26,115,232,0.3) !important;
        transition: 0.2s !important;
    }
    .stButton button[kind="primary"]:hover {
        background-color: #1557b0 !important;
        box-shadow: 0 4px 12px rgba(26,115,232,0.4) !important;
        transform: translateY(-1px) !important;
    }
    .stButton button:not([kind="primary"]) {
        background-color: #f1f3f4 !important;
        color: #1a73e8 !important;
        border: 1px solid #dadce0 !important;
        border-radius: 8px !important;
        font-weight: 500 !important;
        padding: 8px 20px !important;
        transition: 0.2s !important;
    }
    .stButton button:not([kind="primary"]):hover {
        background-color: #e8eaed !important;
        border-color: #1a73e8 !important;
    }
    h1, h2, h3 { color: #0d2b3e !important; font-weight: 600 !important; }
    h1 {
        font-size: 2.2rem !important;
        border-bottom: 3px solid #1a73e8 !important;
        padding-bottom: 8px !important;
        display: inline-block !important;
    }
    .badge-perfil {
        display: inline-block !important;
        padding: 4px 12px !important;
        border-radius: 20px !important;
        font-size: 12px !important;
        font-weight: 600 !important;
        color: white !important;
    }
    .badge-superadmin { background-color: #dc3545 !important; }
    .badge-gerente { background-color: #1a73e8 !important; }
    .badge-corretor { background-color: #28a745 !important; }
    hr { margin: 2rem 0 !important; border: 0 !important; border-top: 1px solid #e2e8f0 !important; }
    
    .stButton button:disabled {
        background-color: #e2e8f0 !important;
        color: #94a3b8 !important;
        border: 1px solid #cbd5e1 !important;
        cursor: not-allowed !important;
    }
</style>
""", unsafe_allow_html=True)

# =========================================================
# ROTAS PÚBLICAS (LANDING PAGE E LGPD)
# =========================================================
if st.query_params.get("lead") == "true":
    campanha_id = st.query_params.get("campanha", "Direto")
    from src.crm.landing_page import renderizar_landing_page
    renderizar_landing_page(campanha_id=campanha_id)
    st.stop()

if st.query_params.get("consentimento"):
    token = st.query_params.get("consentimento")
    from src.documentos_storage import verificar_consentimento, autorizar_consentimento, validar_otp_consentimento
    
    st.markdown("<h1 style='text-align: center;'>🔒 Termo de Consentimento (LGPD)</h1>", unsafe_allow_html=True)
    st.markdown("---")
    
    status_atual = verificar_consentimento(token)
    if status_atual == "autorizado":
        st.success("✅ Você já autorizou o uso dos seus documentos. Obrigado!")
    elif status_atual == "pendente":
        st.info("Para a sua segurança, enviamos um código de 6 dígitos para o seu WhatsApp. Por favor, insira-o abaixo para liberar a autorização.")
        
        codigo_input = st.text_input("Digite o código recebido:", max_chars=6, key="input_otp_cliente")
        
        if st.button("✅ Validar Código e Autorizar", type="primary", use_container_width=True):
            if validar_otp_consentimento(token, codigo_input):
                if autorizar_consentimento(token):
                    st.success("🎉 Autorização registrada com sucesso! Você já pode fechar esta página.")
                    st.balloons()
                else:
                    st.error("Erro ao registrar autorização. Tente novamente.")
            else:
                st.error("❌ Código inválido. Verifique o WhatsApp e tente novamente.")
    else:
        st.error("❌ Link inválido ou expirado.")
    st.stop()

# =========================================================
# CARREGA DADOS BÁSICOS
# =========================================================
USUARIOS = carregar_usuarios()
# Garante que o módulo padrão exista na sessão ao logar
if "modulo_atual" not in st.session_state:
    st.session_state.modulo_atual = "📊 Simulador"
    
CONSTRUTORAS = carregar_construtoras()

# =========================================================
# RENDERIZA A SIDEBAR
# =========================================================
from src.menu_sidebar import renderizar_sidebar
renderizar_sidebar(USUARIOS, CONSTRUTORAS)

# =========================================================
# ROTEAMENTO DE PÁGINAS E LÓGICA DA BIA
# =========================================================
if st.session_state.get("usuario_logado") is None:
    from src.auth import pagina_login
    pagina_login()
else:
    # 1. LÓGICA DO CHAT DA BIA
    if st.session_state.get("mostrar_bia_chat", False):
        st.markdown("## 🤖 BIA - Assistente Imobiliária")
        st.markdown("---")
        
        col_bia, _ = st.columns([3, 1]) 
        with col_bia:
            from src.bia_operacional import pagina_bia_operacional
            pagina_bia_operacional(
                usuario_logado=st.session_state.usuario_logado, 
                USUARIOS=USUARIOS
            )
        
        if st.button("❌ Fechar BIA e Voltar", key="btn_fechar_bia", type="primary", use_container_width=True):
            st.session_state["mostrar_bia_chat"] = False
            st.rerun()
            
        st.markdown("---")
        st.stop()

    # 2. ROTEAMENTO NORMAL
    from src.rotas import renderizar_pagina_atual
    renderizar_pagina_atual(USUARIOS, CONSTRUTORAS)