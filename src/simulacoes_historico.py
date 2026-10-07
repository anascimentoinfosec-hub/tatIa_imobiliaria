import streamlit as st
from datetime import datetime
from src.simulacoes_storage import (
    carregar_simulacoes, excluir_simulacao, STATUS_PROPOSTA,
    atualizar_status_proposta,
)
from src.utils import formatar_valor_br


def renderizar_historico(usuario_logado=None, USUARIOS=None):
    st.title("📚 Simulações")
    st.markdown("---")

    perfil = "corretor"
    nome_usuario = ""
    if usuario_logado and USUARIOS and usuario_logado in USUARIOS:
        perfil = USUARIOS[usuario_logado].get("perfil", "corretor")
        nome_usuario = USUARIOS[usuario_logado].get("nome", "")

    is_corretor = perfil == "corretor"
    is_gerente = perfil in ["gerente", "superadmin"]

    simulacoes = carregar_simulacoes()

    if not simulacoes:
        st.info("📭 Nenhuma simulação registrada ainda.")
        return

    if is_corretor:
        st.info(f"👤 Mostrando suas simulações — **{nome_usuario}**")
        simulacoes = [s for s in simulacoes if s.get("gerente") == nome_usuario]
        if not simulacoes:
            st.info(f"📭 Nenhuma simulação registrada para **{nome_usuario}**.")
            return

    # === FILTROS ===
    filtros_col1, filtros_col2, filtros_col3, filtros_col4 = st.columns(4)

    with filtros_col1:
        clientes = sorted(set(s["cliente"] for s in simulacoes if s.get("cliente")))
        cliente_filtro = st.selectbox("👤 Cliente", ["Todos"] + clientes, key="hist_filtro_cliente")

    with filtros_col2:
        if not is_corretor:
            responsaveis = sorted(set(s["gerente"] for s in simulacoes if s.get("gerente")))
            responsavel_filtro = st.selectbox("👤 Responsável", ["Todos"] + responsaveis, key="hist_filtro_responsavel")
        else:
            responsavel_filtro = "Todos"

    with filtros_col3:
        origens = sorted(set(s["origem"] for s in simulacoes if s.get("origem")))
        origem_filtro = st.selectbox("🎯 Origem", ["Todas"] + origens, key="hist_filtro_origem")

    with filtros_col4:
        status_opcoes = ["Todos"] + list(STATUS_PROPOSTA.keys())
        status_filtro = st.selectbox(
            "📋 Status", status_opcoes, key="hist_filtro_status",
            format_func=lambda s: "Todos" if s == "Todos" else STATUS_PROPOSTA[s]["nome"],
        )

    filtradas = simulacoes
    if cliente_filtro != "Todos":
        filtradas = [s for s in filtradas if s.get("cliente") == cliente_filtro]
    if responsavel_filtro != "Todos":
        filtradas = [s for s in filtradas if s.get("gerente") == responsavel_filtro]
    if origem_filtro != "Todas":
        filtradas = [s for s in filtradas if s.get("origem") == origem_filtro]
    if status_filtro != "Todos":
        filtradas = [s for s in filtradas if s.get("status_proposta", "pendente") == status_filtro]

    st.markdown("---")
    _renderizar_metricas(filtradas)
    st.markdown("---")

    if not filtradas:
        st.warning("⚠️ Nenhuma simulação encontrada com os filtros atuais.")
        return

    _renderizar_acoes_em_massa(filtradas)
    st.markdown("---")
    st.markdown(f"#### 📋 {len(filtradas)} simulações encontradas")

    for sim in filtradas:
        _renderizar_card_simulacao(sim, is_gerente)


