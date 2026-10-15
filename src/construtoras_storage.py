"""
Camada de leitura/gravação de construtoras no Supabase.
Cada construtora é uma linha: nome + dados (JSONB com produtos).
"""
from src.db import get_client
from src.utils import hash_senha  # não usado, mas mantém padrão
from datetime import datetime


def _client():
    c = get_client()
    if not c:
        raise Exception("Supabase não configurado.")
    return c


# =========================================================
# CONSTRUTORAS
# =========================================================
def carregar_construtoras():
    """
    Retorna dict {nome_construtora: {tipo_desconto, produtos: {...}}}
    igual ao formato do JSON antigo.
    """
    client = _client()
    try:
        response = client.table("construtoras").select("*").execute()
        construtoras = {}
        for r in response.data or []:
            nome = r.get("nome")
            dados = r.get("dados") or {}
            if nome:
                construtoras[nome] = dados
        return construtoras
    except Exception as e:
        import streamlit as st
        st.error(f"❌ Erro ao carregar construtoras: {str(e)}")
        return {}


def salvar_construtoras(construtoras_dict):
    """
    Sincroniza o dict inteiro com o Supabase:
    - Atualiza quem já existe
    - Insere quem é novo
    - Remove quem sumiu
    """
    client = _client()
    try:
        # Lista atual no banco
        response = client.table("construtoras").select("nome").execute()
        nomes_banco = {r["nome"] for r in (response.data or [])}
        nomes_dict = set(construtoras_dict.keys())

        # Atualiza ou insere
        for nome, dados in construtoras_dict.items():
            if nome in nomes_banco:
                client.table("construtoras").update({
                    "dados": dados,
                    "atualizado_em": datetime.now().isoformat(),
                }).eq("nome", nome).execute()
            else:
                client.table("construtoras").insert({
                    "nome": nome,
                    "dados": dados,
                }).execute()

        # Remove quem sumiu
        for nome_remover in nomes_banco - nomes_dict:
            client.table("construtoras").delete().eq("nome", nome_remover).execute()

    except Exception as e:
        import streamlit as st
        st.error(f"❌ Erro ao salvar construtoras: {str(e)}")


def migrar_do_json(caminho_json="dados/construtoras.json"):
    """Migra construtoras do JSON antigo para o Supabase (1x)."""
    import json
    import os

    if not os.path.exists(caminho_json):
        return 0, "Arquivo JSON não encontrado."

    try:
        with open(caminho_json, "r", encoding="utf-8") as f:
            dados_json = json.load(f)
    except Exception as e:
        return 0, f"Erro ao ler JSON: {str(e)}"

    client = _client()
    response = client.table("construtoras").select("nome").execute()
    nomes_existentes = {r["nome"] for r in (response.data or [])}

    count = 0
    for nome, dados in dados_json.items():
        if nome in nomes_existentes:
            continue
        client.table("construtoras").insert({
            "nome": nome,
            "dados": dados,
        }).execute()
        count += 1

    return count, "OK"


# =========================================================
# CIDADES
# =========================================================
def carregar_cidades():
    client = _client()
    try:
        response = client.table("cidades").select("*").order("ordem").execute()
        return [r["nome"] for r in (response.data or [])]
    except Exception:
        return []


def salvar_cidades(lista_cidades):
    client = _client()
    try:
        response = client.table("cidades").select("nome").execute()
        nomes_banco = {r["nome"] for r in (response.data or [])}
        nomes_lista = set(lista_cidades)

        # Insere novas
        for i, nome in enumerate(lista_cidades):
            if nome not in nomes_banco:
                client.table("cidades").insert({"nome": nome, "ordem": i}).execute()

        # Remove as que sumiram
        for nome_remover in nomes_banco - nomes_lista:
            client.table("cidades").delete().eq("nome", nome_remover).execute()

    except Exception as e:
        import streamlit as st
        st.error(f"❌ Erro ao salvar cidades: {str(e)}")


