import streamlit as st
import json
from src.construtoras_storage import salvar_construtoras
from src.bia_planilha import analisar_planilha_com_bia


def renderizar_aba_adicionar(CONSTRUTORAS, cidades):
    """Renderiza a aba 'Adicionar Construtora' com análise da BIA."""
    st.markdown("### Adicionar Nova Construtora")

    # =========================================================
    # BLOCO BIA — Analisar planilha e preencher automaticamente
    # =========================================================
    with st.expander("🤖 Preencher automaticamente com a BIA (opcional)", expanded=False):
        st.caption(
            "Suba a planilha da construtora e clique em **Analisar com BIA**. "
            "Ela identificará a estrutura e preencherá os campos abaixo."
        )

        uploaded = st.file_uploader(
            "Planilha de referência",
            type=["xlsx", "xls", "csv"],
            key="bia_upload_construtora",
            help="A planilha não é salva — serve apenas para a BIA analisar.",
        )

        if st.button("🤖 Analisar com BIA", use_container_width=True, key="btn_bia_construtora"):
            if uploaded is None:
                st.warning("⚠️ Faça upload de uma planilha primeiro.")
            else:
                with st.spinner("A BIA está analisando a planilha..."):
                    resultado = analisar_planilha_com_bia(uploaded)

                if "erro" in resultado:
                    st.error(f"❌ {resultado['erro']}")
                else:
                    # Preenche o session_state com as sugestões
                    st.session_state["nova_produto_nome"] = _sugerir_nome_produto(uploaded.name)
                    st.session_state["nova_produto_mapeamento_input"] = json.dumps(
                        resultado.get("mapeamento", {}), indent=2, ensure_ascii=False
                    )
                    st.session_state["nova_produto_colunas_ordem_input"] = ", ".join(
                        resultado.get("colunas_ordem", [])
                    )
                    st.session_state["nova_produto_colunas_numericas_input"] = ", ".join(
                        resultado.get("colunas_monetarias", [])
                        + resultado.get("colunas_numericas", [])
                    )
                    st.session_state["nova_skiprows_input"] = int(
                        resultado.get("skiprows", resultado.get("header_row", 0))
                    )
                    st.session_state["bia_obs_construtora"] = resultado.get("observacoes", "")

                    st.success("✅ BIA preencheu os campos abaixo! Revise antes de salvar.")
                    if resultado.get("observacoes"):
                        st.info(f"💬 **Observação da BIA:** {resultado['observacoes']}")
                    st.rerun()

    # =========================================================
    # FORMULÁRIO (fora do st.form para permitir preenchimento)
    # =========================================================
    nome = st.text_input(
        "Nome da Construtora",
        key="nova_construtora_nome",
        placeholder="Ex: Construtora XYZ",
    )

    tipo_desconto = st.selectbox(
        "💡 Desconto será aplicado sobre:",
        ["AVALIAÇÃO", "PREÇO"],
        key="nova_construtora_tipo_desconto",
    )

    st.markdown("---")
    st.markdown("**📦 Produto inicial (opcional)**")
    st.caption("Você pode criar a construtora sem produto e adicionar depois em 'Gerenciar Produtos'.")

    produto_nome = st.text_input(
        "Nome do Produto",
        key="nova_produto_nome",
        placeholder="Ex: Torre A",
    )

    opcoes_cidade = [""] + cidades
    cidade_selecionada = st.selectbox(
        "📍 Cidade",
        opcoes_cidade,
        key="nova_cidade_produto",
    )

    skiprows_default = st.session_state.get("nova_skiprows_input", 2)
    skiprows = st.number_input(
        "Linhas para pular antes do cabeçalho",
        min_value=0,
        value=int(skiprows_default),
        step=1,
        key="nova_skiprows_input_final",
    )

    mapeamento_default = st.session_state.get("nova_produto_mapeamento_input", "")
    mapeamento_str = st.text_area(
        "Mapeamento (índice: nome)",
        value=mapeamento_default,
        placeholder='{"0": "UNIDADE", "1": "PREÇO"}',
        height=120,
        key="nova_produto_mapeamento_input_final",
    )

    colunas_ordem_default = st.session_state.get("nova_produto_colunas_ordem_input", "")
    colunas_ordem_str = st.text_input(
        "Colunas para exibir (separadas por vírgula)",
        value=colunas_ordem_default,
        placeholder="UNIDADE, PAVTO, PREÇO",
        key="nova_produto_colunas_ordem_input_final",
    )

    colunas_num_default = st.session_state.get("nova_produto_colunas_numericas_input", "")
    colunas_numericas_str = st.text_input(
        "Colunas monetárias/numéricas (separadas por vírgula)",
        value=colunas_num_default,
        placeholder="PREÇO, M², ANDAR",
        key="nova_produto_colunas_numericas_input_final",
    )

    if st.button("➕ Adicionar Construtora", use_container_width=True, type="primary", key="btn_adicionar_construtora"):
        _processar_nova_construtora(
            CONSTRUTORAS=CONSTRUTORAS,
            nome=nome,
            tipo_desconto=tipo_desconto,
            produto_nome=produto_nome,
            cidade_selecionada=cidade_selecionada,
            skiprows=skiprows,
            mapeamento_str=mapeamento_str,
            colunas_ordem_str=colunas_ordem_str,
            colunas_numericas_str=colunas_numericas_str,
        )


