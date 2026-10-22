import streamlit as st
from datetime import date
from src.crm.campanhas_storage import criar_campanha, carregar_campanhas
from src.crm.leads_storage import carregar_leads

def renderizar_campanhas():
    st.title("📣 Gestão de Campanhas de Marketing")
    
    # === MÁGICA DA MENSAGEM DE SUCESSO (Sobrevive ao F5) ===
    if "msg_sucesso_campanha" in st.session_state:
        st.success(st.session_state["msg_sucesso_campanha"])
        del st.session_state["msg_sucesso_campanha"]
        
    st.markdown("---")

    tab1, tab2 = st.tabs(["📋 Listar e Copiar Links", "➕ Nova Campanha"])

    with tab2:
        st.markdown("### Criar Nova Campanha")
        st.caption("Configure a campanha para gerar o link de tráfego pago (Instagram/Facebook).")
        
        with st.form("form_nova_campanha"):
            col1, col2 = st.columns(2)
            with col1:
                nome = st.text_input("Nome da Campanha (ex: Insta Outubro)")
                investimento = st.number_input("Investimento Previsto (R$)", min_value=0.0, step=100.0)
            with col2:
                data_fim = st.date_input("Data de Término", value=date.today())
            
            if st.form_submit_button("🚀 Criar e Gerar Link", use_container_width=True, type="primary"):
                if not nome:
                    st.warning("⚠️ Digite o nome da campanha.")
                else:
                    sucesso, campanha_id = criar_campanha(nome, investimento, data_fim)
                    if sucesso:
                        # Guarda a mensagem para a tela recarregar e mostrar ela linda!
                        st.session_state["msg_sucesso_campanha"] = f"✅ Campanha '{nome}' criada com sucesso! O link já está disponível na aba 'Listar'."
                        st.rerun()

    with tab1:
        campanhas = carregar_campanhas()
        if not campanhas:
            st.info("Nenhuma campanha cadastrada ainda.")
            return

        # Verifica quantos leads cada campanha trouxe
        leads = carregar_leads()
        contagem_leads = {}
        for l in leads:
            c_id = l.get("campanha_id")
            if c_id:
                contagem_leads[c_id] = contagem_leads.get(c_id, 0) + 1

        for camp in campanhas:
            with st.container():
                st.markdown(
                    f"""
                    <div style='background-color:#f8fafc; border-left: 4px solid #0ea5e9; padding:15px; border-radius:8px; margin-bottom:15px;'>
                        <h3 style='margin:0;'>📣 {camp['nome']}</h3>
                        <p style='margin:5px 0; color:#666;'>Investimento: R$ {camp['investimento']:,.2f} | Fim: {camp['data_fim']}</p>
                        <p style='margin:5px 0; color:#0ea5e9; font-weight:bold;'>🎯 Leads gerados: {contagem_leads.get(camp['id'], 0)}</p>
                    </div>
                    """, unsafe_allow_html=True
                )
                
                # GERA O LINK DINÂMICO
                # Tenta pegar a URL base dos secrets. Se não achar, usa localhost.
                try:
                    link_base = st.secrets.get("APP_BASE_URL", "http://localhost:8080")
                except:
                    link_base = "http://localhost:8080"
                    
                link_completo = f"{link_base}/?lead=true&campanha={camp['id']}"
                
                st.caption("Copie o link abaixo e cole no seu anúncio (Meta Ads, Google, etc):")
                st.code(link_completo, language="text")
                
                st.markdown("---")