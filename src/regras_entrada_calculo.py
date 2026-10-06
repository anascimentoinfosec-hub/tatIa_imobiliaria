import math


def calcular_plano_entrada(valor_entrada, renda_mensal, regra,
                            valor_final_imovel=0, num_pre=36, num_pos=24):
    """
    Parcela a ENTRADA respeitando as regras da construtora.

    Args:
        valor_entrada: valor que o cliente dará de entrada
        renda_mensal: renda bruta mensal
        regra: dict com regras
        valor_final_imovel: valor final do imóvel (para validar teto)
        num_pre, num_pos: número de parcelas
    """
    ato = float(regra.get("ato_minimo", 1000))
    comissao_pct = float(regra.get("comissao_pct", 4.2))
    comissao_fixa = float(regra.get("comissao_fixa", 1000))
    teto_pct = float(regra.get("teto_parcelamento_pct", 15.0))

    pre_pct = float(regra.get("pre_chaves", {}).get("parcela_max_pct_renda", 30))
    pos_pct = float(regra.get("pos_chaves", {}).get("parcela_max_pct_renda", 5))
    soma_max = int(regra.get("soma_max_parcelas", 60))

    # === TETO DE PARCELAMENTO ===
    teto_parcelamento = (valor_final_imovel * (teto_pct / 100)) if valor_final_imovel > 0 else None
    excede_teto = teto_parcelamento is not None and valor_entrada > teto_parcelamento

    # === CÁLCULO ===
    comissao_total = valor_entrada * (comissao_pct / 100) + comissao_fixa
    a_parcelar = max(0, valor_entrada - ato - comissao_total)

    parcela_pre_max = renda_mensal * (pre_pct / 100)
    parcela_pos_max = renda_mensal * (pos_pct / 100)

    num_pre = max(0, int(num_pre))
    num_pos = max(0, int(num_pos))
    total_parcelas = num_pre + num_pos

    valor_pre = a_parcelar / num_pre if num_pre > 0 else 0
    valor_pos = a_parcelar / num_pos if num_pos > 0 else 0

    # === ALERTAS ===
    alertas = []

    if excede_teto:
        valor_excedente = valor_entrada - teto_parcelamento
        alertas.append(
            f"🔴 Entrada (R$ {valor_entrada:,.2f}) excede o teto de parcelamento da construtora "
            f"({teto_pct}% = R$ {teto_parcelamento:,.2f}). "
            f"Cliente precisa dar R$ {valor_excedente:,.2f} à vista."
        )

    if total_parcelas > soma_max:
        alertas.append(
            f"🔴 Soma de parcelas ({total_parcelas}) ultrapassa o máximo ({soma_max})."
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

    if a_parcelar <= 0:
        alertas.append("🟢 Entrada coberta pelo Ato + Comissão. Nada a parcelar.")

    return {
        "valor_entrada": valor_entrada,
        "valor_final_imovel": valor_final_imovel,
        "renda_mensal": renda_mensal,
        "teto_parcelamento": teto_parcelamento,
        "teto_pct": teto_pct,
        "excede_teto": excede_teto,
        "ato": ato,
        "comissao_pct": comissao_pct,
        "comissao_fixa": comissao_fixa,
        "comissao_total": comissao_total,
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
        "viavel": not any("🔴" in a for a in alertas),
    }


def sugerir_parcelas(valor_entrada, renda_mensal, regra):
    """Sugere (num_pre, num_pos) que caibam nas regras."""
    ato = float(regra.get("ato_minimo", 1000))
    comissao_pct = float(regra.get("comissao_pct", 4.2))
    comissao_fixa = float(regra.get("comissao_fixa", 1000))
    soma_max = int(regra.get("soma_max_parcelas", 60))

    pre_pct = float(regra.get("pre_chaves", {}).get("parcela_max_pct_renda", 30))
    pos_pct = float(regra.get("pos_chaves", {}).get("parcela_max_pct_renda", 5))

    comissao_total = valor_entrada * (comissao_pct / 100) + comissao_fixa
    a_parcelar = max(0, valor_entrada - ato - comissao_total)

    if a_parcelar <= 0:
        return 0, 0

    parcela_pre_max = renda_mensal * (pre_pct / 100)
    parcela_pos_max = renda_mensal * (pos_pct / 100)

    for num_pre in range(soma_max, -1, -1):
        num_pos = soma_max - num_pre
        if num_pos == 0:
            continue
        valor_pre = a_parcelar / num_pre if num_pre > 0 else 0
        valor_pos = a_parcelar / num_pos if num_pos > 0 else 0
        if valor_pre <= parcela_pre_max and valor_pos <= parcela_pos_max:
            return num_pre, num_pos

    return 0, soma_max