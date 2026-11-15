import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, date
from src.vendas_storage import (
    carregar_vendas, carregar_status, obter_status_por_id,
)

def renderizar_dashboard_vendas():
    st.title("📈 Dashboard de Vendas")
    st.markdown("---")

    vendas_brutas = carregar_vendas()

    if not vendas_brutas:
        st.info("📭 Nenhuma venda cadastrada ainda. Adicione na tela de Gestão de Vendas.")
        return

    # =========================================================
    # FILTRO DE DATA
    # =========================================================
    st.markdown("### 📅 Filtrar Período")
    col_d1, col_d2 = st.columns(2)
    
    # Pega a data atual para o filtro padrão
    hoje = date.today()
    inicio_mes = date(hoje.year, hoje.month, 1)

    with col_d1:
        data_inicio = st.date_input("Data Inicial", value=inicio_mes, format="DD/MM/YYYY")
    with col_d2:
        data_fim = st.date_input("Data Final", value=hoje, format="DD/MM/YYYY")

    # Converte as datas do filtro
    dt_inicio = datetime.combine(data_inicio, datetime.min.time())
    dt_fim = datetime.combine(data_fim, datetime.max.time())

    # Filtra a lista de vendas
    vendas_filtradas = []
    for v in vendas_brutas:
        data_str = v.get("data_venda", "")
        try:
            # Tenta converter de DD/MM/YYYY para datetime
            data_venda = datetime.strptime(data_str, "%d/%m/%Y")
            if dt_inicio <= data_venda <= dt_fim:
                vendas_filtradas.append(v)
        except ValueError:
            # Se a data estiver vazia ou errada, ignora no filtro
            pass

    st.caption(f"Mostrando **{len(vendas_filtradas)}** vendas no período selecionado.")
    st.markdown("---")

    if not vendas_filtradas:
        st.warning("⚠️ Nenhuma venda encontrada neste período.")
        return

    # =========================================================
    # CÁLCULO DAS MÉTRICAS (Agora usando apenas a lista filtrada)
    # =========================================================
    metricas = _calcular_metricas(vendas_filtradas)

    _renderizar_cards_metricas(metricas)
    st.markdown("---")
    _renderizar_graficos(metricas)
    st.markdown("---")
    _renderizar_kanban(vendas_filtradas)


# =========================================================
# LÓGICA DE MÉTRICAS (Extraída para aplicar no filtro)
# =========================================================
def _calcular_metricas(vendas):
    vgv_total = 0.0
    por_status = {}
    por_construtora = {}
    por_responsavel = {}

    for v in vendas:
        try:
            vgv = float(v.get("vgv", 0) or 0)
        except (ValueError, TypeError):
            vgv = 0.0
        vgv_total += vgv

        status_id = v.get("status", "nao_iniciado")
        por_status[status_id] = por_status.get(status_id, 0) + 1

        construtora = v.get("construtora", "N/A") or "N/A"
        por_construtora[construtora] = por_construtora.get(construtora, 0) + vgv

        resp = v.get("responsavel", "N/A") or "N/A"
        if resp not in por_responsavel:
            por_responsavel[resp] = {"qtd": 0, "vgv": 0.0}
        por_responsavel[resp]["qtd"] += 1
        por_responsavel[resp]["vgv"] += vgv

    return {
        "total_vendas": len(vendas),
        "vgv_total": round(vgv_total, 2),
        "vgv_medio": round(vgv_total / len(vendas), 2) if vendas else 0.0,
        "por_status": por_status,
        "por_construtora": por_construtora,
        "por_responsavel": por_responsavel,
    }


# =========================================================
# CARDS E GRÁFICOS (Mantidos do código anterior)
# =========================================================
def _renderizar_cards_metricas(metricas):
    col1, col2, col3, col4 = st.columns(4)
    with col1: st.metric("💼 Total de Vendas", metricas["total_vendas"])
    with col2: st.metric("💰 VGV Total", f"R$ {_formatar_brl(metricas['vgv_total'])}")
    with col3: st.metric("📊 VGV Médio", f"R$ {_formatar_brl(metricas['vgv_medio'])}")
    with col4: st.metric("✅ Concluídas", metricas["por_status"].get("concluido", 0))

def _renderizar_graficos(metricas):
    col1, col2 = st.columns(2)
    with col1:
        fig = _grafico_funil(metricas)
        if fig: st.plotly_chart(fig, use_container_width=True)
    with col2:
        fig = _grafico_construtora(metricas)
        if fig: st.plotly_chart(fig, use_container_width=True)
    col3, col4 = st.columns(2)
    with col3:
        fig = _grafico_responsavel(metricas)
        if fig: st.plotly_chart(fig, use_container_width=True)
    with col4:
        fig = _grafico_status_pizza(metricas)
        if fig: st.plotly_chart(fig, use_container_width=True)

