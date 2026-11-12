def renderizar_espelho_vendas():
    # === CSS PARA COMPACTAR O TOPO DA TELA ===
    st.markdown("""
        <style>
        .block-container { padding-top: 1rem !important; padding-bottom: 0rem !important; }
        h1 { font-size: 1.8rem !important; margin-top: 0 !important; margin-bottom: 5px !important; padding-bottom: 0 !important; border-bottom: none !important; }
        div[data-testid="stHorizontalBlock"] { margin-bottom: -10px !important; }
        .stSelectbox { margin-bottom: 0px !important; }
        hr { margin: 0.5rem 0 !important; }
        .legenda-compacta { font-size: 13px; margin-top: 5px; margin-bottom: 10px; color: #475569; }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("<h1>🏢 Espelho de Vendas</h1>", unsafe_allow_html=True)

    from src.construtoras_storage import carregar_construtoras
    construtoras = carregar_construtoras()
    
    if not construtoras:
        st.warning("Nenhuma construtora cadastrada.")
        return

    # === SELETORES ===
    col1, col2, col3 = st.columns(3)
    
    with col1:
        construtora = st.selectbox("🏗️ Construtora", list(construtoras.keys()), key="esp_c")
    
    with col2:
        produtos = list(construtoras[construtora].get("produtos", {}).keys())
        if produtos:
            produto = st.selectbox("📦 Produto", produtos, key="esp_p")
        else:
            st.warning("Sem produtos para esta construtora.")
            return

    # 2. Carrega os dados
    if not tem_planilha_cache(construtora, produto):
        st.warning(f"⚠️ Nenhuma planilha em cache para {construtora} - {produto}.")
        return

    df = carregar_planilha_cache(construtora, produto)
    if df is None or df.empty:
        st.warning("Planilha vazia.")
        return

    # 3. Inteligência de Detecção de Colunas
    col_bloco = next((c for c in ["BLOCO", "TORRE"] if c in df.columns), None)
    col_andar = next((c for c in ["PAVTO", "ANDAR"] if c in df.columns), None)
    col_unidade = next((c for c in ["UNIDADE", "APT"] if c in df.columns), None)
    col_preco = next((c for c in ["VALOR_DA_AVALIACAO", "VALOR_DO_IMOVEL", "PREÇO"] if c in df.columns), None)
    
    # NOVO: Detectar coluna de Empreendimento
    col_empreendimento = next((c for c in ["EMPREENDIMENTO", "NOME_DO_PRODUTO", "PRODUTO"] if c in df.columns), None)

    if not col_unidade:
        st.error("A planilha não tem uma coluna de Unidade/APT identificável.")
        return

    # === SELETOR DE BLOCO E EMPREENDIMENTO ===
    with col3:
        if col_bloco:
            blocos_disponiveis = ["Todos"] + sorted(df[col_bloco].dropna().astype(str).unique().tolist())
            filtro_bloco = st.selectbox("🏢 Bloco", blocos_disponiveis, key="esp_b")
            if filtro_bloco != "Todos":
                df = df[df[col_bloco].astype(str) == filtro_bloco]
        else:
            st.info("Planilha sem coluna de Bloco.")

    if col_empreendimento:
        colunas_filtro_emp = st.columns(3)
        with colunas_filtro_emp[0]:
            emps_disponiveis = ["Todos"] + sorted(df[col_empreendimento].dropna().astype(str).unique().tolist())
            filtro_emp = st.selectbox("🏙️ Empreendimento", emps_disponiveis, key="esp_emp")
            if filtro_emp != "Todos":
                df = df[df[col_empreendimento].astype(str) == filtro_emp]

    # 4. Carrega os status das unidades do banco
    marcadas = carregar_todas_marcadas()

    # 5. Legenda Compacta
    st.markdown("""
        <div class="legenda-compacta">
            <b>Legenda:</b> 
            <span style="color:#22c55e; font-size:16px;">●</span> Disponível &nbsp;&nbsp;
            <span style="color:#f59e0b; font-size:16px;">●</span> Em Processo &nbsp;&nbsp;
            <span style="color:#ef4444; font-size:16px;">●</span> Vendido &nbsp;&nbsp;
            <span style="color:#cbd5e1; font-size:16px;">●</span> Sem Info
        </div>
    """, unsafe_allow_html=True)

    # Ordena por bloco e andar
    if col_bloco:
        df = df.sort_values(by=[col_bloco, col_andar if col_andar else col_unidade])
    elif col_andar:
        df = df.sort_values(by=[col_andar, col_unidade])
    else:
        df = df.sort_values(by=[col_unidade])

    # Renderiza o Grid
    _renderizar_grid_html(df, construtora, produto, marcadas, col_bloco, col_andar, col_unidade, col_preco)