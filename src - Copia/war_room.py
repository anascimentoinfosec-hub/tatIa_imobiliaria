import streamlit as st
import time
from src.crm.leads_storage import carregar_leads
from src.vendas_storage import calcular_metricas
from src.configuracoes_storage import obter_configuracao

def renderizar_war_room():
    # Puxa as configurações do banco
    titulo = obter_configuracao("war_room_titulo", "WAR ROOM - IMOBILIÁRIA")
    tema = obter_configuracao("war_room_tema", "padrao")
    logo = obter_configuracao("war_room_logo", "")

    # Define as cores baseadas no tema
    cores = {
        "padrao": {"bg": "#0f172a", "card": "#1e293b", "texto": "#e2e8f0", "destaque": "#38bdf8"},
        "natal": {"bg": "#064e3b", "card": "#065f46", "texto": "#fef3c7", "destaque": "#ef4444"},
        "halloween": {"bg": "#1c1917", "card": "#292524", "texto": "#f97316", "destaque": "#facc15"},
        "aniversario": {"bg": "#312e81", "card": "#3730a3", "texto": "#fdf4ff", "destaque": "#ec4899"}
    }
    cor = cores.get(tema, cores["padrao"])

    # CSS Mágico
    st.markdown(f"""
        <style>
        [data-testid="collapsedControl"] {{display: none !important;}}
        section[data-testid="stSidebar"] {{display: none !important;}}
        header[data-testid="stHeader"] {{display: none !important;}}
        footer {{display: none !important;}}
        .stButton {{display: none !important;}}
        
        .block-container {{
            padding-top: 0.5rem !important;
            padding-bottom: 0rem !important;
            max-width: 95% !important;
        }}
        
        .stApp {{background-color: {cor['bg']} !important;}}
        h1, h2, h3, p, span, div {{color: {cor['texto']} !important;}}
        </style>
    """, unsafe_allow_html=True)

    # === EXIBE O LOGO (Se existir) ===
    if logo:
        st.markdown(f"<div style='text-align: center;'><img src='{logo}' style='max-height: 80px; margin-bottom: 10px;'></div>", unsafe_allow_html=True)

    # Título
    st.markdown(f"<h1 style='text-align: center; color: {cor['destaque']}; margin-top: 0; margin-bottom: 0;'>{titulo}</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align: center; font-size: 12px; margin-top: 5px;'>Atualizado em: {time.strftime('%d/%m/%Y %H:%M:%S')}</p>", unsafe_allow_html=True)
    st.markdown("---")

    # === MÉTRICAS ===
    metricas = calcular_metricas()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"<div style='text-align:center; background-color:{cor['card']}; padding:20px; border-radius:10px;'><h2 style='color:#22c55e; margin:0;'>R$ {metricas['vgv_total']:,.2f}</h2><p>VGV Total</p></div>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<div style='text-align:center; background-color:{cor['card']}; padding:20px; border-radius:10px;'><h2 style='color:{cor['destaque']}; margin:0;'>{metricas['total_vendas']}</h2><p>Vendas Fechadas</p></div>", unsafe_allow_html=True)
    with col3:
        st.markdown(f"<div style='text-align:center; background-color:{cor['card']}; padding:20px; border-radius:10px;'><h2 style='color:#f59e0b; margin:0;'>R$ {metricas['vgv_medio']:,.2f}</h2><p>Ticket Médio</p></div>", unsafe_allow_html=True)
    with col4:
        leads = carregar_leads()
        st.markdown(f"<div style='text-align:center; background-color:{cor['card']}; padding:20px; border-radius:10px;'><h2 style='color:#ef4444; margin:0;'>{len(leads)}</h2><p>Leads no Funil</p></div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # === KANBAN ===
    st.markdown(f"<h2 style='text-align: center; color: {cor['destaque']};'>🎯 Funil de Vendas</h2>", unsafe_allow_html=True)
    
    status_colunas = {
        "novo": "Novo Lead", "agendado": "Agendado", "atendimento": "Em Atendimento",
        "aprovacao": "Em Aprovação", "proposta": "Proposta", "venda": "Venda Ganha"
    }
    
    por_status = {k: [] for k in status_colunas.keys()}
    for l in leads:
        st_atual = l.get("status", "novo")
        if st_atual in por_status:
            por_status[st_atual].append(l)

    cols = st.columns(len(status_colunas))
    for i, (status_key, status_nome) in enumerate(status_colunas.items()):
        with cols[i]:
            st.markdown(f"<div style='background-color:{cor['card']}; padding:10px; border-radius:5px; text-align:center; font-weight:bold; border-top: 4px solid {cor['destaque']};'>{status_nome} ({len(por_status[status_key])})</div>", unsafe_allow_html=True)
            
            for lead in por_status[status_key][:5]:
                st.markdown(f"""
                <div style='background-color:{cor['bg']}; padding:10px; border-radius:5px; margin-top:8px; font-size:12px; border: 1px solid {cor['card']};'>
                    <b>{lead['nome']}</b><br>
                    R$ {lead.get('renda', 0):,.0f}<br>
                    <span style='color:#94a3b8;'>{lead.get('origem', '')}</span>
                </div>
                """, unsafe_allow_html=True)
            if len(por_status[status_key]) > 5:
                st.caption(f"+ {len(por_status[status_key]) - 5} outros")

    time.sleep(60)
    st.rerun()