import streamlit as st
import pandas as pd
from src.auth import carregar_usuarios

def renderizar_diretor_rh():
    st.title("👥 Diretoria de Recursos Humanos")
    st.caption("Gestão de Pessoas, Cultura e Recrutamento")
    st.markdown("---")

    usuarios = carregar_usuarios()
    
    if not usuarios:
        st.info("Nenhum colaborador cadastrado no sistema.")
        return

    # === CÁLCULO DE MÉTRICAS ===
    total_ativos = sum(1 for u in usuarios.values() if u.get("ativo"))
    total_mfa = sum(1 for u in usuarios.values() if u.get("mfa_ativo"))
    
    corretores = sum(1 for u in usuarios.values() if u.get("perfil") == "corretor")
    gestores = sum(1 for u in usuarios.values() if u.get("perfil") in ["gerente", "superadmin"])
    
    # === CARDS ===
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"<div class='card-moderno' style='text-align:center;'><h3 style='font-size:24px; margin:0; color:#1a73e8;'>{total_ativos}</h3><p style='margin:0; color:#5f6368;'>Colaboradores Ativos</p></div>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<div class='card-moderno' style='text-align:center;'><h3 style='font-size:24px; margin:0; color:#28a745;'>{corretores}</h3><p style='margin:0; color:#5f6368;'>Corretores</p></div>", unsafe_allow_html=True)
    with col3:
        st.markdown(f"<div class='card-moderno' style='text-align:center;'><h3 style='font-size:24px; margin:0; color:#f59e0b;'>{gestores}</h3><p style='margin:0; color:#5f6368;'>Gestores/Admins</p></div>", unsafe_allow_html=True)
    with col4:
        st.markdown(f"<div class='card-moderno' style='text-align:center;'><h3 style='font-size:24px; margin:0; color:#8b5cf6;'>{total_mfa}</h3><p style='margin:0; color:#5f6368;'>Com MFA Ativado</p></div>", unsafe_allow_html=True)

    st.markdown("---")

    # === TABELA DE COLABORADORES ===
    st.subheader("📋 Quadro de Colaboradores")
    
    dados = []
    for login, info in usuarios.items():
        dados.append({
            "Nome": info.get("nome", ""),
            "E-mail": info.get("email", ""),
            "Perfil": info.get("perfil", "").capitalize(),
            "Status": "🟢 Ativo" if info.get("ativo") else "🔴 Inativo",
            "MFA": "✅ Sim" if info.get("mfa_ativo") else "❌ Não"
        })
        
    df = pd.DataFrame(dados)
    st.dataframe(df, use_container_width=True)

    st.markdown("---")
    
    # === INVENTÁRIO PARA O FINANCEIRO ===
    st.subheader("📊 Inventário para o Financeiro")
    st.caption("Esta visão será integrada ao módulo financeiro para cálculo de folha e comissões.")
    
    st.info("💡 **Nota do Sistema:** O RH é o detentor da informação de quem são os corretores ativos. Em breve, o Financeiro puxará esses dados automaticamente para cruzar com as vendas e gerar os repasses.")