def _renderizar_acoes_em_massa(simulacoes):
    col1, col2, col3 = st.columns([2, 2, 3])
    with col1:
        if st.button("✅ Selecionar todas", use_container_width=True, key="hist_sel_todas"):
            for sim in simulacoes:
                st.session_state[f"select_sim_{sim['id']}"] = True
            st.rerun()
    with col2:
        if st.button("❌ Desmarcar todas", use_container_width=True, key="hist_desmarcar"):
            for sim in simulacoes:
                st.session_state[f"select_sim_{sim['id']}"] = False
            st.rerun()
    with col3:
        marcadas = [s for s in simulacoes if st.session_state.get(f"select_sim_{s['id']}", False)]
        qtd = len(marcadas)
        if qtd > 0:
            st.session_state["confirmar_apagar_lote"] = True
        if st.session_state.get("confirmar_apagar_lote") and qtd > 0:
            if st.button(f"🗑️ Apagar {qtd} selecionada(s)", use_container_width=True,
                         type="primary", key="hist_apagar_lote"):
                for sim in marcadas:
                    excluir_simulacao(sim["id"])
                    st.session_state.pop(f"select_sim_{sim['id']}", None)
                st.session_state["confirmar_apagar_lote"] = False
                st.rerun()


def _renderizar_metricas(simulacoes):
    total = len(simulacoes)
    renda_media = sum(s["renda"] for s in simulacoes) / total if total else 0

    por_status = {}
    for s in simulacoes:
        status = s.get("status_proposta", "pendente")
        por_status[status] = por_status.get(status, 0) + 1

    col1, col2 = st.columns(2)
    with col1:
        st.metric("📊 Total de Simulações", total)
    with col2:
        st.metric("💰 Renda Média", formatar_valor_br(renda_media))

    if por_status:
        st.markdown("**📋 Por status:**")
        cols = st.columns(min(len(por_status), 5))
        for i, (status, qtd) in enumerate(por_status.items()):
            info = STATUS_PROPOSTA.get(status, {"nome": status, "cor": "#94a3b8"})
            with cols[i % len(cols)]:
                st.markdown(
                    f"<div style='background-color:{info['cor']}; color:white; padding:6px 12px; "
                    f"border-radius:8px; text-align:center; font-size:13px; margin-bottom:8px;'>"
                    f"{info['nome']}<br><b>{qtd}</b></div>",
                    unsafe_allow_html=True,
                )


