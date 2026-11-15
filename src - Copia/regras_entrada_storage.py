import json
import os
from src.db import supabase_disponivel

ARQUIVO_REGRAS_ENTRADA = "dados/regras_entrada.json"

PADRAO = {
    "comissao_pct": 4.2,
    "comissao_fixa": 1000.0,
    "ato_minimo": 1000.0,
    "teto_parcelamento_pct": 15.0,
    "pre_chaves": {
        "parcela_max_pct_renda": 30.0,
        "intermediaria_max_pct_renda": 80.0,
    },
    "pos_chaves": {
        "parcela_max_pct_renda": 5.0,
        "intermediaria_max_pct_renda": 30.0,
    },
    "soma_max_parcelas": 60,
    "ativo": True,
}


def carregar_regras_entrada():
    if supabase_disponivel():
        from src.regras_entrada_storage_supabase import carregar_regras_entrada_sb, migrar_regras_entrada_do_json
        dados = carregar_regras_entrada_sb()
        if not dados:
            count, _ = migrar_regras_entrada_do_json()
            if count > 0:
                dados = carregar_regras_entrada_sb()
        return dados

    try:
        if os.path.exists(ARQUIVO_REGRAS_ENTRADA):
            with open(ARQUIVO_REGRAS_ENTRADA, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def salvar_regras_entrada(dados):
    if supabase_disponivel():
        from src.regras_entrada_storage_supabase import salvar_regras_entrada_sb
        salvar_regras_entrada_sb(dados)
    else:
        os.makedirs(os.path.dirname(ARQUIVO_REGRAS_ENTRADA), exist_ok=True)
        with open(ARQUIVO_REGRAS_ENTRADA, "w", encoding="utf-8") as f:
            json.dump(dados, f, indent=2, ensure_ascii=False)


def salvar_regra_construtora(nome, dados):
    todas = carregar_regras_entrada()
    todas[nome] = dados
    salvar_regras_entrada(todas)


def excluir_regra_construtora(nome):
    todas = carregar_regras_entrada()
    if nome in todas:
        del todas[nome]
        salvar_regras_entrada(todas)
        return True
    return False


def obter_regra_construtora(nome):
    todas = carregar_regras_entrada()
    if nome in todas:
        return todas[nome]
    return {"nome": nome, **PADRAO}


def regras_ativas():
    return {k: v for k, v in carregar_regras_entrada().items() if v.get("ativo", True)}