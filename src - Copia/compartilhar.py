import streamlit as st
import pandas as pd
from src.utils import formatar_valor_br
from src.pdf_export import gerar_pdf_simulacao


def gerar_resumo(nome_cliente, renda, entrada, bairro, top_imoveis,
                 nome_gerente=None, desconto=0, tipo_desconto="AVALIAÇÃO",
                 origem=None, fgts=0, subsidio=0,
                 financiamento_caixa=0, parcela_morando=0,
                 data_nascimento=None, documentacao_paga=False,
                 plano_entrada=None):
    """Gera um resumo formatado para compartilhamento."""
    linhas = []
    linhas.append("SIMULACAO IMOBILIARIA")
    linhas.append("=" * 40)
    linhas.append("")
    linhas.append(f"Cliente: {nome_cliente}")
    if data_nascimento:
        linhas.append(f"Data de nascimento: {data_nascimento}")
    if origem and origem != "(Nao informado)":
        linhas.append(f"Origem: {origem}")
    if bairro:
        linhas.append(f"Bairro: {bairro}")

    linhas.append("")
    linhas.append("--- DADOS FINANCEIROS ---")
    linhas.append(f"Renda bruta: {formatar_valor_br(renda)}")
    linhas.append(f"Entrada: {formatar_valor_br(entrada)}")
    if fgts and fgts > 0:
        linhas.append(f"FGTS: {formatar_valor_br(fgts)}")
    if subsidio and subsidio > 0:
        linhas.append(f"Subsidio: {formatar_valor_br(subsidio)}")
    if financiamento_caixa and financiamento_caixa > 0:
        linhas.append(f"Financiamento Caixa: {formatar_valor_br(financiamento_caixa)}")
    if parcela_morando and parcela_morando > 0:
        linhas.append(f"Parcela morando (financ. Caixa): {formatar_valor_br(parcela_morando)}")

    if desconto > 0:
        linhas.append(f"Desconto acordado: {formatar_valor_br(desconto)} (sobre {tipo_desconto})")

    if documentacao_paga:
        linhas.append("Documentacao: JA PAGA pelo cliente")

    linhas.append("")
    linhas.append("=" * 40)
    linhas.append("")

    if top_imoveis is not None and not top_imoveis.empty:
        linhas.append("OPORTUNIDADE ESCOLHIDA")
        linhas.append("")
        for i, (idx, row) in enumerate(top_imoveis.iterrows(), 1):
            unidade = row.get("UNIDADE", "N/A")
            tipologia = row.get("TIPOLOGIA", "")
            construtora = row.get("_construtora", "")
            produto = row.get("_produto", "")
            bloco = row.get("BLOCO", "")
            pavto = row.get("PAVTO", row.get("ANDAR", ""))
            avaliacao = row.get("AVALIAÇÃO", 0)
            preco = row.get("PREÇO", 0)
            valor_base = row.get("valor_base", 0)

            local_partes = []
            if bloco and str(bloco).lower() != "nan":
                local_partes.append(f"Bloco {bloco}")
            if pavto and str(pavto).lower() != "nan":
                local_partes.append(f"Andar {pavto}")
            local = f" ({' - '.join(local_partes)})" if local_partes else ""

            if construtora:
                linhas.append(f"Construtora: {construtora}")
            if produto:
                linhas.append(f"Produto: {produto}")
            linhas.append(f"Unidade: {unidade}{local}")
            if tipologia:
                linhas.append(f"Tipologia: {tipologia}")
            if avaliacao:
                linhas.append(f"Valor de Avaliacao: {formatar_valor_br(avaliacao)}")
            if preco:
                linhas.append(f"Valor de Preco (tabela): {formatar_valor_br(preco)}")
            if desconto > 0:
                linhas.append(f"Desconto: {formatar_valor_br(desconto)}")
            linhas.append(f"Valor Final: {formatar_valor_br(valor_base)}")
            linhas.append("")
    else:
        linhas.append("Nenhuma oportunidade encontrada.")

    # === PLANO DE ENTRADA ===
    if plano_entrada:
        linhas.append("=" * 40)
        linhas.append("")
        linhas.append("PLANO DE ENTRADA")
        linhas.append("")
        linhas.append(f"Ato minimo: {formatar_valor_br(plano_entrada.get('ato', 0))}")
        linhas.append(f"Comissao: {formatar_valor_br(plano_entrada.get('comissao_total', 0))}")
        if plano_entrada.get("teto_parcelamento"):
            linhas.append(
                f"Teto de parcelamento ({plano_entrada.get('teto_pct', 15)}%): "
                f"{formatar_valor_br(plano_entrada['teto_parcelamento'])}"
            )
        linhas.append(f"A parcelar: {formatar_valor_br(plano_entrada.get('a_parcelar', 0))}")
        linhas.append("")

        if plano_entrada.get("soma_inter_total", 0) > 0:
            linhas.append(f"Intermediarias: {formatar_valor_br(plano_entrada['soma_inter_total'])}")
            linhas.append(f"Restante nas parcelas: {formatar_valor_br(plano_entrada.get('restante_parcelas', 0))}")
            linhas.append("")

        if plano_entrada.get("num_pre", 0) > 0:
            linhas.append(f"Pre-chaves ({plano_entrada['num_pre']} parcelas):")
            for linha in _agrupar_parcelas_txt(plano_entrada, "pre"):
                linhas.append(f"  {linha}")

        if plano_entrada.get("num_pos", 0) > 0:
            linhas.append("")
            linhas.append(f"Pos-chaves ({plano_entrada['num_pos']} parcelas):")
            for linha in _agrupar_parcelas_txt(plano_entrada, "pos"):
                linhas.append(f"  {linha}")

        alertas = plano_entrada.get("alertas", [])
        if alertas:
            linhas.append("")
            linhas.append("ALERTAS:")
            for a in alertas:
                linhas.append(f"  {a}")

        linhas.append("")

    linhas.append("=" * 40)
    linhas.append("")
    linhas.append(f"Gerado em: {pd.Timestamp.now().strftime('%d/%m/%Y %H:%M')}")

    if nome_gerente:
        linhas.append(f"Responsavel: {nome_gerente}")
    else:
        linhas.append("App: simulador-credito.streamlit.app")

    return "\n".join(linhas)