def _renderizar_card_simulacao(sim, is_gerente):
    data = _formatar_data(sim.get("data_hora", ""))
    cliente = sim.get("cliente", "N/A")
    responsavel = sim.get("gerente", "")
    status = sim.get("status_proposta", "pendente")
    info_status = STATUS_PROPOSTA.get(status, {"nome": status, "cor": "#94a3b8"})

    col_check, col_titulo = st.columns([0.5, 11])
    with col_check:
        st.checkbox("sel", key=f"select_sim_{sim['id']}", label_visibility="collapsed")
    with col_titulo:
        st.markdown(f"**👤 {cliente} — {data}**")

    with st.expander("Ver detalhes", expanded=False):
        # Badge de status
        st.markdown(
            f"<div style='background-color:{info_status['cor']}; color:white; "
            f"padding:6px 14px; border-radius:20px; display:inline-block; "
            f"font-weight:600; font-size:13px; margin-bottom:12px;'>{info_status['nome']}</div>",
            unsafe_allow_html=True,
        )

        # === DADOS DO CLIENTE ===
        st.markdown("##### 🧑 Dados do Cliente")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.write(f"**Nome:** {cliente}")
            if sim.get("data_nascimento"):
                st.write(f"**Data Nasc.:** {sim['data_nascimento']}")
            if sim.get("origem"):
                st.write(f"**Origem:** {sim['origem']}")
        with col2:
            st.write(f"**Renda:** {formatar_valor_br(sim.get('renda', 0))}")
            st.write(f"**Entrada:** {formatar_valor_br(sim.get('entrada', 0))}")
            if sim.get("fgts", 0) > 0:
                st.write(f"**FGTS:** {formatar_valor_br(sim['fgts'])}")
        with col3:
            if sim.get("subsidio", 0) > 0:
                st.write(f"**Subsídio:** {formatar_valor_br(sim['subsidio'])}")
            if sim.get("financiamento_caixa", 0) > 0:
                st.write(f"**Financ. Caixa:** {formatar_valor_br(sim['financiamento_caixa'])}")
            if sim.get("parcela_morando", 0) > 0:
                st.write(f"**Parcela Morando:** {formatar_valor_br(sim['parcela_morando'])}")
            if responsavel:
                st.write(f"**Responsável:** {responsavel}")

        if sim.get("documentacao_paga"):
            st.success("📄 Documentação já paga pelo cliente")

        # === PLANO DE ENTRADA ===
        plano = sim.get("plano_entrada")
        if plano:
            st.markdown("---")
            st.markdown("##### 💰 Plano de Entrada")
            col_p1, col_p2, col_p3 = st.columns(3)
            with col_p1:
                st.write(f"**Entrada:** {formatar_valor_br(plano.get('valor_entrada', 0))}")
                st.write(f"**Ato mínimo:** {formatar_valor_br(plano.get('ato', 0))}")
            with col_p2:
                st.write(f"**Comissão:** {formatar_valor_br(plano.get('comissao_total', 0))}")
                st.write(f"**A parcelar:** {formatar_valor_br(plano.get('a_parcelar', 0))}")
            with col_p3:
                if plano.get("teto_parcelamento"):
                    st.write(f"**Teto ({plano.get('teto_pct', 15)}%):** {formatar_valor_br(plano['teto_parcelamento'])}")

            col_pre, col_pos = st.columns(2)
            with col_pre:
                st.markdown("**⏳ Pré-chaves**")
                if plano.get("num_pre", 0) > 0:
                    st.write(f"{plano['num_pre']}x de **{formatar_valor_br(plano.get('valor_pre', 0))}**")
                    st.caption(f"Máx {plano.get('pre_pct', 30)}% renda")
                else:
                    st.caption("Sem parcelas pré-chaves")
            with col_pos:
                st.markdown("**🔑 Pós-chaves**")
                if plano.get("num_pos", 0) > 0:
                    st.write(f"{plano['num_pos']}x de **{formatar_valor_br(plano.get('valor_pos', 0))}**")
                    st.caption(f"Máx {plano.get('pos_pct', 5)}% renda")
                else:
                    st.caption("Sem parcelas pós-chaves")

            # Alertas
            alertas = plano.get("alertas", [])
            if alertas:
                for a in alertas:
                    if "🟢" in a:
                        st.success(a)
                    elif "🔴" in a:
                        st.error(a)
                    else:
                        st.warning(a)
            elif plano.get("viavel"):
                st.success("✅ Plano viável dentro das regras da construtora.")

        # === AÇÕES DE STATUS ===
        if is_gerente:
            st.markdown("---")
            st.markdown("**🎯 Ações do Gerente:**")
            _renderizar_acoes_status(sim, status, responsavel)

        # === OPORTUNIDADES ===
        st.markdown("---")
        oportunidades = sim.get("oportunidades", [])
        if oportunidades:
            st.markdown("##### 🏢 Oportunidade")
            for i, op in enumerate(oportunidades, 1):
                _renderizar_oportunidade(i, op)

        st.markdown("---")
        col_e1, col_e2 = st.columns([4, 1])
        with col_e2:
            if st.button("🗑️ Excluir", key=f"del_sim_{sim['id']}", use_container_width=True):
                excluir_simulacao(sim["id"])
                st.rerun()


def _renderizar_acoes_status(sim, status, responsavel):
    """Botões de ação conforme o status atual."""
    sim_id = sim["id"]

    col1, col2, col3, col4 = st.columns(4)

    if status == "pendente":
        with col1:
            if st.button("📤 Enviar p/ análise", key=f"acao_pend_{sim_id}", use_container_width=True):
                atualizar_status_proposta(sim_id, "em_analise", responsavel)
                st.rerun()

    elif status == "em_analise":
        with col1:
            if st.button("✅ Aprovar", key=f"acao_apr_{sim_id}", use_container_width=True):
                atualizar_status_proposta(sim_id, "aprovada", responsavel)
                st.rerun()
        with col2:
            if st.button("❌ Rejeitar", key=f"acao_rej_{sim_id}", use_container_width=True):
                motivo = st.session_state.get(f"motivo_{sim_id}", "")
                atualizar_status_proposta(sim_id, "rejeitada", responsavel, motivo=motivo)
                st.rerun()
        with col3:
            st.text_input("Motivo (se rejeitar)", key=f"motivo_{sim_id}", placeholder="Ex: renda insuficiente")

    elif status == "aprovada":
        with col1:
            if st.button("🏢 Cadastrar na construtora", key=f"acao_cad_{sim_id}", use_container_width=True):
                atualizar_status_proposta(sim_id, "aguardando_construtora", responsavel)
                st.rerun()

    elif status == "aguardando_construtora":
        with col1:
            if st.button("📄 Contrato enviado", key=f"acao_ctr_{sim_id}", use_container_width=True):
                atualizar_status_proposta(sim_id, "contrato_enviado", responsavel)
                st.rerun()

    elif status == "contrato_enviado":
        with col1:
            if st.button("🎉 Confirmar Venda", key=f"acao_venda_{sim_id}",
                         use_container_width=True, type="primary"):
                _confirmar_venda_real(sim, responsavel)
                st.rerun()

    else:
        st.caption(f"Status final: **{STATUS_PROPOSTA.get(status, {}).get('nome', status)}**")


