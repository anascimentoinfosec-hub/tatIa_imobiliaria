import streamlit as st
import json
from src.construtoras_storage import salvar_construtoras
from src.bia_planilha import analisar_planilha_com_bia
from src.planilha_processor import processar_planilha_e_salvar_cache
from src.mensagens import exibir_mensagem_pendente, mostrar_msg

def renderizar_aba_adicionar(CONSTRUTORAS, cidades):
    st.markdown("### Adicionar Nova Construtora")

    with st.expander("🤖 Preencher automaticamente com a BIA (opcional)", expanded=False):
        st.caption(
            "Suba a planilha da construtora, clique em **Analisar com BIA** "
            "e os campos serão preenchidos. A mesma planilha será salva no cache."
        )

        uploaded = st.file_uploader(
            "Planilha de referência",
            type=["xlsx", "xls", "csv"],
            key="bia_upload_construtora",
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
                    st.session_state["bia_arquivo_bytes"] = uploaded.getvalue()
                    st.session_state["bia_arquivo_nome"] = uploaded.name
                    st.session_state["bia_arquivo_produto_sugerido"] = _sugerir_nome_produto(uploaded.name)

                    # Seta direto nas KEYS DOS WIDGETS
                    st.session_state["nova_produto_mapeamento_input_final"] = json.dumps(
                        resultado.get("mapeamento", {}), indent=2, ensure_ascii=False
                    )
                    st.session_state["nova_produto_colunas_ordem_input_final"] = ", ".join(
                        resultado.get("colunas_ordem", [])
                    )
                    st.session_state["nova_produto_colunas_numericas_input_final"] = ", ".join(
                        resultado.get("colunas_monetarias", []) + resultado.get("colunas_numericas", [])
                    )
                    st.session_state["nova_skiprows_input_final"] = int(
                        resultado.get("skiprows", resultado.get("header_row", 0))
                    )
                    st.session_state["nova_produto_nome"] = st.session_state["bia_arquivo_produto_sugerido"]

                    st.success("✅ BIA preencheu os campos! Revise antes de salvar.")
                    if resultado.get("observacoes"):
                        st.info(f"💬 **Observação da BIA:** {resultado['observacoes']}")
                    st.rerun()

    # === FORMULÁRIO ===
    nome = st.text_input("Nome da Construtora", key="nova_construtora_nome", placeholder="Ex: Construtora XYZ")
    tipo_desconto = st.selectbox(
        "💡 Desconto será aplicado sobre:",
        ["AVALIAÇÃO", "PREÇO"],
        key="nova_construtora_tipo_desconto",
    )

    st.markdown("---")
    st.markdown("**📦 Produto inicial**")
    st.caption("Se preencher, a planilha analisada pela BIA será salva automaticamente no cache.")

    produto_nome = st.text_input("Nome do Produto", key="nova_produto_nome", placeholder="Ex: Torre A")

    opcoes_cidade = [""] + cidades
    cidade_selecionada = st.selectbox("📍 Cidade", opcoes_cidade, key="nova_cidade_produto")

    skiprows = st.number_input(
        "Linhas para pular antes do cabeçalho",
        min_value=0, step=1, key="nova_skiprows_input_final",
    )

    mapeamento_str = st.text_area(
        "Mapeamento (índice: nome)",
        placeholder='{"0": "UNIDADE", "1": "PREÇO"}',
        height=120, key="nova_produto_mapeamento_input_final",
    )

    colunas_ordem_str = st.text_input(
        "Colunas para exibir (separadas por vírgula)",
        placeholder="UNIDADE, PAVTO, PREÇO",
        key="nova_produto_colunas_ordem_input_final",
    )

    colunas_numericas_str = st.text_input(
        "Colunas monetárias/numéricas (separadas por vírgula)",
        placeholder="PREÇO, M², ANDAR",
        key="nova_produto_colunas_numericas_input_final",
    )

    if st.button("➕ Adicionar Construtora", use_container_width=True, type="primary", key="btn_adicionar_construtora"):
        _processar_nova_construtora(
            CONSTRUTORAS=CONSTRUTORAS, nome=nome, tipo_desconto=tipo_desconto,
            produto_nome=produto_nome, cidade_selecionada=cidade_selecionada,
            skiprows=skiprows, mapeamento_str=mapeamento_str,
            colunas_ordem_str=colunas_ordem_str, colunas_numericas_str=colunas_numericas_str,
        )


def _sugerir_nome_produto(nome_arquivo):
    base = nome_arquivo.rsplit(".", 1)[0]
    return base.replace("_", " ").replace("-", " ").title()


def _processar_nova_construtora(CONSTRUTORAS, nome, tipo_desconto, produto_nome,
                                 cidade_selecionada, skiprows, mapeamento_str,
                                 colunas_ordem_str, colunas_numericas_str):
    if not nome:
        st.warning("⚠️ Digite o nome da construtora!")
        return

    if produto_nome and not mapeamento_str.strip():
        st.error("❌ **Mapeamento vazio.** Preencha ou use a BIA antes de salvar.")
        return

    if produto_nome and not cidade_selecionada:
        st.error("❌ Selecione a **cidade** do produto.")
        return

    try:
        nova_construtora = {"tipo_desconto": tipo_desconto, "produtos": {}}
        config_produto = None

        if produto_nome and cidade_selecionada:
            try:
                mapeamento = json.loads(mapeamento_str)
            except json.JSONDecodeError:
                st.error("❌ O mapeamento não é um JSON válido.")
                return

            if not mapeamento:
                st.error("❌ O mapeamento está vazio.")
                return

            colunas_ordem = [c.strip() for c in colunas_ordem_str.split(",") if c.strip()]
            colunas_numericas = [c.strip() for c in colunas_numericas_str.split(",") if c.strip()]

            config_produto = {
                "cidade": cidade_selecionada,
                "skiprows": skiprows,
                "mapeamento": {str(k): v for k, v in mapeamento.items()},
                "colunas_ordem": colunas_ordem,
                "colunas_para_converter": colunas_numericas,
            }
            nova_construtora["produtos"][produto_nome] = config_produto

        if nome in CONSTRUTORAS:
            st.error(f"❌ Já existe uma construtora com o nome '{nome}'.")
            return

        CONSTRUTORAS[nome] = nova_construtora
        salvar_construtoras(CONSTRUTORAS)

        msg_cache = ""
        if produto_nome and config_produto and "bia_arquivo_bytes" in st.session_state:
            ok, msg = processar_planilha_e_salvar_cache(
                file_bytes=st.session_state["bia_arquivo_bytes"],
                file_name=st.session_state["bia_arquivo_nome"],
                config=config_produto, construtora=nome, produto=produto_nome,
            )
            msg_cache = msg if ok else f"⚠️ {msg}"

        # MARCA FLAG para mostrar mensagem após rerun
        mostrar_msg(f"Construtora **{nome}** adicionada com sucesso!", "sucesso")
        if msg_cache:
            mostrar_msg(msg_cache, "info")

        _limpar_chaves_form_construtora()
        st.rerun()
    except Exception as e:
        st.error(f"❌ Erro: {str(e)}")


def _limpar_chaves_form_construtora():
    keys = [
        "nova_construtora_nome", "nova_construtora_tipo_desconto",
        "nova_produto_nome", "nova_cidade_produto",
        "nova_skiprows_input", "nova_skiprows_input_final",
        "nova_produto_mapeamento_input", "nova_produto_mapeamento_input_final",
        "nova_produto_colunas_ordem_input", "nova_produto_colunas_ordem_input_final",
        "nova_produto_colunas_numericas_input", "nova_produto_colunas_numericas_input_final",
        "bia_arquivo_bytes", "bia_arquivo_nome", "bia_arquivo_resultado",
        "bia_arquivo_produto_sugerido",
    ]
    for k in keys:
        if k in st.session_state:
            del st.session_state[k]