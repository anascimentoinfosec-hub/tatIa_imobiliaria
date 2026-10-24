import streamlit as st
import pandas as pd
from src.utils import hash_senha
from src.auth import salvar_usuarios, carregar_usuarios

# Lista de todas as páginas controláveis
PAGINAS_SISTEMA = {
    "operacional": ["simulador", "crm", "vendas", "simulacoes", "chat_ia"],
    "gestao": ["dashboard", "dashboard_vendas", "construtoras", "regras_fin", "regras_ent", "origens", "usuarios", "campanhas", "configuracoes", "war_room"],
    "diretoria": ["diretor_comercial", "diretor_vendas", "diretor_financeiro", "diretor_rh"]
}

# Template de permissões padrão por perfil
PERMISSOES_PADRAO = {
    "corretor": {
        "simulador": True, "crm": True, "vendas": True, "simulacoes": True, "chat_ia": True,
        "dashboard": False, "dashboard_vendas": False, "construtoras": False, "regras_fin": False, 
        "regras_ent": False, "origens": False, "usuarios": False, "campanhas": False, 
        "configuracoes": False, "war_room": False, "diretor_comercial": False
    },
    "gerente": {
        "simulador": True, "crm": True, "vendas": True, "simulacoes": True, "chat_ia": True,
        "dashboard": True, "dashboard_vendas": True, "construtoras": True, "regras_fin": True, 
        "regras_ent": True, "origens": True, "usuarios": True, "campanhas": True, 
        "configuracoes": True, "war_room": True, "diretor_comercial": False
    },
    "diretor_comercial": {
        "simulador": False, "crm": True, "vendas": False, "simulacoes": False, "chat_ia": False,
        "dashboard": False, "dashboard_vendas": True, "construtoras": False, "regras_fin": False, 
        "regras_ent": False, "origens": False, "usuarios": False, "campanhas": True, 
        "configuracoes": False, "war_room": True, "diretor_comercial": True
    },
    "diretor_vendas": {
        "simulador": False, "crm": True, "vendas": True, "simulacoes": False, "chat_ia": False,
        "dashboard": False, "dashboard_vendas": True, "construtoras": False, "regras_fin": False, 
        "regras_ent": False, "origens": False, "usuarios": False, "campanhas": False, 
        "configuracoes": False, "war_room": True, "diretor_comercial": False, "diretor_vendas": True
    },
    "diretor_financeiro": {
        "simulador": False, "crm": False, "vendas": True, "simulacoes": False, "chat_ia": False,
        "dashboard": False, "dashboard_vendas": True, "construtoras": False, "regras_fin": False, 
        "regras_ent": False, "origens": False, "usuarios": False, "campanhas": False, 
        "configuracoes": False, "war_room": True, "diretor_comercial": False, "diretor_vendas": False, "diretor_financeiro": True
    },
    "diretor_rh": {
        "simulador": False, "crm": False, "vendas": False, "simulacoes": False, "chat_ia": False,
        "dashboard": False, "dashboard_vendas": False, "construtoras": False, "regras_fin": False, 
        "regras_ent": False, "origens": False, "usuarios": True, "campanhas": False, 
        "configuracoes": False, "war_room": False, "diretor_comercial": False, "diretor_vendas": False, "diretor_financeiro": False, "diretor_rh": True
    },
    "superadmin": {
        pag: True for pag in sum(PAGINAS_SISTEMA.values(), [])
    }
}

def renderizar_tela_permissoes(permissoes_atuais, prefixo, sufixo=""):
    """Renderiza os checkboxes agrupados em 3 colunas."""
    novas_permissoes = {}
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**📈 Operacional**")
        for pag in PAGINAS_SISTEMA["operacional"]:
            valor_atual = permissoes_atuais.get(pag, True)
            novas_permissoes[pag] = st.checkbox(
                pag.capitalize().replace("_", " "), 
                value=valor_atual, 
                key=f"{prefixo}_perm_{pag}_{sufixo}"
            )
            
    with col2:
        st.markdown("**⚙️ Gestão**")
        for pag in PAGINAS_SISTEMA["gestao"]:
            valor_atual = permissoes_atuais.get(pag, True)
            novas_permissoes[pag] = st.checkbox(
                pag.capitalize().replace("_", " "), 
                value=valor_atual, 
                key=f"{prefixo}_perm_{pag}_{sufixo}"
            )

    with col3:
        st.markdown("**👔 Diretoria**")
        for pag in PAGINAS_SISTEMA["diretoria"]:
            valor_atual = permissoes_atuais.get(pag, True)
            novas_permissoes[pag] = st.checkbox(
                pag.capitalize().replace("_", " "), 
                value=valor_atual, 
                key=f"{prefixo}_perm_{pag}_{sufixo}"
            )
            
    return novas_permissoes