# =========================================================
# HELPERS
# =========================================================
def _sugerir_nome_produto(nome_arquivo):
    """Sugere um nome de produto a partir do nome do arquivo."""
    base = nome_arquivo.rsplit(".", 1)[0]
    return base.replace("_", " ").replace("-", " ").title()


def _processar_nova_construtora(CONSTRUTORAS, nome, tipo_desconto, produto_nome,
                                 cidade_selecionada, skiprows, mapeamento_str,
                                 colunas_ordem_str, colunas_numericas_str):
    """Processa e salva uma nova construtora."""
    if not nome:
        st.warning("⚠️ Digite o nome da construtora!")
        return

    try:
        nova_construtora = {"tipo_desconto": tipo_desconto, "produtos": {}}

        if produto_nome and cidade_selecionada:
            mapeamento = json.loads(mapeamento_str) if mapeamento_str else {}
            colunas_ordem = [c.strip() for c in colunas_ordem_str.split(",") if c.strip()]
            colunas_numericas = [c.strip() for c in colunas_numericas_str.split(",") if c.strip()]

            nova_construtora["produtos"][produto_nome] = {
                "cidade": cidade_selecionada,
                "skiprows": skiprows,
                "mapeamento": {str(k): v for k, v in mapeamento.items()},
                "colunas_ordem": colunas_ordem,
                "colunas_para_converter": colunas_numericas,
            }

        CONSTRUTORAS[nome] = nova_construtora
        salvar_construtoras(CONSTRUTORAS)

        # Limpa chaves do session_state
        _limpar_chaves_form_construtora()

        st.success(f"✅ Construtora '{nome}' adicionada com sucesso!")
        st.rerun()
    except json.JSONDecodeError:
        st.error("❌ Erro no mapeamento: formato JSON inválido!")
    except Exception as e:
        st.error(f"❌ Erro: {str(e)}")


def _limpar_chaves_form_construtora():
    """Limpa as chaves do session_state usadas no formulário."""
    keys = [
        "nova_construtora_nome", "nova_construtora_tipo_desconto",
        "nova_produto_nome", "nova_cidade_produto",
        "nova_skiprows_input", "nova_skiprows_input_final",
        "nova_produto_mapeamento_input", "nova_produto_mapeamento_input_final",
        "nova_produto_colunas_ordem_input", "nova_produto_colunas_ordem_input_final",
        "nova_produto_colunas_numericas_input", "nova_produto_colunas_numericas_input_final",
        "bia_obs_construtora",
    ]
    for k in keys:
        if k in st.session_state:
            del st.session_state[k]