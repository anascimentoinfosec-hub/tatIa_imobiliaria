import re
import pandas as pd

def hash_senha(senha: str) -> str:
    import hashlib
    return hashlib.sha256(senha.encode()).hexdigest()

def converter_para_float(valor):
    """
    Converte QUALQUER formato de moeda BR para float.
    Exemplos: R$ 440.000,00 | R$440.000,00 | 440.000,00 | 440000,00
    """
    if valor is None or pd.isna(valor):
        return 0.0
    if isinstance(valor, (int, float)):
        return float(valor)
    
    valor_str = str(valor).strip()
    
    # Remove R$, RS, R e espaços
    valor_str = re.sub(r'R\$\s*', '', valor_str)
    valor_str = re.sub(r'RS\s*', '', valor_str)
    valor_str = re.sub(r'R\s*', '', valor_str)
    valor_str = valor_str.strip()
    
    # Se tiver ponto e vírgula (formato BR: 1.234,56)
    if '.' in valor_str and ',' in valor_str:
        # Remove pontos de milhar e substitui vírgula por ponto
        valor_str = valor_str.replace('.', '').replace(',', '.')
    # Se tiver só vírgula (formato: 1234,56 ou 59,49)
    elif ',' in valor_str:
        partes = valor_str.split(',')
        # Se for decimal (2 dígitos depois da vírgula)
        if len(partes) == 2 and len(partes[1]) <= 2:
            valor_str = valor_str.replace(',', '.')
        else:
            # Senão, remove a vírgula (milhar)
            valor_str = valor_str.replace(',', '')
    
    # Remove qualquer caractere que não seja número ou ponto
    valor_str = re.sub(r'[^0-9.]', '', valor_str)
    
    try:
        return float(valor_str)
    except:
        return 0.0