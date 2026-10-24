import streamlit as st
import pandas as pd
from src.utils import hash_senha
from src.auth import salvar_usuarios, carregar_usuarios

PAGINAS_SISTEMA = {
    "operacional": ["simulador", "crm", "vendas", "simulacoes", "chat_ia"],
    "gestao": ["dashboard", "dashboard_vendas", "construtoras", "regras_fin", "regras_ent", "origens", "usuarios"]
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
    "superadmin": {
        # Superadmin tem tudo True
        pag: True for pag in sum(PAGINAS_SISTEMA.values(), [])
    }
}

def renderizar_tela_permissoes(permissoes_atuais, prefixo, sufixo=""):
    """Renderiza os checkboxes agrupados. O 'sufixo' evita erro de cache entre usuários."""
    novas_permissoes = {}
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**📈 Operacional**")
        for pag in PAGINAS_SISTEMA["operacional"]:
            valor_atual = permissoes_atuais.get(pag, True)
            novas_permissoes[pag] = st.checkbox(
                pag.capitalize().replace("_", " "), 
                value=valor_atual, 
                key=f"{prefixo}_perm_{pag}_{sufixo}" # <-- A MÁGICA ESTÁ AQUI
            )
            
    with col2:
        st.markdown("**⚙️ Gestão**")
        for pag in PAGINAS_SISTEMA["gestao"]:
            valor_atual = permissoes_atuais.get(pag, True)
            novas_permissoes[pag] = st.checkbox(
                pag.capitalize().replace("_", " "), 
                value=valor_atual, 
                key=f"{prefixo}_perm_{pag}_{sufixo}" # <-- A MÁGICA ESTÁ AQUI
            )
            
    return novas_permissoes

def pagina_gestao_usuarios(USUARIOS):
    st.title("👥 Gestão de Usuários")
    
    # === TOAST DE SUCESSO ===
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
            if perfil_logado == "superadmin":
                perfis = ["corretor", "gerente", "diretor_comercial", "superadmin"]
                perfil = st.selectbox("Perfil", perfis, key="add_perfil")
            else:
                perfil = "corretor"
                st.info("Perfil: corretor")
            ativo = st.checkbox("Ativo", value=True, key="add_ativo")
        
        st.markdown("---")
        st.markdown("### 🔐 Permissões de Acesso")
        st.caption("As caixinhas abaixo já vêm pré-selecionadas conforme o perfil escolhido, mas você pode ajustar manualmente.")
        
        # Pega o template baseado no perfil selecionado
        template_atual = PERMISSOES_PADRAO.get(perfil, {})
        
        # Renderiza os checkboxes já com os valores do template
        permissoes_novas = renderizar_tela_permissoes(template_atual, prefixo="add")
        
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
                    st.session_state["msg_sucesso_usuario"] = f"Usuário '{login}' criado como {perfil}!"
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
                
                if perfil_logado == "gerente" and dados["perfil"] == "superadmin":
                    st.error("❌ Você não tem permissão para editar o Super Admin!")
                    st.stop()
                
                with st.form("form_editar_usuario"):
                    col1, col2 = st.columns(2)
                    with col1:
                        nome = st.text_input("Nome", value=dados["nome"])
                        email = st.text_input("E-mail", value=dados.get("email", ""))
                        if perfil_logado == "superadmin":
                            perfis = ["corretor", "gerente", "superadmin"]
                            idx = perfis.index(dados["perfil"]) if dados["perfil"] in perfis else 0
                            perfil = st.selectbox("Perfil", perfis, index=idx)
                        else:
                            perfil = dados["perfil"]
                            st.info(f"Perfil atual: {perfil}")
                    
                    with col2:
                        senha = st.text_input("Nova senha (opcional)", type="password")
                        ativo = st.checkbox("Ativo", value=dados["ativo"])
                        
                    st.markdown("---")
                    st.markdown("### 🔐 Permissões de Acesso")
                    permissoes_atuais = dados.get("permissoes", {})
                    permissoes_editadas = renderizar_tela_permissoes(permissoes_atuais, prefixo="edit", sufixo="novo")
                    
                    col_btn1, col_btn2 = st.columns(2)
                    with col_btn1:
                        if st.form_submit_button("💾 Salvar", use_container_width=True, type="primary"):
                            dados["nome"] = nome
                            dados["email"] = email
                            if perfil_logado == "superadmin": dados["perfil"] = perfil
                            if senha: dados["hash"] = hash_senha(senha)
                            dados["ativo"] = ativo
                            dados["permissoes"] = permissoes_editadas
                            
                            salvar_usuarios(USUARIOS)
                            st.session_state["msg_sucesso_usuario"] = "Usuário atualizado com sucesso!"
                            st.rerun()
                    
                    with col_btn2:
                        pode_excluir = (perfil_logado == "superadmin") or (perfil_logado == "gerente" and dados["perfil"] == "corretor")
                        if pode_excluir:
                            if st.form_submit_button("🗑️ Excluir", use_container_width=True):
                                if usuario_editar == "superadmin":
                                    st.error("❌ Não é possível excluir o Super Admin!")
                                else:
                                    del USUARIOS[usuario_editar]
                                    salvar_usuarios(USUARIOS)
                                    st.session_state["msg_sucesso_usuario"] = "Usuário excluído com sucesso!"
                                    st.rerun()