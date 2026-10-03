import streamlit as st
from datetime import datetime
from src.simulacoes_storage import carregar_simulacoes, excluir_simulacao
from src.utils import formatar_valor_br


def renderizar_historico(usuario_logado=None, USUARIOS=None):
    st.title("📚 Histórico de Simulações")
    st.markdown("---")

    perfil = "corretor"
    nome_usuario = ""
    if usuario_logado and USUARIOS and usuario_logado in USUARIOS:
        perfil = USUARIOS[usuario_logado].get("perfil", "corretor")
        nome_usuario = USUARIOS[usuario_logado].get("nome", "")

    is_corretor = perfil == "corretor"

    simulacoes = carregar_simulacoes()

    if not simulacoes:
        st.info("📭 Nenhuma simulação registrada ainda. Faça uma análise no Simulador.")
        return

    if is_corretor:
        st.info(f"👤 Mostrando suas simulações — **{nome_usuario}**")
        simulacoes = [s for s in simulacoes if s.get("gerente") == nome_usuario]
        if not simulacoes:
            st.info(f"📭 Nenhuma simulação registrada para **{nome_usuario}**.")
            return

    simulacoes_filtradas = _renderizar_filtros(simulacoes, esconder_responsavel=is_corretor)

    st.markdown("---")
    _renderizar_metricas(simulacoes_filtradas)
    st.markdown("---")

    if not simulacoes_filtradas:
        st.warning("⚠️ Nenhuma simulação encontrada com os filtros atuais.")
        return

    st.markdown(f"#### 📋 {len(simulacoes_filtradas)} simulações encontradas")

    for sim in simulacoes_filtradas:
        _renderizar_card_simulacao(sim)


def _renderizar_filtros(simulacoes, esconder_responsavel=False):
    if esconder_responsavel:
        col1, col2 = st.columns(2)
    else:
        col1, col2, col3 = st.columns(3)

    clientes = sorted(set(s["cliente"] for s in simulacoes if s.get("cliente")))
    with col1:
        cliente_filtro = st.selectbox("👤 Cliente", ["Todos"] + clientes, key="hist_filtro_cliente")

    origens = sorted(set(s["origem"] for s in simulacoes if s.get("origem")))

    if esconder_responsavel:
        with col2:
            origem_filtro = st.selectbox("🎯 Origem", ["Todas"] + origens, key="hist_filtro_origem")
        responsavel_filtro = "Todos"
    else:
        responsaveis = sorted(set(s["gerente"] for s in simulacoes if s.get("gerente")))
        with col2:
            responsavel_filtro = st.selectbox(
                "👤 Responsável",
                ["Todos"] + responsaveis,
                key="hist_filtro_responsavel",
                help="Quem fez a simulação (corretor ou gerente).",
            )
        with col3:
            origem_filtro = st.selectbox("🎯 Origem", ["Todas"] + origens, key="hist_filtro_origem")

    filtradas = simulacoes
    if cliente_filtro != "Todos":
        filtradas = [s for s in filtradas if s.get("cliente") == cliente_filtro]
    if responsavel_filtro != "Todos":
        filtradas = [s for s in filtradas if s.get("gerente") == responsavel_filtro]
    if origem_filtro != "Todas":
        filtradas = [s for s in filtradas if s.get("origem") == origem_filtro]

    return filtradas


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


def _renderizar_card_simulacao(sim):
    data = _formatar_data(sim.get("data_hora", ""))
    cliente = sim.get("cliente", "N/A")
    responsavel = sim.get("gerente", "")
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
            if responsavel:
                st.write(f"**👤 Responsável:** {responsavel}")
        with col3:
            desconto = sim.get("desconto", 0)
            if desconto > 0:
                st.write(f"**💸 Desconto:** {formatar_valor_br(desconto)}")
            st.write(f"**📋 Oportunidades:** {total_op}")

        st.markdown("---")

        oportunidades = sim.get("oportunidades", [])
        if oportunidades:
            st.markdown("##### 🏢 Top Oportunidades")
            for i, op in enumerate(oportunidades, 1):
                _renderizar_oportunidade(i, op)
        else:
            st.caption("Nenhuma oportunidade registrada.")

        st.markdown("---")
        col_e1, col_e2 = st.columns([4, 1])
        with col_e2:
            if st.button("🗑️ Excluir", key=f"del_sim_{sim['id']}", use_container_width=True):
                excluir_simulacao(sim["id"])
                st.success("✅ Simulação excluída!")
                st.rerun()


def _renderizar_oportunidade(idx, op):
    unidade = op.get("UNIDADE", "N/A")
    tipologia = op.get("TIPOLOGIA", "")
    valor_base = op.get("valor_base", 0)
    avaliacao = op.get("AVALIAÇÃO", 0)
    construtora = op.get("_construtora", "")
    produto = op.get("_produto", "")

    linha_extra = ""
    if construtora or produto:
        partes = []
        if construtora:
            partes.append(f"🏗️ {construtora}")
        if produto:
            partes.append(f"📦 {produto}")
        linha_extra = f" — {' • '.join(partes)}"

    st.write(f"**{idx}. 🏢 {unidade}**{linha_extra}")
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


def _formatar_data(iso_str):
    try:
        dt = datetime.fromisoformat(iso_str)
        return dt.strftime("%d/%m/%Y %H:%M")
    except Exception:
        return "Data desconhecida"