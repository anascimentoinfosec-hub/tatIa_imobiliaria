import streamlit as st
from datetime import datetime, date
from src.vendas_storage import (
    carregar_vendas,
    salvar_venda,
    atualizar_venda,
    excluir_venda,
    obter_venda,
    carregar_status,
    salvar_status,
    obter_status_por_id,
    carregar_campos_extras,
    adicionar_campo_extra,
    remover_campo_extra,
)
from src.origens_storage import carregar_origens
from src.construtoras_storage import carregar_construtoras


def renderizar_gestao_vendas():
    """Tela principal de gestão de vendas."""
    st.title("💼 Gestão de Vendas")
    st.markdown("---")

    tabs = st.tabs([
        "📋 Listar",
        "➕ Adicionar",
        "✏️ Editar",
        "⚙️ Status",
        "🔧 Campos Extras",
    ])

    with tabs[0]:
        _renderizar_lista()

    with tabs[1]:
        _renderizar_form_adicionar()

    with tabs[2]:
        _renderizar_form_editar()

    with tabs[3]:
        _renderizar_gestao_status()

    with tabs[4]:
        _renderizar_gestao_campos_extras()


# =========================================================
# LISTAR
# =========================================================
def _renderizar_lista():
    vendas = carregar_vendas()

    if not vendas:
        st.info("📭 Nenhuma venda cadastrada ainda.")
        return

    # Filtros
    col1, col2, col3 = st.columns(3)

    status_list = carregar_status()
    opcoes_status = ["(Todos)"] + [s["nome"] for s in status_list]

    with col1:
        filtro_status = st.selectbox("Status", opcoes_status, key="vendas_filtro_status")

    with col2:
        construtoras_unicas = sorted(set(v.get("construtora", "") for v in vendas if v.get("construtora")))
        filtro_construtora = st.selectbox("Construtora", ["(Todas)"] + construtoras_unicas, key="vendas_filtro_construtora")

    with col3:
        responsaveis = sorted(set(v.get("responsavel", "") for v in vendas if v.get("responsavel")))
        filtro_responsavel = st.selectbox("Responsável", ["(Todos)"] + responsaveis, key="vendas_filtro_responsavel")

    # Aplica filtros
    filtradas = vendas
    if filtro_status != "(Todos)":
        status_id = next((s["id"] for s in status_list if s["nome"] == filtro_status), None)
        if status_id:
            filtradas = [v for v in filtradas if v.get("status") == status_id]
    if filtro_construtora != "(Todas)":
        filtradas = [v for v in filtradas if v.get("construtora") == filtro_construtora]
    if filtro_responsavel != "(Todos)":
        filtradas = [v for v in filtradas if v.get("responsavel") == filtro_responsavel]

    st.markdown(f"#### 📋 {len(filtradas)} venda(s)")

    for v in filtradas:
        _renderizar_card_venda(v)


def _renderizar_card_venda(v):
    cliente = v.get("cliente", "N/A")
    produto = v.get("produto", "")
    vgv = v.get("vgv", 0)
    status_id = v.get("status", "nao_iniciado")
    status = obter_status_por_id(status_id)
    cor = status["cor"] if status else "#94a3b8"
    nome_status = status["nome"] if status else "N/A"

    titulo = f"🏠 {cliente}  •  {produto}  •  R$ {vgv:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    with st.expander(titulo):
        col1, col2 = st.columns([3, 2])

        with col1:
            st.markdown(f"**Status:** <span style='background-color:{cor}; color:white; padding:3px 10px; border-radius:12px; font-size:13px;'>{nome_status}</span>", unsafe_allow_html=True)
            st.write(f"**Construtora:** {v.get('construtora', 'N/A')}")
            st.write(f"**Bloco/Apt:** {v.get('bloco', '')} / {v.get('apt', '')}")
            st.write(f"**Responsável:** {v.get('responsavel', 'N/A')}")
            st.write(f"**Data da venda:** {v.get('data_venda', 'N/A')}")
            st.write(f"**Fonte:** {v.get('fonte', 'N/A')}")

        with col2:
            st.write(f"**VGV:** R$ {_formatar_brl(vgv)}")
            st.write(f"**Ato pago:** {v.get('ato_pago', 'N/A')}")

        if v.get("observacoes"):
            st.markdown("---")
            st.caption(f"💬 **Observações:** {v['observacoes']}")

        # Campos extras
        extras = v.get("campos_extras", {})
        if extras:
            st.markdown("---")
            st.markdown("**Campos extras:**")
            campos_def = {c["id"]: c["nome"] for c in carregar_campos_extras()}
            for k, val in extras.items():
                nome = campos_def.get(k, k)
                st.write(f"• **{nome}:** {val}")

        st.markdown("---")
        col_btn1, col_btn2 = st.columns([4, 1])
        with col_btn2:
            if st.button("🗑️ Excluir", key=f"del_venda_{v['id']}", use_container_width=True):
                excluir_venda(v["id"])
                st.success("✅ Venda excluída!")
                st.rerun()


