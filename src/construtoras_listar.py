import streamlit as st
from src.construtoras_storage import carregar_construtoras, salvar_construtoras


def renderizar_aba_listar(CONSTRUTORAS):
    """Renderiza a aba 'Listar' com botão de excluir."""
    st.markdown("### Construtoras e Produtos")

    # === MENSAGEM DE SUCESSO/ERRO PÓS-EXCLUSÃO ===
    if st.session_state.get("msg_exclusao"):
        msg = st.session_state.pop("msg_exclusao")
        if "✅" in msg:
            st.success(msg)
        else:
            st.error(msg)

    if not CONSTRUTORAS:
        st.info("Nenhuma construtora cadastrada.")
        return

    for construtora, dados in list(CONSTRUTORAS.items()):
        _renderizar_card_construtora(construtora, dados)


def _renderizar_card_construtora(construtora, dados):
    tipo_desconto = dados.get("tipo_desconto", "AVALIAÇÃO")
    produtos = dados.get("produtos", {})
    qtd_produtos = len(produtos)

    titulo = f"🏢 {construtora}  •  💡 {tipo_desconto}  •  📦 {qtd_produtos} produto(s)"

    with st.expander(titulo):
        # Produtos
        if produtos:
            for produto, config in produtos.items():
                cidade = config.get("cidade", "Não definida")
                colunas = len(config.get("colunas_ordem", []))
                st.write(f"  📄 **{produto}** — 📍 {cidade} — {colunas} colunas")
        else:
            st.caption("  ⚠️ Nenhum produto cadastrado")

        st.markdown("---")

        # Botão de excluir
        col1, col2 = st.columns([4, 1])
        with col2:
            if st.button("🗑️ Excluir", key=f"del_construtora_{construtora}", use_container_width=True):
                st.session_state["confirmar_exclusao"] = construtora
                st.rerun()

        # Confirmação
        if st.session_state.get("confirmar_exclusao") == construtora:
            st.warning(
                f"⚠️ **Tem certeza?** Excluir **{construtora}** vai apagar "
                f"a construtora e seus {qtd_produtos} produto(s)."
            )
            col_sim, col_nao = st.columns(2)
            with col_sim:
                if st.button("✅ Sim, excluir", key=f"confirm_sim_{construtora}",
                             use_container_width=True, type="primary"):
                    _excluir_construtora(construtora)
                    st.session_state.pop("confirmar_exclusao", None)
                    st.rerun()
            with col_nao:
                if st.button("❌ Cancelar", key=f"confirm_nao_{construtora}",
                             use_container_width=True):
                    st.session_state.pop("confirmar_exclusao", None)
                    st.rerun()


def _excluir_construtora(construtora):
    try:
        dados_atuais = carregar_construtoras()
        if construtora in dados_atuais:
            del dados_atuais[construtora]
            salvar_construtoras(dados_atuais)
            st.session_state["msg_exclusao"] = f"✅ Construtora **{construtora}** excluída com sucesso!"
    except Exception as e:
        st.session_state["msg_exclusao"] = f"❌ Erro ao excluir: {str(e)}"