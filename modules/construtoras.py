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
    
    # --- ADICIONAR ---
    with st.expander("➕ Adicionar Nova Construtora", expanded=False):
        with st.form("form_nova_construtora"):
            col1, col2 = st.columns(2)
            with col1:
                nome = st.text_input("Nome da Construtora")
                skiprows = st.number_input("Linhas para pular (skiprows)", min_value=0, value=0, step=1)
            with col2:
                colunas_ordem_str = st.text_input(
                    "Colunas para exibir (separadas por vírgula)",
                    placeholder="UNIDADE, PAVTO, PREÇO"
                )
                colunas_numericas_str = st.text_input(
                    "Colunas numéricas (separadas por vírgula)",
                    placeholder="PREÇO, M², ANDAR"
                )
            
            st.markdown("*Mapeamento de colunas (índice: nome)*")
            st.caption('Ex: {"0": "UNIDADE", "1": "PAVTO", "2": "PREÇO"}')
            mapeamento_str = st.text_area(
                "Digite o mapeamento",
                placeholder='{"0": "UNIDADE", "1": "PAVTO", "2": "PREÇO"}',
                height=80
            )
            
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
                        st.success(f"✅ Construtora '{nome}' adicionada!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Erro: {str(e)}")
    
    st.markdown("---")
    st.markdown("### 📋 Construtoras Cadastradas")
    
    # --- LISTAR CONSTRUTORAS COM BOTÕES DE EDITAR E EXCLUIR ---
    if CONSTRUTORAS:
        for nome, config in CONSTRUTORAS.items():
            with st.container():
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.write(f"*{nome}*")
                    st.caption(f"{len(config.get('colunas_ordem', []))} colunas")
                with col2:
                    if st.button(f"✏️ Editar", key=f"edit_{nome}"):
                        st.session_state['editando_construtora'] = nome
                        st.rerun()
                with col3:
                    if st.button(f"🗑️ Excluir", key=f"del_{nome}"):
                        del CONSTRUTORAS[nome]
                        salvar_construtoras(CONSTRUTORAS)
                        st.rerun()
                
                # --- FORMULÁRIO DE EDIÇÃO (aparece quando clica em Editar) ---
                if st.session_state.get('editando_construtora') == nome:
                    with st.form(f"form_edit_{nome}"):
                        st.markdown(f"*Editando: {nome}*")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            novo_nome = st.text_input("Novo nome", value=nome)
                            novo_skiprows = st.number_input("Skiprows", value=config.get("skiprows", 0), step=1)
                        with col2:
                            novo_colunas_ordem = st.text_input(
                                "Colunas para exibir",
                                value=", ".join(config.get("colunas_ordem", []))
                            )
                            novo_colunas_numericas = st.text_input(
                                "Colunas numéricas",
                                value=", ".join(config.get("colunas_para_converter", []))
                            )
                        
                        novo_mapeamento = st.text_area(
                            "Mapeamento",
                            value=json.dumps(config.get("mapeamento", {}), indent=2, ensure_ascii=False),
                            height=100
                        )
                        
                        col_btn1, col_btn2 = st.columns(2)
                        with col_btn1:
                            if st.form_submit_button("💾 Salvar alterações", use_container_width=True):
                                try:
                                    # Remove a antiga
                                    del CONSTRUTORAS[nome]
                                    # Adiciona com o novo nome
                                    CONSTRUTORAS[novo_nome] = {
                                        "skiprows": novo_skiprows,
                                        "mapeamento": json.loads(novo_mapeamento),
                                        "colunas_ordem": [c.strip() for c in novo_colunas_ordem.split(',') if c.strip()],
                                        "colunas_para_converter": [c.strip() for c in novo_colunas_numericas.split(',') if c.strip()]
                                    }
                                    salvar_construtoras(CONSTRUTORAS)
                                    st.session_state['editando_construtora'] = None
                                    st.success("✅ Construtora atualizada!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"❌ Erro: {str(e)}")
                        with col_btn2:
                            if st.form_submit_button("❌ Cancelar", use_container_width=True):
                                st.session_state['editando_construtora'] = None
                                st.rerun()
                
                st.markdown("---")
    else:
        st.info("Nenhuma construtora cadastrada.")