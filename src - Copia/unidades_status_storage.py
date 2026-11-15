"""
Controle de status das unidades (disponível / em processo / vendida).
Impede que 2 corretores ofertem a mesma unidade.
"""
from src.db import get_client
from datetime import datetime


STATUS_UNIDADE = {
    "disponivel": {"nome": "🟢 Disponível", "cor": "#22c55e"},
    "em_processo": {"nome": "🟡 Em processo", "cor": "#f59e0b"},
    "vendida": {"nome": "🔴 Vendida", "cor": "#ef4444"},
}


def _client():
    c = get_client()
    if not c:
        raise Exception("Supabase não configurado.")
    return c


def _gerar_id(construtora, produto, unidade):
    """ID único por chave lógica."""
    import re
    import unicodedata
    def slug(s):
        s = unicodedata.normalize("NFKD", str(s)).encode("ASCII", "ignore").decode("ASCII")
        return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_") or "x"
    return f"{slug(construtora)}__{slug(produto)}__{slug(unidade)}"


def marcar_unidade(construtora, produto, unidade, status="em_processo",
                    proposta_id=None, cliente=None, corretor=None):
    """Marca uma unidade com um status."""
    client = _client()
    try:
        uid = _gerar_id(construtora, produto, unidade)
        client.table("unidades_status").upsert({
            "id": uid,
            "construtora": str(construtora),
            "produto": str(produto),
            "unidade": str(unidade),
            "status": status,
            "proposta_id": proposta_id,
            "cliente": cliente or "",
            "corretor": corretor or "",
            "atualizado_em": datetime.now().isoformat(),
        }).execute()
        return True
    except Exception as e:
        import streamlit as st
        st.error(f"❌ Erro ao marcar unidade: {str(e)}")
        return False


def desmarcar_unidade(construtora, produto, unidade):
    """Remove o status (volta a disponível)."""
    client = _client()
    try:
        uid = _gerar_id(construtora, produto, unidade)
        client.table("unidades_status").delete().eq("id", uid).execute()
        return True
    except Exception as e:
        import streamlit as st
        st.error(f"❌ Erro ao desmarcar unidade: {str(e)}")
        return False


def carregar_todas_marcadas():
    """Retorna dict {chave: {status, proposta_id, cliente, corretor}}."""
    client = _client()
    try:
        response = client.table("unidades_status").select("*").execute()
        resultado = {}
        for r in response.data or []:
            chave = (str(r.get("construtora", "")), str(r.get("produto", "")), str(r.get("unidade", "")))
            resultado[chave] = {
                "status": r.get("status", "disponivel"),
                "proposta_id": r.get("proposta_id"),
                "cliente": r.get("cliente", ""),
                "corretor": r.get("corretor", ""),
            }
        return resultado
    except Exception:
        return {}


def carregar_status_unidade(construtora, produto, unidade):
    """Retorna o dict da unidade ou None se não estiver marcada."""
    todas = carregar_todas_marcadas()
    chave = (str(construtora), str(produto), str(unidade))
    return todas.get(chave)