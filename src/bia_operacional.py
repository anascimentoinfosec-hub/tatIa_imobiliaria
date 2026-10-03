import streamlit as st
import json
import os
from datetime import datetime
from openai import OpenAI
from src.bia_tools import buscar_web
from src.vendas_storage import carregar_vendas, carregar_status, calcular_metricas
from src.simulacoes_storage import carregar_simulacoes
from src.construtoras_storage import carregar_construtoras
from src.regras_storage import carregar_regras
from src.origens_storage import carregar_origens

MAX_HISTORICO = 10


def pagina_bia_operacional(usuario_logado=None, USUARIOS=None):
    st.title("💬 BIA — Assistente Operacional")
    st.markdown("---")
    st.caption(
        "Sou sua assistente **operacional**. Posso consultar dados do sistema "
        "(vendas, simulações, construtoras, regras) e buscar informações na web."
    )

    if "OPENAI_API_KEY" not in st.secrets:
        st.error("❌ Chave da OpenAI não configurada.")
        return

    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

    # === Contexto do sistema ===
    perfil = "corretor"
    nome_usuario = ""
    if usuario_logado and USUARIOS and usuario_logado in USUARIOS:
        perfil = USUARIOS[usuario_logado].get("perfil", "corretor")
        nome_usuario = USUARIOS[usuario_logado].get("nome", "")

    contexto = _montar_contexto_sistema(perfil, nome_usuario)

    # === Histórico ===
    if "hist_bia_op" not in st.session_state:
        st.session_state.hist_bia_op = [
            {"role": "assistant", "content": f"Olá, {nome_usuario or 'bem-vindo'}! 👋 Posso te ajudar com dados do sistema e informações da web. O que você quer saber?"}
        ]

    # Botão limpar
    col_a, col_b = st.columns([4, 1])
    with col_b:
        if st.button("🗑️ Limpar conversa", use_container_width=True, key="bia_op_limpar"):
            st.session_state.hist_bia_op = [
                {"role": "assistant", "content": "Conversa reiniciada. Como posso ajudar?"}
            ]
            st.rerun()

    # Botões rápidos (sugestões)
    st.markdown("**💡 Sugestões rápidas:**")
    cols = st.columns(4)
    sugestoes = [
        "Como estão minhas vendas este mês?",
        "Qual a taxa atual da Caixa?",
        "Quantas unidades temos em cache?",
        "Resumo do meu desempenho",
    ]
    for i, sug in enumerate(sugestoes):
        with cols[i]:
            if st.button(sug, key=f"bia_op_sug_{i}", use_container_width=True):
                _processar_pergunta(client, sug, contexto, perfil, nome_usuario)
                st.rerun()

    st.markdown("---")

    # === Histórico de mensagens ===
    for msg in st.session_state.hist_bia_op:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # === Input ===
    pergunta = st.chat_input("Digite sua pergunta...")

    if pergunta:
        st.session_state.hist_bia_op.append({"role": "user", "content": pergunta})
        with st.chat_message("user"):
            st.markdown(pergunta)

        with st.chat_message("assistant"):
            with st.spinner("Analisando..."):
                resposta = _gerar_resposta(client, st.session_state.hist_bia_op, contexto, perfil, nome_usuario)
                st.markdown(resposta)
                st.session_state.hist_bia_op.append({"role": "assistant", "content": resposta})


