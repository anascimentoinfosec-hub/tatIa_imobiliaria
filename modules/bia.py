import streamlit as st
import pandas as pd
import openai

def pagina_chat():
    st.title("💬 BIA - IA Imobiliária")
    st.markdown("---")
    
    if "df_imoveis" not in st.session_state or st.session_state.df_imoveis is None:
        st.warning("⚠️ Nenhuma planilha disponível. Carregue uma planilha no Simulador primeiro.")
        return
    
    if "OPENAI_API_KEY" not in st.secrets:
        st.error("❌ Chave da OpenAI não configurada. Peça ao administrador para configurar.")
        return
    
    # Verifica saldo (opcional)
    try:
        from modules.creditos import CREDITO_TOTAL, obter_uso_api
        uso = obter_uso_api(st.secrets["OPENAI_API_KEY"])
        if uso is not None and (CREDITO_TOTAL - uso) <= 0:
            st.error("❌ Créditos esgotados. Adicione mais créditos na OpenAI.")
            return
    except:
        pass
    
    openai.api_key = st.secrets["OPENAI_API_KEY"]
    df = st.session_state.df_imoveis.copy()
    dados_resumidos = df.to_string(index=False)
    
    if "hist_chat" not in st.session_state:
        st.session_state.hist_chat = [
            {"role": "assistant", "content": "Olá! Sou a BIA, sua assistente imobiliária com inteligência avançada. Pergunte sobre os imóveis, perfil de clientes, análises comparativas e muito mais!"}
        ]
    
    for msg in st.session_state.hist_chat:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    
    pergunta = st.chat_input("Digite sua pergunta...")
    
    if pergunta:
        st.session_state.hist_chat.append({"role": "user", "content": pergunta})
        with st.chat_message("user"):
            st.markdown(pergunta)
        
        with st.chat_message("assistant"):
            with st.spinner("Pensando..."):
                resposta = processar_com_chatgpt(pergunta, dados_resumidos)
                st.markdown(resposta)
                st.session_state.hist_chat.append({"role": "assistant", "content": resposta})

def processar_com_chatgpt(pergunta, dados_imoveis):
    try:
        prompt = f"""
        Você é a BIA, uma assistente imobiliária especializada.
        Dados dos imóveis disponíveis:
        {dados_imoveis}
        
        Pergunta: "{pergunta}"
        
        Responda de forma clara, profissional, usando padrão brasileiro (R$ 1.234,56).
        """
        response = openai.ChatCompletion.create(
            model="gpt-40-mini",
            messages=[
                {"role": "system", "content": "Você é um assistente imobiliário especializado."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=800,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"❌ Erro ao processar: {str(e)}"