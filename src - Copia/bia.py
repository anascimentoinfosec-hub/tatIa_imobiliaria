import streamlit as st
from openai import OpenAI
from src.bia_tools import buscar_web

# Quantas mensagens anteriores enviar para o GPT (economiza tokens)
MAX_HISTORICO = 10


def pagina_bia():
    st.title("💬 BIA - IA Imobiliária")
    st.markdown("---")

    if "df_imoveis" not in st.session_state or st.session_state.df_imoveis is None:
        st.warning("⚠️ Nenhuma planilha disponível. Carregue uma planilha no Simulador primeiro.")
        return

    if "OPENAI_API_KEY" not in st.secrets:
        st.error("❌ Chave da OpenAI não configurada.")
        return

    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    df = st.session_state.df_imoveis.copy()
    dados_resumidos = df.to_string(index=False)

    # Inicializa histórico
    if "hist_bia" not in st.session_state:
        st.session_state.hist_bia = [
            {"role": "assistant", "content": "Olá! Sou a BIA, sua assistente imobiliária. Pergunte sobre os imóveis, perfil de clientes, análises comparativas e muito mais!"}
        ]

    # Botão para limpar conversa
    col_a, col_b = st.columns([4, 1])
    with col_b:
        if st.button("🗑️ Limpar conversa", use_container_width=True):
            st.session_state.hist_bia = [
                {"role": "assistant", "content": "Conversa reiniciada. Como posso ajudar?"}
            ]
            st.rerun()

    # Renderiza mensagens
    for msg in st.session_state.hist_bia:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Input do usuário
    pergunta = st.chat_input("Digite sua pergunta...")

    if pergunta:
        st.session_state.hist_bia.append({"role": "user", "content": pergunta})
        with st.chat_message("user"):
            st.markdown(pergunta)

        with st.chat_message("assistant"):
            with st.spinner("Pensando..."):
                resposta = processar_com_chatgpt(client, st.session_state.hist_bia, dados_resumidos)
                st.markdown(resposta)
                st.session_state.hist_bia.append({"role": "assistant", "content": resposta})


def processar_com_chatgpt(client, historico, dados_imoveis):
    """Processa a pergunta com memória de contexto."""
    try:
        # Pega a última pergunta do usuário
        ultima_pergunta = ""
        for msg in reversed(historico):
            if msg["role"] == "user":
                ultima_pergunta = msg["content"]
                break

        # Decide se precisa buscar na web
        contexto_externo = ""
        if _precisa_busca_web(client, ultima_pergunta):
            resultado_busca = buscar_web(ultima_pergunta)
            if resultado_busca and "❌" not in resultado_busca:
                contexto_externo = f"\n\nInformações da web (use se for relevante):\n{resultado_busca}"

        # Monta system prompt
        system_prompt = f"""Você é a BIA, uma assistente imobiliária especializada e prestativa.

Dados dos imóveis disponíveis no sistema:
{dados_imoveis}
{contexto_externo}

Regras:
- Responda de forma clara, profissional e use padrão brasileiro (R$ 1.234,56).
- Considere o contexto da conversa anterior (memória).
- Se o usuário usar "ele", "esse imóvel", "aquele cliente", refira-se ao que foi dito antes.
- Se não souber algo, seja honesta.
"""

        # Monta mensagens (system + últimas N mensagens)
        mensagens = [{"role": "system", "content": system_prompt}]
        mensagens.extend(historico[-MAX_HISTORICO:])

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=mensagens,
            max_tokens=800,
            temperature=0.7,
        )
        return response.choices[0].message.content

    except Exception as e:
        return f"❌ Erro na IA: {str(e)}"


def _precisa_busca_web(client, pergunta):
    """Decide se a pergunta exige busca externa."""
    if not pergunta.strip():
        return False

    try:
        prompt = f"""O usuário perguntou: "{pergunta}"

Você precisa buscar informações atualizadas na web para responder (notícias, indicadores econômicos, tendências de mercado, preço médio de bairros, etc.)?

Responda APENAS com "SIM" ou "NAO".
"""
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=5,
            temperature=0,
        ).choices[0].message.content.strip().upper()

        return "SIM" in resp
    except Exception:
        return False