import streamlit as st
import pandas as pd
from modules.utils import hash_senha
from modules.auth import salvar_usuarios  # Você precisa adicionar esta função no auth.py

def pagina_gestao_usuarios(USUARIOS):
    st.title("👥 Gestão de Usuários")
    
    tabs = st.tabs(["📋 Listar", "➕ Adicionar", "✏️ Editar"])
    
    with tabs[0]:
        st.markdown("### Usuários cadastrados:")
        if USUARIOS:
            dados = []
            for login, info in USUARIOS.items():
                dados.append({
                    "Login": login,
                    "Nome": info["nome"],
                    "Perfil": "👑 Gerente" if info["perfil"] == "gerente" else "👤 Corretor",
                    "Status": "✅ Ativo" if info["ativo"] else "❌ Inativo"
                })
            st.dataframe(pd.DataFrame(dados), use_container_width=True)
        else:
            st.info("Nenhum usuário cadastrado.")
    
    with tabs[1]:
        with st.form("form_novo_usuario"):
            col1, col2 = st.columns(2)
            with col1:
                login = st.text_input("Login")
                nome = st.text_input("Nome completo")
            with col2:
                senha = st.text_input("Senha", type="password")
                perfil = st.selectbox("Perfil", ["corretor", "gerente"])
                ativo = st.checkbox("Ativo", value=True)
            
            if st.form_submit_button("➕ Adicionar", use_container_width=True):
                if login and nome and senha:
                    if login in USUARIOS:
                        st.error("❌ Usuário já existe!")
                    else:
                        USUARIOS[login] = {
                            "nome": nome,
                            "hash": hash_senha(senha),
                            "perfil": perfil,
                            "ativo": ativo,
                            "email": ""
                        }
                        from modules.auth import salvar_usuarios
                        salvar_usuarios(USUARIOS)
                        st.success(f"✅ Usuário '{login}' adicionado!")
                        st.rerun()
                else:
                    st.error("❌ Preencha todos os campos!")
    
    with tabs[2]:
        usuarios_lista = list(USUARIOS.keys())
        if usuarios_lista:
            usuario = st.selectbox("Selecione", usuarios_lista)
            if usuario:
                dados = USUARIOS[usuario]
                with st.form("form_editar_usuario"):
                    col1, col2 = st.columns(2)
                    with col1:
                        nome = st.text_input("Nome", value=dados["nome"])
                        perfil = st.selectbox("Perfil", ["corretor", "gerente"], index=0 if dados["perfil"] == "corretor" else 1)
                    with col2:
                        senha = st.text_input("Nova senha (opcional)", type="password")
                        ativo = st.checkbox("Ativo", value=dados["ativo"])
                    
                    col_btn1, col_btn2 = st.columns(2)
                    with col_btn1:
                        if st.form_submit_button("💾 Salvar", use_container_width=True):
                            dados["nome"] = nome
                            if senha:
                                dados["hash"] = hash_senha(senha)
                            dados["perfil"] = perfil
                            dados["ativo"] = ativo
                            from modules.auth import salvar_usuarios
                            salvar_usuarios(USUARIOS)
                            st.success("✅ Atualizado!")
                            st.rerun()
                    with col_btn2:
                        if st.form_submit_button("🗑️ Excluir", use_container_width=True):
                            if usuario == "gerente":
                                st.error("❌ Não exclua o gerente principal!")
                            else:
                                del USUARIOS[usuario]
                                from modules.auth import salvar_usuarios
                                salvar_usuarios(USUARIOS)
                                st.success(f"✅ Usuário '{usuario}' excluído!")
                                st.rerun()
        else:
            st.warning("Nenhum usuário cadastrado.")