# =========================================================
# ADICIONAR
# =========================================================
def _renderizar_form_adicionar():
    st.markdown("### ➕ Adicionar nova venda")
    st.caption("Preencha os dados abaixo para registrar uma nova venda.")

    with st.form("form_nova_venda"):
        col1, col2 = st.columns(2)

        with col1:
            fonte = st.selectbox(
                "Fonte",
                ["(Não informado)"] + carregar_origens(),
                key="venda_fonte",
                help="De onde veio esse cliente (Lead, Indicação, etc.).",
            )
            cliente = st.text_input("Nome do cliente", key="venda_cliente")
            produto = st.text_input("Produto/Empreendimento", key="venda_produto")
            bloco = st.text_input("Bloco", key="venda_bloco")
            apt = st.text_input("Apt/Unidade", key="venda_apt")
            construtora = st.selectbox(
                "Construtora",
                ["(Nenhuma)"] + list(carregar_construtoras().keys()),
                key="venda_construtora",
            )

        with col2:
            vgv = st.number_input(
                "VGV (R$)", min_value=0.0, value=0.0, step=10000.0, format="%.2f",
                key="venda_vgv",
                help="Valor Geral da Venda.",
            )
            responsavel = st.text_input("Responsável pela venda", key="venda_responsavel")
            data_venda = st.date_input("Data da venda", value=date.today(), key="venda_data")
            ato_pago = st.selectbox(
                "Ato pago",
                ["(Não informado)", "Sim", "Não", "Parcialmente"],
                key="venda_ato_pago",
            )
            status_list = carregar_status()
            status_opcoes = {s["nome"]: s["id"] for s in status_list}
            status_nome = st.selectbox("Status", list(status_opcoes.keys()), key="venda_status")

        observacoes = st.text_area("Observações", key="venda_obs", height=80)

        # Campos extras
        campos_extras = carregar_campos_extras()
        valores_extras = {}
        if campos_extras:
            st.markdown("---")
            st.markdown("**Campos extras:**")
            for campo in campos_extras:
                valores_extras[campo["id"]] = st.text_input(
                    campo["nome"],
                    key=f"venda_extra_{campo['id']}",
                )

        if st.form_submit_button("➕ Registrar venda", use_container_width=True, type="primary"):
            if not cliente.strip():
                st.warning("⚠️ Informe o nome do cliente!")
            else:
                salvar_venda({
                    "fonte": "" if fonte == "(Não informado)" else fonte,
                    "cliente": cliente.strip(),
                    "produto": produto.strip(),
                    "bloco": bloco.strip(),
                    "apt": apt.strip(),
                    "construtora": "" if construtora == "(Nenhuma)" else construtora,
                    "vgv": vgv,
                    "responsavel": responsavel.strip(),
                    "data_venda": data_venda.strftime("%d/%m/%Y"),
                    "ato_pago": "" if ato_pago == "(Não informado)" else ato_pago,
                    "status": status_opcoes[status_nome],
                    "observacoes": observacoes.strip(),
                    "campos_extras": valores_extras,
                })
                st.success(f"✅ Venda de '{cliente}' registrada!")
                st.rerun()


# =========================================================
# EDITAR
# =========================================================
def _renderizar_form_editar():
    vendas = carregar_vendas()
    if not vendas:
        st.info("Nenhuma venda para editar.")
        return

    opcoes = {f"{v.get('cliente', 'N/A')} — {v.get('produto', '')} (#{v['id'][-6:]})": v["id"] for v in vendas}
    escolha = st.selectbox("Selecione a venda", list(opcoes.keys()), key="venda_editar_select")
    venda_id = opcoes[escolha]
    v = obter_venda(venda_id)

    if not v:
        st.error("Venda não encontrada.")
        return

    st.markdown("---")

    with st.form("form_editar_venda"):
        col1, col2 = st.columns(2)

        with col1:
            fonte = st.text_input("Fonte", value=v.get("fonte", ""), key="edit_fonte")
            cliente = st.text_input("Nome do cliente", value=v.get("cliente", ""), key="edit_cliente")
            produto = st.text_input("Produto", value=v.get("produto", ""), key="edit_produto")
            bloco = st.text_input("Bloco", value=v.get("bloco", ""), key="edit_bloco")
            apt = st.text_input("Apt/Unidade", value=v.get("apt", ""), key="edit_apt")
            construtora = st.text_input("Construtora", value=v.get("construtora", ""), key="edit_construtora")

        with col2:
            vgv = st.number_input("VGV (R$)", min_value=0.0, value=float(v.get("vgv", 0) or 0),
                                   step=10000.0, format="%.2f", key="edit_vgv")
            responsavel = st.text_input("Responsável", value=v.get("responsavel", ""), key="edit_responsavel")
            data_venda_str = v.get("data_venda", "")
            data_venda = st.text_input("Data da venda", value=data_venda_str, key="edit_data")

            ato_opcoes = ["(Não informado)", "Sim", "Não", "Parcialmente"]
            ato_idx = ato_opcoes.index(v.get("ato_pago", "")) if v.get("ato_pago", "") in ato_opcoes else 0
            ato_pago = st.selectbox("Ato pago", ato_opcoes, index=ato_idx, key="edit_ato")

            status_list = carregar_status()
            status_nomes = [s["nome"] for s in status_list]
            status_ids = [s["id"] for s in status_list]
            status_idx = status_ids.index(v.get("status", "nao_iniciado")) if v.get("status", "nao_iniciado") in status_ids else 0
            status_nome = st.selectbox("Status", status_nomes, index=status_idx, key="edit_status")

        observacoes = st.text_area("Observações", value=v.get("observacoes", ""), key="edit_obs", height=80)

        # Campos extras
        campos_extras = carregar_campos_extras()
        valores_extras = {}
        if campos_extras:
            st.markdown("---")
            st.markdown("**Campos extras:**")
            for campo in campos_extras:
                valores_extras[campo["id"]] = st.text_input(
                    campo["nome"],
                    value=v.get("campos_extras", {}).get(campo["id"], ""),
                    key=f"edit_extra_{campo['id']}",
                )

        if st.form_submit_button("💾 Salvar alterações", use_container_width=True, type="primary"):
            atualizar_venda(venda_id, {
                "fonte": fonte, "cliente": cliente, "produto": produto,
                "bloco": bloco, "apt": apt, "construtora": construtora,
                "vgv": vgv, "responsavel": responsavel, "data_venda": data_venda,
                "ato_pago": ato_pago, "status": status_ids[status_nomes.index(status_nome)],
                "observacoes": observacoes, "campos_extras": valores_extras,
            })
            st.success("✅ Venda atualizada!")
            st.rerun()


