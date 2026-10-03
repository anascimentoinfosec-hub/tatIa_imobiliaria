import math


def calcular_plano_entrada(valor_base, renda_mensal, entrada_disponivel, regra,
                            num_pre=36, num_pos=24):
    """
    Calcula o plano de entrada respeitando as regras da construtora.

    Args:
        valor_base: valor total do imóvel
        renda_mensal: renda bruta mensal do cliente
        entrada_disponivel: quanto o cliente tem pra dar de entrada
        regra: dict com as regras da construtora
        num_pre: número de parcelas pré-chaves
        num_pos: número de parcelas pós-chaves

    Returns:
        dict com o plano completo + validações
    """
    ato = float(regra.get("ato_minimo", 1000))
    comissao_pct = float(regra.get("comissao_pct", 4.2))
    comissao_fixa = float(regra.get("comissao_fixa", 1000))

    pre_pct = float(regra.get("pre_chaves", {}).get("parcela_max_pct_renda", 30))
    pre_inter_pct = float(regra.get("pre_chaves", {}).get("intermediaria_max_pct_renda", 80))
    pos_pct = float(regra.get("pos_chaves", {}).get("parcela_max_pct_renda", 5))
    pos_inter_pct = float(regra.get("pos_chaves", {}).get("intermediaria_max_pct_renda", 30))
    soma_max = int(regra.get("soma_max_parcelas", 60))

    comissao_total = valor_base * (comissao_pct / 100) + comissao_fixa

    entrada_efetiva = min(float(entrada_disponivel), valor_base)
    a_parcelar = max(0, valor_base - ato - comissao_total - entrada_efetiva)

    parcela_pre_max = renda_mensal * (pre_pct / 100)
    parcela_pos_max = renda_mensal * (pos_pct / 100)

    num_pre = max(0, int(num_pre))
    num_pos = max(0, int(num_pos))
    total_parcelas = num_pre + num_pos

    valor_pre = a_parcelar / num_pre if num_pre > 0 else 0
    valor_pos = a_parcelar / num_pos if num_pos > 0 else 0

    # =========================================================
    # VALIDAÇÕES
    # =========================================================
    alertas = []

    if total_parcelas > soma_max:
        alertas.append(
            f"🔴 Soma de parcelas ({total_parcelas}) ultrapassa o máximo permitido ({soma_max})."
        )

    if num_pre > 0 and valor_pre > parcela_pre_max:
        alertas.append(
            f"🔴 Parcela pré-chaves (R$ {valor_pre:,.2f}) excede "
            f"{pre_pct}% da renda (R$ {parcela_pre_max:,.2f})."
        )

    if num_pos > 0 and valor_pos > parcela_pos_max:
        alertas.append(
            f"🔴 Parcela pós-chaves (R$ {valor_pos:,.2f}) excede "
            f"{pos_pct}% da renda (R$ {parcela_pos_max:,.2f})."
        )

    if a_parcelar <= 0 and entrada_efetiva >= valor_base:
        alertas.append("🟢 Cliente pode comprar à vista (entrada cobre 100% do valor).")

    return {
        "valor_base": valor_base,
        "renda_mensal": renda_mensal,
        "ato": ato,
        "comissao_pct": comissao_pct,
        "comissao_fixa": comissao_fixa,
        "comissao_total": comissao_total,
        "entrada_efetiva": entrada_efetiva,
        "a_parcelar": a_parcelar,
        "num_pre": num_pre,
        "num_pos": num_pos,
        "valor_pre": valor_pre,
        "valor_pos": valor_pos,
        "total_parcelas": total_parcelas,
        "parcela_pre_max": parcela_pre_max,
        "parcela_pos_max": parcela_pos_max,
        "pre_pct": pre_pct,
        "pos_pct": pos_pct,
        "soma_max": soma_max,
        "alertas": alertas,
        "viavel": len(alertas) == 0 or (len(alertas) == 1 and "à vista" in alertas[0]),
    }


def sugerir_parcelas(valor_base, renda_mensal, entrada_disponivel, regra):
    """
    Retorna uma sugestão inteligente de (num_pre, num_pos)
    respeitando os limites de parcela.
    """
    ato = float(regra.get("ato_minimo", 1000))
    comissao_pct = float(regra.get("comissao_pct", 4.2))
    comissao_fixa = float(regra.get("comissao_fixa", 1000))
    soma_max = int(regra.get("soma_max_parcelas", 60))

    pre_pct = float(regra.get("pre_chaves", {}).get("parcela_max_pct_renda", 30))
    pos_pct = float(regra.get("pos_chaves", {}).get("parcela_max_pct_renda", 5))

    comissao_total = valor_base * (comissao_pct / 100) + comissao_fixa
    entrada_efetiva = min(float(entrada_disponivel), valor_base)
    a_parcelar = max(0, valor_base - ato - comissao_total - entrada_efetiva)

    if a_parcelar <= 0:
        return 0, 0

    parcela_pre_max = renda_mensal * (pre_pct / 100)
    parcela_pos_max = renda_mensal * (pos_pct / 100)

    # Estratégia: usar 50% pra pré (parcela maior) e 50% pra pós (parcela menor)
    # Testa combinações até achar a melhor
    for num_pre in range(soma_max, -1, -1):
        num_pos = soma_max - num_pre
        if num_pos == 0:
            continue
        valor_pre = a_parcelar / num_pre if num_pre > 0 else 0
        valor_pos = a_parcelar / num_pos if num_pos > 0 else 0

        if valor_pre <= parcela_pre_max and valor_pos <= parcela_pos_max:
            return num_pre, num_pos

    # Fallback: tudo em pós (parcela menor)
    num_pos = soma_max
    return 0, num_pos