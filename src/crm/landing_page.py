import streamlit as st
from openai import OpenAI
from src.crm.leads_storage import criar_lead
import urllib.parse
import re # <--- A MÁGICA ESTÁ AQUI
import json

def renderizar_landing_page(campanha_id=None):
    # Se a URL tem uma campanha nova, limpa o estado antigo
    if campanha_id and st.session_state.get("campanha_atual") != campanha_id:
        for k in list(st.session_state.keys()):
            if k in ["hist_landing", "dados_lead", "lead_salvo"]:
                del st.session_state[k]
        st.session_state["campanha_atual"] = campanha_id

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

    # Se o lead já foi salvo
    if st.session_state.get("lead_salvo", False):
        st.success("✅ Sua solicitação foi registrada! Em breve um corretor falará com você.")
        st.balloons()
        
        # === BOTÃO DE WHATSAPP ===
        from src.configuracoes_storage 
        import obter_configuracao
        tel_imobiliaria = obter_configuracao("whatsapp_imobiliaria", "5521999999999")
            
        mensagem_wa = f"Olá! Sou o {st.session_state.dados_lead['nome']}. Acabei de falar com a Bia no site e gostaria de ver as oportunidades de imóveis!"
        mensagem_encoded = urllib.parse.quote(mensagem_wa)
        link_wa = f"https://wa.me/{tel_imobiliaria}?text={mensagem_encoded}"
        
        st.markdown(f"""
        <div style='text-align: center; margin-top: 20px;'>
            <p>Para agilizar, você pode iniciar a conversa agora mesmo no WhatsApp:</p>
            <a href="{link_wa}" target="_blank" style='background-color:#25D366; color:white; padding:12px 24px; text-decoration:none; border-radius:8px; font-weight:bold; font-size:16px;'>
                📱 Chamar no WhatsApp
            </a>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        # BOTÃO PARA TESTAR NOVAMENTE
        if st.button("🔄 Fazer nova simulação (Limpar conversa)"):
            for k in list(st.session_state.keys()):
                if k in ["hist_landing", "dados_lead", "lead_salvo"]:
                    del st.session_state[k]
            st.rerun()
            
        return

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

        if st.session_state.dados_lead["nome"] and st.session_state.dados_lead["telefone"] and st.session_state.dados_lead["renda"] > 0:
            if not st.session_state.get("lead_salvo", False):
                # Limpa o telefone (só números)
                tel_limpo = re.sub(r'\D', '', str(st.session_state.dados_lead["telefone"]))
                # Se for 10 ou 11 dígitos (DDD + número), adiciona o 55
                if len(tel_limpo) in (10, 11):
                    tel_limpo = "55" + tel_limpo
                
                st.session_state.dados_lead["telefone"] = tel_limpo

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
                st.rerun()

def processar_chat_landing(client, historico, dados_atuais, campanha_id):
    system_prompt = f"""Você é a BIA, uma consultora imobiliária simpática e profissional.
Seu objetivo é descobrir 3 coisas com o cliente, uma de cada vez, de forma natural:
1. O nome completo dele.
2. O WhatsApp para contato (peça com DDD, ex: 21999999999).
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
        
        match = re.search(r'<json>(.*?)</json>', texto_completo, re.DOTALL)
        if match:
            try:
                dados_json = json.loads(match.group(1))
                if "renda" in dados_json and isinstance(dados_json["renda"], str):
                    try:
                        dados_json["renda"] = float(re.sub(r'[^\d.]', '', dados_json["renda"].replace(',', '.')))
                    except:
                        dados_json["renda"] = 0
                        
                texto_limpo = re.sub(r'<json>.*?</json>', '', texto_completo, flags=re.DOTALL).strip()
                return texto_limpo, dados_json
            except Exception:
                pass
        
        return texto_completo, dados_atuais
    except Exception:
        return "❌ Desculpe, tive um erro técnico. Pode repetir?", dados_atuais