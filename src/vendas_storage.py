import json
import os
from datetime import datetime

ARQUIVO_VENDAS = "dados/vendas.json"
ARQUIVO_STATUS = "dados/vendas_status.json"
ARQUIVO_CAMPOS_EXTRAS = "dados/vendas_campos_extras.json"

# =========================================================
# STATUS PADRÃO
# =========================================================
STATUS_PADRAO = [
    {"id": "nao_iniciado", "nome": "Não iniciado", "cor": "#94a3b8", "ordem": 1},
    {"id": "em_validacao", "nome": "Em validação de pendências", "cor": "#f59e0b", "ordem": 2},
    {"id": "ato_parcial", "nome": "Ato pago (parcial)", "cor": "#eab308", "ordem": 3},
    {"id": "ato_integral", "nome": "Ato pago integral", "cor": "#3b82f6", "ordem": 4},
    {"id": "aguardando_matricula", "nome": "Aguardando atualização de matrícula", "cor": "#8b5cf6", "ordem": 5},
    {"id": "aguardando_assinatura", "nome": "Aguardando assinatura de contrato", "cor": "#06b6d4", "ordem": 6},
    {"id": "concluido", "nome": "Ato resolvido (comissão paga) - Concluído", "cor": "#22c55e", "ordem": 7},
]

# =========================================================
# CAMPOS PADRÃO (fixos) DA VENDA
# =========================================================
CAMPOS_FIXOS = [
    "fonte",
    "cliente",
    "produto",
    "bloco",
    "apt",
    "construtora",
    "vgv",
    "responsavel",
    "data_venda",
    "ato_pago",
    "status",
    "observacoes",
]


# =========================================================
# HELPERS
# =========================================================
def _carregar_json(arquivo, padrao):
    try:
        if os.path.exists(arquivo):
            with open(arquivo, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return padrao


def _salvar_json(arquivo, dados):
    os.makedirs(os.path.dirname(arquivo), exist_ok=True)
    with open(arquivo, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=2, ensure_ascii=False, default=str)


def _gerar_id():
    return datetime.now().strftime("%Y%m%d%H%M%S%f")


# =========================================================
# VENDAS — CRUD
# =========================================================
def carregar_vendas():
    """Retorna todas as vendas (mais recentes primeiro)."""
    vendas = _carregar_json(ARQUIVO_VENDAS, [])
    return list(reversed(vendas))


def salvar_venda(dados):
    """Adiciona uma nova venda. Retorna o ID gerado."""
    vendas = _carregar_json(ARQUIVO_VENDAS, [])

    registro = {
        "id": _gerar_id(),
        "criado_em": datetime.now().isoformat(),
    }

    # Preenche campos fixos (se existirem nos dados)
    for campo in CAMPOS_FIXOS:
        if campo in dados:
            registro[campo] = dados[campo]

    # Campos extras
    registro["campos_extras"] = dados.get("campos_extras", {})

    vendas.append(registro)
    _salvar_json(ARQUIVO_VENDAS, vendas)
    return registro["id"]


def atualizar_venda(venda_id, dados):
    """Atualiza uma venda existente."""
    vendas = _carregar_json(ARQUIVO_VENDAS, [])
    for v in vendas:
        if v["id"] == venda_id:
            for campo in CAMPOS_FIXOS:
                if campo in dados:
                    v[campo] = dados[campo]
            if "campos_extras" in dados:
                v["campos_extras"] = dados["campos_extras"]
            v["atualizado_em"] = datetime.now().isoformat()
            break
    _salvar_json(ARQUIVO_VENDAS, vendas)


def excluir_venda(venda_id):
    """Remove uma venda pelo ID."""
    vendas = _carregar_json(ARQUIVO_VENDAS, [])
    novas = [v for v in vendas if v["id"] != venda_id]
    if len(novas) < len(vendas):
        _salvar_json(ARQUIVO_VENDAS, novas)
        return True
    return False


def obter_venda(venda_id):
    """Retorna uma venda pelo ID."""
    vendas = _carregar_json(ARQUIVO_VENDAS, [])
    for v in vendas:
        if v["id"] == venda_id:
            return v
    return None


# =========================================================
# STATUS
# =========================================================
def carregar_status():
    status = _carregar_json(ARQUIVO_STATUS, None)
    if status is None:
        _salvar_json(ARQUIVO_STATUS, STATUS_PADRAO)
        return STATUS_PADRAO.copy()
    return sorted(status, key=lambda s: s.get("ordem", 999))


def salvar_status(lista_status):
    _salvar_json(ARQUIVO_STATUS, lista_status)


def obter_status_por_id(status_id):
    for s in carregar_status():
        if s["id"] == status_id:
            return s
    return None


# =========================================================
# CAMPOS EXTRAS (personalizáveis)
# =========================================================
def carregar_campos_extras():
    """Retorna lista de campos extras: [{"id": "x", "nome": "X", "tipo": "texto"}, ...]"""
    return _carregar_json(ARQUIVO_CAMPOS_EXTRAS, [])


def salvar_campos_extras(campos):
    _salvar_json(ARQUIVO_CAMPOS_EXTRAS, campos)


def adicionar_campo_extra(nome, tipo="texto"):
    campos = carregar_campos_extras()
    campo_id = nome.lower().strip().replace(" ", "_")
    # Remove acentos básicos
    import unicodedata
    campo_id = unicodedata.normalize("NFKD", campo_id).encode("ASCII", "ignore").decode("ASCII")
    campos.append({"id": campo_id, "nome": nome.strip(), "tipo": tipo})
    salvar_campos_extras(campos)


def remover_campo_extra(campo_id):
    campos = carregar_campos_extras()
    novos = [c for c in campos if c["id"] != campo_id]
    if len(novos) < len(campos):
        salvar_campos_extras(novos)
        return True
    return False


# =========================================================
# MÉTRICAS AGREGADAS (para dashboard)
# =========================================================
def calcular_metricas():
    """Retorna dict com métricas agregadas para o dashboard."""
    vendas = carregar_vendas()

    vgv_total = 0.0
    por_status = {}
    por_construtora = {}
    por_responsavel = {}

    for v in vendas:
        try:
            vgv = float(v.get("vgv", 0) or 0)
        except (ValueError, TypeError):
            vgv = 0.0

        vgv_total += vgv

        status_id = v.get("status", "nao_iniciado")
        por_status[status_id] = por_status.get(status_id, 0) + 1

        construtora = v.get("construtora", "N/A") or "N/A"
        por_construtora[construtora] = por_construtora.get(construtora, 0) + vgv

        resp = v.get("responsavel", "N/A") or "N/A"
        if resp not in por_responsavel:
            por_responsavel[resp] = {"qtd": 0, "vgv": 0.0}
        por_responsavel[resp]["qtd"] += 1
        por_responsavel[resp]["vgv"] += vgv

    return {
        "total_vendas": len(vendas),
        "vgv_total": round(vgv_total, 2),
        "vgv_medio": round(vgv_total / len(vendas), 2) if vendas else 0.0,
        "por_status": por_status,
        "por_construtora": por_construtora,
        "por_responsavel": por_responsavel,
    }