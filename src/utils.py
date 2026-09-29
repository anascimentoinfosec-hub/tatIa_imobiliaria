import re
import pandas as pd
import streamlit as st

def hash_senha(senha: str) -> str:
    import hashlib
    return hashlib.sha256(senha.encode()).hexdigest()

def converter_para_float(valor):
    """Converte QUALQUER formato de moeda BR para float."""
    if valor is None or pd.isna(valor):
        return 0.0
    if isinstance(valor, (int, float)):
        return float(valor)
    
    valor_str = str(valor).strip()
    valor_str = re.sub(r'R\$\s*', '', valor_str)
    valor_str = re.sub(r'RS\s*', '', valor_str)
    valor_str = re.sub(r'R\s*', '', valor_str)
    valor_str = valor_str.strip()
    
    if '.' in valor_str and ',' in valor_str:
        valor_str = valor_str.replace('.', '').replace(',', '.')
    elif ',' in valor_str:
        partes = valor_str.split(',')
        if len(partes) == 2 and len(partes[1]) <= 2:
            valor_str = valor_str.replace(',', '.')
        else:
            valor_str = valor_str.replace(',', '')
    
    valor_str = re.sub(r'[^0-9.]', '', valor_str)
    try:
        return float(valor_str)
    except:
        return 0.0

def formatar_valor_br(valor):
    """Formata um float no padrão BR: R$ 1.234,56"""
    if valor is None or pd.isna(valor):
        return "R$ 0,00"
    us = f"{valor:,.2f}"
    br = us.replace(',', 'X').replace('.', ',').replace('X', '.')
    return f"R$ {br}"
def _parse_brl(texto: str) -> float:
    """Converte '1.234,56' ou '1234.56' ou 'R$ 1.234,56' em float."""
    if not texto:
        return 0.0
    s = str(texto).strip()
    s = re.sub(r"R\$\s*", "", s)
    s = re.sub(r"RS\s*", "", s)
    s = s.strip()
    # Remove tudo que não é dígito, vírgula ou ponto
    s = re.sub(r"[^\d,.]", "", s)

    if not s:
        return 0.0

    # Tem vírgula? Formato BR
    if "," in s:
        s = s.replace(".", "").replace(",", ".")
    else:
        # Pode ser 1234.56 ou 1.234 (só separador de milhar)
        # Se tem ponto e a parte depois tem 3 dígitos, é milhar
        if "." in s:
            partes = s.split(".")
            if len(partes[-1]) == 3 and all(len(p) == 3 for p in partes[1:]):
                s = s.replace(".", "")

    try:
        return float(s)
    except ValueError:
        return 0.0


def _formatar_brl_input(valor) -> str:
    """Formata float como '1.234,56' (sem R$)."""
    try:
        v = float(valor or 0)
        return f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (ValueError, TypeError):
        return "0,00"


def _reformatar_campo_moeda(chave_texto):
    """Callback que reformata o valor quando o usuário sai do campo."""
    if chave_texto in st.session_state:
        valor = _parse_brl(st.session_state[chave_texto])
        st.session_state[chave_texto] = _formatar_brl_input(valor)


def campo_moeda(label, valor_inicial=0.0, key=None, help=None, placeholder="Ex: 450.000,00"):
    """
    Campo de entrada de moeda com separador de milhar BR.
    Reformata automaticamente quando o usuário sai do campo (on_change).
    Retorna o valor como float.
    """
    chave_texto = f"{key}_texto" if key else None

    # Se o campo ainda não existe, inicializa com valor formatado
    if chave_texto and chave_texto not in st.session_state:
        st.session_state[chave_texto] = _formatar_brl_input(valor_inicial)

    texto = st.text_input(
        label,
        key=chave_texto,
        help=help,
        placeholder=placeholder,
        on_change=_reformatar_campo_moeda,
        args=(chave_texto,),
    )

    return _parse_brl(texto)