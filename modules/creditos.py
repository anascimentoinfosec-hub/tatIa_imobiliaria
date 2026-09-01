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
    if "OPENAI_API_KEY" not in st.secrets:
        st.warning("⚠️ Chave da OpenAI não configurada.")
        return
    api_key = st.secrets["OPENAI_API_KEY"]
    with st.spinner("Consultando uso..."):
        uso = obter_uso_api(api_key)
    if uso is None:
        st.error("❌ Não foi possível obter o uso.")
        return
    saldo = CREDITO_TOTAL - uso
    col1, col2, col3 = st.columns(3)
    col1.metric("💰 Crédito Total", f"US$ {CREDITO_TOTAL:.2f}")
    col2.metric("📊 Consumo (30 dias)", f"US$ {uso:.2f}", f"{uso/CREDITO_TOTAL*100:.1f}%")
    col3.metric("✅ Saldo Restante", f"US$ {saldo:.2f}")
    if saldo < 1.00:
        st.warning("⚠️ Saldo baixo! Menos de US$ 1,00 restante.")
    if saldo <= 0:
        st.error("❌ Créditos esgotados! Adicione mais créditos.")
    st.caption("Dados atualizados em até 24h pela OpenAI.")