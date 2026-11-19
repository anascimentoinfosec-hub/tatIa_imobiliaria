import streamlit as st
import re
from src.configuracoes_storage import obter_configuracao, salvar_configuracao

def renderizar_configuracoes():
    st.title("⚙️ Configurações Gerais")
    st.markdown("---")

    if "msg_sucesso_config" in st.session_state:
        st.success(st.session_state["msg_sucesso_config"])
        del st.session_state["msg_sucesso_config"]

    tab1, tab2 = st.tabs(["📱 WhatsApp", "📺 War Room (TV)"])

    with tab1:
        st.markdown("### 📱 WhatsApp da Imobiliária")
        st.caption("Este número é usado no botão de WhatsApp da Landing Page (quando o cliente fala com a BIA). Use o formato: 5521999999999 (55 + DDD + Número).")
        valor_atual = obter_configuracao("whatsapp_imobiliaria", "5521999999999")
        novo_numero = st.text_input("Número do WhatsApp", value=valor_atual, max_chars=15, key="config_wpp_imob")
        
        if st.button("💾 Salvar WhatsApp", type="primary"):
            num_limpo = re.sub(r'\D', '', novo_numero)
            if len(num_limpo) < 10:
                st.error("❌ Número inválido.")
            else:
                if salvar_configuracao("whatsapp_imobiliaria", num_limpo):
                    st.session_state["msg_sucesso_config"] = "✅ Número atualizado!"
                    st.rerun()

        st.markdown("---")
        st.markdown("### 📲 Alerta de Novos Leads (Gerente)")
        st.caption("Número que receberá o alerta quando a BIA captar um novo lead.")
        
        gerente_zap = obter_configuracao("whatsapp_gerente", "")
        novo_gerente_zap = st.text_input("WhatsApp do Gerente", value=gerente_zap, max_chars=15, key="config_wpp_gerente")
        
        if st.button("💾 Salvar WhatsApp do Gerente", type="primary", key="btn_salvar_wpp_gerente"):
            num_limpo = re.sub(r'\D', '', novo_gerente_zap)
            if len(num_limpo) < 10:
                st.error("❌ Número inválido.")
            else:
                if salvar_configuracao("whatsapp_gerente", num_limpo):
                    st.session_state["msg_sucesso_config"] = "✅ Número do gerente atualizado!"
                    st.rerun()

        # NOVO: WhatsApp de Testes (Admin)
        st.markdown("---")
        st.markdown("### 🧪 WhatsApp para Testes (Admin)")
        st.caption("Número que receberá mensagens de teste do sistema (OTP, simulações, etc).")
        
        whatsapp_teste = obter_configuracao("whatsapp_teste", "")
        novo_whatsapp_teste = st.text_input("WhatsApp de Teste", value=whatsapp_teste, max_chars=15, key="config_wpp_teste")
        
        if st.button("💾 Salvar WhatsApp de Teste", type="primary", key="btn_salvar_wpp_teste"):
            num_limpo = re.sub(r'\D', '', novo_whatsapp_teste)
            if len(num_limpo) < 10:
                st.error("❌ Número inválido.")
            else:
                if salvar_configuracao("whatsapp_teste", num_limpo):
                    st.session_state["msg_sucesso_config"] = "✅ Número de teste atualizado!"
                    st.rerun()

    with tab2:
        st.markdown("### 📺 Personalizar War Room (TV)")
        
        titulo_atual = obter_configuracao("war_room_titulo", "WAR ROOM - IMOBILIÁRIA")
        novo_titulo = st.text_input("Título da Tela", value=titulo_atual)
        
        st.markdown("**Tema Visual:**")
        temas = {
            "padrao": "Padrão (Azul Escuro)",
            "natal": "Natal (Verde e Vermelho)",
            "halloween": "Halloween (Laranja e Preto)",
            "aniversario": "Aniversário (Festa/Colorido)"
        }
        tema_atual = obter_configuracao("war_room_tema", "padrao")
        opcoes_temas = list(temas.keys())
        idx_tema = opcoes_temas.index(tema_atual) if tema_atual in opcoes_temas else 0
        
        novo_tema = st.selectbox("Selecione o tema", opcoes_temas, index=idx_tema, format_func=lambda x: temas[x])

        logo_atual = obter_configuracao("war_room_logo", "")
        
        if logo_atual:
            st.image(logo_atual, width=150)
            if st.button("🗑️ Remover Logo"):
                salvar_configuracao("war_room_logo", "")
                st.session_state["msg_sucesso_config"] = "✅ Logo removido!"
                st.rerun()
                
        uploaded_logo = st.file_uploader("Enviar novo Logo (PNG ou JPG)", type=["png", "jpg", "jpeg"])
        if uploaded_logo:
            if st.button("Salvar Novo Logo"):
                import base64
                bytes_data = uploaded_logo.getvalue()
                b64_str = base64.b64encode(bytes_data).decode('utf-8')
                data_uri = f"data:{uploaded_logo.type};base64,{b64_str}"
                salvar_configuracao("war_room_logo", data_uri)
                st.session_state["msg_sucesso_config"] = "✅ Logo atualizado com sucesso!"
                st.rerun()

        if st.button("💾 Salvar Textos e Tema", type="primary"):
            salvar_configuracao("war_room_titulo", novo_titulo)
            salvar_configuracao("war_room_tema", novo_tema)
            st.session_state["msg_sucesso_config"] = "✅ Configurações da War Room atualizadas!"
            st.rerun()