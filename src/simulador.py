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
from src.regras_entrada_storage import obter_regra_construtora
from src.regras_entrada_calculo import calcular_plano_entrada


def pagina_simulador(CONSTRUTORAS, USUARIOS):
    if not CONSTRUTORAS:
        st.warning("⚠️ Nenhuma construtora cadastrada. Cadastre uma primeiro.")
        return

    st.title("🏢 Simulador de Entrada de Construtora")
    st.caption("Analise o potencial do cliente em **todas as construtoras** disponíveis.")

    usuario_logado = st.session_state.get("usuario_logado")

    # ---------- 1. Carrega TODAS as planilhas ----------
    df_total, resumo = carregar_todas_planilhas(CONSTRUTORAS)
    renderizar_sidebar_resumo(CONSTRUTORAS)

    if df_total is None or df_total.empty:
        st.warning("⚠️ Nenhuma planilha em cache. Peça ao gerente para subir planilhas.")
        return

    st.info(f"📦 {len(resumo)} produto(s) • {len(df_total)} unidades totais em cache")

    # ---------- 2. Área do cliente ----------
    renderizar_area_cliente(df_total, usuario_logado, USUARIOS)

    # ---------- 3. Resultados ----------
    if st.session_state.get("simulacao_ativa"):
        sim = st.session_state.simulacao_ativa

        st.markdown("---")
        top_refinado = renderizar_refinamento()
        sim["top_recomendacoes"] = top_refinado

        idx_escolhido = renderizar_seletor_proposta(top_refinado)
        st.session_state.unidade_escolhida_idx = idx_escolhido

        # === PLANO DE ENTRADA ===
        plano = None
        if idx_escolhido is not None and top_refinado is not None and not top_refinado.empty:
            top_para_pdf = top_refinado.loc[[idx_escolhido]]
            num_pre = st.session_state.get(f"plano_pre_{idx_escolhido}", 0)
            num_pos = st.session_state.get(f"plano_pos_{idx_escolhido}", 0)
            inter_list = st.session_state.get(f"inter_list_{idx_escolhido}", [])

            row = top_para_pdf.iloc[0]
            valor_base = float(row.get("valor_base", 0) or 0)
            construtora = str(row.get("_construtora", ""))
            renda = float(sim.get("renda", 0) or 0)
            entrada = float(sim.get("entrada", 0) or 0)

            regra = obter_regra_construtora(construtora)
            plano = calcular_plano_entrada(
                entrada, renda, regra,
                valor_final_imovel=valor_base,
                num_pre=int(num_pre), num_pos=int(num_pos),
                intermediarias=inter_list,
            )
        else:
            top_para_pdf = top_refinado

        # === CARDS (com plano e intermediárias) ===
        st.markdown("---")
        renderizar_cards(
            top_refinado,
            sim["desconto_acordado"],
            sim["tipo_desconto"],
            sim["coluna_base"],
            sim["preco_col"],
            sim["nome_cliente"],
        )

        # === COMPARTILHAR + ENVIAR PROPOSTA ===
        if idx_escolhido is not None:
            st.markdown("---")
            st.markdown("### 📤 Compartilhar Simulação")
            st.caption(
                "Envie a simulação para o cliente (TXT, WhatsApp ou PDF). "
                "Depois de alinhar com o cliente, clique em **Enviar Proposta ao Gerente**."
            )

            dados_pdf = _montar_dados_pdf(sim, usuario_logado, USUARIOS, top_para_pdf, plano)
            resumo_texto = _montar_resumo_texto(sim, usuario_logado, USUARIOS, top_para_pdf, plano)
            botoes_compartilhar(resumo_texto, sim["nome_cliente"], dados_pdf)

            st.markdown("---")
            st.info(
                "💡 **Revise o plano de entrada** no card acima (pré/pós-chaves e intermediárias) "
                "antes de enviar. A proposta só é registrada agora."
            )

            if st.button(
                "📤 Enviar Proposta ao Gerente",
                use_container_width=True,
                type="primary",
            ):
                num_pre = st.session_state.get(f"plano_pre_{idx_escolhido}", 0)
                num_pos = st.session_state.get(f"plano_pos_{idx_escolhido}", 0)
                _salvar_proposta(
                    sim, top_refinado, idx_escolhido, usuario_logado, USUARIOS,
                    num_pre=num_pre, num_pos=num_pos,
                )
                st.success("✅ Proposta enviada! **O gerente foi notificado.**")
                st.rerun()

        st.markdown("---")
        renderizar_ajuste_global(df_total, "PREÇO")

    st.markdown("---")
    if st.button("💬 Perguntar à BIA (IA Imobiliária)", use_container_width=True):
        st.session_state.pagina = "ChatIA"
        st.rerun()


