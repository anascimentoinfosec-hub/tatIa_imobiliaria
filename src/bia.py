import streamlit as st
import pandas as pd
from openai import OpenAI
from src.bia_tools import buscar_web

def pagina_bia():
    st.title("💬 BIA - IA Imobiliária")
    st.markdown("---")
    
    if "df_imoveis" not in st.session_state or st.session_state.df_imoveis is None:
        st.warning("⚠️ Nenhuma planilha disponível. Carregue uma planilha no Simulador primeiro.")
        return
    
    if "OPENAI_API_KEY" not in st.secrets:
        st.error("❌ Chave da OpenAI não configurada. Configure em Settings → Secrets do Streamlit.")
        return
    
    # Inicializa o cliente OpenAI (nova sintaxe)
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    
    df = st.session_state.df_imoveis.copy()
    dados_resumidos = df.to_string(index=False)
    
    if "hist_bia" not in st.session_state:
        st.session_state.hist_bia = [
            {"role": "assistant", "content": "Olá! Sou a BIA, sua assistente imobiliária com inteligência avançada. Pergunte sobre os imóveis, perfil de clientes, análises comparativas e muito mais!"}
        ]
    
    for msg in st.session_state.hist_bia:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    
    pergunta = st.chat_input("Digite sua pergunta...")
    
    if pergunta:
        st.session_state.hist_bia.append({"role": "user", "content": pergunta})
        with st.chat_message("user"):
            st.markdown(pergunta)
        
        with st.chat_message("assistant"):
            with st.spinner("Pensando..."):
                resposta = processar_com_chatgpt(client, pergunta, dados_resumidos)
                st.markdown(resposta)
                st.session_state.hist_bia.append({"role": "assistant", "content": resposta})

def processar_com_chatgpt(client, pergunta, dados_imoveis):
    """Processa a pergunta do usuário, usando busca na web se necessário."""
    try:
        # 1. Primeiro, decide se precisa de busca externa
        prompt_decisao = f"""
        Você é a BIA, uma assistente imobiliária.
        O usuário perguntou: "{pergunta}"
        
        Você tem acesso a uma ferramenta de busca na web para responder a perguntas que exigem informações externas (notícias, tendências, dados econômicos, preço médio de mercado, etc.).
        
        Com base na pergunta, você precisa de uma busca na web?
        Responda APENAS com "SIM" ou "NAO".
        """

        resposta_decisao = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt_decisao}],
            max_tokens=5,
            temperature=0
        ).choices[0].message.content.strip().upper()

        contexto_externo = ""
        if "SIM" in resposta_decisao:
            # 2. Se precisar, faz a busca na web
            contexto_externo = buscar_web(pergunta)
            contexto_externo = f"\n\nInformações da web (use se for relevante):\n{contexto_externo}"

        # 3. Monta o prompt final para o LLM
        prompt_final = f"""
        Você é a BIA, uma assistente imobiliária especializada e prestativa.
        
        Dados dos imóveis disponíveis no sistema:
        {dados_imoveis}
        {contexto_externo}
        
        Com base APENAS nas informações acima (sistema e web), responda à pergunta do usuário de forma clara, profissional e usando o padrão brasileiro (R$ 1.234,56).
        
        Pergunta: "{pergunta}"
        """

        # 4. Gera a resposta final
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Você é um assistente imobiliário especializado."},
                {"role": "user", "content": prompt_final}
            ],
            max_tokens=800,
            temperature=0.7
        )
        return response.choices[0].message.content

    except Exception as e:
        return f"❌ Erro na IA: {str(e)}"