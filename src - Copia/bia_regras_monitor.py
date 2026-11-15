import streamlit as st
from src.bia_tools import buscar_web
from src.regras_storage import carregar_regras


def verificar_regras_banco(regra_id, nome_regra, banco, taxa_atual):
    """
    Busca na web a taxa atual de um banco/sistema e compara com a regra local.
    Retorna dict com diagnóstico ou None em caso de falha.
    """
    query = f"{banco} taxa financiamento imobiliário {nome_regra} 2026 atual"
    resultado_busca = buscar_web(query, max_results=3)

    if not resultado_busca or "❌" in resultado_busca:
        return None

    return {
        "regra_id": regra_id,
        "nome_regra": nome_regra,
        "banco": banco,
        "taxa_atual_sistema": taxa_atual,
        "resultado_busca": resultado_busca,
    }


def analisar_divergencia_com_ia(client, dados_verificacao):
    """
    Usa a IA para comparar a taxa do sistema com o que foi encontrado na web.
    Retorna dict com:
      - divergencia: bool
      - taxa_sugerida: float ou None
      - justificativa: str
      - fonte: str
    """
    prompt = f"""Você é um analista de crédito imobiliário.

Regra no sistema:
- Nome: {dados_verificacao['nome_regra']}
- Banco: {dados_verificacao['banco']}
- Taxa atual cadastrada: {dados_verificacao['taxa_atual_sistema'] * 100:.2f}% a.a.

Resultados de busca na web (podem estar desatualizados ou serem irrelevantes):
{dados_verificacao['resultado_busca']}

Analise e responda APENAS com um JSON válido no formato:
{{
  "divergencia": true ou false,
  "taxa_sugerida": número (ex: 0.1149 para 11,49%) ou null,
  "justificativa": "explicação curta em português",
  "fonte": "URL ou site de onde veio a informação"
}}

Regras:
- Só marque divergencia=true se tiver CERTEZA de que a taxa mudou (fonte confiável, data recente).
- Se houver dúvida, marque divergencia=false.
- Não invente taxas. Se não encontrar, taxa_sugerida=null.
"""
    try:
        resposta = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=400,
            response_format={"type": "json_object"},
        )
        import json
        return json.loads(resposta.choices[0].message.content)
    except Exception as e:
        return {
            "divergencia": False,
            "taxa_sugerida": None,
            "justificativa": f"Erro ao analisar: {str(e)}",
            "fonte": "",
        }


def verificar_todas_regras(client):
    """Percorre todas as regras ativas e verifica cada uma. Retorna lista de resultados."""
    regras = carregar_regras()
    resultados = []

    for regra_id, dados in regras.items():
        if not dados.get("ativo", True):
            continue

        verificacao = verificar_regras_banco(
            regra_id=regra_id,
            nome_regra=dados.get("nome", regra_id),
            banco=dados.get("banco", ""),
            taxa_atual=dados.get("taxa_anual", 0),
        )

        if verificacao is None:
            continue

        analise = analisar_divergencia_com_ia(client, verificacao)
        verificacao["analise"] = analise
        resultados.append(verificacao)

    return resultados