# =========================================================
def _montar_dados_pdf(sim, usuario_logado, USUARIOS, top_filtrado, plano=None):
    """Monta o dicionário de dados para o PDF."""
    oportunidades = []

    if top_filtrado is not None and not top_filtrado.empty:
        for _, row in top_filtrado.iterrows():
            item = {}
            for col in row.index:
                col_str = str(col)
                val = row[col]
                if hasattr(val, "item"):
                    val = val.item()
                if isinstance(val, float) and (val != val):
                    val = ""
                item[col_str] = val
            oportunidades.append(item)

    nome_gerente = ""
    if usuario_logado and usuario_logado in USUARIOS:
        nome_gerente = USUARIOS[usuario_logado].get("nome", "")

    return {
        "nome_cliente": sim.get("nome_cliente", ""),
        "data_nascimento": sim.get("data_nascimento", ""),
        "renda": sim.get("renda", 0),
        "entrada": sim.get("entrada", 0),
        "fgts": sim.get("fgts", 0),
        "subsidio": sim.get("subsidio", 0),
        "financiamento_caixa": sim.get("financiamento_caixa", 0),
        "parcela_morando": sim.get("parcela_morando", 0),
        "documentacao_paga": sim.get("documentacao_paga", False),
        "bairro": "",
        "origem": "",
        "desconto": sim.get("desconto_acordado", 0),
        "tipo_desconto": "MISTO",
        "nome_gerente": nome_gerente,
        "oportunidades": oportunidades,
        "plano_entrada": plano,
    }


# =========================================================
def _montar_resumo_texto(sim, usuario_logado, USUARIOS, top_filtrado, plano=None):
    from src.compartilhar import gerar_resumo

    nome_gerente = ""
    if usuario_logado and usuario_logado in USUARIOS:
        nome_gerente = USUARIOS[usuario_logado].get("nome", "")

    return gerar_resumo(
        nome_cliente=sim.get("nome_cliente", ""),
        renda=sim.get("renda", 0),
        entrada=sim.get("entrada", 0),
        bairro="",
        top_imoveis=top_filtrado,
        nome_gerente=nome_gerente,
        desconto=sim.get("desconto_acordado", 0),
        tipo_desconto="MISTO",
        origem="",
        fgts=sim.get("fgts", 0),
        subsidio=sim.get("subsidio", 0),
        financiamento_caixa=sim.get("financiamento_caixa", 0),
        parcela_morando=sim.get("parcela_morando", 0),
        data_nascimento=sim.get("data_nascimento", ""),
        documentacao_paga=sim.get("documentacao_paga", False),
        plano_entrada=plano,
    )


# =========================================================
def _salvar_proposta(sim, top, idx_escolhido, usuario_logado, USUARIOS,
                     num_pre=0, num_pos=0):
    from src.simulacoes_storage import salvar_simulacao

    top_unit = top.loc[[idx_escolhido]]
    nome_gerente = USUARIOS[usuario_logado]["nome"] if usuario_logado in USUARIOS else ""

    row = top_unit.iloc[0]
    valor_base = float(row.get("valor_base", 0) or 0)
    construtora = str(row.get("_construtora", ""))
    renda = float(sim.get("renda", 0) or 0)
    entrada = float(sim.get("entrada", 0) or 0)

    regra = obter_regra_construtora(construtora)
    inter_list = st.session_state.get(f"inter_list_{idx_escolhido}", [])
    plano = calcular_plano_entrada(
        entrada, renda, regra,
        valor_final_imovel=valor_base,
        num_pre=int(num_pre), num_pos=int(num_pos),
        intermediarias=inter_list,
    )

    top_unit = top_unit.copy()
    top_unit["num_pre"] = num_pre
    top_unit["num_pos"] = num_pos

    dados_extra = {
        "data_nascimento": sim.get("data_nascimento", ""),
        "fgts": sim.get("fgts", 0),
        "subsidio": sim.get("subsidio", 0),
        "parcela_morando": sim.get("parcela_morando", 0),
        "financiamento_caixa": sim.get("financiamento_caixa", 0),
        "documentacao_paga": sim.get("documentacao_paga", False),
        "plano_entrada": _serializar_plano(plano),
    }

    sim_id = salvar_simulacao(
        nome_cliente=sim["nome_cliente"],
        renda=renda,
        entrada=entrada,
        bairro="",
        origem="",
        desconto=sim.get("desconto_acordado", 0),
        tipo_desconto="MISTO",
        gerente=nome_gerente,
        top_recomendacoes=top_unit,
        status_proposta="pendente",
        dados_extra=dados_extra,
    )
    st.toast(f"📤 Proposta enviada (ID: {sim_id[-6:]})")


def _serializar_plano(plano):
    if not isinstance(plano, dict):
        return {}
    resultado = {}
    for k, v in plano.items():
        if isinstance(v, (str, int, float, bool)) or v is None:
            resultado[k] = v
        elif isinstance(v, list):
            resultado[k] = [str(x) for x in v]
        else:
            resultado[k] = str(v)
    return resultado