import streamlit as st
import json
import os
from datetime import datetime
from modules.utils import hash_senha

ARQUIVO_USUARIOS = "dados/usuarios.json"

def carregar_usuarios():
    try:
        if os.path.exists(ARQUIVO_USUARIOS):
            with open(ARQUIVO_USUARIOS, 'r', encoding='utf-8') as f:
                return json.load(f)
    except:
        pass
    return {
        "gerente": {
            "nome": "Gerente Geral",
            "hash": hash_senha("gerente2026"),
            "perfil": "gerente",
            "ativo": True,
            "email": "gerente@email.com",
            "criado_em": datetime.now().isoformat()
        }
    }

def verificar_login(usuario: str, senha: str, usuarios: dict) -> bool:
    if usuario not in usuarios:
        return False
    return usuarios[usuario]["hash"] == hash_senha(senha) and usuarios[usuario]["ativo"]

def pagina_login():
    st.markdown("""
    <style>
    .login-hero {
        background: linear-gradient(135deg, #1a237e, #0d47a1, #1565c0);
        padding: 40px 30px;
        border-radius: 16px;
        color: white;
        text-shadow: 2px 2px 8px rgba(0,0,0,0.8);
        margin-bottom: 30px;
        text-align: center;
    }
    .login-hero h1 { font-size: 36px; margin: 0; }
    .login-hero p { font-size: 18px; margin: 8px 0 0 0; opacity: 0.9; }
    </style>
    <div class="login-hero">
        <h1>🏢 Simulador de Crédito Imobiliário</h1>
        <p>Rio de Janeiro • Oásis II e outras construtoras</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### 📊 Mercado Imobiliário")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Taxa Selic", "10,50%")
        st.metric("TR", "1,50% a.a.")
    with col2:
        st.metric("Taxa SFH", "9,50% a.a.")
        st.metric("Entrada média", "20-30%")
    with col3:
        st.metric("Valor m² (RJ)", "R$ 12.800")
        st.metric("Prazo máximo", "420 meses")
    
    st.markdown("---")
    st.markdown("### 🏗️ Empreendimento em Destaque")
    st.success("*Oásis II*  \n📍 Barra da Tijuca - Rio de Janeiro  \n🏢 18 andares • 115 unidades • 2 e 3 quartos  \n💰 Preços a partir de R$ 384.950")
