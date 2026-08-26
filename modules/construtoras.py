import streamlit as st
import json
import os

ARQUIVO_CONFIG = "dados/construtoras.json"

def carregar_construtoras():
    try:
        if os.path.exists(ARQUIVO_CONFIG):
            with open(ARQUIVO_CONFIG, 'r', encoding='utf-8') as f:
                return json.load(f)
    except:
        pass
    return {
        "Oásis II": {
            "skiprows": 2,
            "mapeamento": {
                "0": "UNIDADE", "1": "PAVTO", "2": "COLUNA", "3": "M²",
                "4": "TIPOLOGIA", "5": "VAGA", "6": "SOL",
                "8": "1ª AVALIAÇÃO OÁSIS II", "10": "DESCONTO", "12": "PREÇO", "13": "DISPONIBILIDADE"
            },
            "colunas_ordem": ["UNIDADE", "PAVTO", "COLUNA", "M²", "TIPOLOGIA", "VAGA", "SOL", "1ª AVALIAÇÃO OÁSIS II", "DESCONTO", "PREÇO", "DISPONIBILIDADE"],
            "colunas_para_converter": ["PREÇO", "1ª AVALIAÇÃO OÁSIS II", "DESCONTO", "M²", "PAVTO"]
        }
    }

def salvar_construtoras(construtoras):
    with open(ARQUIVO_CONFIG, 'w', encoding='utf-8') as f:
        json.dump(construtoras, f, indent=2, ensure_ascii=False)

def pagina_gestao_construtoras(CONSTRUTORAS):
    st.title("🏗️ Gestão de Construtoras")
    
    with st.expander("➕ Adicionar", expanded=True):
        with st.form("form_nova_construtora"):
            nome = st.text_input("Nome da Construtora")
            skiprows = st.number_input("Linhas para pular", min_value=0, value=0, step=1)
            mapeamento_str = st.text_area("Mapeamento", placeholder='{"0": "UNIDADE", "1": "PREÇO"}', height=80)
            colunas_ordem_str = st.text_input("Colunas para exibir", placeholder="UNIDADE, PAVTO, PREÇO")
            colunas_numericas_str = st.text_input("Colunas numéricas", placeholder="PREÇO, M²")
            
            if st.form_submit_button("➕ Adicionar", use_container_width=True):
                if nome:
                    try:
                        mapeamento = json.loads(mapeamento_str) if mapeamento_str else {}
                        colunas_ordem = [c.strip() for c in colunas_ordem_str.split(',') if c.strip()]
                        colunas_numericas = [c.strip() for c in colunas_numericas_str.split(',') if c.strip()]
                        
                        CONSTRUTORAS[nome] = {
                            "skiprows": skiprows,
                            "mapeamento": {str(k): v for k, v in mapeamento.items()},
                            "colunas_ordem": colunas_ordem,
                            "colunas_para_converter": colunas_numericas
                        }
                        salvar_construtoras(CONSTRUTORAS)
                        st.success(f"✅ '{nome}' adicionada!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Erro: {str(e)}")
    
    st.markdown("---")
    st.markdown("### 📋 Construtoras Cadastradas")
    for nome, config in CONSTRUTORAS.items():
        col1, col2, col3 = st.columns([3, 2, 1])
        with col1:
            st.write(f"*{nome}*")
        with col2:
            st.write(f"{len(config.get('colunas_ordem', []))} colunas")
        with col3:
            if st.button(f"🗑️ Excluir", key=f"del_{nome}"):
                del CONSTRUTORAS[nome]
                salvar_construtoras(CONSTRUTORAS)
                st.rerun()
