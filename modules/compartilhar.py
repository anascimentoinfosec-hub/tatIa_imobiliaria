import streamlit as st
import pandas as pd
from modules.utils import formatar_valor_br

def gerar_resumo(nome_cliente, renda, entrada, bairro, top_imoveis, nome_gerente=None, desconto=0, tipo_desconto="AVALIAÇÃO"):
    """Gera um resumo formatado para compartilhamento (sem emojis)"""
    linhas = []
    linhas.append("SIMULAÇÃO IMOBILIÁRIA")
    linhas.append("=" * 40)
    linhas.append("")
    linhas.append(f"Cliente: {nome_cliente}")
    if bairro:
        linhas.append(f"Bairro: {bairro}")
    linhas.append(f"Renda: {formatar_valor_br(renda)}")
    linhas.append(f"Entrada disponível: {formatar_valor_br(entrada)}")
    if desconto > 0:
        linhas.append(f"Desconto acordado: {formatar_valor_br(desconto)} (sobre {tipo_desconto})")
    linhas.append("")
    linhas.append("=" * 40)
    linhas.append("")
    if top_imoveis is not None and not top_imoveis.empty:
        linhas.append("TOP 3 OPORTUNIDADES")
        linhas.append("")
        for i, (idx, row) in enumerate(top_imoveis.head(3).iterrows()):
            preco = row.get("PREÇO", 0)
            parcela = preco * 0.005 if preco else 0
            unidade = row.get("UNIDADE", "N/A")
            tipologia = row.get("TIPOLOGIA", "")
            r_m2 = row.get("R$/m²", 0)
            valor_base = row.get("valor_base", preco)
            linhas.append(f"{i+1}. {unidade} - {formatar_valor_br(preco)}")
            if desconto > 0:
                linhas.append(f"   Valor base: {formatar_valor_br(valor_base)}")
            linhas.append(f"   Parcela estimada: {formatar_valor_br(parcela)}")
            linhas.append(f"   R$/m²: {formatar_valor_br(r_m2)}")
            if tipologia:
                linhas.append(f"   Tipo: {tipologia}")
            linhas.append("")
    else:
        linhas.append("Nenhuma oportunidade encontrada.")
    linhas.append("=" * 40)
    linhas.append("")
    linhas.append(f"Gerado em: {pd.Timestamp.now().strftime('%d/%m/%Y %H:%M')}")
    if nome_gerente:
        linhas.append(f"Gerente responsável: {nome_gerente}")
    else:
        linhas.append("App: simulador-credito.streamlit.app")
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
        st.markdown(
            f'<a href="{link}" target="_blank" style="display:block; background-color:#25D366; color:white; text-align:center; padding:8px; border-radius:8px; text-decoration:none; font-weight:600;">📱 Enviar WhatsApp</a>',
            unsafe_allow_html=True
        )
    with col3:
        st.caption("📄 PDF em breve")