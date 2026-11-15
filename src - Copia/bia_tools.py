import streamlit as st
from tavily import TavilyClient

def buscar_web(query: str, max_results: int = 5) -> str:
    """
    Realiza uma busca na web usando a API Tavily.
    Retorna os resultados formatados como texto para o LLM.
    """
    try:
        api_key = st.secrets["TAVILY_API_KEY"]
    except KeyError:
        return "❌ Erro: A chave TAVILY_API_KEY não foi configurada nos secrets."

    try:
        client = TavilyClient(api_key=api_key)
        # O parâmetro 'search_depth' controla o custo: 'basic' = 1 crédito, 'advanced' = 2 créditos[reference:1]
        response = client.search(query, max_results=max_results, search_depth="basic")

        if not response.get("results"):
            return "Nenhum resultado encontrado na web."

        # Formata os resultados para o LLM
        resultados_formatados = []
        for r in response["results"]:
            resultados_formatados.append(
                f"Título: {r['title']}\n"
                f"URL: {r['url']}\n"
                f"Conteúdo: {r['content']}\n"
            )
        return "\n---\n".join(resultados_formatados)

    except Exception as e:
        return f"❌ Erro na busca web: {str(e)}"