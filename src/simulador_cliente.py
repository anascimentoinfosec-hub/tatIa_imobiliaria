import streamlit as st
from src.construtoras_storage import carregar_cidades
from src.compartilhar import gerar_resumo
from src.origens_storage import carregar_origens
from src.simulacoes_storage import salvar_simulacao
from src.lazer_storage import carregar_lazer
from src.utils import campo_moeda


def renderizar_area_cliente(resultado, tipo_desconto, preco_col, usuario_logado, USUARIOS):
    """Renderiza a área do cliente (inputs + botão Analisar)."""
    st.subheader("🧑 Área do Cliente")
    st.markdown("Preencha os dados abaixo para receber recomendações personalizadas.")

    with st.container():
        col1, col2 = st.columns(2)

        with col1:
            nome_cliente = st.text_input(
                "Nome do Cliente",
                placeholder="Ex: João Silva",
                key="cliente_nome",
                help="Nome completo do cliente. Aparecerá no resumo compartilhado.",
            )

            renda_cliente = campo_moeda(
                "💰 Renda bruta mensal (R$)",
                valor_inicial=5000.0,
                key="cliente_renda",
                help="Renda BRUTA mensal do cliente.",
                placeholder="Ex: 5.000,00",
            )

            entrada_cliente = campo_moeda(
                "🏦 Valor disponível para entrada (R$)",
                valor_inicial=100000.0,
                key="cliente_entrada",
                help="Quanto o cliente tem disponível para dar de entrada. Sem limite.",
                placeholder="Ex: 100.000,00",
            )

            origem_cliente = _renderizar_origem_cliente()

        with col2:
            cidades_disponiveis = carregar_cidades()
            bairro_preferencia = st.selectbox(
                "📍 Bairro de preferência", [""] + cidades_disponiveis, key="cliente_bairro",
                help="Filtra os imóveis pelo bairro de interesse.",
            )
            quartos_preferencia = st.selectbox(
                "🛏️ Quantos quartos?", ["Indiferente", "1", "2", "3", "4+"], key="cliente_quartos",
                help="Filtra os imóveis pela quantidade de quartos.",
            )
            tipo_preferencia = st.selectbox(
                "🏠 Tipo de imóvel", ["Indiferente", "Apartamento", "Cobertura", "Garden"], key="cliente_tipo",
                help="Filtra os imóveis pelo tipo.",
            )

            vagas_preferencia = st.selectbox(
                "🚗 Vagas necessárias",
                ["Indiferente", "1", "2", "3", "4+"],
                key="cliente_vagas",
                help="O cliente precisa de no mínimo essa quantidade de vagas?",
            )

            desconto_acordado = campo_moeda(
                "💸 Desconto acordado (R$)",
                valor_inicial=0.0,
                key="cliente_desconto",
                help=f"Desconto a ser subtraído do {tipo_desconto} do imóvel.",
                placeholder="Ex: 80.000,00",
            )

        lazer_preferencias = _renderizar_area_lazer()

        if st.button("🔍 Analisar Oportunidades", use_container_width=True):
            if not nome_cliente:
                st.warning("⚠️ Por favor, informe o nome do cliente.")
                return

            with st.spinner("Analisando oportunidades..."):
                try:
                    dados_simulacao = _analisar(
                        resultado=resultado,
                        nome_cliente=nome_cliente,
                        renda_cliente=renda_cliente,
                        entrada_cliente=entrada_cliente,
                        bairro_preferencia=bairro_preferencia,
                        quartos_preferencia=quartos_preferencia,
                        tipo_preferencia=tipo_preferencia,
                        vagas_preferencia=vagas_preferencia,
                        lazer_preferencias=lazer_preferencias,
                        desconto_acordado=desconto_acordado,
                        tipo_desconto=tipo_desconto,
                        preco_col=preco_col,
                        usuario_logado=usuario_logado,
                        USUARIOS=USUARIOS,
                        origem_cliente=origem_cliente,
                    )

                    if dados_simulacao is None:
                        return

                    st.session_state.simulacao_ativa = dados_simulacao

                    nome_gerente = USUARIOS[usuario_logado]["nome"] if usuario_logado in USUARIOS else ""
                    sim_id = salvar_simulacao(
                        nome_cliente=nome_cliente,
                        renda=renda_cliente,
                        entrada=entrada_cliente,
                        bairro=bairro_preferencia,
                        origem=origem_cliente if origem_cliente != "(Não informado)" else "",
                        desconto=desconto_acordado,
                        tipo_desconto=tipo_desconto,
                        gerente=nome_gerente,
                        top_recomendacoes=dados_simulacao["top_recomendacoes"],
                    )
                    st.session_state.ultima_simulacao_id = sim_id
                    st.toast(f"💾 Simulação salva no histórico (ID: {sim_id[-6:]})")

                except Exception as e:
                    st.error(f"❌ Erro ao analisar oportunidades: {str(e)}")


