import streamlit as st
import pandas as pd
from modules.utils import formatar_valor_br

def gerar_resumo(nome, renda, entrada, bairro, top_imoveis):
    linhas = []
    linhas.append("🏢 SIMULAÇÃO IMOBILIÁRIA")
    linhas.append("━" * 40)
    linhas.append(f"🧑 Cliente: {nome}")
    if bairro:
        linhas.append(f"📍 Bairro: {bairro}")
    linhas.append(f"💰 Renda: {formatar_valor_br(renda)}")
    linhas.append(f"🏦 Entrada: {formatar_valor_br(entrada)}")
    linhas.append("")
    if top_imoveis is not None and not top_imoveis.empty:
        linhas.append("🏆 TOP 3 OPORTUNIDADES")
        for i, row in top_imoveis.head(3).iterrows():
            preco = row.get("PREÇO", 0)
            unidade = row.get("UNIDADE", "N/A")
            linhas.append(f"{i+1}. {unidade} – {formatar_valor_br(preco)}")
    linhas.append("")
    linhas.append(f"📅 {pd.Timestamp.now().strftime('%d/%m/%Y %H:%M')}")
    return "\n".join(linhas)

def botoes_compartilhar(resumo, nome_cliente):
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.download_button(
            label="📄 Baixar TXT",
            data=resumo,
            file_name=f"simulacao_{nome_cliente.replace(' ', '_')}.txt",
            mime="text/plain",
            use_container_width=True
        )
    
    with col2:
        mensagem = resumo.replace('\n', '%0A')
        link = f"https://wa.me/?text={mensagem}"
        st.markdown(f'<a href="{link}" target="_blank" style="display:block; background-color:#25D366; color:white; text-align:center; padding:8px; border-radius:8px; text-decoration:none;">📱 WhatsApp</a>', unsafe_allow_html=True)
    
    with col3:
        st.caption("PDF em breve")