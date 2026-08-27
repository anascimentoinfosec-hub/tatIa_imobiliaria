import streamlit as st
import pandas as pd
from datetime import datetime
from modules.utils import hash_senha
from modules.auth import salvar_usuarios, carregar_usuarios

def pagina_superadmin(USUARIOS):
    st.title("👑 Super Admin - Gestão do Sistema")
    st.markdown("---")
    
    # --- GERENTES ---
    st.subheader("👥 Gerenciar Gerentes")
    
    gerentes = {login: dados for login, dados in USUARIOS.items() if dados["perfil"] == "gerente" or login == "gerente"}
    
    # Listar gerentes
    if gerentes:
        dados = []
        for login, info in gerentes.items():
            dados.append({
                "Login": login,
                "Nome": info["nome"],
                "E-mail": info.get("email", ""),
                "Status": "✅ Ativo" if info["ativo"] else "❌ Inativo"
            })
        st.dataframe(pd.DataFrame(dados), use_container_width=True)
    else:
        st.info("Nenhum gerente cadastrado.")
    
    st.markdown("---")
    
    # --- ADICIONAR GERENTE ---
    with st.expander("➕ Adicionar Novo Gerente", expanded=False):
        with st.form("form_novo_gerente"):
            col1, col2 = st.columns(2)
            with col1:
                login = st.text_input("Login")
                nome = st.text_input("Nome completo")
                email = st.text_input("E-mail")
            with col2:
                senha = st.text_input("Senha", type="password")
                ativo = st.checkbox("Ativo", value=True)
            
            if st.form_submit_button("➕ Adicionar Gerente", use_container_width=True):
                if login and nome and senha and email:
                    if login in USUARIOS:
                        st.error("❌ Usuário já existe!")
                    else:
                        USUARIOS[login] = {
                            "nome": nome,
                            "hash": hash_senha(senha),
                            "perfil": "gerente",
                            "ativo": ativo,
                            "email": email,
                            "criado_em": datetime.now().isoformat()
                        }
                        salvar_usuarios(USUARIOS)
                        st.success(f"✅ Gerente '{login}' adicionado!")
                        st.rerun()
                else:
                    st.error("❌ Preencha todos os campos (Login, Nome, E-mail e Senha)!")
    
    # --- REMOVER GERENTE ---
    if gerentes:
        with st.expander("🗑️ Remover Gerente", expanded=False):
            gerente_remover = st.selectbox("Selecione o gerente", list(gerentes.keys()))
            if st.button("🗑️ Remover", use_container_width=True):
                if gerente_remover == "gerente":
                    st.error("❌ Não é possível remover o gerente padrão!")
                elif gerente_remover == "superadmin":
                    st.error("❌ Não é possível remover o Super Admin!")
                else:
                    del USUARIOS[gerente_remover]
                    salvar_usuarios(USUARIOS)
                    st.success(f"✅ Gerente '{gerente_remover}' removido!")
                    st.rerun()
    
    st.markdown("---")
    
    # --- LOGS DO SISTEMA (simplificado) ---
    with st.expander("📋 Logs do Sistema", expanded=False):
        st.caption("Registro de atividades recentes (em desenvolvimento)")
        st.info("💡 Em breve: histórico de acessos e ações dos usuários.")
    
    st.caption("👑 Área exclusiva para Super Admin")