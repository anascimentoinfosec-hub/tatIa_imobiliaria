import streamlit as st
import json
from src.construtoras_storage import carregar_construtoras, salvar_construtoras


def renderizar_aba_produtos(cidades):
    """Renderiza a aba 'Gerenciar Produtos'."""
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


# =========================================================
# SELEÇÃO DE CONSTRUTORA
# =========================================================
def _selecionar_construtora(construtoras_lista):
    if ("construtora_edit" not in st.session_state
            or st.session_state.construtora_edit not in construtoras_lista):
        st.session_state.construtora_edit = construtoras_lista[0]

    index_atual = construtoras_lista.index(st.session_state.construtora_edit) \
        if st.session_state.construtora_edit in construtoras_lista else 0

    construtora_edit = st.selectbox(
        "Selecione a construtora",
        construtoras_lista,
        index=index_atual,
        key="select_construtora_produtos",
    )
    st.session_state.construtora_edit = construtora_edit
    return construtora_edit


# =========================================================
# EDITOR DE TIPO DE DESCONTO
# =========================================================
def _renderizar_editor_desconto(construtora_edit, tipo_desconto):
    col_td1, col_td2 = st.columns([2, 1])
    with col_td1:
        novo_tipo_desconto = st.selectbox(
            "💡 Desconto será aplicado sobre:",
            ["AVALIAÇÃO", "PREÇO"],
            index=0 if tipo_desconto == "AVALIAÇÃO" else 1,
            key="edit_tipo_desconto",
        )
    with col_td2:
        st.write("")
        st.write("")
        if st.button("💾 Salvar regra", use_container_width=True, key="btn_salvar_regra"):
            dados_atuais = carregar_construtoras()
            dados_atuais[construtora_edit]["tipo_desconto"] = novo_tipo_desconto
            salvar_construtoras(dados_atuais)
            st.success(f"✅ Regra alterada para: {novo_tipo_desconto}")
            st.rerun()


# =========================================================
# LISTAGEM DE PRODUTOS
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
            if st.button("✏️ Editar", key=f"edit_prod_{produto}"):
                st.session_state["editando_produto"] = produto
                st.rerun()
        with col4:
            if st.button("🗑️ Excluir", key=f"del_prod_{produto}"):
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
# ADICIONAR PRODUTO
# =========================================================
def _renderizar_form_adicionar_produto(construtora_edit, cidades, tipo_desconto):
    st.markdown("#### Adicionar Produto")

    novo_produto = st.text_input("Nome do Produto", placeholder="Ex: Torre A", key="novo_produto_nome")
    nova_cidade = st.selectbox("📍 Cidade", [""] + cidades, key="nova_cidade_produto")
    novo_skiprows = st.number_input("Skiprows", min_value=0, value=2, step=1, key="novo_produto_skiprows")
    novo_mapeamento = st.text_area(
        "Mapeamento (índice: nome)",
        placeholder='{"0": "UNIDADE", "1": "PAVTO", "2": "PREÇO"}',
        height=80,
        key="novo_produto_mapeamento",
    )
    novo_colunas_ordem = st.text_input(
        "Colunas para exibir (separadas por vírgula)",
        placeholder="UNIDADE, PAVTO, PREÇO",
        key="novo_produto_colunas_ordem",
    )
    novo_colunas_numericas = st.text_input(
        "Colunas numéricas (separadas por vírgula)",
        placeholder="PREÇO, M², ANDAR",
        key="novo_produto_colunas_numericas",
    )

    if st.button("💾 Salvar Produto", use_container_width=True, key="btn_salvar_produto"):
        _salvar_novo_produto(
            construtora_edit=construtora_edit,
            tipo_desconto=tipo_desconto,
            novo_produto=novo_produto,
            nova_cidade=nova_cidade,
            novo_skiprows=novo_skiprows,
            novo_mapeamento=novo_mapeamento,
            novo_colunas_ordem=novo_colunas_ordem,
            novo_colunas_numericas=novo_colunas_numericas,
        )


def _salvar_novo_produto(construtora_edit, tipo_desconto, novo_produto, nova_cidade,
                          novo_skiprows, novo_mapeamento, novo_colunas_ordem,
                          novo_colunas_numericas):
    if not novo_produto:
        st.warning("⚠️ Digite o nome do produto!")
        return

    try:
        dados_atuais = carregar_construtoras()
        if construtora_edit not in dados_atuais:
            dados_atuais[construtora_edit] = {"tipo_desconto": tipo_desconto, "produtos": {}}

        produtos_atuais = dados_atuais[construtora_edit].get("produtos", {})

        mapeamento = json.loads(novo_mapeamento) if novo_mapeamento else {}
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

        for key in ["novo_produto_nome", "novo_produto_skiprows", "novo_produto_mapeamento",
                    "novo_produto_colunas_ordem", "novo_produto_colunas_numericas",
                    "nova_cidade_produto"]:
            if key in st.session_state:
                del st.session_state[key]

        st.success(f"✅ Produto '{novo_produto}' adicionado com sucesso!")
        st.rerun()
    except json.JSONDecodeError:
        st.error("❌ Erro no mapeamento: formato JSON inválido!")
    except Exception as e:
        st.error(f"❌ Erro ao adicionar produto: {str(e)}")


# =========================================================
# EDITAR PRODUTO
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
            "📍 Cidade",
            [""] + cidades,
            index=([""] + cidades).index(cidade_atual) if cidade_atual in cidades else 0,
            key="edit_cidade_produto",
        )
        novo_skiprows = st.number_input("Skiprows", value=config.get("skiprows", 2), step=1, key="edit_skiprows")
        novo_mapeamento = st.text_area(
            "Mapeamento",
            value=json.dumps(config.get("mapeamento", {}), indent=2, ensure_ascii=False),
            height=100,
            key="edit_mapeamento",
        )
        novo_colunas_ordem = st.text_input(
            "Colunas para exibir",
            value=", ".join(config.get("colunas_ordem", [])),
            key="edit_colunas_ordem",
        )
        novo_colunas_numericas = st.text_input(
            "Colunas numéricas",
            value=", ".join(config.get("colunas_para_converter", [])),
            key="edit_colunas_numericas",
        )

        col1, col2 = st.columns(2)
        with col1:
            if st.form_submit_button("💾 Salvar", use_container_width=True):
                _salvar_edicao_produto(
                    construtora_edit=construtora_edit,
                    produto_edit=produto_edit,
                    novo_nome=novo_nome,
                    cidade_edit=cidade_edit,
                    novo_skiprows=novo_skiprows,
                    novo_mapeamento=novo_mapeamento,
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
            "cidade": cidade_edit,
            "skiprows": novo_skiprows,
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