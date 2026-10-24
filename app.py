import streamlit as st
from src.auth import carregar_usuarios, pagina_login, exibir_login_sidebar
from src.usuarios import pagina_gestao_usuarios
from src.construtoras_storage import carregar_construtoras
from src.construtoras import pagina_gestao_construtoras
from src.simulador import pagina_simulador
from src.bia import pagina_bia
from src.superadmin import pagina_superadmin, renderizar_limpeza_teste
from src.creditos import pagina_creditos
from src.dashboard import pagina_dashboard
from src.origens_gerenciar import renderizar_gestao_origens
from src.simulacoes_historico import renderizar_historico
from src.regras_gerenciar import renderizar_gestao_regras
from src.vendas_gerenciar import renderizar_gestao_vendas
from src.vendas_dashboard import renderizar_dashboard_vendas
from src.bia_operacional import pagina_bia_operacional
from src.regras_entrada_gerenciar import renderizar_gestao_regras_entrada
from src.conta_seguranca import renderizar_conta_seguranca
from src.conta_seguranca import renderizar_conta_seguranca, renderizar_mfa_obrigatorio
from src.crm.kanban import renderizar_kanban
from src.crm.campanhas_ui import renderizar_campanhas
from src.configuracoes_gerenciar import renderizar_configuracoes
from src.war_room import renderizar_war_room
from src.diretor_comercial import renderizar_diretor_comercial
from src.diretor_vendas import renderizar_diretor_vendas


# =========================================================
# ROTA PÚBLICA: LANDING PAGE COM BIA
# =========================================================
# Verifica se o link tem a tag "?lead=true"
if st.query_params.get("lead") == "true":
    campanha_id = st.query_params.get("campanha", "Direto")
    from src.crm.landing_page import renderizar_landing_page
    renderizar_landing_page(campanha_id=campanha_id)
    st.stop() # O st.stop() para o código aqui e não mostra o login!

