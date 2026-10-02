import streamlit as st
import pandas as pd
from src.origens_storage import carregar_origens
from src.simulacoes_storage import salvar_simulacao
from src.lazer_storage import carregar_lazer
from src.utils import campo_moeda


def renderizar_area_cliente(df_total, usuario_logado, USUARIOS):
    """
    Área do cliente no novo fluxo: cliente primeiro.
    Recebe o DataFrame unificado de TODAS as planilhas.
    """
    if df_total is None or df_total.empty:
        st.warning("⚠️ Nenhuma planilha disponível. Peça ao gerente para subir planilhas.")
        return

    st.subheader("🧑 Dados do Cliente")
    st.caption("Preencha os dados. O sistema buscará oportunidades em **todas as construtoras** disponíveis.")

    with st.container():
        col1, col2 = st.columns(2)

        with col1:
            nome_cliente = st.text_input(
                "Nome do Cliente", placeholder="Ex: João Silva",
                key="cliente_nome", help="Nome completo do cliente.",
            )
            renda_cliente = campo_moeda(
                "💰 Renda bruta mensal (R$)", valor_inicial=5000.0,
                key="cliente_renda", placeholder="Ex: 5.000,00",
            )
            entrada_cliente = campo_moeda(
                "🏦 Valor disponível para entrada (R$)", valor_inicial=100000.0,
                key="cliente_entrada", placeholder="Ex: 100.000,00",
            )
            origem_cliente = _renderizar_origem_cliente()

        with col2:
            quartos_preferencia = st.selectbox(
                "🛏️ Quantos quartos?", ["Indiferente", "1", "2", "3", "4+"],
                key="cliente_quartos",
            )
            tipo_preferencia = st.selectbox(
                "🏠 Tipo de imóvel", ["Indiferente", "Apartamento", "Cobertura", "Garden"],
                key="cliente_tipo",
            )
            vagas_preferencia = st.selectbox(
                "🚗 Vagas necessárias", ["Indiferente", "1", "2", "3", "4+"],
                key="cliente_vagas",
            )
            desconto_acordado = campo_moeda(
                "💸 Desconto acordado (R$)", valor_inicial=0.0,
                key="cliente_desconto", placeholder="Ex: 80.000,00",
            )

    # === FILTROS OPCIONAIS ===
    st.markdown("---")
    with st.expander("🎯 Filtros opcionais (deixe em branco para buscar em tudo)", expanded=False):
        col_f1, col_f2 = st.columns(2)

        with col_f1:
            construtoras_unicas = ["(Todas)"] + sorted(df_total["_construtora"].unique().tolist())
            filtro_construtora = st.selectbox(
                "🏗️ Construtora específica", construtoras_unicas, key="cliente_filtro_construtora",
            )
        with col_f2:
            if filtro_construtora == "(Todas)":
                produtos_opcoes = ["(Todos)"] + sorted(df_total["_produto"].unique().tolist())
            else:
                produtos_disponiveis = df_total[df_total["_construtora"] == filtro_construtora]["_produto"].unique().tolist()
                produtos_opcoes = ["(Todos)"] + sorted(produtos_disponiveis)
            filtro_produto = st.selectbox("📦 Produto específico", produtos_opcoes, key="cliente_filtro_produto")

    # === LAZER ===
    lazer_preferencias = _renderizar_area_lazer()

    # === BOTÃO ANALISAR ===
    if st.button("🔍 Analisar Oportunidades", use_container_width=True, type="primary"):
        if not nome_cliente:
            st.warning("⚠️ Por favor, informe o nome do cliente.")
            return

        with st.spinner("Analisando oportunidades em todas as construtoras..."):
            try:
                dados_simulacao = _analisar(
                    df_total=df_total,
                    nome_cliente=nome_cliente,
                    renda_cliente=renda_cliente,
                    entrada_cliente=entrada_cliente,
                    quartos_preferencia=quartos_preferencia,
                    tipo_preferencia=tipo_preferencia,
                    vagas_preferencia=vagas_preferencia,
                    lazer_preferencias=lazer_preferencias,
                    desconto_acordado=desconto_acordado,
                    filtro_construtora=filtro_construtora,
                    filtro_produto=filtro_produto,
                    usuario_logado=usuario_logado,
                    USUARIOS=USUARIOS,
                    origem_cliente=origem_cliente,
                )

                if dados_simulacao is None:
                    return

                st.session_state.simulacao_ativa = dados_simulacao

                nome_gerente = USUARIOS[usuario_logado]["nome"] if usuario_logado in USUARIOS else ""
                sim_id = salvar_simulacao(
                    nome_cliente=nome_cliente, renda=renda_cliente, entrada=entrada_cliente,
                    bairro="", origem=origem_cliente if origem_cliente != "(Não informado)" else "",
                    desconto=desconto_acordado, tipo_desconto="MISTO",
                    gerente=nome_gerente,
                    top_recomendacoes=dados_simulacao["top_recomendacoes"],
                )
                st.session_state.ultima_simulacao_id = sim_id
                st.toast(f"💾 Simulação salva (ID: {sim_id[-6:]})")

            except Exception as e:
                st.error(f"❌ Erro ao analisar oportunidades: {str(e)}")


