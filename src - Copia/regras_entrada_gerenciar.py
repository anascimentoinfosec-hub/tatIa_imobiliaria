import streamlit as st
from src.regras_entrada_storage import (
    carregar_regras_entrada,
    salvar_regras_entrada,
    salvar_regra_construtora,
    excluir_regra_construtora,
    obter_regra_construtora,
    PADRAO,
)
from src.construtoras_storage import carregar_construtoras


def renderizar_gestao_regras_entrada():
    st.title("📋 Regras de Entrada por Construtora")
    st.markdown("---")
    st.caption(
        "Configure as regras de entrada (ato, pré-chaves, pós-chaves) de cada construtora. "
        "Essas regras alimentam o Simulador de Entrada."
    )

    construtoras = carregar_construtoras()
    if not construtoras:
        st.warning("⚠️ Cadastre uma construtora primeiro.")
        return

    todas_regras = carregar_regras_entrada()
    nomes_construtoras = list(construtoras.keys())

    tabs = st.tabs(["📋 Listar / Editar", "➕ Adicionar Regra"])

    with tabs[0]:
        _renderizar_lista(nomes_construtoras, todas_regras)

    with tabs[1]:
        _renderizar_form_adicionar(nomes_construtoras, todas_regras)


def _renderizar_lista(nomes_construtoras, todas_regras):
    if not todas_regras:
        st.info(
            "📭 Nenhuma regra configurada ainda. "
            "**Todas as construtoras usam o padrão da imobiliária** (4,2% + R$ 1.000). "
            "Adicione regras específicas na aba ➕."
        )
        _renderizar_padrao_info()
        return

    for nome in nomes_construtoras:
        if nome not in todas_regras:
            continue
        _renderizar_card_regra(nome, todas_regras[nome])


