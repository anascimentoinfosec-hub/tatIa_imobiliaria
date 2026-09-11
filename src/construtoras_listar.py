import streamlit as st


def renderizar_aba_listar(CONSTRUTORAS):
    """Renderiza a aba 'Listar' com as construtoras e produtos cadastrados."""
    st.markdown("### Construtoras e Produtos")

    if not CONSTRUTORAS:
        st.info("Nenhuma construtora cadastrada.")
        return

    for construtora, dados in CONSTRUTORAS.items():
        with st.expander(f"🏢 {construtora}"):
            tipo_desconto = dados.get("tipo_desconto", "AVALIAÇÃO")
            st.caption(f"💡 Desconto sobre: **{tipo_desconto}**")

            produtos = dados.get("produtos", {})
            if produtos:
                for produto, config in produtos.items():
                    cidade = config.get("cidade", "Não definida")
                    st.write(f"  📄 **{produto}** - 📍 {cidade}")
                    st.caption(f"     {len(config.get('colunas_ordem', []))} colunas")
            else:
                st.caption("  ⚠️ Nenhum produto cadastrado")