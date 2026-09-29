import json
import os

ARQUIVO_LAZER = "dados/lazer_opcoes.json"

LAZER_PADRAO = [
    "Complexo Aquático",
    "Salão de Festas",
    "Academia",
    "Cobertura",
    "Churrasqueira",
    "Quadra Poliesportiva",
    "Quadra de Beach Tennis",
    "Playground",
    "Pet Place",
    "Mini Mercado",
    "Redário",
    "Horta",
    "Espaço Piquenique",
    "Fitness",
    "Car Wash",
    "Futmesa",
]


def carregar_lazer():
    """Carrega as opções de lazer do JSON. Se não existir, cria com padrão."""
    try:
        if os.path.exists(ARQUIVO_LAZER):
            with open(ARQUIVO_LAZER, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass

    salvar_lazer(LAZER_PADRAO)
    return LAZER_PADRAO.copy()


def salvar_lazer(opcoes):
    os.makedirs(os.path.dirname(ARQUIVO_LAZER), exist_ok=True)
    with open(ARQUIVO_LAZER, "w", encoding="utf-8") as f:
        json.dump(opcoes, f, indent=2, ensure_ascii=False)


def adicionar_lazer(nome):
    if not nome or not nome.strip():
        return False
    opcoes = carregar_lazer()
    nome = nome.strip()
    if nome in opcoes:
        return False
    opcoes.append(nome)
    salvar_lazer(opcoes)
    return True


def remover_lazer(nome):
    opcoes = carregar_lazer()
    if nome in opcoes:
        opcoes.remove(nome)
        salvar_lazer(opcoes)
        return True
    return False