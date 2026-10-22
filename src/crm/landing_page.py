import streamlit as st
from openai import OpenAI
from src.crm.leads_storage import criar_lead

def renderizar_landing_page(campanha_id=None):
    st.markdown("""
        <style>
        [data-testid="collapsedControl"] {display: none;}
        section[data-testid="stSidebar"] {display: none;}
        </style>
    """, unsafe_allow_html=True)

    st.markdown("""
        <div style='text-align: center; padding: 20px;'>
            <h1>🏢 Encontre o imóvel dos seus sonhos!</h1>
            <p>Nossa inteligência artificial vai te ajudar a encontrar a oportunidade perfeita.</p>
        </div>
    """, unsafe_allow_html=True)

    if "OPENAI_API_KEY" not in st.secrets:
        st.error("IA indisponível no momento.")
        return

    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

    if "hist_landing" not in st.session_state:
        st.session_state.hist_landing = [
            {"role": "assistant", "content": "Olá! Eu sou a Bia, consultora virtual da imobiliária. Para começar, qual é o seu nome?"}
        ]
        st.session_state.dados_lead = {"nome": "", "telefone": "", "renda": 0, "origem": campanha_id or "Site"}
        st.session_state.lead_salvo = False

    for msg in st.session_state.hist_landing:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Se o lead já foi salvo, mostra a mensagem final e NÃO mostra o input
    if st.session_state.get("lead_salvo", False):
        st.success("✅ Sua solicitação foi registrada! Em breve um corretor falará com você.")
        st.balloons()
        return # O return corta o código aqui, escondendo o chat_input

    # Se ainda não foi salvo, mostra o input
    pergunta = st.chat_input("Digite sua resposta...")

    if pergunta:
        st.session_state.hist_landing.append({"role": "user", "content": pergunta})
        with st.chat_message("user"):
            st.markdown(pergunta)

        with st.chat_message("assistant"):
            with st.spinner("Pensando..."):
                resposta, lead_pronto = processar_chat_landing(client, st.session_state.hist_landing, st.session_state.dados_lead, campanha_id)
                st.markdown(resposta)
                st.session_state.hist_landing.append({"role": "assistant", "content": resposta})
                st.session_state.dados_lead.update(lead_pronto)

        # Checa se já temos tudo para salvar
        if st.session_state.dados_lead["nome"] and st.session_state.dados_lead["telefone"] and st.session_state.dados_lead["renda"] > 0:
            if not st.session_state.get("lead_salvo", False):
                criar_lead(
                    nome=st.session_state.dados_lead["nome"],
                    telefone=st.session_state.dados_lead["telefone"],
                    email="",
                    renda=st.session_state.dados_lead["renda"],
                    origem=st.session_state.dados_lead["origem"],
                    corretor="Não atribuído",
                    campanha_id=campanha_id
                )
                st.session_state["lead_salvo"] = True
                st.rerun() # Dá um rerun para esconder o input imediatamente


def processar_chat_landing(client, historico, dados_atuais, campanha_id):
    system_prompt = f"""Você é a BIA, uma consultora imobiliária simpática e profissional.
Seu objetivo é descobrir 3 coisas com o cliente, uma de cada vez, de forma natural:
1. O nome completo dele.
2. O WhatsApp para contato.
3. A renda mensal aproximada (familiar) para sabermos qual financiamento ele consegue.

Dados já coletados até agora: {dados_atuais}

REGRAS:
- Faça apenas UMA pergunta por vez.
- Seja breve, como uma conversa de WhatsApp.
- Quando você já tiver os 3 dados (nome, telefone, renda), agradeça, diga que um corretor entrará em contato e encerre. NÃO DIGA que vai listar os dados, apenas se despeça amigavelmente.
- SEMPRE no final da sua resposta, retorne um JSON oculto entre as tags <json> e </json> com os dados que você conseguiu extrair até agora. Exemplo: <json>{{"nome": "João", "telefone": "", "renda": 0}}</json>
"""

    mensagens = [{"role": "system", "content": system_prompt}]
    mensagens.extend(historico[-6:])

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=mensagens,
            max_tokens=300,
            temperature=0.5
        )
        texto_completo = response.choices[0].message.content
        
        import json
        import re
        
        match = re.search(r'<json>(.*?)</json>', texto_completo, re.DOTALL)
        if match:
            try:
                dados_json = json.loads(match.group(1))
                # Garante que a renda venha como float/numérico
                if "renda" in dados_json and isinstance(dados_json["renda"], str):
                    try:
                        dados_json["renda"] = float(re.sub(r'[^\d.]', '', dados_json["renda"].replace(',', '.')))
                    except:
                        dados_json["renda"] = 0
                        
                texto_limpo = re.sub(r'<json>.*?</json>', '', texto_completo, flags=re.DOTALL).strip()
                return texto_limpo, dados_json
            except Exception as e:
                pass
        
        return texto_completo, dados_atuais
    except Exception as e:
        return f"❌ Desculpe, tive um erro técnico. Pode repetir?", dados_atuais
