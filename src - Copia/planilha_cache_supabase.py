"""
Cache de planilhas no Supabase (substitui o JSON local).
"""
from src.db import get_client
from datetime import datetime
import pandas as pd
import re


def _client():
    c = get_client()
    if not c:
        raise Exception("Supabase não configurado.")
    return c


def _gerar_id(construtora, produto):
    """ID único por construtora+produto."""
    import unicodedata
    def slug(s):
        s = unicodedata.normalize("NFKD", str(s)).encode("ASCII", "ignore").decode("ASCII")
        return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_") or "x"
    return f"{slug(construtora)}__{slug(produto)}"


def salvar_planilha_sb(construtora, df, produto):
    """Salva um DataFrame no Supabase."""
    client = _client()
    try:
        # Converte DataFrame para dict JSON-safe
        dados = {
            "construtora": construtora,
            "produto": produto,
            "data_upload": datetime.now().isoformat(),
            "colunas": df.columns.tolist(),
            "dados": df.to_dict(orient="records"),
        }
        # Limpa NaN
        from src.db import limpar_nan
        dados = limpar_nan(dados)

        client.table("planilhas_cache").upsert({
            "id": _gerar_id(construtora, produto),
            "construtora": construtora,
            "produto": produto,
            "dados": dados,
            "atualizado_em": datetime.now().isoformat(),
        }).execute()
        return True
    except Exception as e:
        import streamlit as st
        st.error(f"❌ Erro ao salvar planilha no Supabase: {str(e)}")
        return False


def carregar_planilha_sb(construtora, produto):
    """Retorna DataFrame ou None."""
    client = _client()
    try:
        response = client.table("planilhas_cache").select("*").eq(
            "id", _gerar_id(construtora, produto)
        ).limit(1).execute()

        if not response.data:
            return None

        dados = response.data[0].get("dados", {})
        colunas = dados.get("colunas", [])
        registros = dados.get("dados", [])

        if not colunas or not registros:
            return None

        return pd.DataFrame(registros, columns=colunas)
    except Exception as e:
        import streamlit as st
        st.error(f"❌ Erro ao carregar planilha do Supabase: {str(e)}")
        return None


def tem_planilha_sb(construtora, produto):
    """Verifica se existe planilha em cache."""
    client = _client()
    try:
        response = client.table("planilhas_cache").select("id").eq(
            "id", _gerar_id(construtora, produto)
        ).limit(1).execute()
        return len(response.data or []) > 0
    except Exception:
        return False


def excluir_planilha_sb(construtora, produto):
    """Remove uma planilha do cache."""
    client = _client()
    try:
        client.table("planilhas_cache").delete().eq(
            "id", _gerar_id(construtora, produto)
        ).execute()
        return True
    except Exception as e:
        import streamlit as st
        st.error(f"❌ Erro ao excluir planilha: {str(e)}")
        return False


def migrar_planilhas_do_local():
    """Migra todos os JSONs de dados/planilhas/ para o Supabase (1x)."""
    import json
    import os

    pasta = "dados/planilhas"
    if not os.path.exists(pasta):
        return 0, "Pasta não encontrada"

    arquivos = [f for f in os.listdir(pasta) if f.endswith(".json")]
    count = 0

    for arq in arquivos:
        try:
            with open(os.path.join(pasta, arq), "r", encoding="utf-8") as f:
                dados = json.load(f)

            construtora = dados.get("construtora")
            produto = dados.get("produto")
            colunas = dados.get("colunas", [])
            registros = dados.get("dados", [])

            if not construtora or not produto or not registros:
                continue

            client = _client()
            client.table("planilhas_cache").upsert({
                "id": _gerar_id(construtora, produto),
                "construtora": construtora,
                "produto": produto,
                "dados": dados,
                "atualizado_em": datetime.now().isoformat(),
            }).execute()
            count += 1
        except Exception as e:
            print(f"Erro em {arq}: {e}")

    return count, "OK"