def _renderizar_origem_cliente():
    origens = carregar_origens()
    opcoes = ["(Não informado)"] + origens
    return st.selectbox(
        "🎯 Origem do Cliente",
        opcoes,
        key="cliente_origem",
        help="Como esse cliente chegou até nós?",
    )


def _renderizar_area_lazer():
    st.markdown("---")
    st.markdown("#### 🏖️ Preferências de Lazer")
    st.caption("Selecione uma ou mais opções que o cliente procura. O filtro buscará imóveis que atendam.")

    opcoes_lazer = carregar_lazer()

    selecionados = st.multiselect(
        "Opções de lazer desejadas",
        opcoes_lazer,
        key="cliente_lazer",
        help="Deixe em branco para não filtrar por lazer.",
        label_visibility="collapsed",
    )

    return selecionados


def _analisar(resultado, nome_cliente, renda_cliente, entrada_cliente,
              bairro_preferencia, quartos_preferencia, tipo_preferencia,
              vagas_preferencia, lazer_preferencias,
              desconto_acordado, tipo_desconto, preco_col, usuario_logado,
              USUARIOS, origem_cliente):
    """Lógica pura de análise. Retorna dict pronto para o session_state."""
    df_filtrado = resultado.copy()
    total_original = len(df_filtrado)

    # Registra o total após cada etapa (para diagnóstico)
    etapas = [("Inicial", total_original)]

    # === Filtro: Quartos ===
    if quartos_preferencia != "Indiferente":
        qtd = int(quartos_preferencia.replace("+", ""))
        col_quartos = None
        for c in ["QUARTOS", "DORMITÓRIOS", "TIPO"]:
            if c in df_filtrado.columns:
                col_quartos = c
                break
        if col_quartos:
            df_filtrado = df_filtrado[df_filtrado[col_quartos].astype(str).str.contains(str(qtd))]
            etapas.append((f"Quartos ({qtd})", len(df_filtrado)))
        else:
            etapas.append(("Quartos (ignorado - sem coluna)", len(df_filtrado)))

    # === Filtro: Tipo ===
    if tipo_preferencia != "Indiferente" and "TIPOLOGIA" in df_filtrado.columns:
        df_filtrado = df_filtrado[
            df_filtrado["TIPOLOGIA"].astype(str).str.contains(tipo_preferencia, case=False, na=False)
        ]
        etapas.append((f"Tipo ({tipo_preferencia})", len(df_filtrado)))

    # === Filtro: Vagas ===
    if vagas_preferencia != "Indiferente":
        vagas_min = int(vagas_preferencia.replace("+", ""))
        col_vagas = None
        for c in ["VAGA", "VAGAS", "VAGAS_GARAGEM"]:
            if c in df_filtrado.columns:
                col_vagas = c
                break
        if col_vagas:
            import re as _re
            def tem_vagas(s):
                try:
                    numeros = _re.findall(r"\d+", str(s))
                    return any(int(n) >= vagas_min for n in numeros)
                except Exception:
                    return False

            df_filtrado = df_filtrado[df_filtrado[col_vagas].apply(tem_vagas)]
            etapas.append((f"Vagas >= {vagas_min}", len(df_filtrado)))
        else:
            etapas.append(("Vagas (ignorado - sem coluna)", len(df_filtrado)))

    # === Filtro: Lazer ===
    if lazer_preferencias:
        colunas_lazer = [c for c in df_filtrado.columns if "LAZER" in c.upper()]

        if colunas_lazer:
            def atende_lazer(row):
                texto = " ".join(str(row.get(c, "")) for c in colunas_lazer).lower()
                return all(op.lower() in texto for op in lazer_preferencias)

            df_filtrado = df_filtrado[df_filtrado.apply(atende_lazer, axis=1)]
            etapas.append((f"Lazer ({len(lazer_preferencias)} opções)", len(df_filtrado)))
        else:
            etapas.append(("Lazer (ignorado - sem coluna)", len(df_filtrado)))

    # === Aplica desconto ===
    coluna_base_desejada = "AVALIAÇÃO" if tipo_desconto == "AVALIAÇÃO" else "PREÇO"

    if coluna_base_desejada not in df_filtrado.columns:
        coluna_encontrada = None
        for c in ["AVALIAÇÃO", "PREÇO", "VALOR"]:
            if c in df_filtrado.columns:
                coluna_encontrada = c
                break

        if coluna_encontrada is None:
            st.error(
                f"❌ Nenhuma coluna de valor encontrada. "
                f"Colunas: {list(df_filtrado.columns)}"
            )
            return None

        coluna_base = coluna_encontrada
        st.warning(
            f"⚠️ Construtora configurada com **{coluna_base_desejada}**, "
            f"mas usando **{coluna_encontrada}** (fallback)."
        )
    else:
        coluna_base = coluna_base_desejada

    df_filtrado["valor_base"] = df_filtrado[coluna_base] - desconto_acordado
    df_filtrado["valor_base"] = df_filtrado["valor_base"].clip(lower=0)

    if "R$/m²" in df_filtrado.columns:
        df_filtrado = df_filtrado.sort_values("R$/m²")

    top_recomendacoes = df_filtrado.head(5)

    # =========================================================
    # DIAGNÓSTICO — se ficou vazio, mostra onde paramos
    # =========================================================
    if df_filtrado.empty:
        _renderizar_diagnostico_vazio(etapas, resultado, vagas_preferencia,
                                       quartos_preferencia, tipo_preferencia,
                                       lazer_preferencias)

    resumo = gerar_resumo(
        nome_cliente,
        renda_cliente,
        entrada_cliente,
        bairro_preferencia,
        top_recomendacoes,
        nome_gerente=USUARIOS[usuario_logado]["nome"] if usuario_logado in USUARIOS else "",
        desconto=desconto_acordado,
        tipo_desconto=tipo_desconto,
        origem=origem_cliente,
    )

    return {
        "top_recomendacoes": top_recomendacoes,
        "df_filtrado_completo": df_filtrado,  # ← NOVO (para refinamento)
        "desconto_acordado": desconto_acordado,
        "tipo_desconto": tipo_desconto,
        "coluna_base": coluna_base,
        "preco_col": preco_col,
        "nome_cliente": nome_cliente,
        "resumo": resumo,
        "renda": renda_cliente,
        "entrada": entrada_cliente,
        "vagas_preferencia": vagas_preferencia,
        "lazer_preferencias": lazer_preferencias,
    }


