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

def extrair_renda(texto):
    """
    Extrai o valor da renda de um texto, reconhecendo formatos BR com tolerância a zeros extras.
    Ex: R$ 5.0000,00 -> 5000.00
    """
    # Remove R$ e espaços
    texto_limpo = re.sub(r'R\$?\s*', '', texto)
    # Encontra padrão com vírgula decimal e ponto de milhar (flexível)
    # Ex: 5.0000,00 ou 10.0000,00 ou 5.000,00
    match = re.search(r'(\d{1,3}(?:\.\d{3,})*,\d{2})', texto_limpo)
    if match:
        raw = match.group(1)
        # Remove todos os pontos (milhar) e converte vírgula para ponto
        raw = raw.replace('.', '').replace(',', '.')
        return float(raw)
    # Tenta capturar números com vírgula decimal (ex: 5000,00)
    match = re.search(r'(\d+,\d{2})', texto_limpo)
    if match:
        raw = match.group(1).replace(',', '.')
        return float(raw)
    # Tenta capturar números inteiros (ex: 5000)
    match = re.search(r'(\d+)', texto_limpo)
    if match:
        return float(match.group(1))
    return None

def formatar_valor_br(valor):
    """Formata um float no padrão BR: R$ 1.234,56"""
    if valor is None or pd.isna(valor):
        return "R$ 0,00"
    us = f"{valor:,.2f}"
    br = us.replace(',', 'X').replace('.', ',').replace('X', '.')
    return f"R$ {br}"

def processar_pergunta(pergunta, df):
    pergunta_lower = pergunta.lower()
    resposta = []
    
    # 1. Recomendações por perfil (renda, preferências)
    if "cliente" in pergunta_lower or "renda" in pergunta_lower or "recomenda" in pergunta_lower:
        renda = extrair_renda(pergunta)
        
        if renda:
            resposta.append(f"💰 *Renda identificada:* {formatar_valor_br(renda)}")
        else:
            resposta.append("⚠️ *Nenhuma renda identificada na pergunta.*")
            resposta.append("💡 Tente usar formato como 'R$ 10.000,00'")
        
        # Extrai preferências (simplificado)
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
        
        # Debug do perfil
        resposta.append(f"📋 *Perfil montado:* {perfil_cliente}")
        
        recomendados = recomendar_imoveis(df, perfil_cliente=perfil_cliente)
        
        if recomendados is not None and not recomendados.empty:
            resposta.append(f"🔍 *Encontrei {len(recomendados)} oportunidades:*")
            for idx, row in recomendados.iterrows():
                parcela = row.get("PREÇO", 0) * 0.005
                unidade = row.get('UNIDADE', 'N/A')
                preco = row.get('PREÇO', 0)
                r_m2 = row.get('R$/m²', 0)
                resposta.append(
                    f"- *Unidade {unidade}* - {formatar_valor_br(preco)} | "
                    f"Parcela: {formatar_valor_br(parcela)} | R$/m²: {formatar_valor_br(r_m2)}"
                )
        else:
            resposta.append("⚠️ Nenhum imóvel encontrado para o perfil informado.")
            resposta.append("💡 Verifique se a renda está dentro da faixa dos imóveis disponíveis.")
    
    # 2. Pergunta sobre o melhor custo-benefício
    elif "melhor" in pergunta_lower or "custo-benefício" in pergunta_lower:
        if "R$/m²" in df.columns:
            melhor = df.loc[df["R$/m²"].idxmin()]
            resposta.append(f"🏆 *Melhor custo-benefício:* Unidade {melhor.get('UNIDADE', 'N/A')}")
            resposta.append(f"   - Preço: {formatar_valor_br(melhor.get('PREÇO', 0))}")
            resposta.append(f"   - R$/m²: {formatar_valor_br(melhor.get('R$/m²', 0))}")
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
                resposta.append(f"   - Faixa de preço: {formatar_valor_br(disponiveis['PREÇO'].min())} a {formatar_valor_br(disponiveis['PREÇO'].max())}")
        else:
            resposta.append("⚠️ Não foi possível verificar a disponibilidade.")
    
    # 4. Pergunta geral (resumo)
    else:
        resposta.append(f"📊 *Resumo dos imóveis disponíveis:*")
        resposta.append(f"   - Total: {len(df)} unidades")
        if "PREÇO" in df.columns:
            resposta.append(f"   - Faixa de preço: {formatar_valor_br(df['PREÇO'].min())} a {formatar_valor_br(df['PREÇO'].max())}")
        if "DISPONIBILIDADE" in df.columns:
            disp = df[df["DISPONIBILIDADE"] == "LIVRE"]
            resposta.append(f"   - Disponíveis: {len(disp)} unidades")
        resposta.append("\n💡 *Dica:* Pergunte sobre um cliente específico, melhor custo-benefício ou disponibilidade.")
    
    return "\n".join(resposta)