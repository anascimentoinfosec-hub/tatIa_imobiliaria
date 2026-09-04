import streamlit as st
from modules.auth import carregar_usuarios, pagina_login, exibir_login_sidebar
from modules.usuarios import pagina_gestao_usuarios
from modules.construtoras import carregar_construtoras, pagina_gestao_construtoras
from modules.simulador import pagina_simulador
from modules.bia import pagina_bia
from modules.superadmin import pagina_superadmin
from modules.creditos import pagina_creditos
from modules.dashboard import pagina_dashboard

# CONFIGURAÇÃO DA PÁGINA
st.set_page_config(
    page_title="Simulador de Crédito",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================================================
# CSS PERSONALIZADO – PALETA MODERNA COM CONTRASTE
# =========================================================
st.markdown("""
<style>
    /* Fundo principal */
    .stApp {
        background-color: #eef2f7 !important;
    }
    
    /* Sidebar */
    .css-1d391kg, .st-emotion-cache-1d391kg {
        background-color: #ffffff !important;
        border-right: 1px solid #d0d7de !important;
    }
    
    /* Cards modernos */
    .card-moderno {
        background-color: #ffffff !important;
        border-radius: 12px !important;
        padding: 20px !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06) !important;
        border: 1px solid #e2e8f0 !important;
        margin-bottom: 16px !important;
    }
    .card-moderno:hover {
        box-shadow: 0 4px 16px rgba(0,0,0,0.10) !important;
    }
    
    /* Botão primário (salvar, carregar, analisar) */
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
    .stButton button[kind="primary"]:active {
        transform: translateY(0px) !important;
    }
    
    /* Botão secundário (cancelar, limpar, etc) */
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
    
    /* Títulos */
    h1, h2, h3 {
        color: #0d2b3e !important;
        font-weight: 600 !important;
    }
    h1 {
        font-size: 2.2rem !important;
        border-bottom: 3px solid #1a73e8 !important;
        padding-bottom: 8px !important;
        display: inline-block !important;
    }
    
    /* Inputs */
    .stTextInput input, .stSelectbox select, .stNumberInput input {
        border-radius: 8px !important;
        border: 1px solid #d0d7de !important;
        padding: 8px 12px !important;
        background-color: #ffffff !important;
        transition: 0.2s !important;
    }
    .stTextInput input:focus, .stSelectbox select:focus, .stNumberInput input:focus {
        border-color: #1a73e8 !important;
        box-shadow: 0 0 0 3px rgba(26,115,232,0.15) !important;
    }
    
    /* Tabelas (Dataframe) */
    .stDataFrame {
        border-radius: 8px !important;
        overflow: hidden !important;
        border: 1px solid #e2e8f0 !important;
    }
    .stDataFrame thead tr th {
        background-color: #f1f5f9 !important;
        font-weight: 600 !important;
        color: #0d2b3e !important;
        padding: 10px 12px !important;
    }
    .stDataFrame tbody tr:hover {
        background-color: #f8fafc !important;
    }
    
    /* Métricas (cards) */
    .stMetric {
        background-color: #e8f0fe !important;
        border-radius: 12px !important;
        padding: 16px !important;
        border-left: 4px solid #1a73e8 !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.04) !important;
    }
    .stMetric .stMetric-label {
        font-size: 14px !important;
        color: #1e293b !important;
        font-weight: 500 !important;
    }
    .stMetric .stMetric-value {
        font-size: 28px !important;
        font-weight: 700 !important;
        color: #0d2b3e !important;
    }
    
    /* Badges de perfil */
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
    
    /* Separador */
    hr {
        margin: 2rem 0 !important;
        border: 0 !important;
        border-top: 1px solid #e2e8f0 !important;
    }
    
    /* Footer */
    .footer {
        text-align: center !important;
        padding: 20px 0 !important;
        color: #64748b !important;
        font-size: 13px !important;
        border-top: 1px solid #e2e8f0 !important;
        margin-top: 30px !important;
    }
    
    /* Ajuste de containers */
    .stContainer {
        background-color: transparent !important;
    }
    
    /* Fundo do conteúdo principal */
    .main > div {
        background-color: #eef2f7 !important;
    }
</style>
""", unsafe_allow_html=True)

# =========================================================
# CARREGA DADOS
# =========================================================
USUARIOS = carregar_usuarios()
CONSTRUTORAS = carregar_construtoras()

# =========================================================
# SIDEBAR
# =========================================================
with st.sidebar:
    st.markdown("### 🏢 **Simulador de Crédito**")
    st.markdown("---")
    
    if "usuario_logado" not in st.session_state:
        st.session_state.usuario_logado = None

    if st.session_state.usuario_logado is None:
        exibir_login_sidebar(USUARIOS)
    else:
        usuario = st.session_state.usuario_logado
        perfil = USUARIOS[usuario]["perfil"]
        
        nome = USUARIOS[usuario]['nome']
        badge_class = "badge-superadmin" if perfil == "superadmin" else "badge-gerente" if perfil == "gerente" else "badge-corretor"
        st.markdown(f"👤 **{nome}**")
        st.markdown(f'<span class="badge-perfil {badge_class}">{perfil.upper()}</span>', unsafe_allow_html=True)
        
        st.markdown("---")
        
        if st.button("🚪 Sair", use_container_width=True):
            st.session_state.usuario_logado = None
            st.rerun()
        
        st.markdown("---")
        
        # Menu
        if st.button("📊 Simulador", use_container_width=True):
            st.session_state.pagina = "Simulador"
            st.rerun()
        
        if st.button("💬 IA Imobiliária", use_container_width=True):
            st.session_state.pagina = "ChatIA"
            st.rerun()
        
        if perfil in ["gerente", "superadmin"]:
            st.markdown("---")
            st.markdown("### ⚙️ Gestão")
            
            if st.button("👥 Usuários", use_container_width=True):
                st.session_state.pagina = "Usuários"
                st.rerun()
            
            if st.button("🏗️ Construtoras", use_container_width=True):
                st.session_state.pagina = "Construtoras"
                st.rerun()
            
            if st.button("📊 Dashboard", use_container_width=True):
                st.session_state.pagina = "Dashboard"
                st.rerun()
        
        if perfil == "superadmin":
            st.markdown("---")
            st.markdown("### 👑 Admin")
            if st.button("👥 Gerenciar Gerentes", use_container_width=True):
                st.session_state.pagina = "SuperAdmin"
                st.rerun()
            if st.button("💰 Créditos OpenAI", use_container_width=True):
                st.session_state.pagina = "Creditos"
                st.rerun()

# =========================================================
# ROTEAMENTO DE PÁGINAS
# =========================================================
if st.session_state.usuario_logado is None:
    pagina_login()
else:
    pagina = st.session_state.get("pagina", "Simulador")
    
    if pagina == "Simulador":
        pagina_simulador(CONSTRUTORAS, USUARIOS)
    elif pagina == "ChatIA":
        pagina_bia()
    elif pagina == "Dashboard":
        pagina_dashboard(CONSTRUTORAS, USUARIOS)
    elif pagina == "SuperAdmin":
        pagina_superadmin(USUARIOS)
    elif pagina == "Usuários":
        pagina_gestao_usuarios(USUARIOS)
    elif pagina == "Construtoras":
        pagina_gestao_construtoras(CONSTRUTORAS)
    elif pagina == "Creditos":
        pagina_creditos()
    else:
        pagina_simulador(CONSTRUTORAS, USUARIOS)