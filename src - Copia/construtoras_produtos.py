import streamlit as st
import json
from src.construtoras_storage import carregar_construtoras, salvar_construtoras
from src.bia_planilha import analisar_planilha_com_bia
from src.planilha_processor import processar_planilha_e_salvar_cache


def renderizar_aba_produtos(cidades):
    st.markdown("### Gerenciar Produtos")

    CONSTRUTORAS_ATUALIZADO = carregar_construtoras()
    construtoras_lista = list(CONSTRUTORAS_ATUALIZADO.keys())

    if not construtoras_lista:
        st.warning("Nenhuma construtora cadastrada.")
        return

    construtora_edit = _selecionar_construtora(construtoras_lista)
    dados = CONSTRUTORAS_ATUALIZADO[construtora_edit]
    tipo_desconto = dados.get("tipo_desconto", "AVALIAÇÃO")

    st.markdown(f"#### Produtos de **{construtora_edit}**")
    _renderizar_editor_desconto(construtora_edit, tipo_desconto)

    st.markdown("---")
    _renderizar_lista_produtos(construtora_edit, dados.get("produtos", {}))

    st.markdown("---")
    _renderizar_form_adicionar_produto(construtora_edit, cidades, tipo_desconto)

    _renderizar_form_editar_produto(construtora_edit, cidades)
    st.markdown("---")
    from src.planilha_cache_ajuste import renderizar_ajuste_valores
    with st.expander("🔧 Ajustar valores de uma planilha (caso importado errado)", expanded=False):
        renderizar_ajuste_valores()

# =========================================================
def _selecionar_construtora(construtoras_lista):
    if ("construtora_edit" not in st.session_state
            or st.session_state.construtora_edit not in construtoras_lista):
        st.session_state.construtora_edit = construtoras_lista[0]

    index_atual = construtoras_lista.index(st.session_state.construtora_edit) \
        if st.session_state.construtora_edit in construtoras_lista else 0

    construtora_edit = st.selectbox(
        "Selecione a construtora", construtoras_lista,
        index=index_atual, key="select_construtora_produtos",
    )
    st.session_state.construtora_edit = construtora_edit
    return construtora_edit


# =========================================================
def _renderizar_editor_desconto(construtora_edit, tipo_desconto):
    col_td1, col_td2 = st.columns([2, 1])
    with col_td1:
        novo_tipo_desconto = st.selectbox(
            "💡 Desconto será aplicado sobre:",
            ["AVALIAÇÃO", "PREÇO"],
            index=0 if tipo_desconto == "AVALIAÇÃO" else 1,
            key="prod_edit_tipo_desconto",
        )
    with col_td2:
        st.write("")
        st.write("")
        if st.button("💾 Salvar regra", use_container_width=True, key="prod_btn_salvar_regra"):
            dados_atuais = carregar_construtoras()
            dados_atuais[construtora_edit]["tipo_desconto"] = novo_tipo_desconto
            salvar_construtoras(dados_atuais)
            st.success(f"✅ Regra alterada para: {novo_tipo_desconto}")
            st.rerun()


# =========================================================
def _renderizar_lista_produtos(construtora_edit, produtos):
    if not produtos:
        st.info("Nenhum produto cadastrado para esta construtora.")
        return

    for produto, config in produtos.items():
        col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
        with col1:
            st.write(f"📄 **{produto}**")
        with col2:
            cidade = config.get("cidade", "Não definida")
            st.write(f"📍 {cidade}")
        with col3:
            if st.button("✏️ Editar", key=f"prod_edit_prod_{produto}"):
                st.session_state["editando_produto"] = produto
                st.rerun()
        with col4:
            if st.button("🗑️ Excluir", key=f"prod_del_prod_{produto}"):
                _excluir_produto(construtora_edit, produto)


def _excluir_produto(construtora_edit, produto):
    try:
        dados_atuais = carregar_construtoras()
        if construtora_edit in dados_atuais and produto in dados_atuais[construtora_edit]["produtos"]:
            del dados_atuais[construtora_edit]["produtos"][produto]
            salvar_construtoras(dados_atuais)
            st.success(f"✅ Produto '{produto}' excluído com sucesso!")
            st.rerun()
    except Exception as e:
        st.error(f"❌ Erro ao excluir: {str(e)}")