def _renderizar_origem_cliente():
    origens = carregar_origens()
    return st.selectbox(
        "🎯 Origem do Cliente", ["(Não informado)"] + origens,
        key="cliente_origem", help="Como esse cliente chegou até nós?",
    )


def _renderizar_area_lazer():
    st.markdown("---")
    st.markdown("#### 🏖️ Preferências de Lazer")
    st.caption("Selecione uma ou mais opções que o cliente procura.")

    opcoes_lazer = carregar_lazer()
    return st.multiselect(
        "Opções de lazer desejadas", opcoes_lazer,
        key="cliente_lazer", label_visibility="collapsed",
    )


def _analisar(df_total, nome_cliente, renda_cliente, entrada_cliente,
              quartos_preferencia, tipo_preferencia, vagas_preferencia,
              lazer_preferencias, desconto_acordado, filtro_construtora,
              filtro_produto, usuario_logado, USUARIOS, origem_cliente):
    """Lógica de análise em todas as planilhas."""
    df = df_total.copy()
    etapas = [("Inicial", len(df))]

    # === Filtro construtora/produto (opcional) ===
    if filtro_construtora != "(Todas)":
        df = df[df["_construtora"] == filtro_construtora]
        etapas.append((f"Construtora ({filtro_construtora})", len(df)))

    if filtro_produto != "(Todos)":
        df = df[df["_produto"] == filtro_produto]
        etapas.append((f"Produto ({filtro_produto})", len(df)))

    # === Filtro quartos ===
    if quartos_preferencia != "Indiferente":
        qtd = int(quartos_preferencia.replace("+", ""))
        col_q = None
        for c in ["QUARTOS", "DORMITÓRIOS", "DORMITORIOS", "TIPO"]:
            if c in df.columns:
                col_q = c
                break
        if col_q:
            df = df[df[col_q].astype(str).str.contains(str(qtd), na=False)]
            etapas.append((f"Quartos ({qtd})", len(df)))

    # === Filtro tipo ===
    if tipo_preferencia != "Indiferente" and "TIPOLOGIA" in df.columns:
        df = df[df["TIPOLOGIA"].astype(str).str.contains(tipo_preferencia, case=False, na=False)]
        etapas.append((f"Tipo ({tipo_preferencia})", len(df)))

    # === Filtro vagas ===
    if vagas_preferencia != "Indiferente":
        vagas_min = int(vagas_preferencia.replace("+", ""))
        col_v = None
        for c in ["VAGA", "VAGAS", "VAGAS_GARAGEM"]:
            if c in df.columns:
                col_v = c
                break
        if col_v:
            import re as _re
            def tem_vagas(s):
                nums = _re.findall(r"\d+", str(s))
                return any(int(n) >= vagas_min for n in nums)
            df = df[df[col_v].apply(tem_vagas)]
            etapas.append((f"Vagas >= {vagas_min}", len(df)))

    # === Filtro lazer ===
    if lazer_preferencias:
        colunas_lazer = [c for c in df.columns if "LAZER" in c.upper()]
        if colunas_lazer:
            def atende_lazer(row):
                texto = " ".join(str(row.get(c, "")) for c in colunas_lazer).lower()
                return all(op.lower() in texto for op in lazer_preferencias)
            df = df[df.apply(atende_lazer, axis=1)]
            etapas.append((f"Lazer ({len(lazer_preferencias)})", len(df)))

    # === Aplica desconto POR LINHA (respeita _tipo_desconto) ===
    df = _aplicar_desconto_por_linha(df, desconto_acordado)

    if df.empty:
        _renderizar_diagnostico_vazio(etapas, df_total)
        return None

    if "R$/m²" in df.columns:
        df = df.sort_values("R$/m²")
    elif "VALOR_DA_AVALIACAO" in df.columns:
        df = df.sort_values("VALOR_DA_AVALIACAO")
    elif "PREÇO" in df.columns:
        df = df.sort_values("PREÇO")

    top_recomendacoes = df.head(5)

    return {
        "top_recomendacoes": top_recomendacoes,
        "df_filtrado_completo": df,
        "desconto_acordado": desconto_acordado,
        "tipo_desconto": "MISTO",
        "coluna_base": "PREÇO",
        "preco_col": "PREÇO",
        "nome_cliente": nome_cliente,
        "resumo": _gerar_resumo_simples(nome_cliente, renda_cliente, entrada_cliente,
                                          origem_cliente, top_recomendacoes),
        "renda": renda_cliente,
        "entrada": entrada_cliente,
        "vagas_preferencia": vagas_preferencia,
        "lazer_preferencias": lazer_preferencias,
    }


