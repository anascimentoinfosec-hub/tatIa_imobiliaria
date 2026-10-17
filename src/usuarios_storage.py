"""
Camada de leitura/gravação de usuários no Supabase.
Substitui o antigo usuarios.json.
"""
from src.db import listar, buscar_por, inserir, atualizar, deletar
from src.utils import hash_senha


def carregar_usuarios():
    """Retorna dict {login: {nome, email, hash, perfil, ativo, telefone, mfa_ativo, mfa_secret}}"""
    registros = listar("usuarios")
    usuarios = {}
    for r in registros:
        login = r.get("login")
        if not login:
            continue
        usuarios[login] = {
            "nome": r.get("nome", ""),
            "email": r.get("email", ""),
            "hash": r.get("hash", ""),
            "perfil": r.get("perfil", "corretor"),
            "ativo": r.get("ativo", True),
            "telefone": r.get("telefone", ""),
            "criado_em": r.get("criado_em", ""),
            "mfa_ativo": r.get("mfa_ativo", False),
            "mfa_secret": r.get("mfa_secret"),
        }
    return usuarios


def salvar_usuarios(usuarios_dict):
    """Sincroniza o dict inteiro com o Supabase."""
    atuais = carregar_usuarios()

    for login, dados in usuarios_dict.items():
        payload = {
            "login": login,
            "nome": dados.get("nome", ""),
            "email": dados.get("email", ""),
            "hash": dados.get("hash", ""),
            "perfil": dados.get("perfil", "corretor"),
            "ativo": bool(dados.get("ativo", True)),
            "telefone": dados.get("telefone", ""),
            "mfa_ativo": bool(dados.get("mfa_ativo", False)),
            "mfa_secret": dados.get("mfa_secret"),
        }

        if login in atuais:
            atualizar("usuarios", "login", login, payload)
        else:
            inserir("usuarios", payload)


def criar_usuario(login, nome, senha, perfil="corretor", email="", ativo=True, telefone=""):
    existente = buscar_por("usuarios", "login", login)
    if existente:
        return False, f"Usuário '{login}' já existe."

    inserir("usuarios", {
        "login": login,
        "nome": nome,
        "email": email,
        "hash": hash_senha(senha),
        "perfil": perfil,
        "ativo": bool(ativo),
        "telefone": telefone,
        "mfa_ativo": False,
        "mfa_secret": None,
    })
    return True, "OK"


def atualizar_usuario(login, dados):
    payload = {}
    for campo in ["nome", "email", "perfil", "ativo", "telefone", "mfa_ativo", "mfa_secret"]:
        if campo in dados:
            if campo in ["ativo", "mfa_ativo"]:
                payload[campo] = bool(dados[campo])
            else:
                payload[campo] = dados[campo]

    if dados.get("senha"):
        payload["hash"] = hash_senha(dados["senha"])

    if payload:
        atualizar("usuarios", "login", login, payload)


def excluir_usuario(login):
    return deletar("usuarios", "login", login)


def migrar_do_json(caminho_json="dados/usuarios.json"):
    import json
    import os

    if not os.path.exists(caminho_json):
        return 0, "Arquivo JSON não encontrado."

    try:
        with open(caminho_json, "r", encoding="utf-8") as f:
            usuarios_json = json.load(f)
    except Exception as e:
        return 0, f"Erro ao ler JSON: {str(e)}"

    count = 0
    for login, dados in usuarios_json.items():
        existente = buscar_por("usuarios", "login", login)
        if existente:
            continue
        inserir("usuarios", {
            "login": login,
            "nome": dados.get("nome", ""),
            "email": dados.get("email", ""),
            "hash": dados.get("hash", ""),
            "perfil": dados.get("perfil", "corretor"),
            "ativo": bool(dados.get("ativo", True)),
            "telefone": dados.get("telefone", ""),
        })
        count += 1

    return count, "OK"