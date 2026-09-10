import streamlit as st
import pandas as pd
import json
import os
from src.planilha import ler_planilha
from src.utils import converter_para_float, formatar_valor_br
from src.planilha_cache import salvar_planilha_cache, carregar_planilha_cache, tem_planilha_cache, excluir_planilha_cache
from src.recomendacoes import recomendar_imoveis
from src.construtoras import carregar_cidades, carregar_construtoras
from src.compartilhar import gerar_resumo, botoes_compartilhar
from src.regras.financeiro import calcular_parcela_price, calcular_entrada_e_financiado, calcular_comprometimento_renda


ARQUIVO_CONFIG = "dados/construtoras.json"

def _obter_tipo_desconto(construtora_selecionada, CONSTRUTORAS):
    try:
        if os.path.exists(ARQUIVO_CONFIG):
            with open(ARQUIVO_CONFIG, 'r', encoding='utf-8') as f:
                dados = json.load(f)
                if construtora_selecionada in dados:
                    return dados[construtora_selecionada].get("tipo_desconto", "AVALIAÇÃO")
    except:
        pass
    return CONSTRUTORAS.get(construtora_selecionada, {}).get("tipo_desconto", "AVALIAÇÃO")

def _renderizar_cards(top_recomendacoes, desconto_acordado, tipo_desconto, coluna_base, preco_col, nome_cliente):
    """Renderiza os cards das recomendações (fora do botão para persistir)"""
    if top_recomendacoes is None or top_recomendacoes.empty:
        st.warning(f"⚠️ Nenhuma oportunidade encontrada para {nome_cliente}.")
        return
    st.success(f"✅ {len(top_recomendacoes)} oportunidades encontradas para {nome_cliente}!")
    for idx, row in top_recomendacoes.iterrows():
        with st.container():
            st.markdown("---")
            col_a, col_b = st.columns([3, 2])
            with col_a:
                st.markdown(f"**🏢 Unidade {row['UNIDADE']}**")
                st.caption(f"💡 Desconto sobre: {tipo_desconto}")

                # SEMPRE mostra AVALIAÇÃO primeiro
                if "AVALIAÇÃO" in row:
                    st.write(f"📊 **Avaliação:** {formatar_valor_br(row['AVALIAÇÃO'])}")

                if coluna_base == "PREÇO" and preco_col in row:
                    st.write(f"💵 **Preço original:** {formatar_valor_br(row[preco_col])}")

                st.write(f"💸 **Desconto:** {formatar_valor_br(desconto_acordado)}")
                st.write(f"💰 **Valor base:** {formatar_valor_br(row['valor_base'])}")
                if 'parcela_estimada' in row:
                    st.write(f"📆 **Parcela estimada:** {formatar_valor_br(row['parcela_estimada'])}")
                if 'TIPOLOGIA' in row:
                    st.write(f"🏠 **Tipo:** {row['TIPOLOGIA']}")
            with col_b:
                entrada_percentual = st.slider(
                    f"Entrada (%) - Unidade {row['UNIDADE']}",
                    min_value=20, max_value=50, value=20, step=5,
                    key=f"entrada_{idx}"
                )
                valor_base = row['valor_base']
                entrada_fin = calcular_entrada_e_financiado(valor_base, entrada_percentual)
                entrada_valor = entrada_fin["entrada"]
                financiado = entrada_fin["financiado"]
                parcela_media = calcular_parcela_price(financiado, 0.10, 420)
                st.write(f"💵 **Entrada:** {formatar_valor_br(entrada_valor)}")
                st.write(f"🏦 **Financiado:** {formatar_valor_br(financiado)}")
                st.write(f"📆 **Parcela:** {formatar_valor_br(parcela_media)}")

