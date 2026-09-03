import streamlit as st
import json
import os

ARQUIVO_CONFIG = "dados/construtoras.json"
ARQUIVO_CIDADES = "dados/cidades.json"

def carregar_cidades():
    try:
        if os.path.exists(ARQUIVO_CIDADES):
            with open(ARQUIVO_CIDADES, 'r', encoding='utf-8') as f:
                return json.load(f)
    except:
        pass
    return ["Barra da Tijuca", "Recreio dos Bandeirantes", "Jacarepaguá", "Rio de Janeiro (Capital)", "Niterói", "São Gonçalo", "Duque de Caxias", "Nova Iguaçu", "Campos dos Goytacazes", "Petrópolis", "Teresópolis"]

def salvar_cidades(cidades):
    with open(ARQUIVO_CIDADES, 'w', encoding='utf-8') as f:
        json.dump(cidades, f, indent=2, ensure_ascii=False)

def carregar_construtoras():
    try:
        if os.path.exists(ARQUIVO_CONFIG):
            with open(ARQUIVO_CONFIG, 'r', encoding='utf-8') as f:
                return json.load(f)
    except:
        pass
    return {}

def salvar_construtoras(construtoras):
    with open(ARQUIVO_CONFIG, 'w', encoding='utf-8') as f:
        json.dump(construtoras, f, indent=2, ensure_ascii=False)

def obter_cidades_em_uso(construtoras):
    cidades = set()
    for construtora, dados in construtoras.items():
        for produto, config in dados.get("produtos", {}).items():
            cidade = config.get("cidade")
            if cidade:
                cidades.add(cidade)
    return cidades