def _aplicar_desconto_por_linha(df, desconto):
    """Aplica o desconto em cada linha respeitando a regra da construtora."""
    if desconto <= 0:
        # Sem desconto: valor_base = valor principal (AVALIAÇÃO ou PREÇO)
        def _sem_desc(row):
            for c in ["AVALIAÇÃO", "AVALIACAO", "VALOR_DA_AVALIACAO", "PREÇO", "PRECO", "VALOR"]:
                if c in row.index and pd.notna(row[c]):
                    try:
                        return float(row[c])
                    except (ValueError, TypeError):
                        continue
            return 0.0
        df["valor_base"] = df.apply(_sem_desc, axis=1)
        return df

    def _com_desc(row):
        tipo = str(row.get("_tipo_desconto", "AVALIAÇÃO")).upper()
        if "AVALIA" in tipo:
            candidatos = ["AVALIAÇÃO", "AVALIACAO", "VALOR_DA_AVALIACAO", "VALOR_DE_AVALIACAO"]
        else:
            candidatos = ["PREÇO", "PRECO", "VALOR_DO_IMOVEL", "VALOR"]

        base = None
        for c in candidatos:
            if c in row.index and pd.notna(row[c]):
                try:
                    base = float(row[c])
                    break
                except (ValueError, TypeError):
                    continue

        if base is None:
            # Fallback: pega qualquer coluna com valor
            for c in ["AVALIAÇÃO", "PREÇO", "VALOR_DA_AVALIACAO", "VALOR_DO_IMOVEL", "VALOR"]:
                if c in row.index and pd.notna(row[c]):
                    try:
                        base = float(row[c])
                        break
                    except (ValueError, TypeError):
                        continue

        if base is None:
            return 0.0
        return max(0.0, base - desconto)

    df["valor_base"] = df.apply(_com_desc, axis=1)
    return df


def _renderizar_diagnostico_vazio(etapas, df_original):
    st.warning("⚠️ Nenhuma oportunidade encontrada. Diagnóstico:")
    with st.expander("🔍 Ver detalhes", expanded=True):
        for nome, qtd in etapas:
            icon = "🔴" if qtd == 0 else "🟢"
            st.write(f"{icon} **{nome}:** {qtd} imóveis")
        st.caption("💡 Dica: diminua filtros (vagas, quartos) ou remova o filtro de lazer.")


def _gerar_resumo_simples(nome_cliente, renda, entrada, origem, top_imoveis):
    """Gera resumo textual simples para compartilhar."""
    from src.utils import formatar_valor_br
    linhas = [f"SIMULAÇÃO — {nome_cliente}", "=" * 40]
    if origem and origem != "(Não informado)":
        linhas.append(f"Origem: {origem}")
    linhas.append(f"Renda: {formatar_valor_br(renda)}")
    linhas.append(f"Entrada: {formatar_valor_br(entrada)}")
    linhas.append("")
    if top_imoveis is not None and not top_imoveis.empty:
        linhas.append("TOP OPORTUNIDADES:")
        for i, (_, row) in enumerate(top_imoveis.iterrows(), 1):
            unidade = row.get("UNIDADE", "N/A")
            construtora = row.get("_construtora", "")
            produto = row.get("_produto", "")
            valor = row.get("valor_base", 0)
            linhas.append(f"{i}. {construtora} • {produto} • Unidade {unidade}")
            linhas.append(f"   Valor: {formatar_valor_br(valor)}")
    return "\n".join(linhas)