def pagina_gestao_usuarios(USUARIOS):
    st.title("👥 Gestão de Usuários")
    
    if "msg_sucesso_usuario" in st.session_state:
        st.toast(st.session_state["msg_sucesso_usuario"], icon="✅")
        del st.session_state["msg_sucesso_usuario"]

    usuario_logado = st.session_state.get("usuario_logado")
    perfil_logado = USUARIOS.get(usuario_logado, {}).get("perfil", "corretor")
    
    tabs = st.tabs(["📋 Listar", "➕ Adicionar", "✏️ Editar"])
    
    # --- LISTAR ---
    with tabs[0]:
        if USUARIOS:
            dados = []
            for login, info in USUARIOS.items():
                dados.append({
                    "Login": login, "Nome": info["nome"], "E-mail": info.get("email", ""),
                    "Perfil": info["perfil"].capitalize(), "MFA": "✅" if info.get("mfa_ativo") else "❌",
                    "Status": "✅ Ativo" if info["ativo"] else "❌ Inativo"
                })
            st.dataframe(pd.DataFrame(dados), use_container_width=True)
        else:
            st.info("Nenhum usuário cadastrado.")
    
    # --- ADICIONAR ---
    with tabs[1]:
        st.markdown("### Adicionar Novo Usuário")
        col1, col2 = st.columns(2)
        with col1:
            login = st.text_input("Login", key="add_login")
            nome = st.text_input("Nome completo", key="add_nome")
            email = st.text_input("E-mail", key="add_email")
        with col2:
            senha = st.text_input("Senha", type="password", key="add_senha")
            
            # Se o cara for superadmin, ele pode escolher qualquer perfil
            if perfil_logado == "superadmin":
                perfis = ["corretor", "gerente", "diretor_comercial", "superadmin", "diretor_vendas", "diretor_financeiro", "diretor_rh"]
                perfil = st.selectbox("Perfil", perfis, key="add_perfil")
            else:
                perfil = "corretor"
                st.info("Perfil: Corretor")
                
            ativo = st.checkbox("Ativo", value=True, key="add_ativo")
        
        st.markdown("---")
        st.markdown("### 🔐 Permissões de Acesso")
        st.caption("As caixinhas abaixo já vêm pré-selecionadas conforme o perfil escolhido, mas você pode ajustar.")
        
        # Pega o template baseado no perfil selecionado
        template_atual = PERMISSOES_PADRAO.get(perfil, {})
        permissoes_novas = renderizar_tela_permissoes(template_atual, prefixo="add", sufixo=perfil)
        
        if st.button("➕ Adicionar Usuário", use_container_width=True, type="primary"):
            if login and nome and senha and email:
                if login in USUARIOS:
                    st.error("❌ Usuário já existe!")
                else:
                    USUARIOS[login] = {
                        "nome": nome, "hash": hash_senha(senha), "perfil": perfil,
                        "ativo": ativo, "email": email, "permissoes": permissoes_novas
                    }
                    salvar_usuarios(USUARIOS)
                    st.session_state["msg_sucesso_usuario"] = f"Usuário '{login}' adicionado!"
                    for key in ["add_login", "add_nome", "add_email", "add_senha"]:
                        if key in st.session_state: del st.session_state[key]
                    st.rerun()
            else:
                st.error("❌ Preencha todos os campos!")
    
    # --- EDITAR ---
    with tabs[2]:
        usuarios_lista = list(USUARIOS.keys())
        if usuarios_lista:
            usuario_editar = st.selectbox("Selecione o usuário", usuarios_lista)
            
            if usuario_editar:
                dados = USUARIOS[usuario_editar]
                
                # Inputs básicos
                nome = st.text_input("Nome", value=dados["nome"])
                email = st.text_input("E-mail", value=dados.get("email", ""))
                
                # O pulo do gato: Usar um key dinâmico para o selectbox do perfil
                if perfil_logado == "superadmin":
                    perfis = ["corretor", "gerente", "diretor_comercial", "diretor_vendas", "superadmin", "diretor_financeiro", "diretor_rh"]
                    idx = perfis.index(dados["perfil"]) if dados["perfil"] in perfis else 0
                    perfil = st.selectbox("Perfil", perfis, index=idx, key=f"edit_perfil_{usuario_editar}")
                else:
                    perfil = dados["perfil"]
                    st.info(f"Perfil atual: {perfil}")
                
                senha = st.text_input("Nova senha (opcional)", type="password")
                ativo = st.checkbox("Ativo", value=dados["ativo"])
                
                st.markdown("---")
                st.markdown("### 🔐 Permissões de Acesso")
                
                # Se o perfil na tela for diferente do perfil salvo no banco, usamos o template novo
                if perfil != dados["perfil"]:
                    permissoes_base = PERMISSOES_PADRAO.get(perfil, {})
                    st.warning(f"⚠️ O perfil foi alterado para '{perfil}'. As permissões abaixo refletem o padrão deste perfil. Salve para aplicar.")
                else:
                    permissoes_base = dados.get("permissoes", {})
                
                # O sufixo agora inclui o perfil selecionado, forçando o Streamlit a recriar as caixinhas
                permissoes_editadas = renderizar_tela_permissoes(permissoes_base, prefixo="edit", sufixo=f"{usuario_editar}_{perfil}")
                
                # Botões de Salvar e Excluir (fora do form para podermos usar o st.rerun)
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    if st.button("💾 Salvar Alterações", use_container_width=True, type="primary"):
                        dados["nome"] = nome
                        dados["email"] = email
                        if perfil_logado == "superadmin": 
                            dados["perfil"] = perfil
                        if senha: 
                            dados["hash"] = hash_senha(senha)
                        dados["ativo"] = ativo
                        dados["permissoes"] = permissoes_editadas
                        
                        salvar_usuarios(USUARIOS)
                        st.session_state["msg_sucesso_usuario"] = "Usuário atualizado!"
                        st.rerun()
                
                with col_btn2:
                    pode_excluir = (perfil_logado == "superadmin") or (perfil_logado == "gerente" and dados["perfil"] == "corretor")
                    if pode_excluir:
                        if st.button("🗑️ Excluir", use_container_width=True):
                            if usuario_editar == "superadmin":
                                st.error("❌ Não é possível excluir o Super Admin!")
                            else:
                                del USUARIOS[usuario_editar]
                                salvar_usuarios(USUARIOS)
                                st.session_state["msg_sucesso_usuario"] = "Usuário excluído!"
                                st.rerun()
                        else:
                            st.warning("⚠️ Você não tem permissão para excluir este usuário.")
        else:
            st.warning("Nenhum usuário cadastrado.")