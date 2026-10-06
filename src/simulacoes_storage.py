import json
import os
from datetime import datetime

ARQUIVO_SIMULACOES = "dados/simulacoes.json"

# =========================================================
# STATUS DO FUNIL DE VENDA
# =========================================================
STATUS_PROPOSTA = {
    "pendente": {
        "nome": "🔔 Pendente (cliente aceitou)",
        "cor": "#f59e0b",
        "ordem": 1,
        "acao": "Enviar para análise",
    },
    "em_analise": {
        "nome": "📤 Em análise (acessoria)",
        "cor": "#3b82f6",
        "ordem": 2,
        "acao": "Aprovar / Rejeitar",
    },
    "aprovada": {
        "nome": "✅ Aprovada (crédito)",
        "cor": "#22c55e",
        "ordem": 3,
        "acao": "Cadastrar na construtora",
    },
    "aguardando_construtora": {
        "nome": "🏢 Aguardando validação construtora",
        "cor": "#8b5cf6",
        "ordem": 4,
        "acao": "Contrato foi enviado?",
    },
    "contrato_enviado": {
        "nome": "📄 Contrato enviado (aguardando assinatura)",
        "cor": "#06b6d4",
        "ordem": 5,
        "acao": "Confirmar venda",
    },
    "venda_confirmada": {
        "nome": "🎉 Venda confirmada",
        "cor": "#10b981",
        "ordem": 6,
        "acao": None,
    },
    "rejeitada": {
        "nome": "❌ Rejeitada",
        "cor": "#ef4444",
        "ordem": 99,
        "acao": None,
    },
}


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
    return datetime.now().strftime("%Y%m%d%H%M%S%f")


def salvar_simulacao(nome_cliente, renda, entrada, bairro, origem,
                     desconto, tipo_desconto, gerente, top_recomendacoes,
                     status_proposta="pendente", dados_extra=None):
    """Salva uma nova simulação no histórico. Retorna o ID gerado."""
    simulacoes = _carregar_raw()

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
        "data_hora": datetime.now().isoformat(),
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
        "historico_status": [
            {"status": status_proposta, "data": datetime.now().isoformat(),
             "por": gerente or "", "motivo": ""}
        ],
    }

    # Dados extras (data_nascimento, fgts, subsidio, parcela_morando, etc.)
    if dados_extra:
        for k, v in dados_extra.items():
            registro[k] = v

    simulacoes.append(registro)
    _salvar_raw(simulacoes)
    return registro["id"]


def atualizar_status_proposta(sim_id, novo_status, por_usuario="", motivo=""):
    """Atualiza o status de uma proposta."""
    if novo_status not in STATUS_PROPOSTA:
        return False

    simulacoes = _carregar_raw()
    for sim in simulacoes:
        if sim["id"] == sim_id:
            sim["status_proposta"] = novo_status
            hist = sim.get("historico_status", [])
            hist.append({
                "status": novo_status,
                "data": datetime.now().isoformat(),
                "por": por_usuario,
                "motivo": motivo,
            })
            sim["historico_status"] = hist
            _salvar_raw(simulacoes)
            return True
    return False


def carregar_simulacoes():
    simulacoes = _carregar_raw()
    return list(reversed(simulacoes))


def carregar_simulacao_por_id(sim_id):
    for sim in _carregar_raw():
        if sim["id"] == sim_id:
            return sim
    return None


def excluir_simulacao(sim_id):
    simulacoes = _carregar_raw()
    novas = [s for s in simulacoes if s["id"] != sim_id]
    if len(novas) < len(simulacoes):
        _salvar_raw(novas)
        return True
    return False


def contar_propostas_pendentes():
    """Conta quantas propostas estão com status 'pendente'."""
    simulacoes = _carregar_raw()
    return sum(1 for s in simulacoes if s.get("status_proposta") == "pendente")


def listar_propostas_por_status(status):
    simulacoes = _carregar_raw()
    return [s for s in reversed(simulacoes) if s.get("status_proposta") == status]


def listar_propostas_ativas():
    """Retorna propostas que ainda estão no fluxo (não confirmadas nem rejeitadas)."""
    simulacoes = _carregar_raw()
    ativos = {"pendente", "em_analise", "aprovada",
              "aguardando_construtora", "contrato_enviado"}
    return [s for s in reversed(simulacoes) if s.get("status_proposta") in ativos]