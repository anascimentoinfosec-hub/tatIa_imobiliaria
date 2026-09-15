import json
import os

ARQUIVO_ORIGENS = "dados/origens_cliente.json"

ORIGENS_PADRAO = ["Lead", "Indicação", "Espontâneo", "Captação Própria"]


def carregar_origens():
    """Carrega lista de origens do JSON. Se não existir, cria com padrão."""
    try:
        if os.path.exists(ARQUIVO_ORIGENS):
            with open(ARQUIVO_ORIGENS, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass

    salvar_origens(ORIGENS_PADRAO)
    return ORIGENS_PADRAO.copy()


def salvar_origens(origens):
    os.makedirs(os.path.dirname(ARQUIVO_ORIGENS), exist_ok=True)
    with open(ARQUIVO_ORIGENS, "w", encoding="utf-8") as f:
        json.dump(origens, f, indent=2, ensure_ascii=False)