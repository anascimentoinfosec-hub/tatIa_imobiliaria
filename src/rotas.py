import streamlit as st

def renderizar_pagina_atual(USUARIOS, CONSTRUTORAS):
    # Pega o perfil do usuário logado
    usuario = st.session_state.usuario_logado
    perfil = USUARIOS[usuario]["perfil"]
    permissoes_usuario = USUARIOS[usuario].get("permissoes", {})
    
    def tem_perm(pagina):
        return permissoes_usuario.get(pagina, True)

    if "pagina" not in st.session_state:
        st.session_state.pagina = "Simulador"

    pagina = st.session_state.get("pagina", "Simulador")

    # Verificação de Segurança (Rotas Protegidas)
    paginas_gestao = ["Dashboard", "DashboardVendas", "Construtoras", "Regras", "RegrasEntrada", "Origens", "Usuários", "Campanhas", "Configuracoes", "WarRoom", "DriveSync"]
    paginas_admin = ["SuperAdmin", "Creditos", "LimpezaTeste"]
    
    acesso_negado = False
    if pagina in paginas_gestao and not any(tem_perm(p.lower()) for p in [pagina]):
        if not any(tem_perm(p) for p in ["dashboard", "dashboard_vendas", "construtoras", "regras_fin", "regras_ent", "origens", "usuarios", "campanhas", "configuracoes", "war_room"]):
            acesso_negado = True

    if pagina in paginas_admin and perfil != "superadmin":
        acesso_negado = True

    if acesso_negado:
        st.error("🔒 Você não tem permissão para acessar esta página.")
        st.session_state.pagina = "Simulador"
        st.rerun()

    else:
        # Renderiza a página correta (Importações feitas aqui dentro para evitar importação circular)
        if pagina == "Simulador":
            from src.simulador import pagina_simulador
            pagina_simulador(CONSTRUTORAS, USUARIOS)
        elif pagina == "CRM":
            from src.crm.kanban import renderizar_kanban
            renderizar_kanban(usuario, USUARIOS)
        elif pagina == "Vendas":
            from src.vendas_gerenciar import renderizar_gestao_vendas
            renderizar_gestao_vendas(usuario_logado=usuario, USUARIOS=USUARIOS)
        elif pagina == "Histórico":
            from src.simulacoes_historico import renderizar_historico
            renderizar_historico(usuario_logado=usuario, USUARIOS=USUARIOS)
        elif pagina == "ChatIA":
            from src.bia_operacional import pagina_bia_operacional
            pagina_bia_operacional(usuario_logado=usuario, USUARIOS=USUARIOS)
        elif pagina == "Dashboard":
            from src.dashboard import pagina_dashboard
            pagina_dashboard(CONSTRUTORAS, USUARIOS)
        elif pagina == "DashboardVendas":
            from src.vendas_dashboard import renderizar_dashboard_vendas
            renderizar_dashboard_vendas()
        elif pagina == "Construtoras":
            from src.construtoras import pagina_gestao_construtoras
            pagina_gestao_construtoras(CONSTRUTORAS)
        elif pagina == "Regras":
            from src.regras_gerenciar import renderizar_gestao_regras
            renderizar_gestao_regras()
        elif pagina == "RegrasEntrada":
            from src.regras_entrada_gerenciar import renderizar_gestao_regras_entrada
            renderizar_gestao_regras_entrada()
        elif pagina == "Origens":
            from src.origens_gerenciar import renderizar_gestao_origens
            renderizar_gestao_origens()
        elif pagina == "Usuários":
            from src.usuarios import pagina_gestao_usuarios
            pagina_gestao_usuarios(USUARIOS)
        elif pagina == "Campanhas":
            from src.crm.campanhas_ui import renderizar_campanhas
            renderizar_campanhas()
        elif pagina == "Configuracoes":
            from src.configuracoes_gerenciar import renderizar_configuracoes
            renderizar_configuracoes()
        elif pagina == "WarRoom":
            from src.war_room import renderizar_war_room
            renderizar_war_room()
        elif pagina == "DiretorComercial":
            from src.diretor_comercial import renderizar_diretor_comercial
            renderizar_diretor_comercial()
        elif pagina == "DiretorVendas":
            from src.diretor_vendas import renderizar_diretor_vendas
            renderizar_diretor_vendas()
        elif pagina == "DiretorFinanceiro":
            from src.diretor_financeiro import renderizar_diretor_financeiro
            renderizar_diretor_financeiro()
        elif pagina == "DiretorRH":
            from src.diretor_rh import renderizar_diretor_rh
            renderizar_diretor_rh()
        elif pagina == "SuperAdmin":
            from src.superadmin import pagina_superadmin
            pagina_superadmin(USUARIOS)
        elif pagina == "Creditos":
            from src.creditos import pagina_creditos
            pagina_creditos()
        elif pagina == "Seguranca":
            from src.conta_seguranca import renderizar_conta_seguranca
            renderizar_conta_seguranca(usuario, USUARIOS)
        elif pagina == "EspelhoVendas":
            from src.espelho_vendas import renderizar_espelho_vendas
            renderizar_espelho_vendas()
        elif pagina == "LimpezaTeste":
            from src.superadmin import renderizar_limpeza_teste
            renderizar_limpeza_teste(USUARIOS)
        elif pagina == "DriveSync":
            from src.drive_gerenciar import renderizar_drive_sync
            renderizar_drive_sync()
        else:
            from src.simulador import pagina_simulador
            pagina_simulador(CONSTRUTORAS, USUARIOS)