import streamlit as st
from src.construtoras_storage import (
    carregar_cidades,
    salvar_cidades,
    carregar_construtoras,
    obter_cidades_em_uso,
)


def renderizar_aba_cidades():
    """Renderiza a aba 'Gerenciar Cidades'."""
    st.markdown("### 📍 Gerenciar Cidades")
    st.markdown("Gerencie a lista de cidades disponíveis para os produtos.")

    cidades_atual = carregar_cidades()
    construtoras_atual = carregar_construtoras()
    cidades_em_uso = obter_cidades_em_uso(construtoras_atual)

    _renderizar_form_adicionar(cidades_atual)

    st.markdown("---")
    st.markdown("#### Lista de Cidades Cadastradas")
    _renderizar_lista(cidades_atual, cidades_em_uso)


def _renderizar_form_adicionar(cidades_atual):
    """Form de adicionar nova cidade."""
    col_add1, col_add2 = st.columns([3, 1])

    with col_add1:
        nova_cidade_input = st.text_input(
            "Digite o nome da nova cidade",
            placeholder="Ex: Belford Roxo",
            key="nova_cidade_input",
        )

    with col_add2:
        if st.button("➕ Adicionar Cidade", use_container_width=True):
            if not nova_cidade_input:
                st.warning("⚠️ Digite o nome da cidade!")
                return

            cidade_limpa = nova_cidade_input.strip()

            if cidade_limpa in cidades_atual:
                st.warning(f"⚠️ Cidade '{cidade_limpa}' já existe!")
                return

            cidades_atual.append(cidade_limpa)
            salvar_cidades(cidades_atual)
            st.success(f"✅ Cidade '{cidade_limpa}' adicionada com sucesso!")
            st.rerun()


def _renderizar_lista(cidades_atual, cidades_em_uso):
    """Lista as cidades com opção de remover (se não estiverem em uso)."""
    if not cidades_atual:
        st.info("Nenhuma cidade cadastrada.")
        return

    for cidade in cidades_atual:
        col1, col2, col3 = st.columns([3, 1, 1])

        with col1:
            st.write(f"📍 {cidade}")

        with col2:
            if cidade in cidades_em_uso:
                st.caption("🔒 Em uso")
            else:
                st.caption("")

        with col3:
            if cidade in cidades_em_uso:
                st.button(
                    "🗑️",
                    key=f"del_cidade_{cidade}",
                    disabled=True,
                    help="Cidade em uso",
                )
            else:
                if st.button("🗑️ Remover", key=f"del_cidade_{cidade}"):
                    cidades_atual.remove(cidade)
                    salvar_cidades(cidades_atual)
                    st.success(f"✅ Cidade '{cidade}' removida com sucesso!")
                    st.rerun()