import streamlit as st
from openai import OpenAI
from src.regras_storage import (
    carregar_regras,
    salvar_regras,
    salvar_regra,
    excluir_regra,
    gerar_id_regra,
)
from src.bia_regras_monitor import verificar_todas_regras


def renderizar_gestao_regras():
    """Tela de gestão das regras de financiamento."""
    st.title("🏦 Regras de Financiamento")
    st.markdown("---")
    st.caption(
        "Configure aqui as taxas, prazos e regras de cada banco/sistema. "
        "Essas regras são usadas nas simulações do corretor."
    )

    regras = carregar_regras()

    tabs = st.tabs(["📋 Listar", "➕ Adicionar", "🔍 Verificar na Web"])

    with tabs[0]:
        _renderizar_lista(regras)

    with tabs[1]:
        _renderizar_form_adicionar()

    with tabs[2]:
        _renderizar_verificacao_web()


# =========================================================
# LISTAGEM + EDIÇÃO
# =========================================================
def _renderizar_lista(regras):
    if not regras:
        st.info("📭 Nenhuma regra cadastrada ainda. Adicione uma na aba '➕ Adicionar'.")
        return

    for regra_id, dados in regras.items():
        _renderizar_card_regra(regra_id, dados)


def _renderizar_card_regra(regra_id, dados):
    nome = dados.get("nome", regra_id)
    banco = dados.get("banco", "")
    ativo = dados.get("ativo", True)
    sistema = dados.get("sistema", "SAC")
    taxa = dados.get("taxa_anual", 0) * 100
    prazo = dados.get("prazo_max_meses", 0)

    status_icon = "🟢" if ativo else "🔴"
    titulo = f"{status_icon} {nome}  •  {taxa:.2f}% a.a.  •  {prazo}m  •  {sistema}"

    with st.expander(titulo):
        col1, col2, col3 = st.columns(3)

        with col1:
            novo_nome = st.text_input(
                "Nome", value=nome, key=f"nome_{regra_id}",
                help="Nome que aparecerá para o corretor no simulador.",
            )
            novo_banco = st.text_input(
                "Banco", value=banco, key=f"banco_{regra_id}",
                help="Nome do banco (agrupamento).",
            )

        with col2:
            nova_taxa = st.number_input(
                "Taxa anual (%)", min_value=0.0, max_value=30.0,
                value=float(taxa), step=0.01, format="%.2f",
                key=f"taxa_{regra_id}",
                help="Taxa de juros anual em %. Ex: 11.49 significa 11,49% a.a.",
            )
            novo_prazo = st.number_input(
                "Prazo máximo (meses)", min_value=12, max_value=500,
                value=int(prazo), step=12, key=f"prazo_{regra_id}",
                help="Prazo máximo do financiamento em meses.",
            )

        with col3:
            novo_sistema = st.selectbox(
                "Sistema de amortização", ["SAC", "PRICE"],
                index=0 if sistema == "SAC" else 1,
                key=f"sistema_{regra_id}",
                help="SAC: parcela decrescente. PRICE: parcela fixa.",
            )
            novo_ativo = st.checkbox(
                "Ativo", value=ativo, key=f"ativo_{regra_id}",
                help="Desmarque para ocultar essa regra do simulador.",
            )

        col_edit1, col_edit2, _ = st.columns(3)
        with col_edit1:
            novo_entrada = st.number_input(
                "Entrada mínima (%)", min_value=0.0, max_value=100.0,
                value=float(dados.get("entrada_minima_pct", 20)),
                step=1.0, key=f"entrada_{regra_id}",
                help="Percentual mínimo de entrada exigido.",
            )
        with col_edit2:
            novo_comprometimento = st.number_input(
                "Comprometimento máx. renda (%)", min_value=0.0, max_value=100.0,
                value=float(dados.get("comprometimento_max_pct", 30)),
                step=1.0, key=f"comprom_{regra_id}",
                help="Percentual máximo da renda que pode comprometer a parcela.",
            )

        st.markdown("---")

        col_btn1, col_btn2 = st.columns([3, 1])
        with col_btn1:
            if st.button("💾 Salvar alterações", key=f"salvar_{regra_id}",
                         use_container_width=True, type="primary"):
                _salvar_edicao(
                    regra_id=regra_id, nome=novo_nome, banco=novo_banco,
                    taxa=nova_taxa, prazo=novo_prazo, sistema=novo_sistema,
                    ativo=novo_ativo, entrada_min=novo_entrada,
                    comprometimento_max=novo_comprometimento,
                )
                st.success(f"✅ Regra '{novo_nome}' atualizada!")
                st.rerun()

        with col_btn2:
            if st.button("🗑️ Excluir", key=f"excluir_{regra_id}", use_container_width=True):
                excluir_regra(regra_id)
                st.success(f"✅ Regra '{nome}' excluída!")
                st.rerun()


