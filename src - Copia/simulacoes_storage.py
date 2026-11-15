import json
import os
from datetime import datetime, timezone, timedelta
from src.db import supabase_disponivel

ARQUIVO_SIMULACOES = "dados/simulacoes.json"

# Define o fuso horário de Brasília (UTC-3)
FUSO_BR = timezone(timedelta(hours=-3))

STATUS_PROPOSTA = {
    "pendente": {"nome": "🔔 Pendente (cliente aceitou)", "cor": "#f59e0b", "ordem": 1, "acao": "Enviar para análise"},
    "em_analise": {"nome": "📤 Em análise (acessoria)", "cor": "#3b82f6", "ordem": 2, "acao": "Aprovar / Rejeitar"},
    "aprovada": {"nome": "✅ Aprovada (crédito)", "cor": "#22c55e", "ordem": 3, "acao": "Cadastrar na construtora"},
    "aguardando_construtora": {"nome": "🏢 Aguardando validação construtora", "cor": "#8b5cf6", "ordem": 4, "acao": "Contrato foi enviado?"},
    "contrato_enviado": {"nome": "📄 Contrato enviado (aguardando assinatura)", "cor": "#06b6d4", "ordem": 5, "acao": "Confirmar venda"},
    "venda_confirmada": {"nome": "🎉 Venda confirmada", "cor": "#10b981", "ordem": 6, "acao": None},
    "rejeitada": {"nome": "❌ Rejeitada", "cor": "#ef4444", "ordem": 99, "acao": None},
}

# =========================================================
# FALLBACK JSON
# =========================================================
def _carregar_raw():
    try:
        if os.path.exists(ARQUIVO_SIMULACOES):
            with open(ARQUIVO_SIMULACOES, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return []

def _salvar_raw(simulacoes):
    os.makedirs(os.path.dirname(ARQUIVO_SIMULACOES), exist_ok=True)
    with open(ARQUIVO_SIMULACOES, "w", encoding="utf-8") as f:
        json.dump(simulacoes, f, indent=2, ensure_ascii=False, default=str)

def _gerar_id():
    return datetime.now(FUSO_BR).strftime("%Y%m%d%H%M%S%f")

# =========================================================
# SALVAR
# =========================================================
def salvar_simulacao(nome_cliente, renda, entrada, bairro, origem,
                     desconto, tipo_desconto, gerente, top_recomendacoes,
                     status_proposta="pendente", dados_extra=None):
    oportunidades = []
    if top_recomendacoes is not None and not top_recomendacoes.empty:
        for _, row in top_recomendacoes.iterrows():
            item = {}
            for col in row.index:
                col_str = str(col)
                val = row[col]
                if hasattr(val, "item"):
                    val = val.item()
                item[col_str] = val
            oportunidades.append(item)

    registro = {
        "id": _gerar_id(),
        "data_hora": datetime.now(FUSO_BR).isoformat(), # <-- FUSO BRASIL AQUI
        "cliente": nome_cliente,
        "renda": float(renda),
        "entrada": float(entrada),
        "bairro": bairro or "",
        "origem": origem or "",
        "desconto": float(desconto),
        "tipo_desconto": tipo_desconto,
        "gerente": gerente or "",
        "total_oportunidades": len(oportunidades),
        "oportunidades": oportunidades,
        "status_proposta": status_proposta,
        "historico_status": [{
            "status": status_proposta,
            "data": datetime.now(FUSO_BR).isoformat(), # <-- FUSO BRASIL AQUI
            "por": gerente or "",
            "motivo": "",
        }],
    }

    if dados_extra:
        for k, v in dados_extra.items():
            registro[k] = v

    if supabase_disponivel():
        from src.simulacoes_storage_supabase import salvar_simulacao_sb
        salvar_simulacao_sb(registro)
    else:
        simulacoes = _carregar_raw()
        simulacoes.append(registro)
        _salvar_raw(simulacoes)

    return registro["id"]

# =========================================================
# CARREGAR
# =========================================================
def carregar_simulacoes():
    if supabase_disponivel():
        from src.simulacoes_storage_supabase import carregar_simulacoes as _sb, migrar_do_json
        dados = _sb()
        if not dados:
            count, _ = migrar_do_json()
            if count > 0:
                dados = _sb()
        return dados

    simulacoes = _carregar_raw()
    return list(reversed(simulacoes))

def carregar_simulacao_por_id(sim_id):
    if supabase_disponivel():
        for sim in carregar_simulacoes():
            if sim.get("id") == sim_id:
                return sim
        return None

    for sim in _carregar_raw():
        if sim["id"] == sim_id:
            return sim
    return None

# =========================================================
# ATUALIZAR STATUS
# =========================================================
def atualizar_status_proposta(sim_id, novo_status, por_usuario="", motivo=""):
    if novo_status not in STATUS_PROPOSTA:
        return False

    if supabase_disponivel():
        from src.simulacoes_storage_supabase import carregar_simulacoes as _sb, salvar_simulacao_sb
        for sim in _sb():
            if sim.get("id") == sim_id:
                sim["status_proposta"] = novo_status
                hist = sim.get("historico_status", [])
                hist.append({
                    "status": novo_status,
                    "data": datetime.now(FUSO_BR).isoformat(),
                    "por": por_usuario,
                    "motivo": motivo,
                })
                sim["historico_status"] = hist
                salvar_simulacao_sb(sim)
                return True
        return False

    simulacoes = _carregar_raw()
    for sim in simulacoes:
        if sim["id"] == sim_id:
            sim["status_proposta"] = novo_status
            hist = sim.get("historico_status", [])
            hist.append({
                "status": novo_status,
                "data": datetime.now(FUSO_BR).isoformat(),
                "por": por_usuario,
                "motivo": motivo,
            })
            sim["historico_status"] = hist
            _salvar_raw(simulacoes)
            return True
    return False

# =========================================================
# EXCLUIR
# =========================================================
def excluir_simulacao(sim_id):
    if supabase_disponivel():
        from src.simulacoes_storage_supabase import excluir_simulacao_sb
        return excluir_simulacao_sb(sim_id)

    simulacoes = _carregar_raw()
    novas = [s for s in simulacoes if s["id"] != sim_id]
    if len(novas) < len(simulacoes):
        _salvar_raw(novas)
        return True
    return False

# =========================================================
# HELPERS
# =========================================================
def contar_propostas_pendentes():
    simulacoes = carregar_simulacoes()
    return sum(1 for s in simulacoes if s.get("status_proposta") == "pendente")

def listar_propostas_por_status(status):
    simulacoes = carregar_simulacoes()
    return [s for s in simulacoes if s.get("status_proposta") == status]

def listar_propostas_ativas():
    ativos = {"pendente", "em_analise", "aprovada", "aguardando_construtora", "contrato_enviado"}
    simulacoes = carregar_simulacoes()
    return [s for s in simulacoes if s.get("status_proposta") in ativos]