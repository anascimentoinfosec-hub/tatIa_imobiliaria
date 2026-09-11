import streamlit as st
import json
from src.construtoras_storage import salvar_construtoras


def renderizar_aba_adicionar(CONSTRUTORAS, cidades):
    """Renderiza a aba 'Adicionar Construtora'."""
    st.markdown("### Adicionar Nova Construtora")

    with st.form("form_nova_construtora"):
        nome = st.text_input("Nome da Construtora")
        tipo_desconto = st.selectbox("💡 Desconto será aplicado sobre:", ["AVALIAÇÃO", "PREÇO"])

        produto_nome = st.text_input("Nome do Produto (opcional)", placeholder="Ex: Torre A")
        opcoes_cidade = [""] + cidades
        cidade_selecionada = st.selectbox("📍 Cidade", opcoes_cidade)
        skiprows = st.number_input("Linhas para pular", min_value=0, value=2, step=1)
        mapeamento_str = st.text_area(
            "Mapeamento (índice: nome)",
            placeholder='{"0": "UNIDADE", "1": "PREÇO"}',
            height=80,
        )
        colunas_ordem_str = st.text_input("Colunas para exibir", placeholder="UNIDADE, PAVTO, PREÇO")
        colunas_numericas_str = st.text_input(
            "Colunas numéricas (apenas valores monetários)", placeholder="PREÇO, M²"
        )

        if st.form_submit_button("➕ Adicionar Construtora", use_container_width=True):
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
        st.success(f"✅ Construtora '{nome}' adicionada com sucesso!")
    except json.JSONDecodeError:
        st.error("❌ Erro no mapeamento: formato JSON inválido!")
    except Exception as e:
        st.error(f"❌ Erro: {str(e)}")