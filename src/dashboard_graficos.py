import plotly.express as px
import pandas as pd


# Paleta de cores do projeto
CORES = {
    "primaria": "#1a73e8",
    "verde": "#28a745",
    "amarelo": "#ffc107",
    "vermelho": "#dc3545",
    "cinza": "#5f6368",
}


def grafico_tipologia(df):
    """🥧 Pizza: imóveis por tipologia."""
    if df.empty or "TIPOLOGIA" not in df.columns:
        return None

    contagem = df["TIPOLOGIA"].value_counts().reset_index()
    contagem.columns = ["Tipologia", "Quantidade"]

    fig = px.pie(
        contagem,
        names="Tipologia",
        values="Quantidade",
        title="🏠 Imóveis por Tipologia",
        hole=0.45,
    )
    fig.update_traces(textposition="inside", textinfo="percent+label")
    fig.update_layout(showlegend=True, height=400)
    return fig


def grafico_faixa_preco(df, preco_col):
    """📊 Barras: imóveis por faixa de preço."""
    if df.empty or preco_col not in df.columns:
        return None

    precos = df[preco_col].dropna()
    if precos.empty:
        return None

    # Cria faixas dinâmicas
    min_preco = precos.min()
    max_preco = precos.max()

    if max_preco <= 500_000:
        bins = [0, 300_000, 400_000, 500_000, 700_000, float("inf")]
        labels = ["Até R$ 300k", "R$ 300k-400k", "R$ 400k-500k", "R$ 500k-700k", "Acima R$ 700k"]
    elif max_preco <= 1_000_000:
        bins = [0, 400_000, 600_000, 800_000, 1_000_000, float("inf")]
        labels = ["Até R$ 400k", "R$ 400k-600k", "R$ 600k-800k", "R$ 800k-1M", "Acima R$ 1M"]
    else:
        bins = [0, 500_000, 1_000_000, 1_500_000, 2_000_000, float("inf")]
        labels = ["Até R$ 500k", "R$ 500k-1M", "R$ 1M-1.5M", "R$ 1.5M-2M", "Acima R$ 2M"]

    faixas = pd.cut(precos, bins=bins, labels=labels, include_lowest=True)
    contagem = faixas.value_counts().reindex(labels, fill_value=0).reset_index()
    contagem.columns = ["Faixa", "Quantidade"]

    fig = px.bar(
        contagem,
        x="Faixa",
        y="Quantidade",
        title="💰 Imóveis por Faixa de Preço",
        color="Quantidade",
        color_continuous_scale="Blues",
        text="Quantidade",
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(
        height=400,
        showlegend=False,
        coloraxis_showscale=False,
        xaxis_title="",
        yaxis_title="Quantidade",
    )
    return fig


def grafico_disponibilidade(df):
    """📈 Colunas: disponibilidade (livre/reservado/vendido)."""
    if df.empty:
        return None

    status_col = None
    for c in ["DISPONIBILIDADE", "STATUS", "SITUAÇÃO"]:
        if c in df.columns:
            status_col = c
            break

    if status_col is None:
        return None

    contagem = df[status_col].value_counts().reset_index()
    contagem.columns = ["Status", "Quantidade"]

    # Cores por status
    mapa_cores = {
        "LIVRE": CORES["verde"],
        "DISPONÍVEL": CORES["verde"],
        "RESERVADA": CORES["amarelo"],
        "RESERVADO": CORES["amarelo"],
        "VENDIDA": CORES["vermelho"],
        "VENDIDO": CORES["vermelho"],
    }

    fig = px.bar(
        contagem,
        x="Status",
        y="Quantidade",
        title="🔑 Disponibilidade dos Imóveis",
        text="Quantidade",
        color="Status",
        color_discrete_map=mapa_cores,
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(
        height=400,
        showlegend=False,
        xaxis_title="",
        yaxis_title="Quantidade",
    )
    return fig


def grafico_preco_por_produto(dados_por_produto):
    """
    💵 Barras horizontais: preço médio por produto.
    dados_por_produto: dict { "Produto A": preco_medio, "Produto B": preco_medio, ... }
    """
    if not dados_por_produto:
        return None

    df = pd.DataFrame(
        list(dados_por_produto.items()),
        columns=["Produto", "Preço Médio"],
    ).sort_values("Preço Médio", ascending=True)

    fig = px.bar(
        df,
        x="Preço Médio",
        y="Produto",
        orientation="h",
        title="💵 Preço Médio por Produto",
        text="Preço Médio",
        color="Preço Médio",
        color_continuous_scale="Greens",
    )
    fig.update_traces(
        texttemplate="R$ %{text:,.0f}",
        textposition="outside",
    )
    fig.update_layout(
        height=max(300, len(df) * 60),
        showlegend=False,
        coloraxis_showscale=False,
        xaxis_title="",
        yaxis_title="",
    )
    return fig