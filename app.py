import streamlit as st
from modules.auth import carregar_usuarios, verificar_login, pagina_login, exibir_login_sidebar
from modules.usuarios import pagina_gestao_usuarios
from modules.construtoras import carregar_construtoras, pagina_gestao_construtoras
from modules.simulador import pagina_simulador
from modules.chat_ia import pagina_chat
from modules.superadmin import pagina_superadmin
from modules.planilha_cache import excluir_planilha_cache

st.set_page_config(page_title="Simulador de Crédito", layout="wide")

USUARIOS = carregar_usuarios()
CONSTRUTORAS = carregar_construtoras()

with st.sidebar:
 st.markdown("### Acesso")
 st.markdown("---")
 
 if "usuario_logado" not in st.session_state:
 st.session_state.usuario_logado = None
 
 if st.session_state.usuario_logado is None:
 exibir_login_sidebar(USUARIOS)
 else:
 usuario = st.session_state.usuario_logado
 perfil = USUARIOS[usuario]["perfil"]
 st.write(f" **{USUARIOS[usuario]['nome']}**")
 st.caption(f"Perfil: {perfil}")
 if st.button(" Sair", use_container_width=True):
 st.session_state.usuario_logado = None
 st.rerun()
 st.markdown("---")
 
 # --- MENU PRINCIPAL (todos os usuários) ---
 if st.button(" Simulador", use_container_width=True):
 st.session_state.pagina = "Simulador"
 st.rerun()
 if st.button(" IA Imobiliária", use_container_width=True):
 st.session_state.pagina = "ChatIA"
 st.rerun()
 
 st.markdown("---")
 
 # --- MENU SUPER ADMIN ---
 if perfil == "superadmin":
 st.markdown("### Administração")
 if st.button(" Gerenciar Gerentes", use_container_width=True):
 st.session_state.pagina = "SuperAdmin"
 st.rerun()
 if st.button(" Usuários", use_container_width=True):
 st.session_state.pagina = "Usuários"
 st.rerun()
 if st.button(" Construtoras", use_container_width=True):
 st.session_state.pagina = "Construtoras"
 st.rerun()
 if st.button(" Limpar cache de planilhas", use_container_width=True):
 for construtora in CONSTRUTORAS.keys():
 excluir_planilha_cache(construtora)
 st.success(" Cache de planilhas limpo!")
 st.rerun()
 
 # --- MENU GERENTE ---
 elif perfil == "gerente":
 st.markdown("### Gestão")
 if st.button(" Usuários", use_container_width=True):
 st.session_state.pagina = "Usuários"
 st.rerun()
 if st.button(" Construtoras", use_container_width=True):
 st.session_state.pagina = "Construtoras"
 st.rerun()
 if st.button(" Limpar cache de planilhas", use_container_width=True):
 for construtora in CONSTRUTORAS.keys():
 excluir_planilha_cache(construtora)
 st.success(" Cache de planilhas limpo!")
 st.rerun()
 
 # --- MENU CORRETOR ---
 else:
 st.caption(" Corretor - Acesso ao simulador e IA")

if st.session_state.usuario_logado is None:
 pagina_login()
else:
 pagina = st.session_state.get("pagina", "Simulador")
 if pagina == "Simulador":
 pagina_simulador(CONSTRUTORAS)
 elif pagina == "ChatIA":
 pagina_chat()
 elif pagina == "SuperAdmin":
 pagina_superadmin(USUARIOS)
 elif pagina == "Usuários":
 pagina_gestao_usuarios(USUARIOS)
 elif pagina == "Construtoras":
 pagina_gestao_construtoras(CONSTRUTORAS)
 else:
 pagina_simulador(CONSTRUTORAS)