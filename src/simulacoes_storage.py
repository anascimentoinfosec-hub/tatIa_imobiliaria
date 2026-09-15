import json
import os
from datetime import datetime

ARQUIVO_SIMULACOES = "dados/simulacoes.json"


def _carregar_raw():
    """Carrega a lista de simulações do JSON."""
    try:
        if os.path.exists(ARQUIVO_SIMULACOES):
            with open(ARQUIVO_SIMULACOES, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return []


def _salvar_raw(simulacoes):
    """Salva a lista de simulações no JSON."""
    os.makedirs(os.path.dirname(ARQUIVO_SIMULACOES), exist_ok=True)
    with open(ARQUIVO_SIMULACOES, "w", encoding="utf-8") as f:
        json.dump(simulacoes, f, indent=2, ensure_ascii=False, default=str)


def _gerar_id():
    """Gera um ID único baseado em timestamp."""
    return datetime.now().strftime("%Y%m%d%H%M%S%f")


def salvar_simulacao(nome_cliente, renda, entrada, bairro, origem,
                     desconto, tipo_desconto, gerente, top_recomendacoes):
    """
    Salva uma nova simulação no histórico.
    Retorna o ID gerado.
    """
    simulacoes = _carregar_raw()

    # Converte o DataFrame em lista de dicts (seguro para JSON)
    oportunidades = []
    if top_recomendacoes is not None and not top_recomendacoes.empty:
        for _, row in top_recomendacoes.iterrows():
            item = {}
            for col in ["UNIDADE", "TIPOLOGIA", "BLOCO", "PAVTO", "ANDAR",
                        "AVALIAÇÃO", "PREÇO", "valor_base", "parcela_estimada"]:
                if col in row.index:
                    val = row[col]
                    # Converte tipos problemáticos
                    if hasattr(val, "item"):
                        val = val.item()
                    item[col] = val
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
    }

    simulacoes.append(registro)
    _salvar_raw(simulacoes)
    return registro["id"]


def carregar_simulacoes():
    """Retorna todas as simulações (mais recentes primeiro)."""
    simulacoes = _carregar_raw()
    return list(reversed(simulacoes))


def carregar_simulacao_por_id(sim_id):
    """Retorna uma simulação pelo ID, ou None."""
    for sim in _carregar_raw():
        if sim["id"] == sim_id:
            return sim
    return None


def excluir_simulacao(sim_id):
    """Remove uma simulação pelo ID."""
    simulacoes = _carregar_raw()
    novas = [s for s in simulacoes if s["id"] != sim_id]
    if len(novas) < len(simulacoes):
        _salvar_raw(novas)
        return True
    return False