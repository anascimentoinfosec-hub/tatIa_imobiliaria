import streamlit as st


def mostrar_msg(mensagem, tipo="sucesso", icone=None):
    """
    Adiciona uma mensagem à fila. Ela sobrevive ao st.rerun() e é exibida
    no topo da próxima página que chamar `exibir_mensagem_pendente()`.
    """
    if not mensagem:
        return
    fila = st.session_state.get("_mensagens_pendentes", [])
    fila.append((mensagem, tipo, icone))
    st.session_state["_mensagens_pendentes"] = fila


def exibir_mensagem_pendente():
    """Renderiza e limpa todas as mensagens pendentes."""
    fila = st.session_state.get("_mensagens_pendentes", [])
    if not fila:
        return

    st.session_state["_mensagens_pendentes"] = []

    icones_padrao = {
        "sucesso": "✅",
        "erro": "❌",
        "aviso": "⚠️",
        "info": "💡",
    }

    for mensagem, tipo, icone in fila:
        icone_final = icone or icones_padrao.get(tipo, "ℹ️")
        texto = f"{icone_final} {mensagem}" if icone_final not in mensagem else mensagem

        if tipo == "sucesso":
            st.success(texto)
        elif tipo == "erro":
            st.error(texto)
        elif tipo == "aviso":
            st.warning(texto)
        else:
            st.info(texto)