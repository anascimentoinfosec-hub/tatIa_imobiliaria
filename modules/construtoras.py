import streamlit as st
import json
import os

ARQUIVO_CONFIG = "dados/construtoras.json"
ARQUIVO_CIDADES = "dados/cidades.json"

# =========================================================
# FUNÇÕES DE CIDADES
# =========================================================
def carregar_cidades():
    """Carrega a lista de cidades do arquivo JSON"""
    try:
        if os.path.exists(ARQUIVO_CIDADES):
            with open(ARQUIVO_CIDADES, 'r', encoding='utf-8') as f:
                return json.load(f)
    except:
        pass
    # Lista padrão
    return [
        "Barra da Tijuca",
        "Recreio dos Bandeirantes",
        "Jacarepaguá",
        "Rio de Janeiro (Capital)",
        "Niterói",
        "São Gonçalo",
        "Duque de Caxias",
        "Nova Iguaçu",
        "Campos dos Goytacazes",
        "Petrópolis",
        "Teresópolis"
    ]

def salvar_cidades(cidades):
    """Salva a lista de cidades no arquivo JSON"""
    with open(ARQUIVO_CIDADES, 'w', encoding='utf-8') as f:
        json.dump(cidades, f, indent=2, ensure_ascii=False)

def cidade_esta_em_uso(cidade, construtoras):
    """Verifica se a cidade está sendo usada em algum produto"""
    for construtora, dados in construtoras.items():
        for produto, config in dados.get("produtos", {}).items():
            if config.get("cidade") == cidade:
                return True
    return False

# =========================================================
# FUNÇÕES DE CONSTRUTORAS
# =========================================================
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
                    "cidade": "Barra da Tijuca",
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

def obter_cidades_em_uso(construtoras):
    """Retorna um set com todas as cidades em uso nos produtos"""
    cidades = set()
    for construtora, dados in construtoras.items():
        for produto, config in dados.get("produtos", {}).items():
            cidade = config.get("cidade")
            if cidade:
                cidades.add(cidade)
    return cidades

