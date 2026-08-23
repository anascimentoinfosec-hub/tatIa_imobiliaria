import streamlit as st
import pandas as pd
import io
import tabula

# CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="IA Imobiliária", layout="wide")
st.title("🏢 IA Imobiliária - Oásis II")
st.markdown("---")

# SIDEBAR
with st.sidebar:
    st.header("⚙️ Configurações")
    uploaded_file = st.file_uploader(
        "📤 Envie a planilha da construtora",
        type=['xlsx', 'xls', 'csv', 'pdf']
    )
    st.markdown("---")
    st.caption("Versão 1.0 - Desenvolvido com IA")

# CORPO PRINCIPAL
if uploaded_file is not None:
    try:
        # Lê o arquivo conforme o tipo
        if uploaded_file.name.endswith('.pdf'):
            # Lê PDF com tabula
            df = tabula.read_pdf(io.BytesIO(uploaded_file.read()), pages='all')[0]
        elif uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file, skiprows=2)
        
        # Limpeza
        df = df.dropna(subset=['UNIDADE'])
        
        with st.expander("📊 Visualizar dados da planilha"):
            st.dataframe(df)
        
        st.markdown("---")
        
        # FILTROS
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            tipologias = ['Todas'] + sorted(df['TIPOLOGIA'].unique().tolist())
            tipo_selecionado = st.selectbox("🏠 Tipologia", tipologias)
        
        with col2:
            andar_min = st.number_input("📌 Andar mínimo", min_value=0, value=0)
        
        with col3:
            preco_max = st.number_input(
                "💰 Preço máximo (R$)",
                min_value=100000,
                value=int(df['PREÇO'].max()),
                step=50000,
                format="%d"
            )
        
        with col4:
            disponibilidade = st.selectbox(
                "🔑 Disponibilidade",
                ['Todas', 'LIVRE', 'RESERVADA', 'VENDIDA']
            )
        
        # APLICA FILTROS
        resultado = df.copy()
        
        if tipo_selecionado != 'Todas':
            resultado = resultado[resultado['TIPOLOGIA'] == tipo_selecionado]
        
        if andar_min > 0:
            resultado = resultado[resultado['PAVTO.'] >= andar_min]
        
        resultado = resultado[resultado['PREÇO'] <= preco_max]
        
        if disponibilidade != 'Todas':
            resultado = resultado[resultado['DISPONIBILIDADE'] == disponibilidade]
        
        # CALCULA INDICADORES
        if not resultado.empty:
            resultado['R$/m²'] = (resultado['PREÇO'] / resultado['M²']).round(2)
            resultado['% DESCONTO'] = ((resultado['1ª AVALIAÇÃO OÁSIS II'] - resultado['PREÇO']) / resultado['1ª AVALIAÇÃO OÁSIS II'] * 100).round(1)
        
        # EXIBE RESULTADOS
        st.subheader(f"🔍 Resultados: {len(resultado)} imóveis encontrados")
        
        if not resultado.empty:
            resultado_ordenado = resultado.sort_values('R$/m²')
            
            colunas_exibir = ['UNIDADE', 'PAVTO.', 'COLUNA', 'M²', 'TIPOLOGIA', 'VAGA', 'SOL', 'PREÇO', 'R$/m²', '% DESCONTO', 'DISPONIBILIDADE']
            st.dataframe(
                resultado_ordenado[colunas_exibir],
                use_container_width=True,
                height=400
            )
            
            st.markdown("---")
            st.subheader("🤖 Recomendação da IA")
            
            melhor = resultado_ordenado.iloc[0]
            
            col_a, col_b = st.columns([2, 1])
            
            with col_a:
                st.success(f"**Melhor custo-benefício:** Unidade {melhor['UNIDADE']}")
                st.write(f"- **Preço:** R$ {melhor['PREÇO']:,.2f}")
                st.write(f"- **R$/m²:** R$ {melhor['R$/m²']:.2f}")
                st.write(f"- **Desconto:** {melhor['% DESCONTO']}%")
                st.write(f"- **Tipologia:** {melhor['TIPOLOGIA']}")
            
            with col_b:
                valor = melhor['PREÇO']
                entrada_percentual = st.slider("Entrada (%)", 20, 50, 30)
                entrada = valor * (entrada_percentual / 100)
                financiado = valor - entrada
                juros = 0.10
                prazo_meses = 420
                parcela_media = financiado * (1 + juros/12) / prazo_meses
                
                st.info(f"**Simulação - Unidade {melhor['UNIDADE']}**")
                st.write(f"Valor total: R$ {valor:,.2f}")
                st.write(f"Entrada ({entrada_percentual}%): R$ {entrada:,.2f}")
                st.write(f"Financiado: R$ {financiado:,.2f}")
                st.write(f"Parcela estimada: R$ {parcela_media:,.2f}")
                st.caption(f"*Prazo: {prazo_meses} meses (35 anos), juros: {juros*100}% a.a. (SAC)*")
        else:
            st.warning("⚠️ Nenhum imóvel encontrado com os filtros atuais. Tente ajustar.")
    
    except Exception as e:
        st.error(f"❌ Erro ao ler a planilha: {str(e)}")
        st.info("Verifique se o arquivo está no formato correto (XLSX, CSV ou PDF)")

else:
    st.info("👈 Envie a planilha da construtora no menu lateral para começar")
    st.markdown("""
    ### Como usar:
    1. Clique em **"Browse files"** no menu lateral
    2. Selecione a planilha (XLSX, CSV ou PDF) da construtora
    3. Ajuste os filtros
    4. A IA recomenda o melhor imóvel
    """)
