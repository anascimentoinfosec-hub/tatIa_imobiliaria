from fpdf import FPDF
from datetime import datetime


class SimulacaoPDF(FPDF):
    """Classe base com header/footer personalizados."""

    def header(self):
        self.set_fill_color(26, 115, 232)  # azul #1a73e8
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
    """
    Gera um PDF com a simulação.

    dados = {
        "nome_cliente": str,
        "renda": float,
        "entrada": float,
        "bairro": str,
        "origem": str,
        "desconto": float,
        "tipo_desconto": str,
        "nome_gerente": str,
        "oportunidades": list[dict],  # cada dict com UNIDADE, TIPOLOGIA, AVALIACAO, PRECO, VALOR_BASE, etc.
    }
    """
    pdf = SimulacaoPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=20)

    # =========================================================
    # DADOS DO CLIENTE
    # =========================================================
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(13, 43, 62)
    pdf.cell(0, 8, "Dados do Cliente", ln=True)
    pdf.ln(2)

    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(60, 60, 60)

    _linha_info(pdf, "Cliente", dados.get("nome_cliente", "-"))
    if dados.get("origem"):
        _linha_info(pdf, "Origem", dados["origem"])
    if dados.get("bairro"):
        _linha_info(pdf, "Bairro de preferencia", dados["bairro"])
    _linha_info(pdf, "Renda mensal", _formatar_brl(dados.get("renda", 0)))
    _linha_info(pdf, "Entrada disponivel", _formatar_brl(dados.get("entrada", 0)))
    if dados.get("desconto", 0) > 0:
        _linha_info(
            pdf,
            "Desconto acordado",
            f"{_formatar_brl(dados['desconto'])} (sobre {dados.get('tipo_desconto', 'AVALIACAO')})",
        )
    if dados.get("nome_gerente"):
        _linha_info(pdf, "Gerente responsavel", dados["nome_gerente"])

    pdf.ln(8)

    # =========================================================
    # OPORTUNIDADES
    # =========================================================
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(13, 43, 62)
    pdf.cell(0, 8, "Oportunidades Recomendadas", ln=True)
    pdf.ln(3)

    oportunidades = dados.get("oportunidades", [])
    if not oportunidades:
        pdf.set_font("Helvetica", "I", 10)
        pdf.set_text_color(120, 120, 120)
        pdf.cell(0, 8, "Nenhuma oportunidade encontrada.", ln=True)
    else:
        for i, op in enumerate(oportunidades, 1):
            _renderizar_oportunidade_pdf(pdf, i, op)

    # =========================================================
    # RODAPÉ INFORMATIVO
    # =========================================================
    pdf.ln(5)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(140, 140, 140)
    pdf.multi_cell(
        0, 5,
        "Parcelas calculadas pela Tabela Price (taxa 10% a.a., prazo de 420 meses). "
        "Valores sujeitos a analise de credito e aprovacao."
    )

    pdf.output(nome_arquivo)
    return nome_arquivo


# =========================================================
# HELPERS
# =========================================================
def _linha_info(pdf, label, valor):
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(55, 7, f"{label}:", border=0)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(40, 40, 40)
    pdf.cell(0, 7, str(valor), border=0, ln=True)


def _renderizar_oportunidade_pdf(pdf, idx, op):
    """Renderiza um bloco de oportunidade."""
    unidade = str(op.get("UNIDADE", "N/A"))
    tipologia = str(op.get("TIPOLOGIA", ""))
    bloco = str(op.get("BLOCO", ""))
    pavto = str(op.get("PAVTO", op.get("ANDAR", "")))

    # Título da unidade
    local_partes = []
    if bloco:
        local_partes.append(f"Bloco {bloco}")
    if pavto:
        local_partes.append(f"Andar {pavto}")
    local = f" ({' - '.join(local_partes)})" if local_partes else ""

    pdf.set_fill_color(232, 240, 254)  # azul claro
    pdf.set_text_color(13, 43, 62)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, f"  {idx}. Unidade {unidade}{local}", ln=True, fill=True)
    pdf.ln(2)

    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(60, 60, 60)

    col_w = 95

    # Linha 1: Avaliação | Valor Base
    if op.get("AVALIAÇÃO", 0):
        _celula_dupla(pdf, "Avaliacao", _formatar_brl(op["AVALIAÇÃO"]),
                      "Valor Base", _formatar_brl(op.get("valor_base", 0)))
    else:
        _celula_dupla(pdf, "Preco", _formatar_brl(op.get("PREÇO", 0)),
                      "Valor Base", _formatar_brl(op.get("valor_base", 0)))

    # Linha 2: Tipologia | Parcela Estimada
    if tipologia or op.get("parcela_estimada"):
        _celula_dupla(pdf, "Tipologia", tipologia or "-",
                      "Parcela Estimada", _formatar_brl(op.get("parcela_estimada", 0)))

    pdf.ln(4)


def _celula_dupla(pdf, label1, valor1, label2, valor2):
    """Escreve duas colunas de label/valor lado a lado."""
    col_w = 95

    # Coluna 1
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(35, 7, f"{label1}:", border=0)

    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(40, 40, 40)
    pdf.cell(col_w - 35, 7, str(valor1), border=0)

    # Coluna 2
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(35, 7, f"{label2}:", border=0)

    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(40, 40, 40)
    pdf.cell(0, 7, str(valor2), border=0, ln=True)


def _formatar_brl(valor):
    """Formata float como R$ 1.234,56 (ASCII safe)."""
    try:
        v = float(valor)
        formatado = f"{v:,.2f}"
        formatado = formatado.replace(",", "X").replace(".", ",").replace("X", ".")
        return f"R$ {formatado}"
    except (ValueError, TypeError):
        return "R$ 0,00"