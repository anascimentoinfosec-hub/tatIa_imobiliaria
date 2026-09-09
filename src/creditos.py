import streamlit as st
import requests
from datetime import datetime, timedelta

try:
    CREDITO_TOTAL = float(st.secrets.get("CREDITO_TOTAL", 5.00))
except:
    CREDITO_TOTAL = 5.00

def obter_uso_api(api_key):
    try:
        hoje = datetime.now()
        data_inicio = (hoje - timedelta(days=30)).strftime("%Y-%m-%d")
        data_fim = hoje.strftime("%Y-%m-%d")
        url = f"https://api.openai.com/v1/usage?start_date={data_inicio}&end_date={data_fim}"
        headers = {"Authorization": f"Bearer {api_key}"}
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            dados = response.json()
            uso_total = sum(item.get("total_usage", 0) for item in dados.get("data", []))
            return uso_total / 100
    except:
        pass
    return None

def pagina_creditos():
    st.title("💰 Monitoramento de Créditos OpenAI")
    st.markdown("---")
    
    # Verifica se a chave está configurada
    if "OPENAI_API_KEY" not in st.secrets:
        st.warning("⚠️ Chave da OpenAI não configurada.")
        st.info("Configure em Settings → Secrets do Streamlit: `OPENAI_API_KEY = 'sua-chave'`")
        return
    
    api_key = st.secrets["OPENAI_API_KEY"]
    
    with st.spinner("Consultando uso da API..."):
        uso = obter_uso_api(api_key)
    
    # =========================================================
    # CARD DE SALDO
    # =========================================================
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div class="card-moderno" style="text-align:center;">
            <p style="color:#5f6368; margin:0; font-size:14px;">💰 Crédito Total</p>
            <h3 style="margin:0; color:#1a73e8;">US$ {CREDITO_TOTAL:.2f}</h3>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        if uso is not None:
            st.markdown(f"""
            <div class="card-moderno" style="text-align:center;">
                <p style="color:#5f6368; margin:0; font-size:14px;">📊 Consumo (30 dias)</p>
                <h3 style="margin:0; color:#0d2b3e;">US$ {uso:.2f}</h3>
                <p style="margin:0; font-size:12px; color:#5f6368;">{(uso/CREDITO_TOTAL*100):.1f}% do total</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="card-moderno" style="text-align:center;">
                <p style="color:#5f6368; margin:0; font-size:14px;">📊 Consumo (30 dias)</p>
                <h3 style="margin:0; color:#f59e0b;">⏳ Aguardando dados</h3>
                <p style="margin:0; font-size:12px; color:#5f6368;">Pode levar até 24h para aparecer</p>
            </div>
            """, unsafe_allow_html=True)
    
    with col3:
        if uso is not None:
            saldo = CREDITO_TOTAL - uso
            cor = "#28a745" if saldo > 1 else "#dc3545"
            st.markdown(f"""
            <div class="card-moderno" style="text-align:center;">
                <p style="color:#5f6368; margin:0; font-size:14px;">✅ Saldo Restante</p>
                <h3 style="margin:0; color:{cor};">US$ {saldo:.2f}</h3>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="card-moderno" style="text-align:center;">
                <p style="color:#5f6368; margin:0; font-size:14px;">✅ Saldo Restante</p>
                <h3 style="margin:0; color:#f59e0b;">US$ {CREDITO_TOTAL:.2f}</h3>
                <p style="margin:0; font-size:12px; color:#5f6368;">(estimado, aguardando uso)</p>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # =========================================================
    # MENSAGENS INFORMATIVAS
    # =========================================================
    if uso is None:
        st.info("""
        ℹ️ **O monitoramento de uso ainda não está disponível.**
        
        Isso pode ocorrer por alguns motivos:
        - A API de uso da OpenAI pode levar até **24h** para começar a exibir dados.
        - Sua conta pode não ter permissão para acessar o endpoint de uso.
        - Você pode estar usando uma chave de API de projeto (em vez de organização).
        
        **Enquanto isso, você pode:**
        - Consultar seu saldo diretamente no [painel da OpenAI](https://platform.openai.com/settings/organization/billing).
        - Continuar usando a BIA normalmente – os créditos são descontados mesmo sem o monitoramento.
        """)
    else:
        if saldo < 1.00:
            st.warning("⚠️ **Saldo baixo!** Menos de US$ 1,00 restante. Considere adicionar mais créditos.")
        if saldo <= 0:
            st.error("❌ **Créditos esgotados!** A BIA não vai funcionar até que novos créditos sejam adicionados.")
    
    st.markdown("---")
    st.caption("🔗 [Acessar Painel OpenAI](https://platform.openai.com/settings/organization/billing)")