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
# CSS PERSONALIZADO (VISUAL MODERNO)
# =========================================================
st.markdown("""
<style>
    /* Fundo geral */
    .stApp {
        background-color: #f8f9fa;
    }
    
    /* Cards modernos */
    .card-moderno {
        background-color: white;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        border: 1px solid #e9ecef;
        margin-bottom: 16px;
        transition: 0.2s;
    }
    .card-moderno:hover {
        box-shadow: 0 4px 16px rgba(0,0,0,0.10);
    }
    
    /* Botões */
    .stButton button {
        border-radius: 8px;
        font-weight: 500;
        transition: 0.2s;
        border: none;
        padding: 8px 20px;
    }
    .stButton button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    .stButton button:active {
        transform: translateY(0px);
    }
    
    /* Botão primário (salvar, carregar) */
    .stButton button[kind="primary"] {
        background-color: #1a73e8;
        color: white;
    }
    .stButton button[kind="primary"]:hover {
        background-color: #1557b0;
    }
    
    /* Títulos */
    h1, h2, h3 {
        color: #1a237e;
        font-weight: 600;
    }
    h1 {
        font-size: 2.2rem;
        border-bottom: 3px solid #1a73e8;
        padding-bottom: 8px;
        display: inline-block;
    }
    
    /* Sidebar */
    .css-1d391kg {
        background-color: #ffffff;
        border-right: 1px solid #e9ecef;
    }
    .css-1d391kg .st-emotion-cache-1wivap2 {
        padding: 2rem 1rem;
    }
    
    /* Inputs */
    .stTextInput input, .stSelectbox select, .stNumberInput input {
        border-radius: 8px;
        border: 1px solid #ced4da;
        padding: 8px 12px;
    }
    .stTextInput input:focus, .stSelectbox select:focus, .stNumberInput input:focus {
        border-color: #1a73e8;
        box-shadow: 0 0 0 2px rgba(26,115,232,0.2);
    }
    
    /* Dataframe (tabelas) */
    .stDataFrame {
        border-radius: 8px;
        overflow: hidden;
        border: 1px solid #e9ecef;
    }
    .stDataFrame thead tr th {
        background-color: #f1f3f5 !important;
        font-weight: 600 !important;
        color: #202124 !important;
        padding: 10px 12px !important;
    }
    .stDataFrame tbody tr:hover {
        background-color: #f8f9fa !important;
    }
    
    /* Métricas */
    .stMetric {
        background-color: white;
        border-radius: 12px;
        padding: 16px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        border: 1px solid #e9ecef;
        text-align: center;
    }
    .stMetric .stMetric-label {
        font-size: 14px;
        color: #5f6368;
        font-weight: 500;
    }
    .stMetric .stMetric-value {
        font-size: 28px;
        font-weight: 700;
        color: #1a237e;
    }
    
    /* Separadores */
    hr {
        margin: 2rem 0;
        border: 0;
        border-top: 1px solid #e9ecef;
    }
    
    /* Badge de perfil */
    .badge-perfil {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
        color: white;
    }
    .badge-superadmin { background-color: #dc3545; }
    .badge-gerente { background-color: #1a73e8; }
    .badge-corretor { background-color: #28a745; }
    
    /* Footer */
    .footer {
        text-align: center;
        padding: 20px 0;
        color: #6c757d;
        font-size: 13px;
        border-top: 1px solid #e9ecef;
        margin-top: 30px;
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
        
        # Nome e perfil com badge
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