import re
import pandas as pd

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