# =========================================================
# CONTEXTO DO SISTEMA
# =========================================================
def _montar_contexto_sistema(perfil, nome_usuario):
    """Monta um resumo do estado atual do sistema para enviar à IA."""
    partes = []

    # === Vendas ===
    vendas = carregar_vendas()
    if perfil == "corretor" and nome_usuario:
        vendas_usuario = [v for v in vendas if v.get("responsavel") == nome_usuario]
    else:
        vendas_usuario = vendas

    if vendas_usuario:
        vgv_total = sum(float(v.get("vgv", 0) or 0) for v in vendas_usuario)
        partes.append(f"### VENDAS ({'do corretor ' + nome_usuario if perfil == 'corretor' else 'todas'})")
        partes.append(f"- Total de vendas: {len(vendas_usuario)}")
        partes.append(f"- VGV total: R$ {vgv_total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

        # Por status
        status_list = carregar_status()
        status_map = {s["id"]: s["nome"] for s in status_list}
        por_status = {}
        for v in vendas_usuario:
            sid = v.get("status", "nao_iniciado")
            nome_status = status_map.get(sid, sid)
            por_status[nome_status] = por_status.get(nome_status, 0) + 1
        if por_status:
            partes.append("- Por status:")
            for nome_s, qtd in por_status.items():
                partes.append(f"  • {nome_s}: {qtd}")
    else:
        partes.append("### VENDAS: Nenhuma venda registrada no sistema.")

    # === Simulações ===
    simulacoes = carregar_simulacoes()
    if perfil == "corretor" and nome_usuario:
        sims_usuario = [s for s in simulacoes if s.get("gerente") == nome_usuario]
    else:
        sims_usuario = simulacoes

    partes.append(f"\n### SIMULAÇÕES ({'do corretor ' + nome_usuario if perfil == 'corretor' else 'todas'})")
    partes.append(f"- Total: {len(sims_usuario)}")
    if sims_usuario:
        clientes_unicos = len(set(s.get("cliente", "") for s in sims_usuario))
        partes.append(f"- Clientes únicos: {clientes_unicos}")
        # Últimas 3
        partes.append("- Últimas 3 simulações:")
        for s in sims_usuario[:3]:
            partes.append(f"  • {s.get('cliente', 'N/A')} ({s.get('data_hora', '')[:10]})")

    # === Construtoras / Produtos ===
    construtoras = carregar_construtoras()
    partes.append(f"\n### CONSTRUTORAS ({len(construtoras)})")
    for nome, dados in construtoras.items():
        produtos = list(dados.get("produtos", {}).keys())
        tipo_desc = dados.get("tipo_desconto", "AVALIAÇÃO")
        partes.append(f"- {nome} (desconto sobre {tipo_desc}): {len(produtos)} produto(s)")
        if produtos:
            partes.append(f"  Produtos: {', '.join(produtos[:5])}")

    # === Planilhas em cache ===
    pasta = "dados/planilhas"
    if os.path.exists(pasta):
        arquivos = [f for f in os.listdir(pasta) if f.endswith(".json")]
        partes.append(f"\n### PLANILHAS EM CACHE: {len(arquivos)}")

    # === Regras de financiamento ===
    regras = carregar_regras()
    partes.append(f"\n### REGRAS DE FINANCIAMENTO ({len(regras)})")
    for rid, dados in regras.items():
        nome_r = dados.get("nome", rid)
        taxa = dados.get("taxa_anual", 0) * 100
        prazo = dados.get("prazo_max_meses", 0)
        partes.append(f"- {nome_r}: {taxa:.2f}% a.a. / {prazo} meses")

    # === Origem do cliente ===
    origens = carregar_origens()
    partes.append(f"\n### ORIGENS DE CLIENTE ({len(origens)}): {', '.join(origens[:8])}")

    return "\n".join(partes)


# =========================================================
# PROCESSAMENTO
# =========================================================
def _gerar_resposta(client, historico, contexto, perfil, nome_usuario):
    """Gera resposta da BIA operacional."""
    try:
        ultima_pergunta = ""
        for msg in reversed(historico):
            if msg["role"] == "user":
                ultima_pergunta = msg["content"]
                break

        # Decide se precisa buscar na web
        contexto_externo = ""
        if _precisa_busca_web(client, ultima_pergunta):
            resultado_busca = buscar_web(ultima_pergunta)
            if resultado_busca and "❌" not in resultado_busca:
                contexto_externo = f"\n\n### INFORMAÇÕES DA WEB (use se for relevante):\n{resultado_busca}"

        system_prompt = f"""Você é a BIA, assistente operacional de uma imobiliária.

Você está conversando com: **{nome_usuario or 'Usuário'}** (perfil: {perfil})

=== DADOS ATUAIS DO SISTEMA ===
{contexto}
{contexto_externo}

=== REGRAS DE RESPOSTA ===
1. Use os dados do sistema para responder perguntas sobre vendas, simulações, construtoras, regras.
2. Se a pergunta for sobre informações externas (taxas de banco atualizadas, notícias, mercado), use os dados da web.
3. Se o perfil for "corretor", foque nos dados DELE (não revele dados de outros corretores).
4. Se o perfil for "gerente" ou "superadmin", você pode ver tudo.
5. Seja direta, profissional e use padrão brasileiro para valores (R$ 1.234,56).
6. Se não souber algo, diga claramente.
7. Mantenha o contexto da conversa (memória).
8. NUNCA invente números — use só o que está nos dados fornecidos.
"""

        mensagens = [{"role": "system", "content": system_prompt}]
        mensagens.extend(historico[-MAX_HISTORICO:])

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=mensagens,
            max_tokens=1000,
            temperature=0.7,
        )
        return response.choices[0].message.content

    except Exception as e:
        return f"❌ Erro na IA: {str(e)}"


def _processar_pergunta(client, pergunta, contexto, perfil, nome_usuario):
    """Processa uma sugestão rápida."""
    st.session_state.hist_bia_op.append({"role": "user", "content": pergunta})
    with st.spinner("Analisando..."):
        resposta = _gerar_resposta(client, st.session_state.hist_bia_op, contexto, perfil, nome_usuario)
        st.session_state.hist_bia_op.append({"role": "assistant", "content": resposta})


def _precisa_busca_web(client, pergunta):
    """Decide se precisa de busca externa."""
    if not pergunta.strip():
        return False

    try:
        prompt = f"""Pergunta do usuário: "{pergunta}"

Precisa buscar informação atualizada na web (taxas de banco HOJE, notícias recentes, mercado atual, Selic hoje, etc.)?

Responda APENAS com "SIM" ou "NAO".
"""
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=5,
            temperature=0,
        ).choices[0].message.content.strip().upper()

        return "SIM" in resp
    except Exception:
        return False