st.set_page_config(
    page_title="Simulador de Crédito",
    layout="wide",
    initial_sidebar_state="expanded",
)

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
    .stDataFrame tbody tr:hover { background-color: #f8fafc !important; }
    .stMetric {
        background-color: #e8f0fe !important;
        border-radius: 12px !important;
        padding: 16px !important;
        border-left: 4px solid #1a73e8 !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.04) !important;
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
    .main > div { background-color: #eef2f7 !important; }
</style>
""", unsafe_allow_html=True)

# =========================================================
# ROTA PÚBLICA: CONSENTIMENTO LGPD
# =========================================================
if st.query_params.get("consentimento"):
    token = st.query_params.get("consentimento")
    from src.documentos_storage import verificar_consentimento, autorizar_consentimento
    
    st.markdown("<h1 style='text-align: center;'>🔒 Termo de Consentimento (LGPD)</h1>", unsafe_allow_html=True)
    st.markdown("---")
    
    status_atual = verificar_consentimento(token)
    
    if status_atual == "autorizado":
        st.success("✅ Você já autorizou o uso dos seus documentos. Obrigado!")
    elif status_atual == "pendente":
        st.info("Para que a imobiliária possa analisar sua proposta de crédito, precisamos da sua autorização para armazenar documentos como RG, CPF e comprovantes de renda.")
        st.markdown("Seus dados serão armazenados em ambiente seguro e utilizados **exclusivamente** para a análise de crédito junto à construtora/banco, conforme a Lei Geral de Proteção de Dados (Lei 13.709/2018).")
        
        if st.button("✅ Eu autorizo o uso dos meus documentos", type="primary", use_container_width=True):
            if autorizar_consentimento(token):
                st.success("🎉 Autorização registrada com sucesso! Você já pode fechar esta página.")
                st.balloons()
            else:
                st.error("Erro ao registrar autorização. Tente novamente.")
    else:
        st.error("❌ Link inválido ou expirado.")
        
    st.stop() # Impede o sistema de carregar o resto (login, etc)
    
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

        # Pega as permissões do usuário (se não tiver nada, assume tudo liberado)
        permissoes_usuario = USUARIOS[usuario].get("permissoes", {})
        
        def tem_perm(pagina):
            return permissoes_usuario.get(pagina, True)

        nome = USUARIOS[usuario]["nome"]
        badge_class = "badge-superadmin" if perfil == "superadmin" else "badge-gerente" if perfil == "gerente" else "badge-corretor"
        st.markdown(f"👤 **{nome}**")
        st.markdown(f'<span class="badge-perfil {badge_class}">{perfil.upper()}</span>', unsafe_allow_html=True)

        st.markdown("---")

        if st.button("🚪 Sair", use_container_width=True):
            # 1. Apaga os cookies do navegador
            from streamlit_cookies_controller import CookieController
            controller = CookieController()
            controller.remove("tatia_mfa_token")
            controller.remove("tatia_mfa_user")
            
            # 2. Limpa a sessão atual
            st.session_state.usuario_logado = None
            
            # 3. Recarrega a página para voltar ao login
            st.rerun()

        st.markdown("---")

        # ---- Operacional ----
        st.markdown("### 📈 Operacional")

        if tem_perm("simulador"):
            if st.button("📊 Simulador", use_container_width=True):
                st.session_state.pagina = "Simulador"
                st.rerun()

        if tem_perm("crm"):
            if st.button("🤝 CRM de Leads", use_container_width=True):
                st.session_state.pagina = "CRM"
                st.rerun()

        if tem_perm("vendas"):
            if st.button("💼 Vendas", use_container_width=True):
                st.session_state.pagina = "Vendas"
                st.rerun()

        if tem_perm("simulacoes"):
            if st.button("📚 Simulações", use_container_width=True):
                st.session_state.pagina = "Histórico"
                st.rerun()

        if tem_perm("chat_ia"):
            if st.button("💬 IA Imobiliária", use_container_width=True):
                st.session_state.pagina = "ChatIA"
                st.rerun()

        # ---- Gestão ----
        if perfil in ["gerente", "superadmin"]:
            st.markdown("---")
            st.markdown("### ⚙️ Gestão")
            
            # Alerta de propostas pendentes
            from src.simulacoes_storage import contar_propostas_pendentes
            qtd_pendentes = contar_propostas_pendentes()
            if qtd_pendentes > 0:
                st.warning(f"🔔 **{qtd_pendentes}** proposta(s) aguardando sua aprovação!")

            if tem_perm("dashboard"):
                if st.button("📊 Dashboard", key="btn_menu_dash", use_container_width=True):
                    st.session_state.pagina = "Dashboard"
                    st.rerun()

            if tem_perm("dashboard_vendas"):
                if st.button("📈 Dashboard Vendas", key="btn_menu_dash_vendas", use_container_width=True):
                    st.session_state.pagina = "DashboardVendas"
                    st.rerun()

            if tem_perm("construtoras"):
                if st.button("🏗️ Construtoras", key="btn_menu_construtoras", use_container_width=True):
                    st.session_state.pagina = "Construtoras"
                    st.rerun()

            if tem_perm("regras_fin"):
                if st.button("🏦 Regras Financiamento", key="btn_menu_regras_fin", use_container_width=True):
                    st.session_state.pagina = "Regras"
                    st.rerun()

            if tem_perm("regras_ent"):
                if st.button("📋 Regras de Entrada", key="btn_menu_regras_ent", use_container_width=True):
                    st.session_state.pagina = "RegrasEntrada"
                    st.rerun()

            if tem_perm("origens"):
                if st.button("🎯 Origens", key="btn_menu_origens", use_container_width=True):
                    st.session_state.pagina = "Origens"
                    st.rerun()

            if tem_perm("usuarios"):
                if st.button("👥 Usuários", key="btn_menu_usuarios", use_container_width=True):
                    st.session_state.pagina = "Usuários"
                    st.rerun()

            if tem_perm("dashboard"):
                if st.button("📣 Campanhas", key="btn_menu_campanhas", use_container_width=True):
                    st.session_state.pagina = "Campanhas"
                    st.rerun()

            if st.button("⚙️ Configurações", key="btn_menu_config", use_container_width=True):
                st.session_state.pagina = "Configuracoes"
                st.rerun()

            if st.button("📺 War Room (TV)", key="btn_war_room", use_container_width=True):
                st.session_state.pagina = "WarRoom"
                st.rerun()

        # ---- Diretoria ----
        if perfil in ["gerente", "superadmin", "diretor_comercial"]: # O gerente tb pode ver por enquanto
            st.markdown("---")
            st.markdown("### 👔 Diretoria")
            
            if st.button("💼 Diretor Comercial", key="btn_dir_comercial", use_container_width=True):
                st.session_state.pagina = "DiretorComercial"
                st.rerun()

            if tem_perm("diretor_vendas"):
                if st.button("📈 Diretor de Vendas", key="btn_dir_vendas", use_container_width=True):
                    st.session_state.pagina = "DiretorVendas"
                    st.rerun()
            
            
        # ---- Admin ----
        if perfil == "superadmin":
            st.markdown("---")
            st.markdown("### 👑 Admin")

            if st.button("👥 Gerenciar Gerentes", use_container_width=True):
                st.session_state.pagina = "SuperAdmin"
                st.rerun()

            if st.button("💰 Créditos OpenAI", use_container_width=True):
                st.session_state.pagina = "Creditos"
                st.rerun()

            if st.button("🧹 Zerar Testes", key="btn_zerar_testes", use_container_width=True):
                                        st.session_state.pagina = "LimpezaTeste"
                                        st.rerun()

# =========================================================
# ROTEAMENTO
# =========================================================
if st.session_state.usuario_logado is None:
    pagina_login()
else:
    # === BLOQUEIO DE SEGURANÇA (MFA OBRIGATÓRIO) ===
    # Pega os dados do usuário logado
    dados_usuario_logado = USUARIOS.get(st.session_state.usuario_logado, {})
    mfa_ativo = dados_usuario_logado.get("mfa_ativo", False)

    if not mfa_ativo:
        # Mostra APENAS a tela de configurar MFA e para a execução aqui
        renderizar_mfa_obrigatorio(st.session_state.usuario_logado, USUARIOS)
        st.stop()  # O st.stop() impede que o resto do app carregue!
        
    # Se tem MFA, segue o fluxo normal abaixo:
    perfil = USUARIOS[st.session_state.usuario_logado]["perfil"]
    
    if "pagina" not in st.session_state:
        st.session_state.pagina = "Simulador"

    pagina = st.session_state.get("pagina", "Simulador")

    paginas_gestao = [
        "Dashboard", "DashboardVendas",
        "Construtoras", "Origens", "Usuários", "Regras", "RegrasEntrada",''
    ]
    paginas_admin = ["SuperAdmin", "Creditos"]

    acesso_negado = False
    if pagina in paginas_gestao and perfil not in ["gerente", "superadmin"]:
        acesso_negado = True
    if pagina in paginas_admin and perfil != "superadmin":
        acesso_negado = True

    if acesso_negado:
        st.error("🔒 Você não tem permissão para acessar esta página.")
        st.session_state.pagina = "Simulador"
        st.rerun()
    else:
        # (Logo no início do bloco 'else:' do roteamento, antes de 'if pagina == "Simulador"')
        if pagina == "Simulador" and not tem_perm("simulador"): st.error("Sem permissão."); st.stop()
        if pagina == "CRM" and not tem_perm("crm"): st.error("Sem permissão."); st.stop()
        if pagina == "Vendas" and not tem_perm("vendas"): st.error("Sem permissão."); st.stop()
        # (faça o mesmo para as outras páginas se quiser ser 100% rigoroso)

        if pagina == "Simulador":
            pagina_simulador(CONSTRUTORAS, USUARIOS)
        elif pagina == "Vendas":
            renderizar_gestao_vendas(usuario_logado=st.session_state.usuario_logado, USUARIOS=USUARIOS)
        elif pagina == "Seguranca":
            renderizar_conta_seguranca(st.session_state.usuario_logado, USUARIOS)
        elif pagina == "Histórico":
            renderizar_historico(usuario_logado=st.session_state.usuario_logado, USUARIOS=USUARIOS)
        elif pagina == "CRM":
            renderizar_kanban(st.session_state.usuario_logado, USUARIOS)
        elif pagina == "Configuracoes":
            renderizar_configuracoes()
        elif pagina == "ChatIA":
            pagina_bia_operacional(
            usuario_logado=st.session_state.usuario_logado,
            USUARIOS=USUARIOS,
        )
        elif pagina == "Dashboard":
            pagina_dashboard(CONSTRUTORAS, USUARIOS)
        elif pagina == "DashboardVendas":
            renderizar_dashboard_vendas()
        elif pagina == "SuperAdmin":
            pagina_superadmin(USUARIOS)
        elif pagina == "Usuários":
            pagina_gestao_usuarios(USUARIOS)
        elif pagina == "Construtoras":
            pagina_gestao_construtoras(CONSTRUTORAS)
        elif pagina == "Regras":
            renderizar_gestao_regras()
        elif pagina == "RegrasEntrada":
            renderizar_gestao_regras_entrada()
        elif pagina == "Origens":
            renderizar_gestao_origens()
        elif pagina == "Campanhas":
            renderizar_campanhas()
        elif pagina == "Creditos":
            pagina_creditos()
        elif pagina == "LimpezaTeste":
            renderizar_limpeza_teste(USUARIOS)
        elif pagina == "WarRoom":
            renderizar_war_room()
        elif pagina == "DiretorComercial":
            renderizar_diretor_comercial()
        elif pagina == "DiretorVendas":
                    renderizar_diretor_vendas()
        else:
            pagina_simulador(CONSTRUTORAS, USUARIOS)