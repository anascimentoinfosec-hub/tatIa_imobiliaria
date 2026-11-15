"""
Camada de conexão com Supabase.
Todos os storages usam essa base para ler/gravar dados.
"""
import streamlit as st

try:
    from supabase import create_client, Client
    _SUPABASE_DISPONIVEL = True
except ImportError:
    _SUPABASE_DISPONIVEL = False
    Client = None


@st.cache_resource
def get_client():
    """Retorna o cliente Supabase configurado (cached)."""
    if not _SUPABASE_DISPONIVEL:
        return None

    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_SERVICE_KEY"]
        return create_client(url, key)
    except Exception as e:
        st.error(f"❌ Erro ao conectar no Supabase: {str(e)}")
        return None


def supabase_disponivel():
    """Retorna True se o Supabase está configurado e disponível."""
    return _SUPABASE_DISPONIVEL and get_client() is not None


# =========================================================
# HELPERS GENÉRICOS
# =========================================================
def inserir(tabela, dados):
    """Insere um registro. Retorna o registro inserido ou None."""
    client = get_client()
    if not client:
        return None
    try:
        response = client.table(tabela).insert(dados).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        st.error(f"❌ Erro ao inserir em {tabela}: {str(e)}")
        return None


def atualizar(tabela, chave_campo, chave_valor, dados):
    """Atualiza um registro identificado por chave_campo=chave_valor."""
    client = get_client()
    if not client:
        return None
    try:
        response = client.table(tabela).update(dados).eq(chave_campo, chave_valor).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        st.error(f"❌ Erro ao atualizar em {tabela}: {str(e)}")
        return None


def deletar(tabela, chave_campo, chave_valor):
    """Deleta um registro."""
    client = get_client()
    if not client:
        return False
    try:
        client.table(tabela).delete().eq(chave_campo, chave_valor).execute()
        return True
    except Exception as e:
        st.error(f"❌ Erro ao deletar em {tabela}: {str(e)}")
        return False


def listar(tabela, ordem_por=None, desc=False):
    """Lista todos os registros."""
    client = get_client()
    if not client:
        return []
    try:
        query = client.table(tabela).select("*")
        if ordem_por:
            query = query.order(ordem_por, desc=desc)
        response = query.execute()
        return response.data or []
    except Exception as e:
        st.error(f"❌ Erro ao listar {tabela}: {str(e)}")
        return []


def buscar_por(tabela, chave_campo, chave_valor):
    """Busca um único registro."""
    client = get_client()
    if not client:
        return None
    try:
        response = client.table(tabela).select("*").eq(chave_campo, chave_valor).limit(1).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        st.error(f"❌ Erro ao buscar em {tabela}: {str(e)}")
        return None

def limpar_nan(obj):
    """
    Substitui recursivamente valores NaN/inf por None (JSON-safe).
    """
    import math
    if isinstance(obj, dict):
        return {k: limpar_nan(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [limpar_nan(v) for v in obj]
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
    # Trata numpy types
    try:
        import numpy as np
        if isinstance(obj, np.floating):
            f = float(obj)
            if math.isnan(f) or math.isinf(f):
                return None
            return f
        if isinstance(obj, np.integer):
            return int(obj)
    except ImportError:
        pass
    return obj