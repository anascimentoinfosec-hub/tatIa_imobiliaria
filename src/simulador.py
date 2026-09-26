import streamlit as st

from src.utils import formatar_valor_br
from src.simulador_upload import renderizar_sidebar, carregar_dataframe
from src.simulador_filtros import (
    renderizar_filtros,
    aplicar_filtros,
    calcular_preco_m2,
    renderizar_tabela,
)
from src.simulador_cliente import renderizar_area_cliente
from src.simulador_cards import (
    renderizar_cards,
    renderizar_ajuste_global,
    renderizar_seletor_proposta,
)
from src.compartilhar import botoes_compartilhar


def pagina_simulador(CONSTRUTORAS, USUARIOS):
    if not CONSTRUTORAS:
        st.warning("⚠️ Nenhuma construtora cadastrada. Cadastre uma construtora primeiro.")
        return

    st.title("📊 Simulador de Crédito")

    usuario_logado = st.session_state.get("usuario_logado")

    sidebar = renderizar_sidebar(CONSTRUTORAS, USUARIOS)
    if sidebar is None:
        st.warning("⚠️ Selecione um produto para visualizar os dados.")
        return

    construtora = sidebar["construtora"]
    produto = sidebar["produto"]
    tipo_desconto = sidebar["tipo_desconto"]
    config = sidebar["config"]

    df = carregar_dataframe(construtora, produto)
    if df is None:
        st.warning(f"⚠️ Nenhuma planilha disponível para '{produto}'. Faça o upload.")
        return

    st.info(f"📂 Planilha carregada do cache: {construtora} - {produto}")
    st.session_state.df_imoveis = df

    st.markdown("---")

    filtros = renderizar_filtros(df)
    if filtros is None:
        return

    preco_col = filtros["preco_col"]
    resultado = aplicar_filtros(df, filtros)
    resultado = calcular_preco_m2(resultado, preco_col)
    renderizar_tabela(resultado, config, construtora, produto, tipo_desconto, preco_col)

    st.markdown("---")

    renderizar_area_cliente(resultado, tipo_desconto, preco_col, usuario_logado, USUARIOS)

    if st.session_state.get("simulacao_ativa"):
        sim = st.session_state.simulacao_ativa
        top = sim["top_recomendacoes"]

        st.markdown("---")

        # === SELETOR DE PROPOSTA ===
        idx_escolhido = renderizar_seletor_proposta(top)
        st.session_state.unidade_escolhida_idx = idx_escolhido

        # Define a lista de imóveis a usar (todos ou só o escolhido)
        if idx_escolhido is not None and top is not None and not top.empty:
            top_para_pdf = top.loc[[idx_escolhido]]
        else:
            top_para_pdf = top

        st.markdown("---")
        st.markdown("### 📤 Compartilhar Simulação")
        dados_pdf = _montar_dados_pdf(sim, usuario_logado, USUARIOS, tipo_desconto, top_para_pdf)
        botoes_compartilhar(sim["resumo"], sim["nome_cliente"], dados_pdf)
        # Diagnóstico financeiro
        diag = st.session_state.get("diagnostico_simulacao")
        if diag:
            with st.expander("🔍 Diagnóstico financeiro da simulação", expanded=False):
                st.markdown(f"""
                - 💰 *Parcela máxima* (comprometimento): {formatar_valor_br(diag['parcela_maxima'])}
                - 🏦 *Financiamento máximo* aprovado: {formatar_valor_br(diag['pv_maximo'])}
                - 🏠 *Valor máximo do imóvel* (financiado + entrada): *{formatar_valor_br(diag['valor_max_imovel'])}*
                
                Se nenhuma oportunidade aparecer, é porque todos os imóveis estão acima desse teto. Aumente a entrada, mude a regra (ex: MCMV) ou revise o comprometimento.
                """)

        st.markdown("---")
        renderizar_cards(
            top,
            sim["desconto_acordado"],
            sim["tipo_desconto"],
            sim["coluna_base"],
            sim["preco_col"],
            sim["nome_cliente"],
        )

        # === BOTÃO SALVAR PROPOSTA ===
        if idx_escolhido is not None:
            st.markdown("---")
            if st.button("💾 Salvar esta unidade como Proposta no Histórico",
                         use_container_width=True, type="primary"):
                _salvar_proposta(sim, top, idx_escolhido, usuario_logado, USUARIOS, tipo_desconto)
                st.success("✅ Proposta salva no histórico!")
                st.rerun()

    renderizar_ajuste_global(df, preco_col)

    st.markdown("---")
    if st.button("💬 Perguntar à BIA (IA Imobiliária)", use_container_width=True):
        st.session_state.pagina = "ChatIA"
        st.rerun()


def _montar_dados_pdf(sim, usuario_logado, USUARIOS, tipo_desconto, top_filtrado):
    """Monta o dicionário de dados para o PDF usando o top filtrado."""
    oportunidades = []

    if top_filtrado is not None and not top_filtrado.empty:
        for _, row in top_filtrado.iterrows():
            item = {}
            for col in ["UNIDADE", "TIPOLOGIA", "BLOCO", "PAVTO", "ANDAR",
                        "AVALIAÇÃO", "PREÇO", "valor_base", "parcela_estimada"]:
                if col in row.index:
                    val = row[col]
                    if hasattr(val, "item"):
                        val = val.item()
                    item[col] = val
            oportunidades.append(item)

    nome_gerente = ""
    if usuario_logado and usuario_logado in USUARIOS:
        nome_gerente = USUARIOS[usuario_logado].get("nome", "")

    return {
        "nome_cliente": sim.get("nome_cliente", ""),
        "renda": 0,
        "entrada": 0,
        "bairro": "",
        "origem": "",
        "desconto": sim.get("desconto_acordado", 0),
        "tipo_desconto": tipo_desconto,
        "nome_gerente": nome_gerente,
        "oportunidades": oportunidades,
    }


def _salvar_proposta(sim, top, idx_escolhido, usuario_logado, USUARIOS, tipo_desconto):
    """Salva um registro de proposta (só 1 unidade) no histórico."""
    from src.simulacoes_storage import salvar_simulacao

    top_unit = top.loc[[idx_escolhido]]
    nome_gerente = USUARIOS[usuario_logado]["nome"] if usuario_logado in USUARIOS else ""

    salvar_simulacao(
        nome_cliente=sim["nome_cliente"],
        renda=0,
        entrada=0,
        bairro="",
        origem="",
        desconto=sim.get("desconto_acordado", 0),
        tipo_desconto=tipo_desconto,
        gerente=nome_gerente,
        top_recomendacoes=top_unit,
    )