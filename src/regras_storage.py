import json
import os

ARQUIVO_REGRAS = "dados/regras_financiamento.json"

# Fallback caso o arquivo não exista
REGRAS_PADRAO = {
    "caixa_sbpe": {
        "nome": "Caixa - SBPE",
        "banco": "Caixa",
        "taxa_anual": 0.1149,
        "prazo_max_meses": 420,
        "entrada_minima_pct": 20,
        "comprometimento_max_pct": 30,
        "sistema": "SAC",
        "ativo": True,
    }
}


def carregar_regras():
    """Carrega todas as regras do JSON."""
    try:
        if os.path.exists(ARQUIVO_REGRAS):
            with open(ARQUIVO_REGRAS, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass

    # Se não existir, cria com o padrão
    salvar_regras(REGRAS_PADRAO)
    return REGRAS_PADRAO.copy()


def salvar_regras(regras):
    """Salva as regras no JSON."""
    os.makedirs(os.path.dirname(ARQUIVO_REGRAS), exist_ok=True)
    with open(ARQUIVO_REGRAS, "w", encoding="utf-8") as f:
        json.dump(regras, f, indent=2, ensure_ascii=False)


def carregar_regras_ativas():
    """Retorna só as regras com ativo=True."""
    regras = carregar_regras()
    return {k: v for k, v in regras.items() if v.get("ativo", True)}


def obter_regra(regra_id):
    """Retorna uma regra específica pelo ID."""
    regras = carregar_regras()
    return regras.get(regra_id)


def salvar_regra(regra_id, dados_regra):
    """Adiciona ou atualiza uma regra."""
    regras = carregar_regras()
    regras[regra_id] = dados_regra
    salvar_regras(regras)


def excluir_regra(regra_id):
    """Remove uma regra."""
    regras = carregar_regras()
    if regra_id in regras:
        del regras[regra_id]
        salvar_regras(regras)
        return True
    return False


def gerar_id_regra(nome):
    """Gera um ID seguro a partir do nome (ex: 'Caixa - SBPE' → 'caixa_sbpe')."""
    import re
    import unicodedata

    # Remove acentos
    nome_normalizado = unicodedata.normalize("NFKD", nome)
    nome_normalizado = nome_normalizado.encode("ASCII", "ignore").decode("ASCII")

    # Minúsculo, troca espaços/hífens por _, remove caracteres especiais
    slug = nome_normalizado.lower().strip()
    slug = re.sub(r"[^a-z0-9]+", "_", slug)
    slug = slug.strip("_")

    return slug or "regra"