def _confirmar_venda_real(sim, responsavel):
    """Confirma a venda: atualiza status + cria Venda no pipeline."""
    from src.vendas_storage import salvar_venda
    from datetime import date

    # 1. Atualiza status
    atualizar_status_proposta(sim["id"], "venda_confirmada", responsavel)

    # 2. Cria venda real no pipeline
    try:
        oportunidades = sim.get("oportunidades", [])
        op = oportunidades[0] if oportunidades else {}

        valor_base = float(op.get("valor_base", 0) or 0)

        salvar_venda({
            "fonte": sim.get("origem", ""),
            "cliente": sim.get("cliente", ""),
            "produto": op.get("_produto", ""),
            "bloco": op.get("BLOCO", ""),
            "apt": op.get("UNIDADE", ""),
            "construtora": op.get("_construtora", ""),
            "vgv": valor_base,
            "responsavel": sim.get("gerente", ""),
            "data_venda": date.today().strftime("%d/%m/%Y"),
            "ato_pago": "Sim",
            "status": "concluido",
            "observacoes": (
                f"Venda confirmada a partir da simulação #{sim['id'][-6:]}. "
                f"Plano: {op.get('num_pre', 0)}x pré + {op.get('num_pos', 0)}x pós."
            ),
            "campos_extras": {},
        })
        st.toast("🎉 Venda criada no pipeline! Confira em 💼 Vendas.")
    except Exception as e:
        st.error(f"Status atualizado, mas erro ao criar venda: {str(e)}")


def _renderizar_oportunidade(idx, op):
    unidade = op.get("UNIDADE", "N/A")
    tipologia = op.get("TIPOLOGIA", "")
    valor_base = op.get("valor_base", 0)
    avaliacao = op.get("AVALIAÇÃO", 0)
    preco = op.get("PREÇO", 0)
    construtora = op.get("_construtora", "")
    produto = op.get("_produto", "")
    num_pre = op.get("num_pre", 0)
    num_pos = op.get("num_pos", 0)

    linha_extra = ""
    if construtora or produto:
        partes = []
        if construtora:
            partes.append(f"🏗️ {construtora}")
        if produto:
            partes.append(f"📦 {produto}")
        linha_extra = f" — {' • '.join(partes)}"

    st.write(f"**{idx}. 🏢 Unidade {unidade}**{linha_extra}")

    col1, col2, col3 = st.columns(3)
    with col1:
        if avaliacao:
            st.caption(f"📊 Avaliação: {formatar_valor_br(avaliacao)}")
        if preco:
            st.caption(f"💵 Preço: {formatar_valor_br(preco)}")
    with col2:
        if valor_base:
            st.caption(f"💰 Valor base: {formatar_valor_br(valor_base)}")
        if tipologia:
            st.caption(f"🏠 {tipologia}")
    with col3:
        if num_pre or num_pos:
            st.caption(f"💼 {num_pre}x pré + {num_pos}x pós")


def _formatar_data(iso_str):
    try:
        dt = datetime.fromisoformat(iso_str)
        return dt.strftime("%d/%m/%Y %H:%M")
    except Exception:
        return "Data desconhecida"