import streamlit as st

from src.simulador_upload import carregar_todas_planilhas, renderizar_sidebar_resumo
from src.simulador_cliente import renderizar_area_cliente
from src.simulador_cards import (
    renderizar_cards,
    renderizar_ajuste_global,
    renderizar_seletor_proposta,
    renderizar_refinamento,
)
from src.compartilhar import botoes_compartilhar


def pagina_simulador(CONSTRUTORAS, USUARIOS):
    if not CONSTRUTORAS:
        st.warning("⚠️ Nenhuma construtora cadastrada. Cadastre uma primeiro.")
        return

    st.title("🏢 Simulador de Entrada de Construtora")
    st.caption("Analise o potencial do cliente em **todas as construtoras** disponíveis.")

    usuario_logado = st.session_state.get("usuario_logado")

    # ---------- 1. Carrega TODAS as planilhas ----------
    df_total, resumo = carregar_todas_planilhas(CONSTRUTORAS)

    # Sidebar de resumo
    renderizar_sidebar_resumo(CONSTRUTORAS)

    if df_total is None or df_total.empty:
        st.warning("⚠️ Nenhuma planilha em cache. Peça ao gerente para subir planilhas.")
        return

    st.info(f"📦 {len(resumo)} produto(s) • {len(df_total)} unidades totais em cache")

    # ---------- 2. Área do cliente ----------
    renderizar_area_cliente(df_total, usuario_logado, USUARIOS)

    # ---------- 3. Resultados (se análise ativa) ----------
    if st.session_state.get("simulacao_ativa"):
        sim = st.session_state.simulacao_ativa

        st.markdown("---")

        # Refinamento
        top_refinado = renderizar_refinamento()
        sim["top_recomendacoes"] = top_refinado

        # Seletor de proposta
        idx_escolhido = renderizar_seletor_proposta(top_refinado)
        st.session_state.unidade_escolhida_idx = idx_escolhido

        if idx_escolhido is not None and top_refinado is not None and not top_refinado.empty:
            top_para_pdf = top_refinado.loc[[idx_escolhido]]
        else:
            top_para_pdf = top_refinado

        st.markdown("---")
        st.markdown("### 📤 Compartilhar Simulação")
        dados_pdf = _montar_dados_pdf(sim, usuario_logado, USUARIOS, top_para_pdf)
        botoes_compartilhar(sim["resumo"], sim["nome_cliente"], dados_pdf)

        st.markdown("---")
        renderizar_cards(
            top_refinado,
            sim["desconto_acordado"],
            sim["tipo_desconto"],
            sim["coluna_base"],
            sim["preco_col"],
            sim["nome_cliente"],
        )

        if idx_escolhido is not None:
            st.markdown("---")
            if st.button("💾 Salvar esta unidade como Proposta",
                         use_container_width=True, type="primary"):
                _salvar_proposta(sim, top_refinado, idx_escolhido, usuario_logado, USUARIOS)
                st.success("✅ Proposta salva no histórico!")
                st.rerun()

        st.markdown("---")
        renderizar_ajuste_global(df_total, "PREÇO")

    st.markdown("---")
    if st.button("💬 Perguntar à BIA (IA Imobiliária)", use_container_width=True):
        st.session_state.pagina = "ChatIA"
        st.rerun()


def _montar_dados_pdf(sim, usuario_logado, USUARIOS, top_filtrado):
    oportunidades = []

    if top_filtrado is not None and not top_filtrado.empty:
        for _, row in top_filtrado.iterrows():
            item = {}
            for col in row.index:
                col_str = str(col)
                if col_str.startswith("_"):
                    item[col_str] = str(row[col])
                elif col_str in ["UNIDADE", "TIPOLOGIA", "BLOCO", "PAVTO", "ANDAR",
                                  "AVALIAÇÃO", "PREÇO", "valor_base",
                                  "VALOR_DA_AVALIACAO", "VALOR_DO_IMOVEL"]:
                    val = row[col]
                    if hasattr(val, "item"):
                        val = val.item()
                    item[col_str] = val
            oportunidades.append(item)

    nome_gerente = ""
    if usuario_logado and usuario_logado in USUARIOS:
        nome_gerente = USUARIOS[usuario_logado].get("nome", "")

    return {
        "nome_cliente": sim.get("nome_cliente", ""),
        "renda": sim.get("renda", 0),
        "entrada": sim.get("entrada", 0),
        "bairro": "",
        "origem": "",
        "desconto": sim.get("desconto_acordado", 0),
        "tipo_desconto": "MISTO",
        "nome_gerente": nome_gerente,
        "oportunidades": oportunidades,
    }


def _salvar_proposta(sim, top, idx_escolhido, usuario_logado, USUARIOS):
    from src.simulacoes_storage import salvar_simulacao

    top_unit = top.loc[[idx_escolhido]]
    nome_gerente = USUARIOS[usuario_logado]["nome"] if usuario_logado in USUARIOS else ""

    salvar_simulacao(
        nome_cliente=sim["nome_cliente"],
        renda=sim.get("renda", 0),
        entrada=sim.get("entrada", 0),
        bairro="",
        origem="",
        desconto=sim.get("desconto_acordado", 0),
        tipo_desconto="MISTO",
        gerente=nome_gerente,
        top_recomendacoes=top_unit,
    )