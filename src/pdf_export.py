from fpdf import FPDF
from datetime import datetime


class SimulacaoPDF(FPDF):
    def header(self):
        self.set_fill_color(26, 115, 232)
        self.rect(0, 0, 210, 25, "F")
        self.set_font("Helvetica", "B", 16)
        self.set_text_color(255, 255, 255)
        self.set_y(8)
        self.cell(0, 10, "SIMULACAO IMOBILIARIA", align="C")
        self.ln(20)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(120, 120, 120)
        self.cell(0, 10, f"Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')}", align="C")


def gerar_pdf_simulacao(dados, nome_arquivo="simulacao.pdf"):
    pdf = SimulacaoPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=20)

    # === DADOS DO CLIENTE ===
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(13, 43, 62)
    pdf.cell(0, 8, "Dados do Cliente", ln=True)
    pdf.ln(2)

    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(60, 60, 60)

    _linha_info(pdf, "Cliente", dados.get("nome_cliente", "-"))
    if dados.get("data_nascimento"):
        _linha_info(pdf, "Data de nascimento", dados["data_nascimento"])
    if dados.get("origem"):
        _linha_info(pdf, "Origem", dados["origem"])
    if dados.get("bairro"):
        _linha_info(pdf, "Bairro", dados["bairro"])
    _linha_info(pdf, "Renda bruta", _formatar_brl(dados.get("renda", 0)))
    _linha_info(pdf, "Entrada", _formatar_brl(dados.get("entrada", 0)))
    if dados.get("fgts", 0) > 0:
        _linha_info(pdf, "FGTS", _formatar_brl(dados["fgts"]))
    if dados.get("subsidio", 0) > 0:
        _linha_info(pdf, "Subsidio", _formatar_brl(dados["subsidio"]))
    if dados.get("financiamento_caixa", 0) > 0:
        _linha_info(pdf, "Financiamento Caixa", _formatar_brl(dados["financiamento_caixa"]))
    if dados.get("parcela_morando", 0) > 0:
        _linha_info(pdf, "Parcela morando", _formatar_brl(dados["parcela_morando"]))
    if dados.get("desconto", 0) > 0:
        _linha_info(
            pdf, "Desconto acordado",
            f"{_formatar_brl(dados['desconto'])} (sobre {dados.get('tipo_desconto', 'AVALIACAO')})",
        )
    if dados.get("documentacao_paga"):
        _linha_info(pdf, "Documentacao", "JA PAGA pelo cliente")
    if dados.get("nome_gerente"):
        _linha_info(pdf, "Responsavel", dados["nome_gerente"])

    pdf.ln(6)

    # === OPORTUNIDADE ESCOLHIDA ===
    oportunidades = dados.get("oportunidades", [])
    if oportunidades:
        pdf.set_font("Helvetica", "B", 13)
        pdf.set_text_color(13, 43, 62)
        pdf.cell(0, 8, "Oportunidade Escolhida", ln=True)
        pdf.ln(3)
        for i, op in enumerate(oportunidades, 1):
            _renderizar_oportunidade_pdf(pdf, i, op)

    # === PLANO DE ENTRADA ===
    plano = dados.get("plano_entrada")
    if plano:
        pdf.ln(4)
        pdf.set_font("Helvetica", "B", 13)
        pdf.set_text_color(13, 43, 62)
        pdf.cell(0, 8, "Plano de Entrada", ln=True)
        pdf.ln(2)

        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(60, 60, 60)

        _linha_info(pdf, "Ato minimo", _formatar_brl(plano.get("ato", 0)))
        _linha_info(pdf, "Comissao", _formatar_brl(plano.get("comissao_total", 0)))
        if plano.get("teto_parcelamento"):
            _linha_info(
                pdf,
                f"Teto ({plano.get('teto_pct', 15)}%)",
                _formatar_brl(plano["teto_parcelamento"]),
            )
        _linha_info(pdf, "A parcelar", _formatar_brl(plano.get("a_parcelar", 0)))

        pdf.ln(2)
        if plano.get("num_pre", 0) > 0:
            pdf.set_font("Helvetica", "B", 10)
            pdf.cell(0, 6, f"Pre-chaves: {plano['num_pre']}x de {_formatar_brl(plano.get('valor_pre', 0))}", ln=True)
        if plano.get("num_pos", 0) > 0:
            pdf.set_font("Helvetica", "B", 10)
            pdf.cell(0, 6, f"Pos-chaves: {plano['num_pos']}x de {_formatar_brl(plano.get('valor_pos', 0))}", ln=True)

        alertas = plano.get("alertas", [])
        if alertas:
            pdf.ln(2)
            pdf.set_font("Helvetica", "", 9)
            for a in alertas:
                pdf.multi_cell(0, 5, a)
                pdf.ln(1)

    pdf.output(nome_arquivo)
    return nome_arquivo


# =========================================================
def _linha_info(pdf, label, valor):
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(60, 7, f"{label}:", border=0)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(40, 40, 40)
    pdf.cell(0, 7, str(valor), border=0, ln=True)


def _renderizar_oportunidade_pdf(pdf, idx, op):
    unidade = str(op.get("UNIDADE", "N/A"))
    tipologia = str(op.get("TIPOLOGIA", ""))
    bloco = str(op.get("BLOCO", ""))
    pavto = str(op.get("PAVTO", op.get("ANDAR", "")))
    construtora = str(op.get("_construtora", ""))
    produto = str(op.get("_produto", ""))

    local_partes = []
    if bloco and bloco.lower() != "nan":
        local_partes.append(f"Bloco {bloco}")
    if pavto and pavto.lower() != "nan":
        local_partes.append(f"Andar {pavto}")
    local = f" ({' - '.join(local_partes)})" if local_partes else ""

    pdf.set_fill_color(232, 240, 254)
    pdf.set_text_color(13, 43, 62)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, f"  {idx}. Unidade {unidade}{local}", ln=True, fill=True)
    pdf.ln(2)

    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(60, 60, 60)

    if construtora:
        _linha_info(pdf, "Construtora", construtora)
    if produto:
        _linha_info(pdf, "Produto", produto)

    avaliacao = op.get("AVALIAÇÃO", 0) or op.get("AVALIACAO", 0)
    preco = op.get("PREÇO", 0) or op.get("PRECO", 0)
    valor_base = op.get("valor_base", 0)

    if avaliacao:
        _linha_info(pdf, "Avaliacao", _formatar_brl(avaliacao))
    if preco:
        _linha_info(pdf, "Preco (tabela)", _formatar_brl(preco))
    _linha_info(pdf, "Valor Final", _formatar_brl(valor_base))
    if tipologia:
        _linha_info(pdf, "Tipologia", tipologia)

    pdf.ln(3)


def _formatar_brl(valor):
    try:
        v = float(valor)
        formatado = f"{v:,.2f}"
        formatado = formatado.replace(",", "X").replace(".", ",").replace("X", ".")
        return f"R$ {formatado}"
    except (ValueError, TypeError):
        return "R$ 0,00"