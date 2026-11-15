import streamlit as st
import pandas as pd
import re

def processar_pergunta(pergunta, df_imoveis):
    """
    Processa uma pergunta do corretor usando lógica local
    """
    if df_imoveis is None or df_imoveis.empty:
        return "⚠️ Nenhuma planilha carregada. Faça upload de uma planilha primeiro."
    
    pergunta_lower = pergunta.lower()
    resposta = []
    
    # 1. Pergunta sobre preço
    if "preço" in pergunta_lower or "custo" in pergunta_lower or "barato" in pergunta_lower:
        if "PREÇO" in df_imoveis.columns:
            imovel = df_imoveis.loc[df_imoveis['PREÇO'].idxmin()]
            resposta.append(f"💰 *Imóvel mais barato:* Unidade {imovel['UNIDADE']} - R$ {imovel['PREÇO']:,.2f}")
    
    # 2. Pergunta sobre melhor custo-benefício
    if "melhor" in pergunta_lower or "recomenda" in pergunta_lower or "top" in pergunta_lower:
        if "R$/m²" in df_imoveis.columns:
            melhor = df_imoveis.loc[df_imoveis['R$/m²'].idxmin()]
            resposta.append(f"🏆 *Melhor custo-benefício:* Unidade {melhor['UNIDADE']}")
            resposta.append(f"   - Preço: R$ {melhor['PREÇO']:,.2f}")
            resposta.append(f"   - R$/m²: R$ {melhor['R$/m²']:.2f}")
    
    # 3. Pergunta sobre disponibilidade
    if "disponível" in pergunta_lower or "tem" in pergunta_lower or "quantos" in pergunta_lower:
        if "DISPONIBILIDADE" in df_imoveis.columns:
            qtde = len(df_imoveis[df_imoveis['DISPONIBILIDADE'] == 'LIVRE'])
            resposta.append(f"📋 *Imóveis disponíveis:* {qtde} unidades livres")
    
    # 4. Pergunta sobre cliente (renda)
    if "cliente" in pergunta_lower or "renda" in pergunta_lower:
        try:
            rendas = re.findall(r'R?\$?\s*(\d+[\.,]?\d*)', pergunta)
            if rendas:
                renda = float(rendas[0].replace(',', '.'))
                parcela_maxima = renda * 0.4
                df_filtrado = df_imoveis[df_imoveis['PREÇO'] * 0.005 <= parcela_maxima]
                if not df_filtrado.empty:
                    resposta.append(f"✅ *Imóveis dentro da faixa de renda:* {len(df_filtrado)} opções")
                    melhor = df_filtrado.loc[df_filtrado['R$/m²'].idxmin()] if "R$/m²" in df_filtrado.columns else df_filtrado.iloc[0]
                    resposta.append(f"   🏠 Recomendo: Unidade {melhor['UNIDADE']} - R$ {melhor['PREÇO']:,.2f}")
                else:
                    resposta.append("⚠️ Nenhum imóvel encontrado dentro da faixa de renda informada.")
        except:
            pass
    
    # 5. Resumo geral (se nenhuma condição foi atendida)
    if not resposta:
        resposta.append("📊 *Resumo dos imóveis disponíveis:*")
        resposta.append(f"   - Total: {len(df_imoveis)} unidades")
        if "PREÇO" in df_imoveis.columns:
            resposta.append(f"   - Faixa de preço: R$ {df_imoveis['PREÇO'].min():,.2f} a R$ {df_imoveis['PREÇO'].max():,.2f}")
        if "DISPONIBILIDADE" in df_imoveis.columns:
            resposta.append(f"   - Disponíveis: {len(df_imoveis[df_imoveis['DISPONIBILIDADE'] == 'LIVRE'])} unidades")
        resposta.append("\n💡 *Dica:* Seja mais específico (ex: 'qual o mais barato?', 'recomende para renda de R$ 8.000')")
    
    return '\n'.join(resposta)

def pagina_chat():
    """Interface do chat com a IA"""
    st.title("💬 IA Imobiliária - Assistente de Vendas")
    st.markdown("---")
    
    if "df_imoveis" not in st.session_state or st.session_state.df_imoveis is None:
        st.warning("⚠️ Nenhuma planilha carregada. Carregue uma planilha no *Simulador* primeiro.")
        return
    
    if "historico_chat" not in st.session_state:
        st.session_state.historico_chat = [
            {"role": "assistant", "content": "Olá! Sou sua IA imobiliária. Pergunte sobre:\n- Preços\n- Disponibilidade\n- Recomendações para clientes"}
        ]
    
    for msg in st.session_state.historico_chat:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    
    pergunta = st.chat_input("Digite sua pergunta sobre os imóveis...")
    if pergunta:
        st.session_state.historico_chat.append({"role": "user", "content": pergunta})
        with st.chat_message("user"):
            st.markdown(pergunta)
        with st.chat_message("assistant"):
            with st.spinner("Analisando..."):
                resposta = processar_pergunta(pergunta, st.session_state.df_imoveis)
                st.markdown(resposta)
                st.session_state.historico_chat.append({"role": "assistant", "content": resposta})