# =========================================================
# PÁGINA DE GESTÃO
# =========================================================
def pagina_gestao_construtoras(CONSTRUTORAS):
    st.title("🏗️ Gestão de Construtoras e Produtos")
    
    # Carrega cidades
    cidades = carregar_cidades()
    
    tabs = st.tabs(["📋 Listar", "➕ Adicionar Construtora", "📦 Gerenciar Produtos", "📍 Gerenciar Cidades"])
    
    # --- LISTAR ---
    with tabs[0]:
        st.markdown("### Construtoras e Produtos")
        if CONSTRUTORAS:
            for construtora, dados in CONSTRUTORAS.items():
                with st.expander(f"🏢 {construtora}"):
                    produtos = dados.get("produtos", {})
                    if produtos:
                        for produto, config in produtos.items():
                            cidade = config.get("cidade", "Não definida")
                            st.write(f"  📄 *{produto}* - 📍 {cidade}")
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
            
            # Selectbox com cidades
            opcoes_cidade = [""] + cidades
            cidade_selecionada = st.selectbox("📍 Cidade", opcoes_cidade)
            
            skiprows = st.number_input("Linhas para pular", min_value=0, value=2, step=1)
            mapeamento_str = st.text_area("Mapeamento", placeholder='{"0": "UNIDADE", "1": "PREÇO"}', height=80)
            colunas_ordem_str = st.text_input("Colunas para exibir", placeholder="UNIDADE, PAVTO, PREÇO")
            colunas_numericas_str = st.text_input("Colunas numéricas", placeholder="PREÇO, M²")
            
            if st.form_submit_button("➕ Adicionar Construtora", use_container_width=True):
                if nome:
                    try:
                        nova_construtora = {"produtos": {}}
                        
                        if produto_nome and cidade_selecionada:
                            mapeamento = json.loads(mapeamento_str) if mapeamento_str else {}
                            colunas_ordem = [c.strip() for c in colunas_ordem_str.split(',') if c.strip()]
                            colunas_numericas = [c.strip() for c in colunas_numericas_str.split(',') if c.strip()]
                            
                            nova_construtora["produtos"][produto_nome] = {
                                "cidade": cidade_selecionada,
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
        
        CONSTRUTORAS_ATUALIZADO = carregar_construtoras()
        cidades_atualizadas = carregar_cidades()
        
        construtoras_lista = list(CONSTRUTORAS_ATUALIZADO.keys())
        if construtoras_lista:
            
            if "construtora_edit" not in st.session_state or st.session_state.construtora_edit not in construtoras_lista:
                st.session_state.construtora_edit = construtoras_lista[0]
            
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
                
                if produtos:
                    for produto, config in produtos.items():
                        col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
                        with col1:
                            st.write(f"📄 *{produto}*")
                        with col2:
                            cidade = config.get("cidade", "Não definida")
                            st.write(f"📍 {cidade}")
                        with col3:
                            if st.button(f"✏️ Editar", key=f"edit_prod_{produto}"):
                                st.session_state['editando_produto'] = produto
                                st.rerun()
                        with col4:
                            if st.button(f"🗑️ Excluir", key=f"del_prod_{produto}"):
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
                
                novo_produto = st.text_input("Nome do Produto", placeholder="Ex: Torre A", key="novo_produto_nome")
                
                # Selectbox com cidades
                opcoes_cidade = [""] + cidades_atualizadas
                nova_cidade = st.selectbox("📍 Cidade", opcoes_cidade, key="nova_cidade_produto")
                
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
                
                if st.button("💾 Salvar Produto", use_container_width=True, key="btn_salvar_produto"):
                    if novo_produto:
                        try:
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
                                    "cidade": nova_cidade,
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
                    
                    dados_atuais = carregar_construtoras()
                    if construtora_edit in dados_atuais:
                        produtos_atuais = dados_atuais[construtora_edit].get("produtos", {})
                        
                        if produto_edit in produtos_atuais:
                            config = produtos_atuais[produto_edit]
                            cidade_atual = config.get("cidade", "")
                            
                            st.markdown("---")
                            st.markdown(f"#### Editando: *{produto_edit}*")
                            
                            with st.form("form_editar_produto"):
                                novo_nome = st.text_input("Novo nome do produto", value=produto_edit)
                                
                                # Selectbox com cidades
                                opcoes_cidade = [""] + cidades_atualizadas
                                idx_cidade = opcoes_cidade.index(cidade_atual) if cidade_atual in opcoes_cidade else 0
                                cidade_edit = st.selectbox("📍 Cidade", opcoes_cidade, index=idx_cidade, key="edit_cidade_produto")
                                
                                novo_skiprows = st.number_input("Skiprows", value=config.get("skiprows", 2), step=1, key="edit_skiprows")
                                novo_mapeamento = st.text_area(
                                    "Mapeamento",
                                    value=json.dumps(config.get("mapeamento", {}), indent=2, ensure_ascii=False),
                                    height=100,
                                    key="edit_mapeamento"
                                )
                                novo_colunas_ordem = st.text_input(
                                    "Colunas para exibir",
                                    value=", ".join(config.get("colunas_ordem", [])),
                                    key="edit_colunas_ordem"
                                )
                                novo_colunas_numericas = st.text_input(
                                    "Colunas numéricas",
                                    value=", ".join(config.get("colunas_para_converter", [])),
                                    key="edit_colunas_numericas"
                                )
                                
                                col1, col2 = st.columns(2)
                                with col1:
                                    if st.form_submit_button("💾 Salvar", use_container_width=True):
                                        try:
                                            dados_atuais = carregar_construtoras()
                                            produtos_atuais = dados_atuais[construtora_edit].get("produtos", {})
                                            
                                            if produto_edit in produtos_atuais:
                                                del produtos_atuais[produto_edit]
                                            
                                            mapeamento = json.loads(novo_mapeamento) if novo_mapeamento else {}
                                            colunas_ordem = [c.strip() for c in novo_colunas_ordem.split(',') if c.strip()]
                                            colunas_numericas = [c.strip() for c in novo_colunas_numericas.split(',') if c.strip()]
                                            
                                            produtos_atuais[novo_nome] = {
                                                "cidade": cidade_edit,
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
    
    # --- GERENCIAR CIDADES ---
    with tabs[3]:
        st.markdown("### 📍 Gerenciar Cidades")
        st.markdown("Gerencie a lista de cidades disponíveis para os produtos.")
        
        # Recarrega dados atualizados
        cidades_atual = carregar_cidades()
        construtoras_atual = carregar_construtoras()
        cidades_em_uso = obter_cidades_em_uso(construtoras_atual)
        
        # --- ADICIONAR CIDADE ---
        col_add1, col_add2 = st.columns([3, 1])
        with col_add1:
            nova_cidade_input = st.text_input("Digite o nome da nova cidade", placeholder="Ex: Belford Roxo", key="nova_cidade_input")
        with col_add2:
            if st.button("➕ Adicionar Cidade", use_container_width=True):
                if nova_cidade_input:
                    cidade_limpa = nova_cidade_input.strip()
                    if cidade_limpa in cidades_atual:
                        st.warning(f"⚠️ Cidade '{cidade_limpa}' já existe!")
                    else:
                        cidades_atual.append(cidade_limpa)
                        salvar_cidades(cidades_atual)
                        st.success(f"✅ Cidade '{cidade_limpa}' adicionada!")
                        st.rerun()
                else:
                    st.warning("⚠️ Digite o nome da cidade!")
        
        st.markdown("---")
        
        # --- LISTA DE CIDADES ---
        st.markdown("#### Lista de Cidades Cadastradas")
        
        if cidades_atual:
            for cidade in cidades_atual:
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.write(f"📍 {cidade}")
                with col2:
                    if cidade in cidades_em_uso:
                        st.caption("🔒 Em uso")
                    else:
                        st.caption("")
                with col3:
                    if cidade in cidades_em_uso:
                        st.button("🗑️", key=f"del_cidade_{cidade}", disabled=True, help="Cidade em uso por um produto")
                    else:
                        if st.button("🗑️ Remover", key=f"del_cidade_{cidade}"):
                            cidades_atual.remove(cidade)
                            salvar_cidades(cidades_atual)
                            st.rerun()
        else:
            st.info("Nenhuma cidade cadastrada.")