# =========================================================
def _renderizar_form_adicionar_produto(construtora_edit, cidades, tipo_desconto):
    st.markdown("#### ➕ Adicionar Produto")

    with st.expander("🤖 Preencher automaticamente com a BIA (opcional)", expanded=False):
        st.caption("Suba uma planilha de referência e clique em **Analisar com BIA**.")

        uploaded = st.file_uploader(
            "Planilha de referência", type=["xlsx", "xls", "csv"],
            key="prod_bia_upload_planilha",
        )

        if st.button("🤖 Analisar com BIA", use_container_width=True, key="prod_btn_bia_analisar"):
            if uploaded is None:
                st.warning("⚠️ Faça upload de uma planilha primeiro.")
            else:
                with st.spinner("A BIA está analisando a planilha..."):
                    resultado = analisar_planilha_com_bia(uploaded)

                if "erro" in resultado:
                    st.error(f"❌ {resultado['erro']}")
                else:
                    st.session_state["prod_bia_resultado"] = resultado
                    st.session_state["prod_bia_arquivo_bytes"] = uploaded.getvalue()
                    st.session_state["prod_bia_arquivo_nome"] = uploaded.name
                    st.success("✅ BIA preencheu o formulário! Revise antes de salvar.")
                    if resultado.get("observacoes"):
                        st.info(f"💬 **Observação da BIA:** {resultado['observacoes']}")
                    st.rerun()

    # === APLICA as sugestões da BIA direto no session_state (antes dos widgets) ===
    if "prod_bia_resultado" in st.session_state:
        bia = st.session_state.pop("prod_bia_resultado")  # pop = aplica e remove
        st.session_state["prod_novo_mapeamento"] = json.dumps(
            bia.get("mapeamento", {}), indent=2, ensure_ascii=False
        )
        st.session_state["prod_novo_colunas_ordem"] = ", ".join(bia.get("colunas_ordem", []))
        st.session_state["prod_novo_colunas_numericas"] = ", ".join(
            bia.get("colunas_monetarias", []) + bia.get("colunas_numericas", [])
        )
        st.session_state["prod_novo_skiprows"] = int(bia.get("skiprows", bia.get("header_row", 2)))

    # === FORMULÁRIO (keys puras, sem value=) ===
    novo_produto = st.text_input("Nome do Produto", placeholder="Ex: Torre A", key="prod_novo_produto_nome")
    nova_cidade = st.selectbox("📍 Cidade", [""] + cidades, key="prod_nova_cidade_produto")

    novo_skiprows = st.number_input(
        "Linhas para pular antes do cabeçalho",
        min_value=0, step=1, key="prod_novo_skiprows",
    )

    novo_mapeamento = st.text_area(
        "Mapeamento (índice: nome)",
        placeholder='{"0": "UNIDADE", "1": "PAVTO", "2": "PREÇO"}',
        height=120, key="prod_novo_mapeamento",
    )

    novo_colunas_ordem = st.text_input(
        "Colunas para exibir (separadas por vírgula)",
        placeholder="UNIDADE, PAVTO, PREÇO", key="prod_novo_colunas_ordem",
    )

    novo_colunas_numericas = st.text_input(
        "Colunas monetárias/numéricas (separadas por vírgula)",
        placeholder="PREÇO, M², ANDAR", key="prod_novo_colunas_numericas",
    )

    if st.button("💾 Salvar Produto", use_container_width=True, type="primary", key="prod_btn_salvar_produto"):
        _salvar_novo_produto(
            construtora_edit=construtora_edit, tipo_desconto=tipo_desconto,
            novo_produto=novo_produto, nova_cidade=nova_cidade,
            novo_skiprows=novo_skiprows, novo_mapeamento=novo_mapeamento,
            novo_colunas_ordem=novo_colunas_ordem, novo_colunas_numericas=novo_colunas_numericas,
        )


def _salvar_novo_produto(construtora_edit, tipo_desconto, novo_produto, nova_cidade,
                          novo_skiprows, novo_mapeamento, novo_colunas_ordem,
                          novo_colunas_numericas):
    if not novo_produto:
        st.warning("⚠️ Digite o nome do produto!")
        return

    if not novo_mapeamento.strip():
        st.error("❌ **Mapeamento vazio.** Preencha manualmente ou use o botão '🤖 Analisar com BIA' antes de salvar.")
        return

    if not nova_cidade:
        st.error("❌ Selecione a **cidade** do produto.")
        return

    try:
        dados_atuais = carregar_construtoras()
        if construtora_edit not in dados_atuais:
            dados_atuais[construtora_edit] = {"tipo_desconto": tipo_desconto, "produtos": {}}

        produtos_atuais = dados_atuais[construtora_edit].get("produtos", {})

        try:
            mapeamento = json.loads(novo_mapeamento)
        except json.JSONDecodeError:
            st.error("❌ O mapeamento não é um JSON válido.")
            return

        if not mapeamento:
            st.error("❌ O mapeamento está vazio.")
            return

        colunas_ordem = [c.strip() for c in novo_colunas_ordem.split(",") if c.strip()]
        colunas_numericas = [c.strip() for c in novo_colunas_numericas.split(",") if c.strip()]

        if novo_produto in produtos_atuais:
            st.error(f"❌ Produto '{novo_produto}' já existe!")
            return

        produtos_atuais[novo_produto] = {
            "cidade": nova_cidade,
            "skiprows": novo_skiprows,
            "mapeamento": {str(k): v for k, v in mapeamento.items()},
            "colunas_ordem": colunas_ordem,
            "colunas_para_converter": colunas_numericas,
        }
        dados_atuais[construtora_edit]["produtos"] = produtos_atuais
        salvar_construtoras(dados_atuais)
        # === SALVA PLANILHA NO CACHE ===
        if "prod_bia_arquivo_bytes" in st.session_state:
            ok, msg = processar_planilha_e_salvar_cache(
                file_bytes=st.session_state["prod_bia_arquivo_bytes"],
                file_name=st.session_state["prod_bia_arquivo_nome"],
                config=produtos_atuais[novo_produto],
                construtora=construtora_edit,
                produto=novo_produto,
            )
            if not ok:
                st.warning(f"⚠️ Produto criado, mas: {msg}")
        _limpar_chaves_form_produto()
        st.success(f"✅ Produto '{novo_produto}' adicionado com sucesso!")
        st.rerun()
    except Exception as e:
        st.error(f"❌ Erro ao adicionar produto: {str(e)}")


