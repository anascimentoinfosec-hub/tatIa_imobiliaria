import streamlit as st
from src.origens_storage import carregar_origens, salvar_origens


def renderizar_gestao_origens():
    """Tela de gestão das origens do cliente (adicionar/remover)."""
    st.markdown("### 🎯 Origens do Cliente")
    st.caption("Gerencie as opções que aparecerão no combo 'Origem do Cliente'.")

    origens = carregar_origens()

    # Form de adicionar
    col1, col2 = st.columns([3, 1])
    with col1:
        nova_origem = st.text_input(
            "Nova origem",
            placeholder="Ex: Facebook Ads, Instagram, Evento...",
            key="nova_origem_input",
            help="Digite o nome de uma nova origem para cadastrar.",
        )
    with col2:
        st.write("")
        st.write("")
        if st.button("➕ Adicionar", use_container_width=True, key="btn_add_origem"):
            if not nova_origem.strip():
                st.warning("⚠️ Digite o nome da origem!")
            elif nova_origem.strip() in origens:
                st.warning(f"⚠️ Origem '{nova_origem}' já existe!")
            else:
                origens.append(nova_origem.strip())
                salvar_origens(origens)
                st.success(f"✅ Origem '{nova_origem}' adicionada!")
                st.rerun()

    st.markdown("---")
    st.markdown("#### Origens cadastradas")

    if not origens:
        st.info("Nenhuma origem cadastrada.")
        return

    for origem in origens:
        col_a, col_b = st.columns([4, 1])
        with col_a:
            st.write(f"🎯 {origem}")
        with col_b:
            if st.button("🗑️ Remover", key=f"del_origem_{origem}", use_container_width=True):
                origens.remove(origem)
                salvar_origens(origens)
                st.success(f"✅ Origem '{origem}' removida!")
                st.rerun()