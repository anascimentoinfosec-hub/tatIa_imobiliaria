import json
import os

ARQUIVO_CONFIG = "dados/construtoras.json"
ARQUIVO_CIDADES = "dados/cidades.json"


def carregar_cidades():
    try:
        if os.path.exists(ARQUIVO_CIDADES):
            with open(ARQUIVO_CIDADES, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return [
        "Barra da Tijuca", "Recreio dos Bandeirantes", "Jacarepaguá",
        "Rio de Janeiro (Capital)", "Niterói", "São Gonçalo",
        "Duque de Caxias", "Nova Iguaçu", "Campos dos Goytacazes",
        "Petrópolis", "Teresópolis",
    ]


def salvar_cidades(cidades):
    with open(ARQUIVO_CIDADES, "w", encoding="utf-8") as f:
        json.dump(cidades, f, indent=2, ensure_ascii=False)


def carregar_construtoras():
    try:
        if os.path.exists(ARQUIVO_CONFIG):
            with open(ARQUIVO_CONFIG, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def salvar_construtoras(construtoras):
    with open(ARQUIVO_CONFIG, "w", encoding="utf-8") as f:
        json.dump(construtoras, f, indent=2, ensure_ascii=False)


def obter_cidades_em_uso(construtoras):
    cidades = set()
    for construtora, dados in construtoras.items():
        for produto, config in dados.get("produtos", {}).items():
            cidade = config.get("cidade")
            if cidade:
                cidades.add(cidade)
    return cidades