def _salvar_edicao(regra_id, nome, banco, taxa, prazo, sistema, ativo,
                   entrada_min, comprometimento_max):
    salvar_regra(regra_id, {
        "nome": nome,
        "banco": banco,
        "taxa_anual": taxa / 100,
        "prazo_max_meses": int(prazo),
        "entrada_minima_pct": entrada_min,
        "comprometimento_max_pct": comprometimento_max,
        "sistema": sistema,
        "ativo": ativo,
    })


# =========================================================
# ADICIONAR
# =========================================================
def _renderizar_form_adicionar():
    st.markdown("### ➕ Adicionar nova regra")
    st.caption("Cadastre as regras de um novo banco ou sistema de financiamento.")

    with st.form("form_nova_regra"):
        col1, col2 = st.columns(2)

        with col1:
            nome = st.text_input("Nome da regra", placeholder="Ex: Caixa - SBPE")
            banco = st.text_input("Banco", placeholder="Ex: Caixa")
            sistema = st.selectbox("Sistema de amortização", ["SAC", "PRICE"])

        with col2:
            taxa = st.number_input(
                "Taxa anual (%)", min_value=0.0, max_value=30.0,
                value=11.49, step=0.01, format="%.2f",
            )
            prazo = st.number_input("Prazo máximo (meses)", min_value=12, max_value=500,
                                     value=420, step=12)
            entrada_min = st.number_input("Entrada mínima (%)", min_value=0.0, max_value=100.0,
                                           value=20.0, step=1.0)

        comprometimento_max = st.number_input(
            "Comprometimento máximo da renda (%)",
            min_value=0.0, max_value=100.0, value=30.0, step=1.0,
        )

        if st.form_submit_button("➕ Adicionar Regra", use_container_width=True, type="primary"):
            if not nome.strip():
                st.warning("⚠️ Digite o nome da regra!")
            else:
                regra_id = gerar_id_regra(nome)
                regras = carregar_regras()

                if regra_id in regras:
                    st.error(f"❌ Já existe uma regra com o ID '{regra_id}'. Escolha outro nome.")
                else:
                    salvar_regra(regra_id, {
                        "nome": nome.strip(),
                        "banco": banco.strip(),
                        "taxa_anual": taxa / 100,
                        "prazo_max_meses": int(prazo),
                        "entrada_minima_pct": entrada_min,
                        "comprometimento_max_pct": comprometimento_max,
                        "sistema": sistema,
                        "ativo": True,
                    })
                    st.success(f"✅ Regra '{nome}' adicionada!")
                    st.rerun()


