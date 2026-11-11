import streamlit as st
import pandas as pd
from src.planilha_cache import carregar_planilha_cache, tem_planilha_cache
from src.unidades_status_storage import carregar_todas_marcadas

def renderizar_espelho_vendas():
    # === CSS PARA COMPACTAR O TOPO DA TELA ===
    st.markdown("""
        <style>
        /* Reduz o espaço em branco do topo da página */
        .block-container { padding-top: 1rem !important; padding-bottom: 0rem !important; }
        /* Deixa o título mais compacto */
        h1 { font-size: 1.8rem !important; margin-top: 0 !important; margin-bottom: 5px !important; padding-bottom: 0 !important; border-bottom: none !important; }
        /* Reduz o espaço entre os seletores e a legenda */
        div[data-testid="stHorizontalBlock"] { margin-bottom: -10px !important; }
        .stSelectbox { margin-bottom: 0px !important; }
        hr { margin: 0.5rem 0 !important; }
        /* Legenda compacta */
        .legenda-compacta { font-size: 13px; margin-top: 5px; margin-bottom: 10px; color: #475569; }
        </style>
    """, unsafe_allow_html=True)

    # Título mais próximo do topo
    st.markdown("<h1>🏢 Espelho de Vendas</h1>", unsafe_allow_html=True)

    # 1. Seleção de Construtora e Produto
    from src.construtoras_storage import carregar_construtoras
    construtoras = carregar_construtoras()
    
    if not construtoras:
        st.warning("Nenhuma construtora cadastrada.")
        return

    col1, col2 = st.columns(2)
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

    # 3. Carrega os status das unidades do banco
    marcadas = carregar_todas_marcadas()

    # 4. Prepara as colunas de exibição
    col_bloco = next((c for c in ["BLOCO", "TORRE"] if c in df.columns), None)
    col_andar = next((c for c in ["PAVTO", "ANDAR"] if c in df.columns), None)
    col_unidade = next((c for c in ["UNIDADE", "APT"] if c in df.columns), None)
    col_preco = next((c for c in ["VALOR_DA_AVALIACAO", "VALOR_DO_IMOVEL", "PREÇO"] if c in df.columns), None)

    if not col_unidade:
        st.error("A planilha não tem uma coluna de Unidade/APT identificável.")
        return

    # 5. Legenda Compacta em uma única linha
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


def _renderizar_grid_html(df, construtora, produto, marcadas, col_bloco, col_andar, col_unidade, col_preco):
    """Desenha os quadradinhos coloridos via HTML/CSS com rolagem."""
    
    st.markdown("""
        <style>
        /* A CAIXA MÁGICA COM ROLAGEM */
        .grid-container {
            max-height: 550px; /* Aumentei um pouco para caber mais coisas na tela */
            overflow-y: auto;
            padding: 15px;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            background-color: #f8fafc;
            margin-bottom: 10px;
        }
        
        /* QUADRADINHO */
        .unidade-card {
            display: inline-block;
            width: 90px;
            height: 60px;
            margin: 5px;
            border-radius: 6px;
            text-align: center;
            font-size: 12px;
            color: white;
            font-weight: bold;
            padding-top: 10px;
            box-sizing: border-box;
            cursor: pointer;
            transition: transform 0.2s;
        }
        .unidade-card:hover {
            transform: scale(1.1);
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        }
        
        /* CORES */
        .status-disponivel { background-color: #22c55e; color: white; }
        .status-em_processo { background-color: #f59e0b; color: white; }
        .status-vendida { background-color: #ef4444; color: white; }
        .status-sem_info { background-color: #cbd5e1; color: #333; }
        
        /* Título do Bloco mais compacto */
        h4 { margin-top: 10px !important; margin-bottom: 5px !important; font-size: 1.1rem !important; }
        </style>
    """, unsafe_allow_html=True)

    agrupador = col_bloco if col_bloco else (col_andar if col_andar else None)

    if agrupador:
        for grupo_nome in df[agrupador].dropna().unique():
            st.markdown(f"#### 🏢 {agrupador}: {grupo_nome}")
            df_grupo = df[df[agrupador] == grupo_nome]
            
            html_str = ""
            for _, row in df_grupo.iterrows():
                unidade = str(row[col_unidade])
                chave = (str(construtora), str(produto), unidade)
                
                info = marcadas.get(chave)
                status = info.get("status") if info else "disponivel"
                
                if status == "vendida":
                    classe = "status-vendida"
                    titulo = "Vendida"
                elif status == "em_processo":
                    classe = "status-em_processo"
                    titulo = "Em Processo"
                else:
                    classe = "status-disponivel"
                    titulo = "Disponível"
                
                preco_str = ""
                if col_preco and pd.notna(row[col_preco]):
                    try:
                        val = float(row[col_preco])
                        preco_str = f"R$ {val:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")
                    except:
                        pass
                
                tooltip = f"{unidade} | {titulo} | {preco_str}"
                
                html_str += f'<div class="unidade-card {classe}" title="{tooltip}">{unidade}<br><span style="font-size:10px;">{preco_str}</span></div>'
            
            st.markdown(f'<div class="grid-container">{html_str}</div>', unsafe_allow_html=True)
            # Removi o st.markdown("---") entre os blocos para economizar espaço
    else:
        st.info("A planilha não tem coluna de Bloco ou Andar para agrupar.")