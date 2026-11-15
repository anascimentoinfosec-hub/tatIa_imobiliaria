import streamlit as st
import pandas as pd
from src.vendas_storage import carregar_vendas, carregar_status

def renderizar_diretor_financeiro():
    st.title("💰 Diretoria Financeira e Administrativa")
    st.caption("Gestão de Contratos, Comissões e Fluxo de Caixa")
    st.markdown("---")

    vendas = carregar_vendas()
    status_list = carregar_status()
    mapa_status = {s["id"]: s["nome"] for s in status_list}

    # Filtra apenas as vendas concluídas para o Financeiro
    vendas_concluidas = [v for v in vendas if v.get("status") == "concluido"]

    if not vendas_concluidas:
        st.info("📭 Nenhuma venda concluída para gerar dados financeiros ainda.")
        return

    # === CÁLCULOS FINANCEIROS BÁSICOS ===
    faturamento_total = sum(float(v.get("vgv", 0)) for v in vendas_concluidas)
    
    # Vamos usar uma taxa média de comissão da imobiliária (ex: 5%) para estimativa
    comissao_estimada = faturamento_total * 0.05 

    # === CARDS DE MÉTRICAS ===
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"<div class='card-moderno' style='text-align:center;'><h3 style='font-size:24px; margin:0; color:#1a73e8;'>R$ {faturamento_total:,.2f}</h3><p style='margin:0; color:#5f6368;'>Faturamento (VGV)</p></div>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<div class='card-moderno' style='text-align:center;'><h3 style='font-size:24px; margin:0; color:#28a745;'>R$ {comissao_estimada:,.2f}</h3><p style='margin:0; color:#5f6368;'>Comissão Estimada (~5%)</p></div>", unsafe_allow_html=True)
    with col3:
        st.markdown(f"<div class='card-moderno' style='text-align:center;'><h3 style='font-size:24px; margin:0; color:#0ea5e9;'>{len(vendas_concluidas)}</h3><p style='margin:0; color:#5f6368;'>Contratos Fechados</p></div>", unsafe_allow_html=True)

    st.markdown("---")

    # === TABELA DE CONTRATOS ===
    st.subheader("📋 Gestão de Contratos e Repasses")
    st.caption("Acompanhe os detalhes financeiros de cada venda fechada.")
    
    dados_tabela = []
    for v in vendas_concluidas:
        vgv = float(v.get("vgv", 0))
        comissao = vgv * 0.05 # Estimativa de 5%
        
        dados_tabela.append({
            "Data": v.get("data_venda", ""),
            "Cliente": v.get("cliente", ""),
            "Produto": f"{v.get('produto', '')} - {v.get('apt', '')}",
            "Construtora": v.get("construtora", ""),
            "VGV (R$)": f"{vgv:,.2f}",
            "Comissão Est. (R$)": f"{comissao:,.2f}",
            "Status Pgto": "Aguardando Repasse" if not v.get("comissao_paga") else "Pago"
        })

    df = pd.DataFrame(dados_tabela)
    st.dataframe(df, use_container_width=True)

    # === BOTÃO DE EXPORTAR ===
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Exportar Relatório CSV",
        data=csv,
        file_name='relatorio_financeiro.csv',
        mime='text/csv',
    )

    st.markdown("---")
    st.info("💡 **Nota:** Os valores de comissão são estimativas baseadas em 5%. Em breve, integraremos o módulo de Contas a Pagar e Receber para lançamentos manuais.")