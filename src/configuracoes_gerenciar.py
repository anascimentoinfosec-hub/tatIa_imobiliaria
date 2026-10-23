import streamlit as st
from src.configuracoes_storage import obter_configuracao, salvar_configuracao

def renderizar_configuracoes():
    st.title("⚙️ Configurações Gerais")
    st.markdown("---")

    if "msg_sucesso_config" in st.session_state:
        st.success(st.session_state["msg_sucesso_config"])
        del st.session_state["msg_sucesso_config"]

    st.markdown("### 📱 WhatsApp da Imobiliária")
    st.caption("Este número é usado no botão de WhatsApp da Landing Page (quando o cliente fala com a BIA). Use o formato: 5521999999999 (55 + DDD + Número).")

    valor_atual = obter_configuracao("whatsapp_imobiliaria", "5521999999999")
    
    novo_numero = st.text_input("Número do WhatsApp", value=valor_atual, max_chars=15)

    if st.button("💾 Salvar Configurações", type="primary", use_container_width=True):
        # Limpa tudo que não for número
        import re
        num_limpo = re.sub(r'\D', '', novo_numero)
        
        if len(num_limpo) < 10:
            st.error("❌ Número inválido. Digite o DDD e o número.")
        else:
            if salvar_configuracao("whatsapp_imobiliaria", num_limpo):
                st.session_state["msg_sucesso_config"] = "✅ Número atualizado com sucesso!"
                st.rerun()