def migrar_cidades_do_json(caminho_json="dados/cidades.json"):
    import json
    import os

    if not os.path.exists(caminho_json):
        return 0, "Arquivo não encontrado"

    try:
        with open(caminho_json, "r", encoding="utf-8") as f:
            cidades = json.load(f)
    except Exception as e:
        return 0, f"Erro: {str(e)}"

    client = _client()
    response = client.table("cidades").select("nome").execute()
    existentes = {r["nome"] for r in (response.data or [])}

    count = 0
    for i, nome in enumerate(cidades):
        if nome in existentes:
            continue
        client.table("cidades").insert({"nome": nome, "ordem": i}).execute()
        count += 1

    return count, "OK"


# =========================================================
# ORIGENS DO CLIENTE
# =========================================================
def carregar_origens():
    client = _client()
    try:
        response = client.table("origens_cliente").select("*").order("ordem").execute()
        return [r["nome"] for r in (response.data or [])]
    except Exception:
        return []


def salvar_origens(lista_origens):
    client = _client()
    try:
        response = client.table("origens_cliente").select("nome").execute()
        nomes_banco = {r["nome"] for r in (response.data or [])}
        nomes_lista = set(lista_origens)

        for i, nome in enumerate(lista_origens):
            if nome not in nomes_banco:
                client.table("origens_cliente").insert({"nome": nome, "ordem": i}).execute()

        for nome_remover in nomes_banco - nomes_lista:
            client.table("origens_cliente").delete().eq("nome", nome_remover).execute()
    except Exception as e:
        import streamlit as st
        st.error(f"❌ Erro ao salvar origens: {str(e)}")


def migrar_origens_do_json(caminho_json="dados/origens_cliente.json"):
    import json
    import os

    if not os.path.exists(caminho_json):
        return 0, "Arquivo não encontrado"

    try:
        with open(caminho_json, "r", encoding="utf-8") as f:
            origens = json.load(f)
    except Exception as e:
        return 0, f"Erro: {str(e)}"

    client = _client()
    response = client.table("origens_cliente").select("nome").execute()
    existentes = {r["nome"] for r in (response.data or [])}

    count = 0
    for i, nome in enumerate(origens):
        if nome in existentes:
            continue
        client.table("origens_cliente").insert({"nome": nome, "ordem": i}).execute()
        count += 1

    return count, "OK"


# =========================================================
# LAZER
# =========================================================
def carregar_lazer():
    client = _client()
    try:
        response = client.table("lazer_opcoes").select("*").order("ordem").execute()
        return [r["nome"] for r in (response.data or [])]
    except Exception:
        return []


def salvar_lazer(lista_lazer):
    client = _client()
    try:
        response = client.table("lazer_opcoes").select("nome").execute()
        nomes_banco = {r["nome"] for r in (response.data or [])}
        nomes_lista = set(lista_lazer)

        for i, nome in enumerate(lista_lazer):
            if nome not in nomes_banco:
                client.table("lazer_opcoes").insert({"nome": nome, "ordem": i}).execute()

        for nome_remover in nomes_banco - nomes_lista:
            client.table("lazer_opcoes").delete().eq("nome", nome_remover).execute()
    except Exception as e:
        import streamlit as st
        st.error(f"❌ Erro ao salvar lazer: {str(e)}")


def migrar_lazer_do_json(caminho_json="dados/lazer_opcoes.json"):
    import json
    import os

    if not os.path.exists(caminho_json):
        return 0, "Arquivo não encontrado"

    try:
        with open(caminho_json, "r", encoding="utf-8") as f:
            lazer = json.load(f)
    except Exception as e:
        return 0, f"Erro: {str(e)}"

    client = _client()
    response = client.table("lazer_opcoes").select("nome").execute()
    existentes = {r["nome"] for r in (response.data or [])}

    count = 0
    for i, nome in enumerate(lazer):
        if nome in existentes:
            continue
        client.table("lazer_opcoes").insert({"nome": nome, "ordem": i}).execute()
        count += 1

    return count, "OK"

# =========================================================
# FUNÇÃO AUXILIAR (usada pela tela de cidades)
# =========================================================
def obter_cidades_em_uso(construtoras):
    """Retorna set de cidades que estão sendo usadas por algum produto."""
    cidades = set()
    for construtora, dados in construtoras.items():
        for produto, config in dados.get("produtos", {}).items():
            cidade = config.get("cidade")
            if cidade:
                cidades.add(cidade)
    return cidades