def _grafico_funil(metricas):
    status_list = carregar_status()
    nomes, quantidades, cores = [], [], []
    for s in status_list:
        qtd = metricas["por_status"].get(s["id"], 0)
        if qtd > 0:
            nomes.append(s["nome"]); quantidades.append(qtd); cores.append(s["cor"])
    if not nomes: return None
    fig = go.Figure(go.Bar(x=quantidades, y=nomes, orientation="h", marker_color=cores, text=quantidades, textposition="outside"))
    fig.update_layout(title="🎯 Funil de Vendas (por status)", height=400, showlegend=False, xaxis_title="Quantidade", yaxis_title="", margin=dict(l=0, r=20, t=40, b=20))
    fig.update_yaxes(autorange="reversed")
    return fig

def _grafico_construtora(metricas):
    dados = metricas["por_construtora"]
    if not dados: return None
    itens = sorted(dados.items(), key=lambda x: x[1], reverse=True)[:10]
    nomes = [k for k, _ in itens]; valores = [v for _, v in itens]
    fig = px.bar(x=valores, y=nomes, orientation="h", title="🏗️ VGV por Construtora", color=valores, color_continuous_scale="Blues", text=[f"R$ {_formatar_brl(v)}" for v in valores])
    fig.update_traces(textposition="outside")
    fig.update_layout(height=400, showlegend=False, coloraxis_showscale=False, xaxis_title="", yaxis_title="", margin=dict(l=0, r=20, t=40, b=20))
    fig.update_yaxes(autorange="reversed")
    return fig

def _grafico_responsavel(metricas):
    dados = metricas["por_responsavel"]
    if not dados: return None
    itens = sorted(dados.items(), key=lambda x: x[1]["vgv"], reverse=True)
    nomes = [k for k, _ in itens]; valores = [v["vgv"] for _, v in itens]
    fig = px.bar(x=valores, y=nomes, orientation="h", title="👥 VGV por Responsável", color=valores, color_continuous_scale="Greens", text=[f"R$ {_formatar_brl(v)}" for v in valores])
    fig.update_traces(textposition="outside")
    fig.update_layout(height=400, showlegend=False, coloraxis_showscale=False, xaxis_title="", yaxis_title="", margin=dict(l=0, r=20, t=40, b=20))
    fig.update_yaxes(autorange="reversed")
    return fig

def _grafico_status_pizza(metricas):
    status_list = carregar_status()
    labels, valores, cores = [], [], []
    for s in status_list:
        qtd = metricas["por_status"].get(s["id"], 0)
        if qtd > 0:
            labels.append(s["nome"]); valores.append(qtd); cores.append(s["cor"])
    if not labels: return None
    fig = go.Figure(go.Pie(labels=labels, values=valores, hole=0.5, marker=dict(colors=cores), textinfo="percent"))
    fig.update_layout(title="🥧 Distribuição por Status", height=400, margin=dict(l=0, r=0, t=40, b=20), showlegend=True, legend=dict(orientation="v", yanchor="middle", y=0.5))
    return fig

def _renderizar_kanban(vendas):
    st.markdown("### 📌 Kanban de Vendas (Filtrado)")
    status_list = carregar_status()
    colunas_com_venda = []
    for s in status_list:
        vds = [v for v in vendas if v.get("status") == s["id"]]
        if vds: colunas_com_venda.append((s, vds))
    if not colunas_com_venda:
        st.info("Nenhuma venda para exibir no kanban neste período.")
        return
    for i in range(0, len(colunas_com_venda), 3):
        bloco = colunas_com_venda[i:i+3]
        cols = st.columns(len(bloco))
        for j, (status, vds) in enumerate(bloco):
            with cols[j]:
                st.markdown(f"<div style='background-color:{status['cor']}; color:white; padding:8px 12px; border-radius:8px 8px 0 0; font-weight:600; text-align:center; font-size:14px;'>{status['nome']} ({len(vds)})</div>", unsafe_allow_html=True)
                for v in vds:
                    st.markdown(f"""<div style='background-color:white; border:1px solid #e2e8f0; border-radius:0 0 8px 8px; padding:10px; margin-bottom:8px; box-shadow:0 1px 3px rgba(0,0,0,0.05);'><div style='font-weight:600; color:#0d2b3e; font-size:13px;'>🏠 {v.get('cliente', 'N/A')}</div><div style='color:#64748b; font-size:12px; margin-top:4px;'>{v.get('produto', '')}</div><div style='color:#1a73e8; font-weight:600; font-size:13px; margin-top:6px;'>R$ {_formatar_brl(v.get('vgv', 0))}</div><div style='color:#94a3b8; font-size:11px; margin-top:4px;'>👤 {v.get('responsavel', '')}</div></div>""", unsafe_allow_html=True)

def _formatar_brl(valor):
    try:
        v = float(valor)
        return f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (ValueError, TypeError):
        return "0,00"