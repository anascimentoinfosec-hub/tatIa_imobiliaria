import streamlit as st
import pandas as pd
from modules.utils import hash_senha
from modules.auth import salvar_usuarios

def pagina_gestao_usuarios(USUARIOS):
    st.title("👥 Gestão de Usuários")
    
    tabs = st.tabs(["📋 Listar", "➕ Adicionar", "✏️ Editar"])
    
    # --- LISTAR ---
    with tabs[0]:
        st.markdown("### Usuários cadastrados:")
        if USUARIOS:
            dados = []
            for login, info in USUARIOS.items():
                dados.append({
                    "Login": login,
                    "Nome": info["nome"],
                    "E-mail": info.get("email", ""),
                    "Perfil": "👑 Gerente" if info["perfil"] == "gerente" else "👤 Corretor",
                    "Status": "✅ Ativo" if info["ativo"] else "❌ Inativo"
                })
            st.dataframe(pd.DataFrame(dados), use_container_width=True)
        else:
            st.info("Nenhum usuário cadastrado.")
    
    # --- ADICIONAR ---
    with tabs[1]:
        with st.form("form_novo_usuario"):
            col1, col2 = st.columns(2)
            with col1:
                login = st.text_input("Login")
                nome = st.text_input("Nome completo")
                email = st.text_input("E-mail")
            with col2:
                senha = st.text_input("Senha", type="password")
                perfil = st.selectbox("Perfil", ["corretor", "gerente"])
                ativo = st.checkbox("Ativo", value=True)
            
            if st.form_submit_button("➕ Adicionar", use_container_width=True):
                if login and nome and senha and email:
                    if login in USUARIOS:
                        st.error("❌ Usuário já existe!")
                    else:
                        USUARIOS[login] = {
                            "nome": nome,
                            "hash": hash_senha(senha),
                            "perfil": perfil,
                            "ativo": ativo,
                            "email": email
                        }
                        salvar_usuarios(USUARIOS)
                        st.success(f"✅ Usuário '{login}' adicionado!")
                        st.rerun()
                else:
                    st.error("❌ Preencha todos os campos (Login, Nome, E-mail e Senha)!")
    
    # --- EDITAR ---
    with tabs[2]:
        usuarios_lista = list(USUARIOS.keys())
        if usuarios_lista:
            usuario = st.selectbox("Selecione o usuário", usuarios_lista)
            if usuario:
                dados = USUARIOS[usuario]
                with st.form("form_editar_usuario"):
                    col1, col2 = st.columns(2)
                    with col1:
                        nome = st.text_input("Nome", value=dados["nome"])
                        email = st.text_input("E-mail", value=dados.get("email", ""))
                        perfil = st.selectbox(
                            "Perfil", 
                            ["corretor", "gerente"], 
                            index=0 if dados["perfil"] == "corretor" else 1
                        )
                    with col2:
                        senha = st.text_input("Nova senha (opcional)", type="password")
                        ativo = st.checkbox("Ativo", value=dados["ativo"])
                    
                    st.caption("💡 Para alterar a senha, digite uma nova senha. Deixe em branco para manter a atual.")
                    
                    col_btn1, col_btn2 = st.columns(2)
                    with col_btn1:
                        if st.form_submit_button("💾 Salvar", use_container_width=True):
                            dados["nome"] = nome
                            dados["email"] = email  # ← AGORA SALVA O E-MAIL
                            if senha:
                                dados["hash"] = hash_senha(senha)
                            dados["perfil"] = perfil
                            dados["ativo"] = ativo
                            salvar_usuarios(USUARIOS)
                            st.success("✅ Usuário atualizado!")
                            st.rerun()
                    with col_btn2:
                        if st.form_submit_button("🗑️ Excluir", use_container_width=True):
                            if usuario == "gerente":
                                st.error("❌ Não é possível excluir o gerente principal!")
                            else:
                                del USUARIOS[usuario]
                                salvar_usuarios(USUARIOS)
                                st.success(f"✅ Usuário '{usuario}' excluído!")
                                st.rerun()
        else:
            st.warning("Nenhum usuário cadastrado.")