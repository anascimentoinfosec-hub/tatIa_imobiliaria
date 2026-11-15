"""
Regras financeiras puras — sem Streamlit, sem UI.
Usadas por: simulador, comercial, financeiro, etc.
"""


def calcular_parcela_price(valor_financiado: float, taxa_anual: float, meses: int) -> float:
    """
    Calcula a parcela pela Tabela Price (parcela fixa).
    
    valor_financiado: valor presente (PV)
    taxa_anual: taxa de juros anual em decimal (ex: 0.10 = 10% a.a.)
    meses: prazo em meses (ex: 420)
    
    Fórmula: PV * i * (1+i)^n / ((1+i)^n - 1)
    """
    if valor_financiado <= 0 or meses <= 0:
        return 0.0
    if taxa_anual <= 0:
        return valor_financiado / meses

    i = taxa_anual / 12  # taxa mensal
    fator = (1 + i) ** meses
    parcela = valor_financiado * i * fator / (fator - 1)
    return round(parcela, 2)


def calcular_parcela_sac(valor_financiado: float, taxa_anual: float, meses: int) -> dict:
    """
    Calcula a primeira e a última parcela pela Tabela SAC (amortização constante).
    Retorna dict com primeira e última parcela.
    """
    if valor_financiado <= 0 or meses <= 0:
        return {"primeira": 0.0, "ultima": 0.0}

    i = taxa_anual / 12 if taxa_anual > 0 else 0
    amortizacao = valor_financiado / meses

    primeira = amortizacao + (valor_financiado * i)
    ultima = amortizacao + (amortizacao * i)

    return {
        "primeira": round(primeira, 2),
        "ultima": round(ultima, 2)
    }


def calcular_entrada_e_financiado(valor_base: float, percentual_entrada: float) -> dict:
    """
    Calcula entrada e valor financiado com base no percentual.
    percentual_entrada: ex: 20 (para 20%)
    """
    if valor_base <= 0:
        return {"entrada": 0.0, "financiado": 0.0}
    entrada = valor_base * (percentual_entrada / 100)
    financiado = valor_base - entrada
    return {
        "entrada": round(entrada, 2),
        "financiado": round(financiado, 2)
    }


def aplicar_desconto(valor_base: float, desconto: float) -> float:
    """Aplica desconto, garantindo que o valor final não seja negativo."""
    resultado = valor_base - desconto
    return max(0.0, round(resultado, 2))


def calcular_comprometimento_renda(parcela: float, renda_mensal: float) -> float:
    """
    Retorna o percentual da renda comprometida com a parcela.
    Ex: parcela 1.500 e renda 5.000 => 30.0
    """
    if renda_mensal <= 0:
        return 0.0
    return round((parcela / renda_mensal) * 100, 2)
def calcular_pv_maximo_price(parcela_maxima: float, taxa_anual: float, meses: int) -> float:
    """
    Inverso do Price: quanto consigo financiar dada uma parcela máxima?
    Fórmula: PV = PMT × ((1+i)^n − 1) / (i × (1+i)^n)
    """
    if parcela_maxima <= 0 or meses <= 0:
        return 0.0
    if taxa_anual <= 0:
        return parcela_maxima * meses
    i = taxa_anual / 12
    fator = (1 + i) ** meses
    return round(parcela_maxima * (fator - 1) / (i * fator), 2)


def calcular_pv_maximo_sac(parcela_maxima: float, taxa_anual: float, meses: int) -> float:
    """
    Inverso do SAC: usa a 1ª parcela como referência.
    Fórmula: PV = PMT / (1/n + i)
    """
    if parcela_maxima <= 0 or meses <= 0:
        return 0.0
    i = taxa_anual / 12 if taxa_anual > 0 else 0
    denominador = (1 / meses) + i
    return round(parcela_maxima / denominador, 2)


def calcular_valor_maximo_imovel(renda, entrada, comprometimento_pct,
                                   taxa_anual, meses, sistema):
    """
    Calcula o valor máximo de imóvel que o cliente consegue comprar.
    Retorna dict com diagnóstico.
    """
    parcela_maxima = renda * (comprometimento_pct / 100)

    if sistema.upper() == "SAC":
        pv_max = calcular_pv_maximo_sac(parcela_maxima, taxa_anual, meses)
    else:
        pv_max = calcular_pv_maximo_price(parcela_maxima, taxa_anual, meses)

    valor_max_imovel = pv_max + entrada

    return {
        "parcela_maxima": round(parcela_maxima, 2),
        "pv_maximo": round(pv_max, 2),
        "valor_max_imovel": round(valor_max_imovel, 2),
    }