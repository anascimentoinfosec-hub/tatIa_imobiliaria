import streamlit as st
from src.mfa import (
    gerar_segredo_mfa, gerar_qr_code, verificar_codigo,
    salvar_segredo_mfa, desativar_mfa, obter_status_mfa
)


def renderizar_conta_seguranca(usuario_logado, USUARIOS):
    st.title("🔐 Segurança da Conta")
    st.markdown("---")

    if not usuario_logado:
        return

    mfa_ativo, mfa_secret = obter_status_mfa(usuario_logado, USUARIOS)
    nome_usuario = USUARIOS.get(usuario_logado, {}).get("nome", usuario_logado)

    st.markdown(f"**Usuário:** {nome_usuario} (`{usuario_logado}`)")

    if mfa_ativo:
        st.success("✅ A Autenticação em Duas Etapas (MFA) está **ATIVADA** na sua conta.")
        st.caption("Você precisará do código de 6 dígitos do seu aplicativo autenticador toda vez que fizer login.")
        
        st.markdown("---")
        if st.button("🚨 Desativar MFA", type="primary", use_container_width=True):
            desativar_mfa(usuario_logado)
            # Atualiza o dicionário local para refletir aprimary mudança imediata
            if usuario_logado in USUARIOS:
                USUARIOS[usuario_logado]["mfa_ativo"] = False
                USUARIOS[usuario_logado]["mfa_secret"] = None
            st.success("MFA desativado com sucesso!")
            st.rerun()

    else:
        st.warning("⚠️ A Autenticação em Duas Etapas (MFA) está **DESATIVADA**.")
        st.markdown("Proteja sua conta. Mesmo que alguém descubra sua senha, não conseguirá entrar sem o código do seu celular.")

        # Se o usuário clicou em ativar, geramos o QR Code
        if "mfa_setup_secret" not in st.session_state:
            if st.button("🔐 Ativar MFA agora", use_container_width=True, type="primary"):
                st.session_state["mfa_setup_secret"] = gerar_segredo_mfa()
                st.rerun()
        else:
            segredo = st.session_state["mfa_setup_secret"]
            
            st.info("1. Abra o **Google Authenticator**, **Authy** ou **Microsoft Authenticator** no seu celular.")
            st.info("2. Escaneie o QR Code abaixo:")
            
            qr_bytes = gerar_qr_code(usuario_logado, segredo)
            
            col1, col2 = st.columns([1, 2])
            with col1:
                st.image(qr_bytes, caption="Escaneie o código", width=200)
            with col2:
                st.markdown("Se não conseguir escanear, digite este código no app:")
                st.code(segredo, language="text")

            st.markdown("---")
            st.markdown("3. Digite o código de 6 dígitos que apareceu no app para confirmar:")
            
            codigo_confirmacao = st.text_input("Código de 6 dígitos", max_chars=6, key="mfa_confirmacao")
            
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                if st.button("✅ Confirmar e Ativar", type="primary", use_container_width=True):
                    if verificar_codigo(segredo, codigo_confirmacao):
                        salvar_segredo_mfa(usuario_logado, segredo)
                        # Atualiza local
                        if usuario_logado in USUARIOS:
                            USUARIOS[usuario_logado]["mfa_ativo"] = True
                            USUARIOS[usuario_logado]["mfa_secret"] = segredo
                        del st.session_state["mfa_setup_secret"]
                        st.success("✅ MFA Ativado com sucesso! Da próxima vez, o código será exigido.")
                        st.balloons()
                        st.rerun()
                    else:
                        st.error("❌ Código incorreto. Verifique a hora do seu celular e tente novamente.")
            with col_btn2:
                if st.button("❌ Cancelar", use_container_width=True):
                    del st.session_state["mfa_setup_secret"]
                    st.rerun()

def renderizar_mfa_obrigatorio(usuario_logado, USUARIOS):
    """Tela bloqueante que aparece se o usuário não tiver MFA ativado."""
    st.title("🔐 Configuração Obrigatória de Segurança")
    st.warning("⚠️ Para acessar no o sistema pela primeira vez, você precisa ativar a Autenticação em Duas Etapas (MFA).")
    
    nome_usuario = USUARIOS.get(usuario_logado, {}).get("nome", usuario_logado)
    st.markdown(f"**Usuário:** {nome_usuario}")

    # Gera o segredo na primeira vez que a tela abre
    if "mfa_setup_secret" not in st.session_state:
        st.session_state["mfa_setup_secret"] = gerar_segredo_mfa()
    
    segredo = st.session_state["mfa_setup_secret"]
    
    st.info("1. Abra o **Google Authenticator**, **Authy** ou **Microsoft Authenticator** no seu celular.")
    st.info("2. Escaneie o QR Code abaixo:")
    
    qr_bytes = gerar_qr_code(usuario_logado, segredo)
    
    col1, col2 = st.columns([1, 2])
    with col1:
        st.image(qr_bytes, caption="Escaneie o código", width=250)
    with col2:
        st.markdown("Se não conseguir escanear, digite este código no app:")
        st.code(segredo, language="text")
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("3. Digite o código de 6 dígitos gerado pelo app para confirmar:")

        codigo_confirmacao = st.text_input("Código de 6 dígitos", max_chars=6, key="mfa_confirmacao_obrigatorio")
        
        if st.button("✅ Confirmar e Acessar o Sistema", type="primary", use_container_width=True):
            if verificar_codigo(segredo, codigo_confirmacao):
                salvar_segredo_mfa(usuario_logado, segredo)
                
                # Atualiza os dados locais do usuário
                if usuario_logado in USUARIOS:
                    USUARIOS[usuario_logado]["mfa_ativo"] = True
                    USUARIOS[usuario_logado]["mfa_secret"] = segredo
                
                del st.session_state["mfa_setup_secret"]
                st.success("✅ Segurança ativada! Bem-vindo ao sistema.")
                st.rerun()
            else:
                st.error("❌ Código incorreto. Tente novamente.")
                
    # Opção para deslogar caso a pessoa não tenha o celular no momento
    st.markdown("---")
    if st.button("Sair (Logout)", use_container_width=False):
        del st.session_state["mfa_setup_secret"]
        st.session_state.usuario_logado = None
        st.rerun()