def botoes_compartilhar(resumo, nome_cliente, dados_pdf=None):
    """Botões de compartilhamento (TXT, WhatsApp, PDF)."""
    col1, col2, col3 = st.columns(3)

    with col1:
        st.download_button(
            label="📄 Baixar TXT",
            data=resumo,
            file_name=f"simulacao_{nome_cliente.replace(' ', '_')}.txt",
            mime="text/plain",
            use_container_width=True,
        )

    with col2:
        mensagem = resumo.replace("\n", "%0A")
        link = f"https://wa.me/?text={mensagem}"
        st.markdown(
            f'<a href="{link}" target="_blank" style="display:block; background-color:#25D366; '
            f'color:white; text-align:center; padding:8px; border-radius:8px; '
            f'text-decoration:none; font-weight:600;">📱 Enviar WhatsApp</a>',
            unsafe_allow_html=True,
        )

    with col3:
        _renderizar_botao_pdf(nome_cliente, dados_pdf)


def _renderizar_botao_pdf(nome_cliente, dados_pdf):
    """Gera o PDF em memória e mostra o botão de download."""
    if dados_pdf is None:
        st.caption("📄 PDF indisponível")
        return

    try:
        nome_arquivo = f"simulacao_{nome_cliente.replace(' ', '_')}.pdf"
        gerar_pdf_simulacao(dados_pdf, nome_arquivo)

        with open(nome_arquivo, "rb") as f:
            pdf_bytes = f.read()

        st.download_button(
            label="📄 Baixar PDF",
            data=pdf_bytes,
            file_name=nome_arquivo,
            mime="application/pdf",
            use_container_width=True,
        )
    except Exception as e:
        st.caption(f"📄 Erro ao gerar PDF: {str(e)[:40]}")

def _agrupar_parcelas_txt(plano, fase):
    """Agrupa parcelas para o texto."""
    if fase == "pre":
        num = int(plano.get("num_pre", 0))
        valor_normal = float(plano.get("valor_pre", 0))
    else:
        num = int(plano.get("num_pos", 0))
        valor_normal = float(plano.get("valor_pos", 0))

    if num <= 0:
        return []

    mapa = {}
    for i in plano.get("intermediarias", []):
        if isinstance(i, dict) and i.get("fase") == fase:
            p = int(i.get("parcela", 0))
            if 1 <= p <= num:
                mapa[p] = mapa.get(p, 0) + float(i.get("valor", 0))

    resultado = []
    buffer_inicio = None
    buffer_fim = None

    for p in range(1, num + 1):
        if p in mapa:
            if buffer_inicio is not None:
                if buffer_inicio == buffer_fim:
                    resultado.append(f"Parcela {buffer_inicio}: {formatar_valor_br(valor_normal)}")
                else:
                    resultado.append(f"Parcelas {buffer_inicio}-{buffer_fim}: {formatar_valor_br(valor_normal)}")
                buffer_inicio = None
                buffer_fim = None

            total = valor_normal + mapa[p]
            resultado.append(
                f"Parcela {p}: {formatar_valor_br(valor_normal)} + "
                f"{formatar_valor_br(mapa[p])} = {formatar_valor_br(total)}"
            )
        else:
            if buffer_inicio is None:
                buffer_inicio = p
            buffer_fim = p

    if buffer_inicio is not None:
        if buffer_inicio == buffer_fim:
            resultado.append(f"Parcela {buffer_inicio}: {formatar_valor_br(valor_normal)}")
        else:
            resultado.append(f"Parcelas {buffer_inicio}-{buffer_fim}: {formatar_valor_br(valor_normal)}")

    return resultado