def pagina_gestao_construtoras(CONSTRUTORAS):
    # Exibe mensagem persistente se houver
    if 'mensagem' in st.session_state:
        tipo, texto = st.session_state['mensagem']
        if tipo == 'success':
            st.success(texto)
        elif tipo == 'error':
            st.error(texto)
        elif tipo == 'warning':
            st.warning(texto)
        del st.session_state['mensagem']

    st.title("🏗️ Gestão de Construtoras e Produtos")
    
    cidades = carregar_cidades()
    tabs = st.tabs(["📋 Listar", "➕ Adicionar Construtora", "📦 Gerenciar Produtos", "📍 Gerenciar Cidades"])
    
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
    
    with tabs[1]:
        st.markdown("### Adicionar Nova Construtora")
        with st.form("form_nova_construtora"):
            nome = st.text_input("Nome da Construtora")
            produto_nome = st.text_input("Nome do Produto (opcional)", placeholder="Ex: Torre A")
            opcoes_cidade = [""] + cidades
            cidade_selecionada = st.selectbox("📍 Cidade", opcoes_cidade)
            skiprows = st.number_input("Linhas para pular", min_value=0, value=2, step=1)
            mapeamento_str = st.text_area("Mapeamento (índice: nome)", placeholder='{"0": "UNIDADE", "1": "PREÇO"}', height=80)
            colunas_ordem_str = st.text_input("Colunas para exibir", placeholder="UNIDADE, PAVTO, PREÇO")
            colunas_numericas_str = st.text_input("Colunas numéricas (apenas valores monetários)", placeholder="PREÇO, M²")
            
            if st.form_submit_button("➕ Adicionar Construtora", use_container_width=True):
                if not nome:
                    st.session_state['mensagem'] = ("warning", "⚠️ Digite o nome da construtora!")
                    st.rerun()
                else:
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
                        st.session_state['mensagem'] = ("success", f"✅ Construtora '{nome}' adicionada com sucesso!")
                        st.rerun()
                    except Exception as e:
                        st.session_state['mensagem'] = ("error", f"❌ Erro: {str(e)}")
                        st.rerun()
    
    with tabs[2]:
        st.markdown("### Gerenciar Produtos")
        CONSTRUTORAS_ATUALIZADO = carregar_construtoras()
        construtoras_lista = list(CONSTRUTORAS_ATUALIZADO.keys())
        if not construtoras_lista:
            st.warning("Nenhuma construtora cadastrada.")
            return
        
        if "construtora_edit" not in st.session_state or st.session_state.construtora_edit not in construtoras_lista:
            st.session_state.construtora_edit = construtoras_lista[0]
        
        construtora_edit = st.selectbox(
            "Selecione a construtora",
            construtoras_lista,
            index=construtoras_lista.index(st.session_state.construtora_edit) if st.session_state.construtora_edit in construtoras_lista else 0,
            key="select_construtora_produtos"
        )
        st.session_state.construtora_edit = construtora_edit
        
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
                        try:
                            dados_atuais = carregar_construtoras()
                            if construtora_edit in dados_atuais and produto in dados_atuais[construtora_edit]["produtos"]:
                                del dados_atuais[construtora_edit]["produtos"][produto]
                                salvar_construtoras(dados_atuais)
                                st.session_state['mensagem'] = ("success", f"✅ Produto '{produto}' excluído com sucesso!")
                                st.rerun()
                        except Exception as e:
                            st.session_state['mensagem'] = ("error", f"❌ Erro ao excluir: {str(e)}")
                            st.rerun()
        else:
            st.info("Nenhum produto cadastrado para esta construtora.")
        
        st.markdown("---")
        st.markdown("#### Adicionar Produto")
        
        # Campos com placeholders e dicas
        novo_produto = st.text_input(
            "Nome do Produto",
            placeholder="Ex: Torre A (sem caracteres especiais: / \\ : * ?)",
            key="novo_produto_nome",
            help="Use apenas letras, números e underline. Evite espaços e barras."
        )
        nova_cidade = st.selectbox(
            "📍 Cidade",
            [""] + cidades,
            key="nova_cidade_produto",
            help="Selecione a cidade onde o produto está localizado."
        )
        novo_skiprows = st.number_input(
            "Skiprows (linhas para pular)",
            min_value=0,
            value=2,
            step=1,
            key="novo_produto_skiprows",
            help="Número de linhas do cabeçalho que devem ser ignoradas na planilha."
        )
        novo_mapeamento = st.text_area(
            "Mapeamento (índice: nome da coluna)",
            placeholder='{"0": "UNIDADE", "1": "PAVTO", "2": "PREÇO"}',
            height=80,
            key="novo_produto_mapeamento",
            help="Mapeie cada coluna da planilha (índice começando em 0) para o nome da coluna."
        )
        novo_colunas_ordem = st.text_input(
            "Colunas para exibir (separadas por vírgula)",
            placeholder="UNIDADE, PAVTO, PREÇO",
            key="novo_produto_colunas_ordem",
            help="Digite os nomes das colunas que deseja mostrar na tabela, na ordem desejada."
        )
        novo_colunas_numericas = st.text_input(
            "Colunas numéricas (separadas por vírgula)",
            placeholder="PREÇO, M², ANDAR",
            key="novo_produto_colunas_numericas",
            help="Informe apenas colunas que contenham valores numéricos (ex: PREÇO, AVALIAÇÃO, M²)."
        )
        
        if st.button("💾 Salvar Produto", use_container_width=True, key="btn_salvar_produto"):
            if not novo_produto:
                st.session_state['mensagem'] = ("warning", "⚠️ Digite o nome do produto!")
                st.rerun()
            else:
                try:
                    dados_atuais = carregar_construtoras()
                    if construtora_edit not in dados_atuais:
                        dados_atuais[construtora_edit] = {"produtos": {}}
                    produtos_atuais = dados_atuais[construtora_edit].get("produtos", {})
                    
                    mapeamento = json.loads(novo_mapeamento) if novo_mapeamento else {}
                    colunas_ordem = [c.strip() for c in novo_colunas_ordem.split(',') if c.strip()]
                    colunas_numericas = [c.strip() for c in novo_colunas_numericas.split(',') if c.strip()]
                    
                    if novo_produto in produtos_atuais:
                        st.session_state['mensagem'] = ("error", f"❌ Produto '{novo_produto}' já existe!")
                        st.rerun()
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
                        
                        # Limpa os campos
                        for key in ['novo_produto_nome', 'novo_produto_skiprows', 'novo_produto_mapeamento', 
                                    'novo_produto_colunas_ordem', 'novo_produto_colunas_numericas', 'nova_cidade_produto']:
                            if key in st.session_state:
                                del st.session_state[key]
                        
                        st.session_state['mensagem'] = ("success", f"✅ Produto '{novo_produto}' adicionado com sucesso!")
                        st.rerun()
                except json.JSONDecodeError:
                    st.session_state['mensagem'] = ("error", "❌ Erro no mapeamento: formato JSON inválido!")
                    st.rerun()
                except Exception as e:
                    st.session_state['mensagem'] = ("error", f"❌ Erro ao adicionar produto: {str(e)}")
                    st.rerun()
        
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
                        cidade_edit = st.selectbox("📍 Cidade", [""] + cidades, index=([""] + cidades).index(cidade_atual) if cidade_atual in cidades else 0, key="edit_cidade_produto")
                        novo_skiprows = st.number_input("Skiprows", value=config.get("skiprows", 2), step=1, key="edit_skiprows")
                        novo_mapeamento = st.text_area("Mapeamento", value=json.dumps(config.get("mapeamento", {}), indent=2, ensure_ascii=False), height=100, key="edit_mapeamento")
                        novo_colunas_ordem = st.text_input("Colunas para exibir", value=", ".join(config.get("colunas_ordem", [])), key="edit_colunas_ordem")
                        novo_colunas_numericas = st.text_input("Colunas numéricas", value=", ".join(config.get("colunas_para_converter", [])), key="edit_colunas_numericas")
                        
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
                                    st.session_state['mensagem'] = ("success", f"✅ Produto '{novo_nome}' atualizado com sucesso!")
                                    st.rerun()
                                except Exception as e:
                                    st.session_state['mensagem'] = ("error", f"❌ Erro ao atualizar: {str(e)}")
                                    st.rerun()
                        with col2:
                            if st.form_submit_button("❌ Cancelar", use_container_width=True):
                                st.session_state['editando_produto'] = None
                                st.rerun()
    
    with tabs[3]:
        st.markdown("### 📍 Gerenciar Cidades")
        st.markdown("Gerencie a lista de cidades disponíveis para os produtos.")
        cidades_atual = carregar_cidades()
        construtoras_atual = carregar_construtoras()
        cidades_em_uso = obter_cidades_em_uso(construtoras_atual)
        
        col_add1, col_add2 = st.columns([3, 1])
        with col_add1:
            nova_cidade_input = st.text_input("Digite o nome da nova cidade", placeholder="Ex: Belford Roxo", key="nova_cidade_input")
        with col_add2:
            if st.button("➕ Adicionar Cidade", use_container_width=True):
                if not nova_cidade_input:
                    st.session_state['mensagem'] = ("warning", "⚠️ Digite o nome da cidade!")
                    st.rerun()
                else:
                    cidade_limpa = nova_cidade_input.strip()
                    if cidade_limpa in cidades_atual:
                        st.session_state['mensagem'] = ("warning", f"⚠️ Cidade '{cidade_limpa}' já existe!")
                        st.rerun()
                    else:
                        cidades_atual.append(cidade_limpa)
                        salvar_cidades(cidades_atual)
                        st.session_state['mensagem'] = ("success", f"✅ Cidade '{cidade_limpa}' adicionada com sucesso!")
                        st.rerun()
        
        st.markdown("---")
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
                        st.button("🗑️", key=f"del_cidade_{cidade}", disabled=True, help="Cidade em uso")
                    else:
                        if st.button("🗑️ Remover", key=f"del_cidade_{cidade}"):
                            cidades_atual.remove(cidade)
                            salvar_cidades(cidades_atual)
                            st.session_state['mensagem'] = ("success", f"✅ Cidade '{cidade}' removida com sucesso!")
                            st.rerun()
        else:
            st.info("Nenhuma cidade cadastrada.")