def _renderizar_diagnostico_vazio(etapas, resultado, vagas_pref,
                                   quartos_pref, tipo_pref, lazer_pref):
    """Mostra um diagnóstico quando 0 imóveis passaram nos filtros."""
    st.warning("⚠️ Nenhuma oportunidade encontrada. Diagnóstico:")

    with st.expander("🔍 Ver detalhes dos filtros aplicados", expanded=True):
        for nome, qtd in etapas:
            icon = "🔴" if qtd == 0 else "🟢"
            st.write(f"{icon} **{nome}:** {qtd} imóveis")

        st.markdown("---")
        st.markdown("**Dicas para tentar de novo:**")

        if vagas_pref != "Indiferente":
            if "VAGA" in resultado.columns:
                valores = resultado["VAGA"].dropna().unique().tolist()[:5]
                st.write(f"• 🚗 As unidades têm estas vagas disponíveis: **{valores}**. "
                         f"Você pediu **{vagas_pref}**. Tente diminuir o filtro.")

        if quartos_pref != "Indiferente":
            for c in ["QUARTOS", "DORMITÓRIOS", "TIPO"]:
                if c in resultado.columns:
                    valores = resultado[c].dropna().unique().tolist()[:5]
                    st.write(f"• 🛏️ Valores de quartos encontrados: **{valores}**")
                    break

        if lazer_pref:
            colunas_lazer = [c for c in resultado.columns if "LAZER" in c.upper()]
            if not colunas_lazer:
                st.write("• 🏖️ A planilha **não tem coluna de lazer**. Remova o filtro de lazer.")
            else:
                st.write(f"• 🏖️ Colunas de lazer encontradas: {colunas_lazer}")

        st.write("• 💸 Tente **aumentar a entrada** ou **ajustar o desconto acordado**.")
        st.write("• 📍 Tente remover o filtro de **bairro**.")