def _renderizar_card_regra(nome, dados):
    ativo = dados.get("ativo", True)
    comissao_pct = dados.get("comissao_pct", PADRAO["comissao_pct"])
    comissao_fixa = dados.get("comissao_fixa", PADRAO["comissao_fixa"])
    ato_min = dados.get("ato_minimo", PADRAO["ato_minimo"])

    status_icon = "🟢" if ativo else "🔴"
    titulo = f"{status_icon} {nome}  •  Comissão {comissao_pct}% + R$ {comissao_fixa:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")

    with st.expander(titulo):
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**💰 Comissão / Ato**")
            novo_pct = st.number_input(
                "Comissão (% na cabeça)", min_value=0.0, max_value=20.0,
                value=float(comissao_pct), step=0.1, format="%.2f",
                key=f"re_pct_{nome}",
                help="Percentual que o corretor recebe 'na cabeça'. Padrão: 4,2%.",
            )
            nova_fixa = st.number_input(
                "Valor fixo adicional (R$)", min_value=0.0,
                value=float(comissao_fixa), step=100.0, format="%.2f",
                key=f"re_fixa_{nome}",
                help="Valor fixo somado à comissão. Padrão: R$ 1.000.",
            )
            novo_ato_min = st.number_input(
                "Ato mínimo (R$)", min_value=0.0,
                value=float(ato_min), step=100.0, format="%.2f",
                key=f"re_ato_{nome}",
                help="Valor mínimo do ato. Padrão: R$ 1.000.",
            )
            novoTetoParcel = st.number_input(
                "Teto de parcelamento (% do valor final)", min_value=0.0, max_value=100.0,
                value=float(dados.get("teto_parcelamento_pct", 15.0)),
                step=1.0, format="%.1f", key=f"re_teto_{nome}",
                help="Máximo do valor final do imóvel que pode ser parcelado. Padrão: 15%.",
            )

        with col2:
            st.markdown("**⏳ Pré-chaves**")
            pre_parc = st.number_input(
                "Parcela máx (% renda)", min_value=0.0, max_value=100.0,
                value=float(dados.get("pre_chaves", {}).get("parcela_max_pct_renda", 30.0)),
                step=1.0, format="%.1f", key=f"re_pre_parc_{nome}",
                help="Padrão: 30% da renda bruta.",
            )
            pre_inter = st.number_input(
                "Intermediária máx (% renda)", min_value=0.0, max_value=100.0,
                value=float(dados.get("pre_chaves", {}).get("intermediaria_max_pct_renda", 80.0)),
                step=1.0, format="%.1f", key=f"re_pre_inter_{nome}",
                help="Padrão: 80% da renda bruta.",
            )

        col3, col4 = st.columns(2)
        with col3:
            st.markdown("**🔑 Pós-chaves**")
            pos_parc = st.number_input(
                "Parcela máx (% renda)", min_value=0.0, max_value=100.0,
                value=float(dados.get("pos_chaves", {}).get("parcela_max_pct_renda", 5.0)),
                step=1.0, format="%.1f", key=f"re_pos_parc_{nome}",
                help="Padrão: 5% da renda bruta.",
            )
            pos_inter = st.number_input(
                "Intermediária máx (% renda)", min_value=0.0, max_value=100.0,
                value=float(dados.get("pos_chaves", {}).get("intermediaria_max_pct_renda", 30.0)),
                step=1.0, format="%.1f", key=f"re_pos_inter_{nome}",
                help="Padrão: 30% da renda bruta.",
            )

        with col4:
            st.markdown("**📏 Limites Gerais**")
            soma_max = st.number_input(
                "Soma máx (nº parcelas)", min_value=1, max_value=200,
                value=int(dados.get("soma_max_parcelas", 60)),
                step=1, key=f"re_soma_{nome}",
                help="Pré + pós não pode ultrapassar essa soma. Padrão: 60 parcelas.",
            )
            novo_ativo = st.checkbox(
                "Regra ativa", value=ativo, key=f"re_ativo_{nome}",
            )

        st.markdown("---")
        col_a, col_b, col_c = st.columns([3, 1, 1])
        with col_b:
            if st.button("💾 Salvar", key=f"re_salvar_{nome}", use_container_width=True, type="primary"):
                dados_atualizados = {
                    "nome": nome,
                    "ativo": novo_ativo,
                    "comissao_pct": novo_pct,
                    "comissao_fixa": nova_fixa,
                    "ato_minimo": novo_ato_min,
                    "teto_parcelamento_pct": novoTetoParcel,
                    "pre_chaves": {
                        "parcela_max_pct_renda": pre_parc,
                        "intermediaria_max_pct_renda": pre_inter,
                    },
                    "pos_chaves": {
                        "parcela_max_pct_renda": pos_parc,
                        "intermediaria_max_pct_renda": pos_inter,
                    },
                    "soma_max_parcelas": soma_max,
                }
                salvar_regra_construtora(nome, dados_atualizados)
                st.success(f"✅ Regra da **{nome}** salva com sucesso!")
                st.rerun()

        with col_c:
            if st.button("🗑️ Excluir", key=f"re_excluir_{nome}", use_container_width=True):
                excluir_regra_construtora(nome)
                st.success(f"✅ Regra da **{nome}** removida. Voltou ao padrão.")
                st.rerun()


def _renderizar_form_adicionar(nomes_construtoras, todas_regras):
    disponiveis = [n for n in nomes_construtoras if n not in todas_regras]

    if not disponiveis:
        st.info("✅ Todas as construtoras já têm regras configuradas.")
        return

    st.markdown("Adicione uma regra específica para uma construtora.")

    construtora = st.selectbox("🏗️ Construtora", disponiveis, key="re_nova_construtora")

    if st.button("➕ Criar regra com padrão", use_container_width=True, type="primary", key="re_criar"):
        salvar_regra_construtora(construtora, {"nome": construtora, **PADRAO})
        st.success(f"✅ Regra padrão criada para **{construtora}**! Edite na aba Listar.")
        st.rerun()


def _renderizar_padrao_info():
    st.markdown("---")
    st.markdown("#### 📋 Padrão da imobiliária (aplicado a todas as construtoras sem regra específica)")
    st.markdown(f"""
    - 💰 **Comissão:** {PADRAO['comissao_pct']}% + R$ {PADRAO['comissao_fixa']:,.2f}
    - 💵 **Ato mínimo:** R$ {PADRAO['ato_minimo']:,.2f}
    - ⏳ **Pré-chaves:** parcela máx {PADRAO['pre_chaves']['parcela_max_pct_renda']}% da renda • intermediária máx {PADRAO['pre_chaves']['intermediaria_max_pct_renda']}%
    - 🔑 **Pós-chaves:** parcela máx {PADRAO['pos_chaves']['parcela_max_pct_renda']}% da renda • intermediária máx {PADRAO['pos_chaves']['intermediaria_max_pct_renda']}%
    - 📏 **Soma máxima:** {PADRAO['soma_max_parcelas']} parcelas
    """)