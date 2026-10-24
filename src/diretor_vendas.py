import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from src.vendas_storage import calcular_metricas, carregar_vendas
from src.crm.leads_storage import carregar_leads

def renderizar_diretor_vendas():
    st.title("📈 Diretoria de Vendas")
    st.caption("Visão Executiva de Performance e Funil")
    st.markdown("---")

    # === CARDS DE MÉTRICAS GERAIS ===
    metricas = calcular_metricas()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("💰 VGV Total", f"R$ {metricas['vgv_total']:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    with col2:
        st.metric("🤝 Vendas Fechadas", metricas['total_vendas'])
    with col3:
        st.metric("🎯 Ticket Médio", f"R$ {metricas['vgv_medio']:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    with col4:
        leads = carregar_leads()
        st.metric("👥 Leads no CRM", len(leads))

    st.markdown("---")

    # === GRÁFICOS (2 colunas) ===
    col_esq, col_dir = st.columns(2)

    with col_esq:
        st.subheader("🏆 Ranking de Corretores")
        dados_resp = metricas.get("por_responsavel", {})
        if dados_resp:
            # Ordena pelo VGV
            ranking = sorted(dados_resp.items(), key=lambda x: x[1]["vgv"], reverse=True)
            nomes = [r[0] for r in ranking]
            valores = [r[1]["vgv"] for r in ranking]
            
            fig = px.bar(x=valores, y=nomes, orientation="h", 
                         text=[f"R$ {v:,.0f}" for v in valores],
                         color=valores, color_continuous_scale="Blues")
            fig.update_traces(textposition="outside")
            fig.update_layout(height=400, showlegend=False, coloraxis_showscale=False, 
                              xaxis_title="", yaxis_title="", margin=dict(l=0, r=20, t=20, b=20))
            fig.update_yaxes(autorange="reversed")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Sem dados de vendas por corretor ainda.")

    with col_dir:
        st.subheader("🎯 Funil de Captação (CRM)")
        # Agrupa os leads por status
        status_map = {
            "novo": "Novo Lead", "agendado": "Agendado", "atendimento": "Em Atendimento",
            "aprovacao": "Em Aprovação", "proposta": "Proposta", "venda": "Venda Ganha", "perdido": "Perdido"
        }
        contagem_status = {v: 0 for v in status_map.values()}
        for l in leads:
            st_atual = l.get("status", "novo")
            nome_st = status_map.get(st_atual)
            if nome_st:
                contagem_status[nome_st] += 1
                
        # Filtra os status que têm zero para o gráfico ficar bonito
        df_funil = pd.DataFrame(list(contagem_status.items()), columns=["Status", "Quantidade"])
        df_funil = df_funil[df_funil["Quantidade"] > 0]

        if not df_funil.empty:
            fig_funil = px.funnel(df_funil, x="Quantidade", y="Status", color="Status")
            fig_funil.update_layout(height=400, showlegend=False, margin=dict(l=0, r=0, t=20, b=20))
            st.plotly_chart(fig_funil, use_container_width=True)
        else:
            st.info("Sem leads no funil ainda.")

    st.markdown("---")
    st.subheader("📋 Últimas Vendas Realizadas")
    vendas_recentes = carregar_vendas()[:5] # Pega as 5 últimas
    if vendas_recentes:
        for v in vendas_recentes:
            st.write(f"✅ **{v.get('cliente', 'N/A')}** — {v.get('produto', '')} — R$ {v.get('vgv', 0):,.2f} ({v.get('responsavel', 'N/A')})")
    else:
        st.info("Nenhuma venda registrada.")