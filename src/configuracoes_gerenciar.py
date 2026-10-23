import streamlit as st
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
        st.caption("Este número é usado no botão de WhatsApp da Landing Page. Use o formato: 5521999999999 (55 + DDD + Número).")
        valor_atual = obter_configuracao("whatsapp_imobiliaria", "5521999999999")
        novo_numero = st.text_input("Número do WhatsApp", value=valor_atual, max_chars=15)
        
        if st.button("💾 Salvar WhatsApp", type="primary"):
            import re
            num_limpo = re.sub(r'\D', '', novo_numero)
            if len(num_limpo) < 10:
                st.error("❌ Número inválido.")
            else:
                if salvar_configuracao("whatsapp_imobiliaria", num_limpo):
                    st.session_state["msg_sucesso_config"] = "✅ Número atualizado!"
                    st.rerun()

    with tab2:
        st.markdown("### 📺 Personalizar War Room (TV)")
        
        # Título
        titulo_atual = obter_configuracao("war_room_titulo", "WAR ROOM - IMOBILIÁRIA")
        novo_titulo = st.text_input("Título da Tela", value=titulo_atual)
        
        # Tema
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

        if st.button("💾 Salvar War Room", type="primary"):
            salvar_configuracao("war_room_titulo", novo_titulo)
            salvar_configuracao("war_room_tema", novo_tema)
            st.session_state["msg_sucesso_config"] = "✅ Configurações da War Room atualizadas!"
            st.rerun()