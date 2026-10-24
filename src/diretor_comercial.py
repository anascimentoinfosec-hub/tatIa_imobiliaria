import streamlit as st
from src.construtoras_storage import carregar_construtoras, salvar_construtoras

def renderizar_diretor_comercial():
    st.title("💼 Diretoria Comercial")
    st.caption("Gestão de Parcerias e Estratégia de Mercado")
    st.markdown("---")

    construtoras = carregar_construtoras()
    
    # Separa as ativas das em negociação
    ativas = {k: v for k, v in construtoras.items() if v.get("status_parceria", "ativa") == "ativa"}
    negociacao = {k: v for k, v in construtoras.items() if v.get("status_parceria") == "em_negociacao"}

    # Cards Rápidos
    col1, col2 = st.columns(2)
    with col1:
        st.metric("🤝 Parcerias Ativas", len(ativas))
    with col2:
        st.metric("⏳ Em Negociação", len(negociacao))

    st.markdown("---")

    tab1, tab2 = st.tabs(["📊 Construtoras Ativas", "🤝 Em Negociação"])

    # === ABA DE ATIVAS ===
    with tab1:
        if not ativas:
            st.info("Nenhuma construtora ativa no momento.")
        else:
            for nome, dados in ativas.items():
                with st.expander(f"🏢 {nome}"):
                    st.write(f"**Desconto Padrão:** {dados.get('tipo_desconto', 'AVALIAÇÃO')}")
                    produtos = list(dados.get("produtos", {}).keys())
                    st.write(f"**Produtos no ERP:** {len(produtos)}")
                    if dados.get("observacoes_comerciais"):
                        st.info(f"📝 {dados['observacoes_comerciais']}")

    # === ABA DE NEGOCIAÇÃO ===
    with tab2:
        st.markdown("### 🤝 Novas Parcerias")
        
        # Formulário para cadastrar nova construtora em negociação
        with st.expander("➕ Adicionar nova negociação"):
            with st.form("form_nova_parceria"):
                nome = st.text_input("Nome da Construtora")
                obs = st.text_area("Observações da Negociação", placeholder="Ex: Aguardando aprovação da diretoria, negociando comissão...")
                tipo_desc = st.selectbox("Desconto Padrão Inicial", ["AVALIAÇÃO", "PREÇO"])
                
                if st.form_submit_button("Registrar Negociação", type="primary"):
                    if not nome:
                        st.warning("⚠️ O nome é obrigatório.")
                    else:
                        dados_atuais = carregar_construtoras()
                        if nome in dados_atuais:
                            st.error("Construtora já cadastrada no sistema.")
                        else:
                            dados_atuais[nome] = {
                                "tipo_desconto": tipo_desc,
                                "produtos": {},
                                "status_parceria": "em_negociacao",
                                "observacoes_comerciais": obs
                            }
                            salvar_construtoras(dados_atuais)
                            st.success(f"Negociação com '{nome}' registrada!")
                            st.rerun()

        st.markdown("---")
        if not negociacao:
            st.info("Nenhuma construtora em negociação no momento.")
        else:
            for nome, dados in negociacao.items():
                with st.container():
                    st.markdown(f"#### 🏢 {nome}")
                    st.caption(f"Desconto previsto: {dados.get('tipo_desconto')}")
                    if dados.get("observacoes_comerciais"):
                        st.write(f"📝 **Notas:** {dados['observacoes_comerciais']}")
                    
                    col_btn1, col_btn2 = st.columns(2)
                    with col_btn1:
                        if st.button("✅ Ativar Parceria (Enviar p/ Gerente)", key=f"ativar_{nome}", type="primary", use_container_width=True):
                            atualizadas = carregar_construtoras()
                            atualizadas[nome]["status_parceria"] = "ativa"
                            salvar_construtoras(atualizadas)
                            st.success(f"Parceria '{nome}' ativada! Já está disponível para o Gerente.")
                            st.rerun()
                    with col_btn2:
                        if st.button("🗑️ Cancelar Negociação", key=f"cancelar_{nome}", use_container_width=True):
                            atualizadas = carregar_construtoras()
                            del atualizadas[nome]
                            salvar_construtoras(atualizadas)
                            st.rerun()
                    st.markdown("---")