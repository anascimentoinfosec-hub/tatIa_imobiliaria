import streamlit as st
import time
from streamlit_cookies_controller import CookieController
from src.simulacoes_storage import contar_propostas_pendentes
from src.notificacao_whatsapp import enviar_alerta_novo_lead
from src.documentos_storage import criar_token_consentimento
from src.notificacao_whatsapp import enviar_otp_lgpd
from src.configuracoes_storage import obter_configuracao
from src.crm.roleta import bater_ponto, sair_do_ponto, puxar_lead_orfao, verificar_se_esta_na_roleta, zerar_roleta

def renderizar_sidebar(USUARIOS, CONSTRUTORAS):
    with st.sidebar:
        st.markdown("### 🏔️ **Everest ERP**")
        st.markdown("---")

        if "usuario_logado" not in st.session_state:
            st.session_state.usuario_logado = None

        if st.session_state.usuario_logado is None:
            from src.auth import exibir_login_sidebar
            exibir_login_sidebar(USUARIOS)
            return 

        usuario = st.session_state.usuario_logado
        perfil = USUARIOS[usuario]["perfil"]
        permissoes_usuario = USUARIOS[usuario].get("permissoes", {})
        
        def tem_perm(pagina):
            return permissoes_usuario.get(pagina, True)

        # --- 1. PERFIL DO USUÁRIO ---
        nome = USUARIOS[usuario]["nome"]
        badge_class = "badge-superadmin" if perfil == "superadmin" else "badge-gerente" if perfil == "gerente" else "badge-corretor"
        st.markdown(f"👤 **{nome}**")
        st.markdown(f'<span class="badge-perfil {badge_class}">{perfil.upper()}</span>', unsafe_allow_html=True)
        st.markdown("---")

        # --- 2. SELETOR DE WORKSPACE (O Topônimo) ---
        modulos_disponiveis = []
        if tem_perm("simulador") or tem_perm("simulacoes"):
            modulos_disponiveis.append("📊 Simulador")
        if tem_perm("crm") or tem_perm("campanhas"):
            modulos_disponiveis.append("🤝 CRM")
        if any(tem_perm(p) for p in ["dashboard", "usuarios", "configuracoes", "construtoras", "diretor_comercial"]):
            modulos_disponiveis.append("⚙️ ERP (Gestão)")

        if modulos_disponiveis:
            # Define o padrão se não tiver nada salvo
            if "modulo_atual" not in st.session_state or st.session_state.modulo_atual not in modulos_disponiveis:
                st.session_state.modulo_atual = modulos_disponiveis[0]
                
            modulo_atual = st.radio(
                "Selecione o Módulo:", 
                modulos_disponiveis, 
                index=modulos_disponiveis.index(st.session_state.modulo_atual),
                key="seletor_modulo",
                horizontal=False
            )
            st.session_state.modulo_atual = modulo_atual
            st.markdown("---")

        # --- 3. CHECK-IN / MEU PONTO (Sempre visível para corretor) ---
        if perfil == "corretor":
            st.markdown("#### 📍 Meu Ponto")
            esta_na_roleta = verificar_se_esta_na_roleta(usuario)
            
            if esta_na_roleta:
                st.success("🟢 Você está na roleta.")
            else:
                st.error("🔴 Fora da roleta.")
            
            col_pt1, col_pt2 = st.columns(2)
            with col_pt1:
                if st.button("🏢 Stand", key="btn_stand", use_container_width=True):
                    if bater_ponto(usuario, "stand"): st.rerun()
            with col_pt2:
                if st.button("🏠 Home", key="btn_home", use_container_width=True):
                    if bater_ponto(usuario, "home"): st.rerun()
            
            if st.button("🚪 Sair da Roleta", key="btn_sair_roleta", use_container_width=True, disabled=not esta_na_roleta):
                if sair_do_ponto(usuario): st.rerun() 
            
            if esta_na_roleta:
                if st.button("🎯 Puxar Lead Órfão", key="btn_puxar_lead", use_container_width=True):
                    if puxar_lead_orfao(usuario):
                        st.success("Lead puxado!")
                        st.rerun()
                    else:
                        st.warning("Nenhum lead órfão.")
            st.markdown("---")

        # --- 4. MENUS DINÂMICOS BASEADOS NO WORKSPACE ---
        
        # MÓDULO SIMULADOR
        if st.session_state.get("modulo_atual") == "📊 Simulador":
            st.markdown("### 📊 Simulação")
            if tem_perm("simulador") and st.button("📊 Simulador", key="btn_menu_sim", use_container_width=True):
                st.session_state.pagina = "Simulador"; st.rerun()
            if tem_perm("simulacoes") and st.button("📚 Histórico Simulações", key="btn_menu_hist", use_container_width=True):
                st.session_state.pagina = "Histórico"; st.rerun()
            if tem_perm("crm") and st.button("🏢 Espelho de Vendas", key="btn_menu_espelho", use_container_width=True):
                st.session_state.pagina = "EspelhoVendas"; st.rerun()
            if tem_perm("chat_ia") and st.button("💬 IA Imobiliária", key="btn_menu_ia", use_container_width=True):
                st.session_state.pagina = "ChatIA"; st.rerun()

        # MÓDULO CRM
        elif st.session_state.get("modulo_atual") == "🤝 CRM":
            st.markdown("### 🤝 CRM e Vendas")
            if tem_perm("crm") and st.button("🤝 Kanban de Leads", key="btn_menu_crm", use_container_width=True):
                st.session_state.pagina = "CRM"; st.rerun()
            if tem_perm("campanhas") and st.button("📣 Campanhas", key="btn_menu_campanhas", use_container_width=True):
                st.session_state.pagina = "Campanhas"; st.rerun()
            if tem_perm("vendas") and st.button("💼 Vendas", key="btn_menu_vendas", use_container_width=True):
                st.session_state.pagina = "Vendas"; st.rerun()

        # MÓDULO ERP / GESTÃO
        elif st.session_state.get("modulo_atual") == "⚙️ ERP (Gestão)":
            st.markdown("### ⚙️ Gestão")
            
            qtd_pendentes = contar_propostas_pendentes()
            if qtd_pendentes > 0: st.warning(f"🔔 **{qtd_pendentes}** pendente(s)!")

            if tem_perm("dashboard") and st.button("📊 Dashboard", key="btn_menu_dash", use_container_width=True):
                st.session_state.pagina = "Dashboard"; st.rerun()
            if tem_perm("dashboard_vendas") and st.button("📈 Dashboard Vendas", key="btn_menu_dash_vendas", use_container_width=True):
                st.session_state.pagina = "DashboardVendas"; st.rerun()
            if tem_perm("construtoras") and st.button("🏗️ Construtoras", key="btn_menu_construtoras", use_container_width=True):
                st.session_state.pagina = "Construtoras"; st.rerun()
            if tem_perm("configuracoes") and st.button("📂 Sincronização Google Drive", key="btn_menu_drive", use_container_width=True):
                st.session_state.pagina = "DriveSync"; st.rerun()
            if tem_perm("usuarios") and st.button("👥 Usuários", key="btn_menu_usuarios", use_container_width=True):
                st.session_state.pagina = "Usuários"; st.rerun()
            if tem_perm("configuracoes") and st.button("⚙️ Configurações", key="btn_menu_config", use_container_width=True):
                st.session_state.pagina = "Configuracoes"; st.rerun()
            if tem_perm("war_room") and st.button("📺 War Room (TV)", key="btn_war_room", use_container_width=True):
                st.session_state.pagina = "WarRoom"; st.rerun()

            # Diretoria
            if perfil in ["superadmin", "diretor"]:
                st.markdown("---")
                st.markdown("#### 👔 Diretoria")
                if tem_perm("diretor_comercial") and st.button("💼 Diretor Comercial", key="btn_dir_comercial", use_container_width=True):
                    st.session_state.pagina = "DiretorComercial"; st.rerun()
                if tem_perm("diretor_vendas") and st.button("📈 Diretor de Vendas", key="btn_dir_vendas", use_container_width=True):
                    st.session_state.pagina = "DiretorVendas"; st.rerun()
                if tem_perm("diretor_financeiro") and st.button("💰 Diretor Financeiro", key="btn_dir_financeiro", use_container_width=True):
                    st.session_state.pagina = "DiretorFinanceiro"; st.rerun()
                if tem_perm("diretor_rh") and st.button("👥 Diretor de RH", key="btn_dir_rh", use_container_width=True):
                    st.session_state.pagina = "DiretorRH"; st.rerun()

            # Admin
            if perfil == "superadmin":
                st.markdown("---")
                st.markdown("#### 👑 Admin")
                if st.button("👥 Gerenciar Gerentes", key="btn_admin_gerentes", use_container_width=True):
                    st.session_state.pagina = "SuperAdmin"; st.rerun()
                if st.button("💰 Créditos OpenAI", key="btn_admin_creditos", use_container_width=True):
                    st.session_state.pagina = "Creditos"; st.rerun()
                if st.button("🔄 Resetar Base", key="btn_admin_reset", use_container_width=True):
                    st.session_state.pagina = "LimpezaTeste"; st.rerun()

        # --- BOTÃO DA BIA ---
        st.markdown("---")
        st.markdown("### 🤖 Assistente Virtual")
        if st.button("💬 Falar com a BIA", key="btn_abrir_bia", use_container_width=True, type="primary"):
            st.session_state["mostrar_bia_chat"] = True
            st.rerun()

        # --- BOTÃO SAIR ---
        st.markdown("---")
        if st.button("🚪 Sair do Sistema", key="btn_sair_sistema", use_container_width=True):
            controller = CookieController()
            try:
                controller.remove("tatia_mfa_token")
                controller.remove("tatia_mfa_user")
            except Exception:
                pass
            st.session_state.clear()
            time.sleep(1)
            st.rerun()