def pagina_simulador(CONSTRUTORAS, USUARIOS):
    if not CONSTRUTORAS:
        st.warning("⚠️ Nenhuma construtora cadastrada. Cadastre uma construtora primeiro.")
        return

    st.title("📊 Simulador de Crédito")

    usuario_logado = st.session_state.get("usuario_logado")
    if usuario_logado and usuario_logado in USUARIOS:
        perfil_usuario = USUARIOS[usuario_logado].get("perfil", "corretor")
    else:
        perfil_usuario = "corretor"

    with st.sidebar:
        st.header("⚙️ Configurações")
        construtora_selecionada = st.selectbox("🏗️ Selecione a construtora", options=list(CONSTRUTORAS.keys()))
        tipo_desconto = _obter_tipo_desconto(construtora_selecionada, CONSTRUTORAS)

        produtos = CONSTRUTORAS[construtora_selecionada].get("produtos", {})
        produtos_lista = list(produtos.keys())
        if produtos_lista:
            produto_selecionado = st.selectbox("📦 Selecione o produto", options=produtos_lista)
        else:
            st.warning("⚠️ Nenhum produto cadastrado para esta construtora.")
            produto_selecionado = None
        st.markdown("---")
        if perfil_usuario in ["gerente", "superadmin"] and produto_selecionado:
            st.markdown("### 📤 Upload")
            uploaded_file = st.file_uploader(
                f"Planilha para {construtora_selecionada} - {produto_selecionado}",
                type=['xlsx', 'xls', 'csv'],
                key=f"upload_{construtora_selecionada}_{produto_selecionado}"
            )
            if st.button("📥 Carregar", use_container_width=True):
                if uploaded_file is None:
                    st.warning("⚠️ Selecione um arquivo primeiro!")
                else:
                    try:
                        config = produtos[produto_selecionado]
                        df = ler_planilha(uploaded_file, config)
                        if df is None:
                            st.error("❌ Erro ao ler a planilha. Verifique o formato e o mapeamento.")
                        else:
                            colunas_monetarias = ['AVALIAÇÃO', 'PREÇO', 'VALOR', 'DESCONTO', '1ª AVALIAÇÃO OÁSIS II']
                            for col in colunas_monetarias:
                                if col in df.columns:
                                    df[col] = df[col].astype(str).str.replace('RS', '', regex=False)
                                    df[col] = df[col].str.replace('R$', '', regex=False)
                                    df[col] = df[col].str.replace('R', '', regex=False)
                                    df[col] = df[col].str.strip()
                                    df[col] = df[col].str.replace('.', '', regex=False)
                                    df[col] = df[col].str.replace(',', '.', regex=False)
                                    df[col] = df[col].str.extract(r'(\d+\.?\d*)')
                                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
                            for col in config.get("colunas_para_converter", []):
                                if col in df.columns and col not in colunas_monetarias:
                                    df[col] = df[col].apply(converter_para_float)
                            salvar_planilha_cache(construtora_selecionada, df, produto_selecionado)
                            st.success(f"✅ Planilha '{produto_selecionado}' carregada com sucesso!")
                    except Exception as e:
                        st.error(f"❌ Erro ao carregar a planilha: {str(e)}")
            st.markdown("---")
            if st.button("🗑️ Limpar cache", use_container_width=True):
                excluir_planilha_cache(construtora_selecionada, produto_selecionado)
                st.success(f"✅ Cache de '{produto_selecionado}' removido!")
        else:
            st.info("🔒 As planilhas são gerenciadas pelo gerente.")
        st.markdown("---")
        st.caption(f"Versão 6.2 - Desconto sobre: {tipo_desconto}")

    if not produto_selecionado:
        st.warning("⚠️ Selecione um produto para visualizar os dados.")
        return

    config = produtos[produto_selecionado]
    df = None
    if tem_planilha_cache(construtora_selecionada, produto_selecionado):
        df = carregar_planilha_cache(construtora_selecionada, produto_selecionado)
    if df is None:
        st.warning(f"⚠️ Nenhuma planilha disponível para '{produto_selecionado}'. Faça o upload.")
        return

    colunas_monetarias = ['AVALIAÇÃO', 'PREÇO', 'VALOR', 'DESCONTO', '1ª AVALIAÇÃO OÁSIS II']
    for col in colunas_monetarias:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    st.info(f"📂 Planilha carregada do cache: {construtora_selecionada} - {produto_selecionado}")
    if "df_imoveis_cache" not in st.session_state:
        st.session_state.df_imoveis_cache = {}
    chave_cache = f"{construtora_selecionada}_{produto_selecionado}"
    st.session_state.df_imoveis_cache[chave_cache] = df
    st.session_state.df_imoveis = df

    st.markdown("---")

    # --- FILTROS ---
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        tipo_col = None
        for c in ['TIPOLOGIA', 'QUARTOS', 'DORMITÓRIOS', 'TIPO']:
            if c in df.columns:
                tipo_col = c
                break
        if tipo_col:
            tipos = ['Todas'] + sorted(df[tipo_col].dropna().unique().tolist())
            tipo_selecionado = st.selectbox("🏠 Tipo", tipos)
        else:
            tipo_selecionado = 'Todas'
    with col2:
        andar_col = None
        for c in ['PAVTO', 'ANDAR']:
            if c in df.columns:
                andar_col = c
                break
        if andar_col:
            andar_min = st.number_input("📌 Andar mínimo", min_value=0, value=0, step=1)
        else:
            andar_min = 0
    with col3:
        preco_col = None
        for c in ['PREÇO', 'VALOR']:
            if c in df.columns:
                preco_col = c
                break
        if preco_col is None:
            st.error("❌ Nenhuma coluna de preço encontrada.")
            return
        if not df[preco_col].isna().all():
            preco_max = st.number_input("💰 Preço máximo (R$)", min_value=0, value=int(df[preco_col].max()) if df[preco_col].max() > 0 else 1000000, step=50000, format="%d")
        else:
            preco_max = 1000000
    with col4:
        status_col = None
        for c in ['DISPONIBILIDADE', 'STATUS', 'SITUAÇÃO']:
            if c in df.columns:
                status_col = c
                break
        if status_col:
            status_opcoes = ['Todas'] + sorted(df[status_col].dropna().unique().tolist())
            status_selecionado = st.selectbox("🔑 Disponibilidade", status_opcoes)
        else:
            status_selecionado = 'Todas'

    resultado = df.copy()
    if tipo_selecionado != 'Todas' and tipo_col:
        resultado = resultado[resultado[tipo_col] == tipo_selecionado]
    if andar_min > 0 and andar_col:
        resultado = resultado[resultado[andar_col] >= andar_min]
    if preco_col and preco_col in df.columns:
        resultado = resultado[resultado[preco_col] <= preco_max]
    if status_selecionado != 'Todas' and status_col:
        resultado = resultado[resultado[status_col] == status_selecionado]

    if not resultado.empty:
        area_col = None
        for c in ['M²', 'AREA_M2', 'AREA']:
            if c in resultado.columns:
                area_col = c
                break
        if preco_col and area_col:
            resultado['R$/m²'] = (resultado[preco_col] / resultado[area_col]).round(2)

    colunas_ordem = config.get("colunas_ordem", list(df.columns)).copy()
    if 'R$/m²' in resultado.columns:
        colunas_ordem.append('R$/m²')
    colunas_ordem = [c for c in colunas_ordem if c in resultado.columns]

    st.subheader(f"🔍 Resultados: {len(resultado)} imóveis encontrados")
    st.caption(f"📌 {construtora_selecionada} - {produto_selecionado}  |  💡 Desconto sobre: {tipo_desconto}")
    if not resultado.empty:
        if 'R$/m²' in resultado.columns:
            resultado_ordenado = resultado.sort_values('R$/m²')
        else:
            resultado_ordenado = resultado
        df_exibicao = resultado_ordenado.copy()
        for col in ['PREÇO', 'VALOR', 'AVALIAÇÃO', 'DESCONTO', '1ª AVALIAÇÃO OÁSIS II', 'R$/m²']:
            if col in df_exibicao.columns:
                df_exibicao[col] = df_exibicao[col].apply(formatar_valor_br)
        if "M²" in df_exibicao.columns:
            df_exibicao["M²"] = df_exibicao["M²"].apply(lambda x: f"{x:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.') if not pd.isna(x) else "")
        st.dataframe(df_exibicao[colunas_ordem], use_container_width=True, height=400)

    st.markdown("---")

    # =========================================================
    # ÁREA DO CLIENTE
    # =========================================================
    st.subheader("🧑 Área do Cliente")
    st.markdown("Preencha os dados abaixo para receber recomendações personalizadas.")

    with st.container():
        col_cliente1, col_cliente2 = st.columns(2)
        with col_cliente1:
            nome_cliente = st.text_input("Nome do Cliente", placeholder="Ex: João Silva", key="cliente_nome")
            renda_cliente = st.number_input("💰 Renda líquida mensal (R$)", min_value=0.0, value=5000.0, step=500.0, format="%.2f", key="cliente_renda")
            entrada_cliente = st.number_input("🏦 Valor disponível para entrada (R$)", min_value=0.0, value=100000.0, step=10000.0, format="%.2f", key="cliente_entrada")
        with col_cliente2:
            cidades_disponiveis = carregar_cidades()
            opcoes_bairro = [""] + cidades_disponiveis
            bairro_preferencia = st.selectbox("📍 Bairro de preferência", opcoes_bairro, key="cliente_bairro")
            quartos_preferencia = st.selectbox("🛏️ Quantos quartos?", ["Indiferente", "1", "2", "3", "4+"], key="cliente_quartos")
            tipo_preferencia = st.selectbox("🏠 Tipo de imóvel", ["Indiferente", "Apartamento", "Cobertura", "Garden"], key="cliente_tipo")

            desconto_acordado = st.number_input(
                "💸 Desconto acordado (R$)",
                min_value=0.0,
                value=0.0,
                step=1000.0,
                format="%.2f",
                help=f"Desconto será aplicado sobre: {tipo_desconto}",
                key="cliente_desconto"
            )

        if st.button("🔍 Analisar Oportunidades", use_container_width=True):
            if not nome_cliente:
                st.warning("⚠️ Por favor, informe o nome do cliente.")
            else:
                with st.spinner("Analisando oportunidades..."):
                    try:
                        df_filtrado = resultado.copy()

                        if quartos_preferencia != "Indiferente":
                            qtd = int(quartos_preferencia.replace("+", ""))
                            col_quartos = None
                            for c in ['QUARTOS', 'DORMITÓRIOS', 'TIPO']:
                                if c in df_filtrado.columns:
                                    col_quartos = c
                                    break
                            if col_quartos:
                                df_filtrado = df_filtrado[df_filtrado[col_quartos].astype(str).str.contains(str(qtd))]

                        if tipo_preferencia != "Indiferente" and "TIPOLOGIA" in df_filtrado.columns:
                            df_filtrado = df_filtrado[df_filtrado["TIPOLOGIA"].astype(str).str.contains(tipo_preferencia, case=False, na=False)]

                        if tipo_desconto == "AVALIAÇÃO":
                            coluna_base = "AVALIAÇÃO"
                        else:
                            coluna_base = "PREÇO"

                        if coluna_base in df_filtrado.columns:
                            df_filtrado["valor_base"] = df_filtrado[coluna_base] - desconto_acordado
                            df_filtrado["valor_base"] = df_filtrado["valor_base"].clip(lower=0)
                        else:
                            df_filtrado["valor_base"] = df_filtrado["PREÇO"]

                        parcela_maxima = renda_cliente * 0.3

                        if preco_col in df_filtrado.columns:
                            df_filtrado["parcela_estimada"] = df_filtrado["valor_base"] * 0.005
                            df_filtrado = df_filtrado[df_filtrado["parcela_estimada"] <= parcela_maxima]
                            if 'R$/m²' in df_filtrado.columns:
                                df_filtrado = df_filtrado.sort_values('R$/m²')

                        top_recomendacoes = df_filtrado.head(5)

                        resumo = gerar_resumo(
                            nome_cliente,
                            renda_cliente,
                            entrada_cliente,
                            bairro_preferencia,
                            top_recomendacoes,
                            nome_gerente=USUARIOS[usuario_logado]['nome'],
                            desconto=desconto_acordado,
                            tipo_desconto=tipo_desconto
                        )

                        # === SALVA NO SESSION_STATE ===
                        st.session_state.simulacao_ativa = {
                            "top_recomendacoes": top_recomendacoes,
                            "desconto_acordado": desconto_acordado,
                            "tipo_desconto": tipo_desconto,
                            "coluna_base": coluna_base,
                            "preco_col": preco_col,
                            "nome_cliente": nome_cliente,
                            "resumo": resumo
                        }
                    except Exception as e:
                        st.error(f"❌ Erro ao analisar oportunidades: {str(e)}")

    # === RENDERIZA A SIMULAÇÃO FORA DO BOTÃO (persiste ao mexer no slider) ===
    if st.session_state.get("simulacao_ativa"):
        sim = st.session_state.simulacao_ativa
        st.markdown("---")
        st.markdown("### 📤 Compartilhar Simulação")
        botoes_compartilhar(sim["resumo"], sim["nome_cliente"])
        st.markdown("---")
        _renderizar_cards(
            sim["top_recomendacoes"],
            sim["desconto_acordado"],
            sim["tipo_desconto"],
            sim["coluna_base"],
            sim["preco_col"],
            sim["nome_cliente"]
        )

    st.markdown("---")
    st.markdown("### 💰 Ajuste de Entrada")
    st.caption("Ajuste o percentual de entrada para simular diferentes cenários.")
    entrada_percentual_global = st.slider("Percentual de entrada (%)", min_value=20, max_value=50, value=20, step=5, key="entrada_global")
    if preco_col in df.columns and not df.empty:
        valor_medio = df[preco_col].mean()
        entrada_fin_g = calcular_entrada_e_financiado(valor_medio, entrada_percentual_global)
        entrada_media = entrada_fin_g["entrada"]
        financiado_medio = entrada_fin_g["financiado"]
        parcela_media_global = calcular_parcela_price(financiado_medio, 0.10, 420)
        st.markdown("**📊 Simulação média com base nos imóveis disponíveis:**")
        col_s1, col_s2, col_s3 = st.columns(3)
        col_s1.metric("💰 Valor médio", formatar_valor_br(valor_medio))
        col_s2.metric(f"💵 Entrada ({entrada_percentual_global}%)", formatar_valor_br(entrada_media))
        col_s3.metric("📆 Parcela média", formatar_valor_br(parcela_media_global))

    st.markdown("---")
    if st.button("💬 Perguntar à BIA (IA Imobiliária)", use_container_width=True):
        st.session_state.pagina = "ChatIA"
        st.rerun()