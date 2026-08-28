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
            "produtos": {
                "Torre A": {
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
        }
    }

def salvar_construtoras(construtoras):
    with open(ARQUIVO_CONFIG, 'w', encoding='utf-8') as f:
        json.dump(construtoras, f, indent=2, ensure_ascii=False)

def pagina_gestao_construtoras(CONSTRUTORAS):
    st.title("🏗️ Gestão de Construtoras e Produtos")
    
    tabs = st.tabs(["📋 Listar", "➕ Adicionar Construtora", "📦 Gerenciar Produtos"])
    
    # --- LISTAR ---
    with tabs[0]:
        st.markdown("### Construtoras e Produtos")
        if CONSTRUTORAS:
            for construtora, dados in CONSTRUTORAS.items():
                with st.expander(f"🏢 {construtora}"):
                    produtos = dados.get("produtos", {})
                    if produtos:
                        for produto, config in produtos.items():
                            st.write(f"  📄 *{produto}*")
                            st.caption(f"     {len(config.get('colunas_ordem', []))} colunas")
                    else:
                        st.caption("  ⚠️ Nenhum produto cadastrado")
        else:
            st.info("Nenhuma construtora cadastrada.")
    
    # --- ADICIONAR CONSTRUTORA ---
    with tabs[1]:
        st.markdown("### Adicionar Nova Construtora")
        with st.form("form_nova_construtora"):
            nome = st.text_input("Nome da Construtora")
            
            st.markdown("#### Produto Inicial (opcional)")
            produto_nome = st.text_input("Nome do Produto", placeholder="Ex: Torre A")
            skiprows = st.number_input("Linhas para pular", min_value=0, value=2, step=1)
            mapeamento_str = st.text_area("Mapeamento", placeholder='{"0": "UNIDADE", "1": "PREÇO"}', height=80)
            colunas_ordem_str = st.text_input("Colunas para exibir", placeholder="UNIDADE, PAVTO, PREÇO")
            colunas_numericas_str = st.text_input("Colunas numéricas", placeholder="PREÇO, M²")
            
            if st.form_submit_button("➕ Adicionar Construtora", use_container_width=True):
                if nome:
                    try:
                        nova_construtora = {"produtos": {}}
                        
                        if produto_nome:
                            mapeamento = json.loads(mapeamento_str) if mapeamento_str else {}
                            colunas_ordem = [c.strip() for c in colunas_ordem_str.split(',') if c.strip()]
                            colunas_numericas = [c.strip() for c in colunas_numericas_str.split(',') if c.strip()]
                            
                            nova_construtora["produtos"][produto_nome] = {
                                "skiprows": skiprows,
                                "mapeamento": {str(k): v for k, v in mapeamento.items()},
                                "colunas_ordem": colunas_ordem,
                                "colunas_para_converter": colunas_numericas
                            }
                        
                        CONSTRUTORAS[nome] = nova_construtora
                        salvar_construtoras(CONSTRUTORAS)
                        st.success(f"✅ Construtora '{nome}' adicionada!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Erro: {str(e)}")
                else:
                    st.error("❌ Digite o nome da construtora!")
    
    # --- GERENCIAR PRODUTOS ---
    with tabs[2]:
        st.markdown("### Gerenciar Produtos")
        
        # Recarrega os dados para garantir que estão atualizados
        CONSTRUTORAS_ATUALIZADO = carregar_construtoras()
        
        construtoras_lista = list(CONSTRUTORAS_ATUALIZADO.keys())
        if construtoras_lista:
            
            # Mantém a construtora selecionada no estado
            if "construtora_edit" not in st.session_state or st.session_state.construtora_edit not in construtoras_lista:
                st.session_state.construtora_edit = construtoras_lista[0]
            
            # Atualiza a construtora quando o usuário mudar
            construtora_edit = st.selectbox(
                "Selecione a construtora",
                construtoras_lista,
                index=construtoras_lista.index(st.session_state.construtora_edit) if st.session_state.construtora_edit in construtoras_lista else 0,
                key="select_construtora_produtos"
            )
            st.session_state.construtora_edit = construtora_edit
            
            if construtora_edit:
                dados = CONSTRUTORAS_ATUALIZADO[construtora_edit]
                produtos = dados.get("produtos", {})
                
                st.markdown(f"#### Produtos de *{construtora_edit}*")
                
                # Listar produtos
                if produtos:
                    for produto, config in produtos.items():
                        col1, col2, col3 = st.columns([3, 1, 1])
                        with col1:
                            st.write(f"📄 *{produto}*")
                            st.caption(f"     {len(config.get('colunas_ordem', []))} colunas")
                        with col2:
                            if st.button(f"✏️ Editar", key=f"edit_prod_{produto}"):
                                st.session_state['editando_produto'] = produto
                                st.rerun()
                        with col3:
                            if st.button(f"🗑️ Excluir", key=f"del_prod_{produto}"):
                                # Recarrega para garantir dados atuais
                                dados_atuais = carregar_construtoras()
                                if construtora_edit in dados_atuais:
                                    if produto in dados_atuais[construtora_edit]["produtos"]:
                                        del dados_atuais[construtora_edit]["produtos"][produto]
                                        salvar_construtoras(dados_atuais)
                                        st.success(f"✅ Produto '{produto}' excluído!")
                                        st.rerun()
                else:
                    st.info("Nenhum produto cadastrado para esta construtora.")
                
                st.markdown("---")
                st.markdown("#### Adicionar Produto")
                
                # --- CAMPOS DO FORMULÁRIO ---
                novo_produto = st.text_input("Nome do Produto", placeholder="Ex: Torre A", key="novo_produto_nome")
                novo_skiprows = st.number_input("Skiprows", min_value=0, value=2, step=1, key="novo_produto_skiprows")
                novo_mapeamento = st.text_area(
                    "Mapeamento (índice: nome)",
                    placeholder='{"0": "UNIDADE", "1": "PAVTO", "2": "PREÇO"}',
                    height=80,
                    key="novo_produto_mapeamento"
                )
                novo_colunas_ordem = st.text_input(
                    "Colunas para exibir (separadas por vírgula)",
                    placeholder="UNIDADE, PAVTO, PREÇO",
                    key="novo_produto_colunas_ordem"
                )
                novo_colunas_numericas = st.text_input(
                    "Colunas numéricas (separadas por vírgula)",
                    placeholder="PREÇO, M², ANDAR",
                    key="novo_produto_colunas_numericas"
                )
                
                # --- BOTÃO SALVAR PRODUTO ---
                if st.button("💾 Salvar Produto", use_container_width=True, key="btn_salvar_produto"):
                    if novo_produto:
                        try:
                            # Recarrega dados atualizados
                            dados_atuais = carregar_construtoras()
                            if construtora_edit not in dados_atuais:
                                dados_atuais[construtora_edit] = {"produtos": {}}
                            
                            produtos_atuais = dados_atuais[construtora_edit].get("produtos", {})
                            
                            mapeamento = json.loads(novo_mapeamento) if novo_mapeamento else {}
                            colunas_ordem = [c.strip() for c in novo_colunas_ordem.split(',') if c.strip()]
                            colunas_numericas = [c.strip() for c in novo_colunas_numericas.split(',') if c.strip()]
                            
                            if novo_produto in produtos_atuais:
                                st.error(f"❌ Produto '{novo_produto}' já existe!")
                            else:
                                produtos_atuais[novo_produto] = {
                                    "skiprows": novo_skiprows,
                                    "mapeamento": {str(k): v for k, v in mapeamento.items()},
                                    "colunas_ordem": colunas_ordem,
                                    "colunas_para_converter": colunas_numericas
                                }
                                dados_atuais[construtora_edit]["produtos"] = produtos_atuais
                                salvar_construtoras(dados_atuais)
                                
                                st.success(f"✅ Produto '{novo_produto}' adicionado com sucesso!")
                                st.rerun()
                        except json.JSONDecodeError:
                            st.error("❌ Erro no mapeamento: formato JSON inválido!")
                        except Exception as e:
                            st.error(f"❌ Erro ao adicionar produto: {str(e)}")
                    else:
                        st.error("❌ Digite o nome do produto!")
                
                # --- EDIÇÃO DE PRODUTO ---
                if st.session_state.get('editando_produto'):
                    produto_edit = st.session_state['editando_produto']
                    
                    # Recarrega dados atualizados
                    dados_atuais = carregar_construtoras()
                    if construtora_edit in dados_atuais:
                        produtos_atuais = dados_atuais[construtora_edit].get("produtos", {})
                        
                        if produto_edit in produtos_atuais:
                            config = produtos_atuais[produto_edit]
                            
                            st.markdown("---")
                            st.markdown(f"#### Editando: *{produto_edit}*")
                            
                            with st.form("form_editar_produto"):
                                novo_nome = st.text_input("Novo nome do produto", value=produto_edit)
                                novo_skiprows = st.number_input("Skiprows", value=config.get("skiprows", 2), step=1)
                                novo_mapeamento = st.text_area(
                                    "Mapeamento",
                                    value=json.dumps(config.get("mapeamento", {}), indent=2, ensure_ascii=False),
                                    height=100
                                )
                                novo_colunas_ordem = st.text_input(
                                    "Colunas para exibir",
                                    value=", ".join(config.get("colunas_ordem", []))
                                )
                                novo_colunas_numericas = st.text_input(
                                    "Colunas numéricas",
                                    value=", ".join(config.get("colunas_para_converter", []))
                                )
                                
                                col1, col2 = st.columns(2)
                                with col1:
                                    if st.form_submit_button("💾 Salvar", use_container_width=True):
                                        try:
                                            # Recarrega dados novamente para evitar conflitos
                                            dados_atuais = carregar_construtoras()
                                            produtos_atuais = dados_atuais[construtora_edit].get("produtos", {})
                                            
                                            if produto_edit in produtos_atuais:
                                                del produtos_atuais[produto_edit]
                                            
                                            mapeamento = json.loads(novo_mapeamento) if novo_mapeamento else {}
                                            colunas_ordem = [c.strip() for c in novo_colunas_ordem.split(',') if c.strip()]
                                            colunas_numericas = [c.strip() for c in novo_colunas_numericas.split(',') if c.strip()]
                                            
                                            produtos_atuais[novo_nome] = {
                                                "skiprows": novo_skiprows,
                                                "mapeamento": {str(k): v for k, v in mapeamento.items()},
                                                "colunas_ordem": colunas_ordem,
                                                "colunas_para_converter": colunas_numericas
                                            }
                                            dados_atuais[construtora_edit]["produtos"] = produtos_atuais
                                            salvar_construtoras(dados_atuais)
                                            
                                            st.session_state['editando_produto'] = None
                                            st.success("✅ Produto atualizado!")
                                            st.rerun()
                                        except Exception as e:
                                            st.error(f"❌ Erro: {str(e)}")
                                
                                with col2:
                                    if st.form_submit_button("❌ Cancelar", use_container_width=True):
                                        st.session_state['editando_produto'] = None
                                        st.rerun()
        else:
            st.warning("Nenhuma construtora cadastrada.")