import streamlit as st
from src.crm.leads_storage import carregar_leads, criar_lead, atualizar_status_lead

# Mapeamento de status para exibição
STATUS_KANBAN = {
    "novo": {"nome": "🟢 Novo Lead", "cor": "#22c55e"},
    "atendimento": {"nome": "💬 Em Atendimento", "cor": "#3b82f6"},
    "simulacao": {"nome": "📊 Em Simulação", "cor": "#8b5cf6"},
    "aprovacao": {"nome": "⏳ Em Aprovação", "cor": "#f59e0b"},
    "proposta": {"nome": "📝 Proposta Enviada", "cor": "#0ea5e9"},
    "venda": {"nome": "🎉 Venda Ganha", "cor": "#10b981"},
    "perdido": {"nome": "❌ Perdido", "cor": "#ef4444"},
}

def renderizar_kanban(usuario_logado, USUARIOS):
    # === CSS MÁGICO PARA O KANBAN HORIZONTAL ===
    st.markdown("""
        <style>
        /* Força a área principal a permitir rolagem horizontal */
        .main .block-container {
            max-width: 100% !important;
            padding-right: 2rem !important;
        }
        /* Transforma a linha de colunas em um flex container que não quebra */
        div[data-testid="stHorizontalBlock"] {
            flex-wrap: nowrap !important; 
            overflow-x: auto !important; 
            gap: 1rem;
            padding-bottom: 20px;
        }
        /* Define uma largura mínima para cada coluna (estilo Trello) */
        div[data-testid="column"] {
            min-width: 340px !important; 
            width: 340px !important;
        }
        </style>
    """, unsafe_allow_html=True)

    st.title("🤝 CRM - Gestão de Leads")
    st.markdown("---")

    if "lead_para_simular" in st.session_state:
        del st.session_state["lead_para_simular"]

    nome_usuario = USUARIOS.get(usuario_logado, {}).get("nome", usuario_logado)
    perfil = USUARIOS.get(usuario_logado, {}).get("perfil", "corretor")
    corretor_filtro = nome_usuario if perfil == "corretor" else None

    # =========================================================
    # NOVO LEAD
    # =========================================================
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

    # =========================================================
    # KANBAN HORIZONTAL
    # =========================================================
    leads = carregar_leads(corretor=corretor_filtro)

    if not leads:
        st.info("📭 Nenhum lead no funil ainda. Cadastre um novo acima.")
        return

    por_status = {k: [] for k in STATUS_KANBAN.keys()}
    for lead in leads:
        st_atual = lead.get("status", "novo")
        if st_atual in por_status:
            por_status[st_atual].append(lead)

    chaves = list(STATUS_KANBAN.keys())
    
    # Renderiza todas as colunas numa única linha (o CSS vai cuidar da rolagem)
    cols = st.columns(len(chaves))
    for j, status in enumerate(chaves):
        with cols[j]:
            _renderizar_coluna(status, por_status[status])


def _renderizar_coluna(status, leads):
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
        with st.container():
            st.markdown(
                f"""
                <div style='background-color:white; border-left: 4px solid {info['cor']}; 
                padding:10px; border-radius:5px; margin-bottom:10px; 
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);'>
                    <h4 style='margin:0; font-size:16px;'>{lead['nome']}</h4>
                    <p style='margin:2px 0; font-size:12px; color:#666;'>📱 {lead.get('telefone', 'Sem tel')}</p>
                    <p style='margin:2px 0; font-size:12px; color:#666;'>💰 R$ {lead.get('renda', 0):,.2f}</p>
                    <p style='margin:2px 0; font-size:11px; color:#999;'>Origem: {lead.get('origem', '-')}</p>
                </div>
                """, 
                unsafe_allow_html=True
            )
            
            col_b1, col_b2 = st.columns(2)
            with col_b1:
                if status == "novo":
                    if st.button("💬 Atender", key=f"avancar_{lead['id']}", use_container_width=True):
                        atualizar_status_lead(lead['id'], "atendimento")
                        st.rerun()
                
                elif status == "atendimento":
                    if st.button("📊 Simular", key=f"simular_{lead['id']}", use_container_width=True):
                        atualizar_status_lead(lead['id'], "simulacao")
                        st.session_state["lead_para_simular"] = lead 
                        st.session_state.pagina = "Simulador" 
                        st.rerun()
                
                elif status == "simulacao":
                    if st.button("📤 Enviar", key=f"voltar_erp_{lead['id']}", use_container_width=True):
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