import streamlit as st
import pandas as pd
from src.planilha_cache import carregar_planilha_cache, tem_planilha_cache
from src.unidades_status_storage import carregar_todas_marcadas

def renderizar_espelho_vendas():
    st.title("🏢 Espelho de Vendas")
    st.caption("Visão interativa do status de cada unidade do empreendimento.")
    st.markdown("---")

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

    # 3. Carrega os status das unidades do banco (Vendida/Em processo)
    marcadas = carregar_todas_marcadas()

    # 4. Prepara as colunas de exibição
    # Descobre a coluna de Bloco/Andar, Unidade e Preço
    col_bloco = next((c for c in ["BLOCO", "TORRE"] if c in df.columns), None)
    col_andar = next((c for c in ["PAVTO", "ANDAR"] if c in df.columns), None)
    col_unidade = next((c for c in ["UNIDADE", "APT"] if c in df.columns), None)
    col_preco = next((c for c in ["VALOR_DA_AVALIACAO", "VALOR_DO_IMOVEL", "PREÇO"] if c in df.columns), None)

    if not col_unidade:
        st.error("A planilha não tem uma coluna de Unidade/APT identificável.")
        return

    # 5. Agrupa os dados para montar o Grid
    st.markdown("### Legenda:")
    st.markdown("🟢 **Disponível** | 🟡 **Em Processo/Reservado** | 🔴 **Vendido** | ⚪ **Sem Info**")
    st.markdown("---")

    # Ordena por bloco e andar para o espelho ficar organizado
    if col_bloco:
        df = df.sort_values(by=[col_bloco, col_andar if col_andar else col_unidade])
    elif col_andar:
        df = df.sort_values(by=[col_andar, col_unidade])
    else:
        df = df.sort_values(by=[col_unidade])

    # Renderiza o Grid
    _renderizar_grid_html(df, construtora, produto, marcadas, col_bloco, col_andar, col_unidade, col_preco)


def _renderizar_grid_html(df, construtora, produto, marcadas, col_bloco, col_andar, col_unidade, col_preco):
    """Desenha os quadradinhos coloridos via HTML/CSS."""
    
    # Cabeçalho CSS dos cards
    st.markdown("""
        <style>
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
        .status-disponivel { background-color: #22c55e; color: white; }
        .status-em_processo { background-color: #f59e0b; color: white; }
        .status-vendida { background-color: #ef4444; color: white; }
        .status-sem_info { background-color: #cbd5e1; color: #333; }
        </style>
    """, unsafe_allow_html=True)

    # Agrupa por Bloco (ou Andar se não tiver bloco)
    agrupador = col_bloco if col_bloco else (col_andar if col_andar else None)

    if agrupador:
        for grupo_nome in df[agrupador].dropna().unique():
            st.markdown(f"#### 🏢 {agrupador}: {grupo_nome}")
            df_grupo = df[df[agrupador] == grupo_nome]
            
            html_str = ""
            for _, row in df_grupo.iterrows():
                unidade = str(row[col_unidade])
                chave = (str(construtora), str(produto), unidade)
                
                # Verifica o status
                info = marcadas.get(chave)
                if info:
                    status = info.get("status")
                else:
                    status = "disponivel" # Se não estiver marcada, está disponível
                
                # Define a cor e o texto
                if status == "vendida":
                    classe = "status-vendida"
                    titulo = "Vendida"
                elif status == "em_processo":
                    classe = "status-em_processo"
                    titulo = "Em Processo"
                else:
                    classe = "status-disponivel"
                    titulo = "Disponível"
                
                # Formata o preço se existir
                preco_str = ""
                if col_preco and pd.notna(row[col_preco]):
                    try:
                        val = float(row[col_preco])
                        preco_str = f"R$ {val:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")
                    except:
                        pass
                
                # Cria o tooltip
                tooltip = f"{unidade} | {titulo} | {preco_str}"
                
                html_str += f'<div class="unidade-card {classe}" title="{tooltip}">{unidade}<br><span style="font-size:10px;">{preco_str}</span></div>'
            
            st.markdown(html_str, unsafe_allow_html=True)
            st.markdown("---")
    else:
        st.info("A planilha não tem coluna de Bloco ou Andar para agrupar.")