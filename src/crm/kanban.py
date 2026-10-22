import streamlit as st
from src.crm.leads_storage import carregar_leads, criar_lead, atualizar_status_lead
from src.crm.campanhas_storage import carregar_campanhas

STATUS_KANBAN = {
    "novo": {"nome": "🟢 Novo Lead", "cor": "#22c55e"},
    "agendado": {"nome": "📅 Agendado", "cor": "#6366f1"},
    "atendimento": {"nome": "💬 Em Atendimento", "cor": "#3b82f6"},
    "aprovacao": {"nome": "⏳ Em Aprovação", "cor": "#f59e0b"},
    "proposta": {"nome": "📝 Proposta Enviada", "cor": "#0ea5e9"},
    "venda": {"nome": "🎉 Venda Ganha", "cor": "#10b981"},
    "perdido": {"nome": "❌ Perdido", "cor": "#ef4444"},
}

def renderizar_kanban(usuario_logado, USUARIOS):
    st.markdown("""
        <style>
        .main .block-container { max-width: 100% !important; padding-right: 2rem !important; }
        div[data-testid="stHorizontalBlock"] { flex-wrap: nowrap !important; overflow-x: auto !important; gap: 1rem; padding-bottom: 20px; }
        div[data-testid="column"] { min-width: 340px !important; width: 340px !important; }
        div[data-testid="stButton"] > button { white-space: nowrap !important; padding: 4px 8px !important; font-size: 13px !important; }
        </style>
    """, unsafe_allow_html=True)

    st.title("🤝 CRM - Gestão de Leads")
    st.markdown("---")

    if "lead_para_simular" in st.session_state:
        del st.session_state["lead_para_simular"]

    nome_usuario = USUARIOS.get(usuario_logado, {}).get("nome", usuario_logado)
    perfil = USUARIOS.get(usuario_logado, {}).get("perfil", "corretor")
    corretor_filtro = nome_usuario if perfil == "corretor" else None

    with st.expander("➕ Cadastrar Novo Lead", expanded=False):
        with st.form("form_novo_lead", clear_on_submit=True):
            col1, col2, col3 = st.columns(3)
            with col1:
                nome = st.text_input("Nome do Lead")
                telefone = st.text_input("WhatsApp (com DDD)")
            with col2:
                renda = st.number_input("Renda Estimada (R$)", min_value=0.0, step=500.0)
                origem = st.selectbox("Origem", ["Instagram", "Facebook", "Indicação", "Captação Própria", "Outro"])
            with col3:
                st.write("")
                st.write("")
                st.write("")
                if st.form_submit_button("✅ Salvar Lead", use_container_width=True, type="primary"):
                    if not nome:
                        st.warning("⚠️ O nome é obrigatório.")
                    else:
                        sucesso, _ = criar_lead(
                            nome=nome, telefone=telefone, email="", renda=renda,
                            origem=origem, corretor=nome_usuario if perfil == "corretor" else "Não atribuído"
                        )
                        if sucesso:
                            st.success("Lead adicionado ao funil!")
                            st.rerun()

    leads = carregar_leads(corretor=corretor_filtro)

    if not leads:
        st.info("📭 Nenhum lead no funil ainda.")
        return

    # === AQUI ESTÁ A TRADUÇÃO DOS IDs ===
    campanhas = carregar_campanhas()
    mapa_campanhas = {c['id']: c['nome'] for c in campanhas}

    por_status = {k: [] for k in STATUS_KANBAN.keys()}
    for lead in leads:
        st_atual = lead.get("status", "novo")
        if st_atual == "simulacao": st_atual = "atendimento"
        
        if st_atual in por_status:
            por_status[st_atual].append(lead)

    chaves = list(STATUS_KANBAN.keys())
    cols = st.columns(len(chaves))
    for j, status in enumerate(chaves):
        with cols[j]:
            _renderizar_coluna(status, por_status[status], mapa_campanhas)


def _renderizar_coluna(status, leads, mapa_campanhas):
    info = STATUS_KANBAN[status]
    
    st.markdown(
        f"<div style='background-color:{info['cor']}; color:white; padding:8px; "
        f"border-radius:8px; text-align:center; font-weight:bold; margin-bottom:10px; font-size:14px;'>"
        f"{info['nome']} ({len(leads)})</div>", 
        unsafe_allow_html=True
    )

    if not leads:
        st.caption("Vazio")
        return

    for lead in leads:
        # Traduz a origem
        origem_id = lead.get('origem', '-')
        origem_exibicao = mapa_campanhas.get(origem_id, origem_id)
        
        # Cria o link do WhatsApp para o corretor
        telefone_lead = lead.get('telefone', '')
        link_corretor = f"https://wa.me/{telefone_lead}" if telefone_lead else "#"

        with st.container():
            st.markdown(
                f"""
                <div style='background-color:white; border-left: 4px solid {info['cor']}; 
                padding:10px; border-radius:5px; margin-bottom:10px; 
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);'>
                    <h4 style='margin:0; font-size:16px;'>{lead['nome']}</h4>
                    <p style='margin:2px 0; font-size:12px;'>
                        <a href="{link_corretor}" target="_blank" style="text-decoration:none; color:#25D366; font-weight:bold;">
                            📱 {lead.get('telefone', 'Sem tel')}
                        </a>
                    </p>
                    <p style='margin:2px 0; font-size:12px; color:#666;'>💰 R$ {lead.get('renda', 0):,.2f}</p>
                    <p style='margin:2px 0; font-size:11px; color:#999;'>Origem: {origem_exibicao}</p>
                </div>
                """, 
                unsafe_allow_html=True
            )
            
            col_b1, col_b2 = st.columns(2)
            with col_b1:
                if status == "novo":
                    if st.button("📅 Agendar", key=f"avancar_{lead['id']}", use_container_width=True):
                        atualizar_status_lead(lead['id'], "agendado")
                        st.rerun()
                
                elif status == "agendado":
                    if st.button("💬 Atender", key=f"atender_{lead['id']}", use_container_width=True):
                        atualizar_status_lead(lead['id'], "atendimento")
                        st.rerun()

                elif status == "atendimento":
                    if st.button("📊 Simular", key=f"simular_{lead['id']}", use_container_width=True):
                        st.session_state["lead_para_simular"] = lead 
                        st.session_state.pagina = "Simulador" 
                        st.rerun()
                
                elif status == "aprovacao":
                    st.caption("⏳ Aguardando")
                
                elif status == "proposta":
                    if st.button("🎉 Ganho", key=f"ganho_{lead['id']}", use_container_width=True):
                        atualizar_status_lead(lead['id'], "venda")
                        st.rerun()
                
                elif status == "venda":
                    st.caption("🏆 Finalizado")

            with col_b2:
                if status not in ["venda", "perdido"]:
                    if st.button("🗑️ Perder", key=f"perder_{lead['id']}", use_container_width=True):
                        atualizar_status_lead(lead['id'], "perdido")
                        st.rerun()