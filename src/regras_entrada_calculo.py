def calcular_plano_entrada(valor_entrada, renda_mensal, regra,
                            valor_final_imovel=0, num_pre=36, num_pos=24,
                            intermediarias=None):
    """
    Parcela a ENTRADA respeitando regras. Intermediárias são listas:
    [{"fase": "pre"/"pos", "parcela": 2, "valor": 5000}, ...]
    """
    if intermediarias is None:
        intermediarias = []

    ato = float(regra.get("ato_minimo", 1000))
    comissao_pct = float(regra.get("comissao_pct", 4.2))
    comissao_fixa = float(regra.get("comissao_fixa", 1000))
    teto_pct = float(regra.get("teto_parcelamento_pct", 15.0))

    pre_pct = float(regra.get("pre_chaves", {}).get("parcela_max_pct_renda", 30))
    pre_inter_pct = float(regra.get("pre_chaves", {}).get("intermediaria_max_pct_renda", 80))
    pos_pct = float(regra.get("pos_chaves", {}).get("parcela_max_pct_renda", 5))
    pos_inter_pct = float(regra.get("pos_chaves", {}).get("intermediaria_max_pct_renda", 30))
    soma_max = int(regra.get("soma_max_parcelas", 60))

    # === TETO ===
    teto_parcelamento = (valor_final_imovel * (teto_pct / 100)) if valor_final_imovel > 0 else None
    excede_teto = teto_parcelamento is not None and valor_entrada > teto_parcelamento

    # === BASE ===
    comissao_total = valor_entrada * (comissao_pct / 100) + comissao_fixa
    a_parcelar_total = max(0, valor_entrada - ato - comissao_total)

    parcela_pre_max = renda_mensal * (pre_pct / 100)
    parcela_pos_max = renda_mensal * (pos_pct / 100)
    inter_pre_max = renda_mensal * (pre_inter_pct / 100)
    inter_pos_max = renda_mensal * (pos_inter_pct / 100)

    num_pre = max(0, int(num_pre))
    num_pos = max(0, int(num_pos))
    total_parcelas = num_pre + num_pos

    # === SOMA DAS INTERMEDIÁRIAS POR FASE ===
    soma_inter_pre = sum(i.get("valor", 0) for i in intermediarias if i.get("fase") == "pre")
    soma_inter_pos = sum(i.get("valor", 0) for i in intermediarias if i.get("fase") == "pos")
    soma_inter_total = soma_inter_pre + soma_inter_pos

    # === O QUE SOBRA PARA AS PARCELAS NORMAIS ===
    restante_parcelas = max(0, a_parcelar_total - soma_inter_total)

    # Proporcional entre pré/pós
    if total_parcelas > 0:
        prop_pre = num_pre / total_parcelas
    else:
        prop_pre = 0.5

    base_pre_normal = restante_parcelas * prop_pre
    base_pos_normal = restante_parcelas * (1 - prop_pre)

    valor_pre_normal = base_pre_normal / num_pre if num_pre > 0 else 0
    valor_pos_normal = base_pos_normal / num_pos if num_pos > 0 else 0

    # === ALERTAS ===
    alertas = []

    if excede_teto:
        valor_excedente = valor_entrada - teto_parcelamento
        alertas.append(
            f"🔴 Entrada (R$ {valor_entrada:,.2f}) excede o teto de parcelamento "
            f"({teto_pct}% = R$ {teto_parcelamento:,.2f}). "
            f"Cliente precisa dar R$ {valor_excedente:,.2f} à vista."
        )

    if total_parcelas > soma_max:
        alertas.append(f"🔴 Soma de parcelas ({total_parcelas}) ultrapassa o máximo ({soma_max}).")

    if soma_inter_total > a_parcelar_total:
        alertas.append(
            f"🔴 Soma das intermediárias (R$ {soma_inter_total:,.2f}) excede o valor a parcelar "
            f"(R$ {a_parcelar_total:,.2f})."
        )

    # Valida cada intermediária individualmente
    for idx_inter, i in enumerate(intermediarias, 1):
        valor_i = i.get("valor", 0)
        fase = i.get("fase", "pre")
        parcela_i = i.get("parcela", 0)

        if fase == "pre":
            if valor_i > inter_pre_max:
                alertas.append(
                    f"🔴 Intermediária #{idx_inter} pré (parcela {parcela_i}) de "
                    f"R$ {valor_i:,.2f} excede {pre_inter_pct}% da renda "
                    f"(R$ {inter_pre_max:,.2f})."
                )
            if parcela_i > num_pre:
                alertas.append(
                    f"🟡 Intermediária #{idx_inter} pré aponta pra parcela {parcela_i}, "
                    f"mas só há {num_pre} pré-chaves."
                )
        else:
            if valor_i > inter_pos_max:
                alertas.append(
                    f"🔴 Intermediária #{idx_inter} pós (parcela {parcela_i}) de "
                    f"R$ {valor_i:,.2f} excede {pos_inter_pct}% da renda "
                    f"(R$ {inter_pos_max:,.2f})."
                )
            if parcela_i > num_pos:
                alertas.append(
                    f"🟡 Intermediária #{idx_inter} pós aponta pra parcela {parcela_i}, "
                    f"mas só há {num_pos} pós-chaves."
                )

    if num_pre > 0 and valor_pre_normal > parcela_pre_max:
        alertas.append(
            f"🔴 Parcela pré (R$ {valor_pre_normal:,.2f}) excede "
            f"{pre_pct}% da renda (R$ {parcela_pre_max:,.2f})."
        )

    if num_pos > 0 and valor_pos_normal > parcela_pos_max:
        alertas.append(
            f"🔴 Parcela pós (R$ {valor_pos_normal:,.2f}) excede "
            f"{pos_pct}% da renda (R$ {parcela_pos_max:,.2f})."
        )

    if a_parcelar_total <= 0:
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
        "a_parcelar": a_parcelar_total,
        "soma_inter_pre": soma_inter_pre,
        "soma_inter_pos": soma_inter_pos,
        "soma_inter_total": soma_inter_total,
        "restante_parcelas": restante_parcelas,
        "inter_pre_max": inter_pre_max,
        "inter_pos_max": inter_pos_max,
        "pre_inter_pct": pre_inter_pct,
        "pos_inter_pct": pos_inter_pct,
        "num_pre": num_pre,
        "num_pos": num_pos,
        "valor_pre": valor_pre_normal,
        "valor_pos": valor_pos_normal,
        "total_parcelas": total_parcelas,
        "parcela_pre_max": parcela_pre_max,
        "parcela_pos_max": parcela_pos_max,
        "pre_pct": pre_pct,
        "pos_pct": pos_pct,
        "soma_max": soma_max,
        "intermediarias": intermediarias,
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