def _limpar_chaves_form_produto():
    keys = [
        "prod_novo_produto_nome", "prod_novo_skiprows", "prod_novo_mapeamento",
        "prod_novo_colunas_ordem", "prod_novo_colunas_numericas",
        "prod_nova_cidade_produto", "prod_bia_resultado",
        "prod_bia_arquivo_bytes", "prod_bia_arquivo_nome",
    ]
    for k in keys:
        if k in st.session_state:
            del st.session_state[k]


# =========================================================
def _renderizar_form_editar_produto(construtora_edit, cidades):
    if not st.session_state.get("editando_produto"):
        return

    produto_edit = st.session_state["editando_produto"]
    dados_atuais = carregar_construtoras()

    if construtora_edit not in dados_atuais:
        return

    produtos_atuais = dados_atuais[construtora_edit].get("produtos", {})
    if produto_edit not in produtos_atuais:
        return

    config = produtos_atuais[produto_edit]
    cidade_atual = config.get("cidade", "")

    st.markdown("---")
    st.markdown(f"#### Editando: **{produto_edit}**")

    with st.form("form_editar_produto"):
        novo_nome = st.text_input("Novo nome do produto", value=produto_edit)
        cidade_edit = st.selectbox(
            "📍 Cidade", [""] + cidades,
            index=([""] + cidades).index(cidade_atual) if cidade_atual in cidades else 0,
            key="prod_edit_cidade_produto",
        )
        novo_skiprows = st.number_input("Skiprows", value=config.get("skiprows", 2), step=1, key="prod_edit_skiprows")
        novo_mapeamento = st.text_area(
            "Mapeamento",
            value=json.dumps(config.get("mapeamento", {}), indent=2, ensure_ascii=False),
            height=100, key="prod_edit_mapeamento",
        )
        novo_colunas_ordem = st.text_input(
            "Colunas para exibir",
            value=", ".join(config.get("colunas_ordem", [])),
            key="prod_edit_colunas_ordem",
        )
        novo_colunas_numericas = st.text_input(
            "Colunas numéricas",
            value=", ".join(config.get("colunas_para_converter", [])),
            key="prod_edit_colunas_numericas",
        )

        col1, col2 = st.columns(2)
        with col1:
            if st.form_submit_button("💾 Salvar", use_container_width=True):
                _salvar_edicao_produto(
                    construtora_edit=construtora_edit, produto_edit=produto_edit,
                    novo_nome=novo_nome, cidade_edit=cidade_edit,
                    novo_skiprows=novo_skiprows, novo_mapeamento=novo_mapeamento,
                    novo_colunas_ordem=novo_colunas_ordem,
                    novo_colunas_numericas=novo_colunas_numericas,
                )
        with col2:
            if st.form_submit_button("❌ Cancelar", use_container_width=True):
                st.session_state["editando_produto"] = None
                st.rerun()


def _salvar_edicao_produto(construtora_edit, produto_edit, novo_nome, cidade_edit,
                            novo_skiprows, novo_mapeamento, novo_colunas_ordem,
                            novo_colunas_numericas):
    try:
        dados_atuais = carregar_construtoras()
        produtos_atuais = dados_atuais[construtora_edit].get("produtos", {})

        if produto_edit in produtos_atuais:
            del produtos_atuais[produto_edit]

        mapeamento = json.loads(novo_mapeamento) if novo_mapeamento else {}
        colunas_ordem = [c.strip() for c in novo_colunas_ordem.split(",") if c.strip()]
        colunas_numericas = [c.strip() for c in novo_colunas_numericas.split(",") if c.strip()]

        produtos_atuais[novo_nome] = {
            "cidade": cidade_edit, "skiprows": novo_skiprows,
            "mapeamento": {str(k): v for k, v in mapeamento.items()},
            "colunas_ordem": colunas_ordem,
            "colunas_para_converter": colunas_numericas,
        }
        dados_atuais[construtora_edit]["produtos"] = produtos_atuais
        salvar_construtoras(dados_atuais)
        st.session_state["editando_produto"] = None
        st.success(f"✅ Produto '{novo_nome}' atualizado com sucesso!")
        st.rerun()
    except Exception as e:
        st.error(f"❌ Erro ao atualizar: {str(e)}")