# =========================================================
# GERENCIAR STATUS
# =========================================================
def _renderizar_gestao_status():
    st.markdown("### ⚙️ Gerenciar Status das Vendas")
    st.caption("Edite, adicione ou remova os status do funil de vendas.")

    status_list = carregar_status()

    # Lista atual
    for s in status_list:
        col1, col2, col3, col4 = st.columns([2, 2, 2, 1])

        with col1:
            st.write(f"**{s['nome']}**")
        with col2:
            st.markdown(f"<span style='background-color:{s['cor']}; padding:2px 10px; border-radius:10px; color:white;'>Cor</span>", unsafe_allow_html=True)
        with col3:
            st.caption(f"Ordem: {s.get('ordem', '?')}")
        with col4:
            if st.button("🗑️", key=f"del_status_{s['id']}"):
                if len(status_list) <= 1:
                    st.error("Não pode remover o último status!")
                else:
                    status_list.remove(s)
                    salvar_status(status_list)
                    st.rerun()

    st.markdown("---")
    st.markdown("#### ➕ Adicionar novo status")

    with st.form("form_novo_status"):
        col1, col2, col3 = st.columns([3, 2, 1])
        with col1:
            nome = st.text_input("Nome do status", key="novo_status_nome")
        with col2:
            cor = st.color_picker("Cor", value="#1a73e8", key="novo_status_cor")
        with col3:
            ordem = st.number_input("Ordem", min_value=1, value=len(status_list) + 1, step=1, key="novo_status_ordem")

        if st.form_submit_button("➕ Adicionar", use_container_width=True, type="primary"):
            if not nome.strip():
                st.warning("⚠️ Digite o nome do status!")
            else:
                import re
                import unicodedata
                sid = unicodedata.normalize("NFKD", nome.lower().strip()).encode("ASCII", "ignore").decode("ASCII")
                sid = re.sub(r"[^a-z0-9]+", "_", sid).strip("_")

                if any(s["id"] == sid for s in status_list):
                    st.error("Já existe um status com esse nome.")
                else:
                    status_list.append({"id": sid, "nome": nome.strip(), "cor": cor, "ordem": int(ordem)})
                    salvar_status(status_list)
                    st.success(f"✅ Status '{nome}' adicionado!")
                    st.rerun()


# =========================================================
# GERENCIAR CAMPOS EXTRAS
# =========================================================
def _renderizar_gestao_campos_extras():
    st.markdown("### 🔧 Campos Extras personalizados")
    st.caption("Adicione campos personalizados que aparecerão no formulário de vendas.")

    campos = carregar_campos_extras()

    if campos:
        for c in campos:
            col1, col2 = st.columns([4, 1])
            with col1:
                st.write(f"• **{c['nome']}** (id: `{c['id']}`)")
            with col2:
                if st.button("🗑️", key=f"del_campo_{c['id']}"):
                    remover_campo_extra(c["id"])
                    st.rerun()
    else:
        st.info("Nenhum campo extra cadastrado.")

    st.markdown("---")
    st.markdown("#### ➕ Adicionar campo")

    with st.form("form_novo_campo"):
        nome = st.text_input("Nome do campo", placeholder="Ex: Data de assinatura")
        if st.form_submit_button("➕ Adicionar campo", type="primary"):
            if not nome.strip():
                st.warning("⚠️ Digite o nome do campo!")
            else:
                adicionar_campo_extra(nome, "texto")
                st.success(f"✅ Campo '{nome}' adicionado!")
                st.rerun()


# =========================================================
# HELPERS
# =========================================================
def _formatar_brl(valor):
    try:
        v = float(valor)
        return f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (ValueError, TypeError):
        return "0,00"