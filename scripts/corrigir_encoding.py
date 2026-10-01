"""
Corrige strings com mojibake em arquivos JSON.
Rodar uma vez: py -3.14 scripts/corrigir_encoding.py
"""
import json
import glob


def _fix_mojibake(texto):
    if not isinstance(texto, str):
        return texto

    # Tenta cp1252 (Windows) primeiro, depois latin-1
    for enc in ("cp1252", "latin-1"):
        try:
            corrigido = texto.encode(enc).decode("utf-8")
            # Se ficou diferente, é porque havia mojibake
            if corrigido != texto:
                return corrigido
        except (UnicodeDecodeError, UnicodeEncodeError):
            continue

    return texto


def _corrigir_objeto(obj):
    if isinstance(obj, dict):
        return {_fix_mojibake(k): _corrigir_objeto(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_corrigir_objeto(i) for i in obj]
    return _fix_mojibake(obj)


def corrigir_arquivo(caminho):
    try:
        with open(caminho, "r", encoding="utf-8") as f:
            dados = json.load(f)
    except json.JSONDecodeError as e:
        print(f"⚠️ {caminho} — JSON inválido, ignorando: {e}")
        return
    except Exception as e:
        print(f"❌ Erro lendo {caminho}: {e}")
        return

    dados_corrigidos = _corrigir_objeto(dados)

    if dados_corrigidos == dados:
        print(f"✅ {caminho} — sem alterações")
        return

    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(dados_corrigidos, f, indent=2, ensure_ascii=False)

    print(f"🔧 {caminho} — CORRIGIDO")


if __name__ == "__main__":
    arquivos = glob.glob("dados/**/*.json", recursive=True)
    if not arquivos:
        print("Nenhum JSON encontrado em dados/")
    for arq in arquivos:
        corrigir_arquivo(arq)
    print("\n✅ Concluído.")