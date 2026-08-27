import streamlit as st
import pandas as pd
from modules.utils import hash_senha
from modules.auth import salvar_usuarios, carregar_usuarios

def pagina_gestao_usuarios(USUARIOS):
    st.title("👥 Gestão de Usuários")
    
    # Verifica o perfil do usuário logado
    usuario_logado = st.session_state.get("usuario_logado")
    perfil_logado = USUARIOS.get(usuario_logado, {}).get("perfil", "corretor")
    
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
                    "Perfil": "👑 Super Admin" if info["perfil"] == "superadmin" else "👑 Gerente" if info["perfil"] == "gerente" else "👤 Corretor",
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
                # Super Admin pode criar qualquer perfil; Gerente só pode criar corretores
                if perfil_logado == "superadmin":
                    perfil = st.selectbox("Perfil", ["corretor", "gerente", "superadmin"])
                else:
                    perfil = st.selectbox("Perfil", ["corretor"])
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
                    st.error("❌ Preencha todos os campos!")
    
    # --- EDITAR ---
    with tabs[2]:
        usuarios_lista = list(USUARIOS.keys())
        if usuarios_lista:
            usuario_editar = st.selectbox("Selecione o usuário", usuarios_lista)
            
            if usuario_editar:
                dados = USUARIOS[usuario_editar]
                
                with st.form("form_editar_usuario"):
                    col1, col2 = st.columns(2)
                    with col1:
                        nome = st.text_input("Nome", value=dados["nome"])
                        email = st.text_input("E-mail", value=dados.get("email", ""))
                        # Super Admin pode editar qualquer perfil; Gerente não pode mudar perfil
                        if perfil_logado == "superadmin":
                            perfis_disponiveis = ["corretor", "gerente", "superadmin"]
                            idx_atual = perfis_disponiveis.index(dados["perfil"]) if dados["perfil"] in perfis_disponiveis else 0
                            perfil = st.selectbox("Perfil", perfis_disponiveis, index=idx_atual)
                        else:
                            perfil = dados["perfil"]
                            st.info(f"Perfil atual: {perfil} (não pode ser alterado por um gerente)")
                    with col2:
                        senha = st.text_input("Nova senha (opcional)", type="password")
                        ativo = st.checkbox("Ativo", value=dados["ativo"])
                    
                    st.caption("💡 Para alterar a senha, digite uma nova senha. Deixe em branco para manter a atual.")
                    
                    col_btn1, col_btn2 = st.columns(2)
                    with col_btn1:
                        if st.form_submit_button("💾 Salvar", use_container_width=True):
                            dados["nome"] = nome
                            dados["email"] = email
                            if perfil_logado == "superadmin":
                                dados["perfil"] = perfil
                            if senha:
                                dados["hash"] = hash_senha(senha)
                            dados["ativo"] = ativo
                            salvar_usuarios(USUARIOS)
                            st.success("✅ Usuário atualizado!")
                            st.rerun()
                    
                    # Super Admin pode excluir qualquer usuário; Gerente não pode excluir gerentes/superadmins
                    with col_btn2:
                        pode_excluir = False
                        if perfil_logado == "superadmin":
                            pode_excluir = True
                        elif perfil_logado == "gerente" and dados["perfil"] == "corretor":
                            pode_excluir = True
                        
                        if pode_excluir:
                            if st.form_submit_button("🗑️ Excluir", use_container_width=True):
                                if usuario_editar == "superadmin":
                                    st.error("❌ Não é possível excluir o Super Admin principal!")
                                elif usuario_editar == "gerente" and perfil_logado == "gerente":
                                    st.error("❌ Gerente não pode excluir outro gerente!")
                                else:
                                    del USUARIOS[usuario_editar]
                                    salvar_usuarios(USUARIOS)
                                    st.success(f"✅ Usuário '{usuario_editar}' excluído!")
                                    st.rerun()
                        else:
                            st.warning("⚠️ Você não tem permissão para excluir este usuário.")
        else:
            st.warning("Nenhum usuário cadastrado.")