import streamlit as st
from datetime import datetime
from src.simulacoes_storage import carregar_simulacoes, excluir_simulacao
from src.utils import formatar_valor_br


def renderizar_historico():
    """Renderiza a tela de histórico de simulações."""
    st.title("📚 Histórico de Simulações")
    st.markdown("---")

    simulacoes = carregar_simulacoes()

    if not simulacoes:
        st.info("📭 Nenhuma simulação registrada ainda. Faça uma análise no Simulador.")
        return

    # =========================================================
    # FILTROS
    # =========================================================
    simulacoes_filtradas = _renderizar_filtros(simulacoes)

    st.markdown("---")

    # =========================================================
    # MÉTRICAS
    # =========================================================
    _renderizar_metricas(simulacoes_filtradas)

    st.markdown("---")

    # =========================================================
    # LISTA
    # =========================================================
    if not simulacoes_filtradas:
        st.warning("⚠️ Nenhuma simulação encontrada com os filtros atuais.")
        return

    st.markdown(f"#### 📋 {len(simulacoes_filtradas)} simulações encontradas")

    for sim in simulacoes_filtradas:
        _renderizar_card_simulacao(sim)


# =========================================================
# FILTROS
# =========================================================
def _renderizar_filtros(simulacoes):
    col1, col2, col3 = st.columns(3)

    # Clientes únicos
    clientes = sorted(set(s["cliente"] for s in simulacoes if s.get("cliente")))
    with col1:
        cliente_filtro = st.selectbox(
            "👤 Cliente",
            ["Todos"] + clientes,
            key="hist_filtro_cliente",
            help="Filtra simulações por cliente.",
        )

    # Gerentes únicos
    gerentes = sorted(set(s["gerente"] for s in simulacoes if s.get("gerente")))
    with col2:
        gerente_filtro = st.selectbox(
            "👔 Gerente",
            ["Todos"] + gerentes,
            key="hist_filtro_gerente",
            help="Filtra simulações pelo gerente responsável.",
        )

    # Origens únicas
    origens = sorted(set(s["origem"] for s in simulacoes if s.get("origem")))
    with col3:
        origem_filtro = st.selectbox(
            "🎯 Origem",
            ["Todas"] + origens,
            key="hist_filtro_origem",
            help="Filtra simulações pela origem do cliente.",
        )

    filtradas = simulacoes

    if cliente_filtro != "Todos":
        filtradas = [s for s in filtradas if s.get("cliente") == cliente_filtro]

    if gerente_filtro != "Todos":
        filtradas = [s for s in filtradas if s.get("gerente") == gerente_filtro]

    if origem_filtro != "Todas":
        filtradas = [s for s in filtradas if s.get("origem") == origem_filtro]

    return filtradas


# =========================================================
# MÉTRICAS
# =========================================================
def _renderizar_metricas(simulacoes):
    total = len(simulacoes)
    renda_media = 0
    if simulacoes:
        renda_media = sum(s["renda"] for s in simulacoes) / total

    col1, col2 = st.columns(2)
    with col1:
        st.metric("📊 Total de Simulações", total)
    with col2:
        st.metric("💰 Renda Média", formatar_valor_br(renda_media))


# =========================================================
# CARD DE CADA SIMULAÇÃO
# =========================================================
def _renderizar_card_simulacao(sim):
    """Renderiza um card com os dados de uma simulação."""
    data = _formatar_data(sim.get("data_hora", ""))
    cliente = sim.get("cliente", "N/A")
    gerente = sim.get("gerente", "")
    origem = sim.get("origem", "")
    total_op = sim.get("total_oportunidades", 0)

    titulo = f"👤 {cliente} — {data}"

    with st.expander(titulo):
        col1, col2, col3 = st.columns(3)

        with col1:
            st.write(f"**💰 Renda:** {formatar_valor_br(sim.get('renda', 0))}")
            st.write(f"**🏦 Entrada:** {formatar_valor_br(sim.get('entrada', 0))}")

        with col2:
            if sim.get("bairro"):
                st.write(f"**📍 Bairro:** {sim['bairro']}")
            if origem:
                st.write(f"**🎯 Origem:** {origem}")
            if gerente:
                st.write(f"**👔 Gerente:** {gerente}")

        with col3:
            desconto = sim.get("desconto", 0)
            tipo_desc = sim.get("tipo_desconto", "AVALIAÇÃO")
            if desconto > 0:
                st.write(f"**💸 Desconto:** {formatar_valor_br(desconto)} ({tipo_desc})")
            st.write(f"**📋 Oportunidades:** {total_op}")

        st.markdown("---")

        # Lista de oportunidades
        oportunidades = sim.get("oportunidades", [])
        if oportunidades:
            st.markdown("##### 🏢 Top Oportunidades")
            for i, op in enumerate(oportunidades, 1):
                _renderizar_oportunidade(i, op)
        else:
            st.caption("Nenhuma oportunidade registrada.")

        st.markdown("---")

        # Botão excluir
        col_e1, col_e2 = st.columns([4, 1])
        with col_e2:
            if st.button("🗑️ Excluir", key=f"del_sim_{sim['id']}", use_container_width=True):
                excluir_simulacao(sim["id"])
                st.success("✅ Simulação excluída!")
                st.rerun()


# =========================================================
# OPORTUNIDADE INDIVIDUAL
# =========================================================
def _renderizar_oportunidade(idx, op):
    """Renderiza uma oportunidade do histórico."""
    unidade = op.get("UNIDADE", "N/A")
    tipologia = op.get("TIPOLOGIA", "")
    bloco = op.get("BLOCO", "")
    pavto = op.get("PAVTO", op.get("ANDAR", ""))
    valor_base = op.get("valor_base", 0)
    avaliacao = op.get("AVALIAÇÃO", 0)
    preco = op.get("PREÇO", 0)

    local = ""
    partes = []
    if bloco:
        partes.append(f"Bloco {bloco}")
    if pavto:
        partes.append(f"Andar {pavto}")
    if partes:
        local = " (" + " - ".join(partes) + ")"

    st.write(f"**{idx}. 🏢 {unidade}{local}**")
    col1, col2, col3 = st.columns(3)
    with col1:
        if avaliacao:
            st.caption(f"📊 Avaliação: {formatar_valor_br(avaliacao)}")
    with col2:
        if valor_base:
            st.caption(f"💰 Valor base: {formatar_valor_br(valor_base)}")
    with col3:
        if tipologia:
            st.caption(f"🏠 {tipologia}")


# =========================================================
# HELPERS
# =========================================================
def _formatar_data(iso_str):
    """Converte ISO em 'DD/MM/YYYY HH:MM'."""
    try:
        dt = datetime.fromisoformat(iso_str)
        return dt.strftime("%d/%m/%Y %H:%M")
    except Exception:
        return "Data desconhecida"