# =========================================================
# VERIFICAÇÃO NA WEB (IA)
# =========================================================
def _renderizar_verificacao_web():
    st.markdown("### 🔍 Verificação automática de taxas")
    st.caption(
        "A BIA busca na web as taxas atuais dos bancos e compara com o que está cadastrado. "
        "⚠️ A IA **sugere**, mas **nunca altera sozinha** — você decide o que aceitar."
    )

    if "OPENAI_API_KEY" not in st.secrets:
        st.error("❌ Chave da OpenAI não configurada.")
        return

    if "verificacao_resultados" not in st.session_state:
        st.session_state.verificacao_resultados = None

    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(
            "Clique abaixo para buscar as taxas atuais na web. "
            "Pode levar **20-40 segundos** (consulta cada banco individualmente)."
        )
    with col2:
        st.write("")
        if st.button("🚀 Verificar agora", use_container_width=True, type="primary"):
            with st.spinner("Consultando bancos e analisando com IA..."):
                try:
                    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
                    resultados = verificar_todas_regras(client)
                    st.session_state.verificacao_resultados = resultados
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Erro na verificação: {str(e)}")

    resultados = st.session_state.verificacao_resultados
    if resultados is None:
        return

    if not resultados:
        st.warning("⚠️ Nenhum resultado obtido. Verifique a chave da Tavily nos secrets.")
        return

    st.markdown("---")
    st.markdown(f"#### 📊 Resultado: {len(resultados)} regras verificadas")

    divergencias = [r for r in resultados if r["analise"].get("divergencia")]
    sem_divergencia = [r for r in resultados if not r["analise"].get("divergencia")]

    if divergencias:
        st.error(f"⚠️ **{len(divergencias)} possível(is) mudança(s) detectada(s):**")
        for r in divergencias:
            _renderizar_card_divergencia(r)
    else:
        st.success("✅ Nenhuma mudança detectada. Todas as taxas parecem atualizadas.")

    with st.expander(f"✅ {len(sem_divergencia)} regra(s) sem divergência", expanded=False):
        for r in sem_divergencia:
            st.write(f"• **{r['nome_regra']}** — {r['taxa_atual_sistema']*100:.2f}% a.a. ({r['analise'].get('justificativa', 'OK')})")

    if st.button("🔄 Limpar resultados", use_container_width=False):
        st.session_state.verificacao_resultados = None
        st.rerun()


def _renderizar_card_divergencia(r):
    regra_id = r["regra_id"]
    analise = r["analise"]
    taxa_atual = r["taxa_atual_sistema"] * 100
    taxa_sugerida = analise.get("taxa_sugerida")

    with st.container():
        st.markdown(f"##### ⚠️ {r['nome_regra']}")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("💾 Taxa atual no sistema", f"{taxa_atual:.2f}% a.a.")
        with col2:
            if taxa_sugerida is not None:
                st.metric("🌐 Taxa sugerida pela web", f"{taxa_sugerida*100:.2f}% a.a.",
                          delta=f"{(taxa_sugerida*100 - taxa_atual):+.2f} pp")

        st.caption(f"**Fonte:** {analise.get('fonte', 'não identificada')}")
        st.info(f"💬 {analise.get('justificativa', '')}")

        if taxa_sugerida is not None:
            col_a, col_b, col_c = st.columns([2, 2, 3])
            with col_a:
                if st.button(f"✅ Aceitar sugestão", key=f"aceitar_{regra_id}",
                             use_container_width=True, type="primary"):
                    regras = carregar_regras()
                    if regra_id in regras:
                        regras[regra_id]["taxa_anual"] = taxa_sugerida
                        salvar_regras(regras)
                        st.success(f"✅ Taxa da '{r['nome_regra']}' atualizada para {taxa_sugerida*100:.2f}%")
                        st.session_state.verificacao_resultados = None
                        st.rerun()
            with col_b:
                if st.button("❌ Ignorar", key=f"ignorar_{regra_id}", use_container_width=True):
                    st.info("Sugestão ignorada. A taxa do sistema foi mantida.")
        else:
            st.warning("⚠️ Não foi possível sugerir uma nova taxa. Verifique manualmente.")

        with st.expander("🔗 Ver detalhes da busca"):
            st.text(r["resultado_busca"][:2000])

        st.markdown("---")