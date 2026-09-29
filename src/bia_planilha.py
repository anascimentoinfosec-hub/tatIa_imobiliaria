import streamlit as st
import pandas as pd
import json
import io
from openai import OpenAI


def analisar_planilha_com_bia(uploaded_file):
    """
    Analisa uma planilha com a BIA (GPT) e retorna sugestões de mapeamento.
    Retorna dict com:
    {
        "header_row": int,
        "mapeamento": {"0": "UNIDADE", ...},
        "colunas_ordem": [...],
        "colunas_monetarias": [...],
        "colunas_numericas": [...],
        "skiprows": int,
        "observacoes": str
    }
    ou {"erro": "mensagem"} em caso de falha.
    """
    if "OPENAI_API_KEY" not in st.secrets:
        return {"erro": "Chave OpenAI não configurada nos secrets."}

    # Lê os bytes do arquivo (permite ler 2x sem problema de ponteiro)
    try:
        file_bytes = uploaded_file.getvalue()

        if uploaded_file.name.lower().endswith(".csv"):
            df_raw = pd.read_csv(io.BytesIO(file_bytes), header=None, dtype=str, nrows=20)
        else:
            df_raw = pd.read_excel(io.BytesIO(file_bytes), header=None, dtype=str, nrows=20)
    except Exception as e:
        return {"erro": f"Erro ao ler arquivo: {str(e)}"}

    if df_raw.empty:
        return {"erro": "Planilha vazia ou sem dados legíveis."}

    # Prepara amostra legível (índice das linhas + conteúdo)
    amostra_linhas = []
    for i, row in df_raw.head(15).iterrows():
        valores = [str(v) if pd.notna(v) else "" for v in row.tolist()]
        amostra_linhas.append(f"Linha {i}: {valores}")
    amostra = "\n".join(amostra_linhas)

    prompt = f"""Você é um especialista em planilhas imobiliárias.

Analise a amostra abaixo (primeiras 15 linhas de uma planilha de construtora):

{amostra}

Sua tarefa: identificar a estrutura dessa planilha.

Responda APENAS com JSON válido no seguinte formato:
{{
  "header_row": número inteiro (linha onde estão os NOMES das colunas, começando em 0),
  "mapeamento": {{"0": "UNIDADE", "1": "BLOCO", "2": "PREÇO", ...}} (índice da coluna → nome padronizado),
  "colunas_ordem": ["UNIDADE", "BLOCO", "TIPOLOGIA", "PREÇO", ...] (ordem sugerida para exibir),
  "colunas_monetarias": ["PREÇO", "AVALIAÇÃO", "DESCONTO", ...],
  "colunas_numericas": ["M²", "ANDAR", "PAVTO", "VAGA", "QUARTOS", ...],
  "skiprows": número de linhas em branco antes do cabeçalho,
  "observacoes": "texto curto sobre características da planilha (ex: cabeçalhos mesclados, dados em 2 linhas, etc)"
}}

REGRAS OBRIGATÓRIAS:
- Padronize nomes de colunas em MAIÚSCULAS, sem acentos, usando underscore se necessário.
- Nomes comuns esperados: UNIDADE, BLOCO, APT, PAVTO, ANDAR, TIPOLOGIA, M², VAGA, VAGAS, AVALIAÇÃO, PREÇO, DESCONTO, STATUS, DISPONIBILIDADE, QUARTOS.
- Se algum nome for ambíguo, mantenha em MAIÚSCULAS com o texto original.
- Colunas monetárias: aquelas cujos valores têm "R$" ou formato de dinheiro BR (ex: 380.000,00).
- Colunas numéricas: valores puramente numéricos (ex: 63.5, 1, 2).
- NÃO invente colunas que não existem.
- Se o cabeçalho estiver mesclado em 2 linhas, use a mais informativa.
- skiprows deve ser igual a header_row quando o cabeçalho é simples.
- Responda em português APENAS no campo observacoes.
"""

    try:
        client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=1000,
            response_format={"type": "json_object"},
        )
        resultado = json.loads(response.choices[0].message.content)
        return resultado
    except json.JSONDecodeError as e:
        return {"erro": f"Resposta inválida da IA: {str(e)}"}
    except Exception as e:
        return {"erro": f"Erro na IA: {str(e)}"}