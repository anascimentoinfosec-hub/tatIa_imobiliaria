import streamlit as st
import pandas as pd
import re
from modules.recomendacoes import recomendar_imoveis

def pagina_bia():
    st.title("💬 BIA - IA Imobiliária")
    st.markdown("---")
    
    if "df_imoveis" not in st.session_state or st.session_state.df_imoveis is None:
        st.warning("⚠️ Nenhuma planilha disponível. Carregue uma planilha no Simulador primeiro.")
        return
    
    df = st.session_state.df_imoveis.copy()
    
    if "hist_bia" not in st.session_state:
        st.session_state.hist_bia = [
            {"role": "assistant", "content": "Olá! Sou a BIA, sua assistente imobiliária. Pergunte sobre os imóveis disponíveis ou informe o perfil do cliente para recomendações."}
        ]
    
    for msg in st.session_state.hist_bia:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    
    pergunta = st.chat_input("Digite sua pergunta para a BIA...")
    
    if pergunta:
        st.session_state.hist_bia.append({"role": "user", "content": pergunta})
        with st.chat_message("user"):
            st.markdown(pergunta)
        
        with st.chat_message("assistant"):
            with st.spinner("Analisando..."):
                resposta = processar_pergunta(pergunta, df)
                st.markdown(resposta)
                st.session_state.hist_bia.append({"role": "assistant", "content": resposta})

def processar_pergunta(pergunta, df):
    pergunta_lower = pergunta.lower()
    resposta = []
    
    # 1. Recomendações por perfil (renda, preferências)
    if "cliente" in pergunta_lower or "renda" in pergunta_lower or "recomenda" in pergunta_lower:
        # --- EXTRAÇÃO DE RENDA (CORRIGIDA) ---
        renda = None
        
        # Remove R$ e espaços extras
        pergunta_limpa = re.sub(r'R\$?\s*', '', pergunta).strip()
        
        # Tenta capturar valores com ponto de milhar e vírgula decimal (ex: 15.000,00)
        match = re.search(r'(\d{1,3}(?:\.\d{3})*,\d{2})', pergunta_limpa)
        if match:
            raw = match.group(1)
            raw = raw.replace('.', '').replace(',', '.')
            renda = float(raw)
        else:
            # Tenta capturar valores com ponto de milhar sem decimais (ex: 15.000)
            match = re.search(r'(\d{1,3}(?:\.\d{3})*)', pergunta_limpa)
            if match:
                raw = match.group(1)
                raw = raw.replace('.', '')
                renda = float(raw)
            else:
                # Tenta capturar valores simples (ex: 15000 ou 15)
                match = re.search(r'(\d+)', pergunta_limpa)
                if match:
                    renda = float(match.group(1))
        
        # Mostra a renda identificada (DEBUG)
        if renda:
            resposta.append(f"💰 *Renda identificada:* R$ {renda:,.2f}")
        else:
            resposta.append("⚠️ *Nenhuma renda identificada na pergunta.*")
        
        # Extrai preferências
        preferencias = {}
        if "2 quartos" in pergunta_lower:
            preferencias["quartos"] = "2"
        elif "3 quartos" in pergunta_lower:
            preferencias["quartos"] = "3"
        elif "4 quartos" in pergunta_lower:
            preferencias["quartos"] = "4"
        if "apartamento" in pergunta_lower:
            preferencias["tipo"] = "Apartamento"
        elif "cobertura" in pergunta_lower:
            preferencias["tipo"] = "Cobertura"
        elif "garden" in pergunta_lower:
            preferencias["tipo"] = "Garden"
        
        perfil_cliente = {}
        if renda:
            perfil_cliente["renda"] = renda
        if preferencias:
            perfil_cliente.update(preferencias)
        
        recomendados = recomendar_imoveis(df, perfil_cliente=perfil_cliente)
        
        if recomendados is not None and not recomendados.empty:
            resposta.append(f"🔍 *Encontrei {len(recomendados)} oportunidades para o perfil informado:*")
            for idx, row in recomendados.iterrows():
                parcela = row.get("PREÇO", 0) * 0.005
                unidade = row.get('UNIDADE', 'N/A')
                preco = row.get('PREÇO', 0)
                r_m2 = row.get('R$/m²', 0)
                resposta.append(f"- *Unidade {unidade}* - R$ {preco:,.2f} | Parcela estimada: R$ {parcela:,.2f} | R$/m²: R$ {r_m2:.2f}")
        else:
            resposta.append("⚠️ Nenhum imóvel encontrado para o perfil informado. Tente ajustar a renda ou as preferências.")
    
    # 2. Pergunta sobre o melhor custo-benefício
    elif "melhor" in pergunta_lower or "custo-benefício" in pergunta_lower:
        if "R$/m²" in df.columns:
            melhor = df.loc[df["R$/m²"].idxmin()]
            resposta.append(f"🏆 *Melhor custo-benefício:* Unidade {melhor.get('UNIDADE', 'N/A')}")
            resposta.append(f"   - Preço: R$ {melhor.get('PREÇO', 0):,.2f}")
            resposta.append(f"   - R$/m²: R$ {melhor.get('R$/m²', 0):.2f}")
            if "TIPOLOGIA" in melhor:
                resposta.append(f"   - Tipo: {melhor['TIPOLOGIA']}")
        else:
            resposta.append("⚠️ Dados insuficientes para calcular o melhor custo-benefício.")
    
    # 3. Pergunta sobre imóveis disponíveis
    elif "disponível" in pergunta_lower or "tem" in pergunta_lower:
        if "DISPONIBILIDADE" in df.columns:
            disponiveis = df[df["DISPONIBILIDADE"] == "LIVRE"]
            resposta.append(f"📋 *Imóveis disponíveis:* {len(disponiveis)} unidades")
            if len(disponiveis) > 0:
                resposta.append(f"   - Faixa de preço: R$ {disponiveis['PREÇO'].min():,.2f} a R$ {disponiveis['PREÇO'].max():,.2f}")
        else:
            resposta.append("⚠️ Não foi possível verificar a disponibilidade.")
    
    # 4. Pergunta geral (resumo)
    else:
        resposta.append(f"📊 *Resumo dos imóveis disponíveis:*")
        resposta.append(f"   - Total: {len(df)} unidades")
        if "PREÇO" in df.columns:
            resposta.append(f"   - Faixa de preço: R$ {df['PREÇO'].min():,.2f} a R$ {df['PREÇO'].max():,.2f}")
        if "DISPONIBILIDADE" in df.columns:
            disp = df[df["DISPONIBILIDADE"] == "LIVRE"]
            resposta.append(f"   - Disponíveis: {len(disp)} unidades")
        resposta.append("\n💡 *Dica:* Pergunte sobre um cliente específico, melhor custo-benefício ou disponibilidade.")
    
    return "\n".join(resposta)