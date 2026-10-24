import streamlit as st
import urllib.parse

from src.simulador_upload import carregar_todas_planilhas, renderizar_sidebar_resumo
from src.simulador_cliente import renderizar_area_cliente
from src.simulador_cards import (
    renderizar_cards, renderizar_ajuste_global, renderizar_seletor_proposta, renderizar_refinamento,
)
from src.compartilhar import botoes_compartilhar
from src.regras_entrada_storage import obter_regra_construtora
from src.regras_entrada_calculo import calcular_plano_entrada
from src.documentos_storage import criar_token_consentimento, verificar_consentimento, upload_documento

def pagina_simulador(CONSTRUTORAS, USUARIOS):
    if not CONSTRUTORAS:
        st.warning("⚠️ Nenhuma construtora cadastrada.")
        return

    st.title("🏢 Simulador de Entrada de Construtora")
    # Mostra mensagem de sucesso que sobrevive ao F5/Rerun
    if "msg_sucesso_proposta" in st.session_state:
        st.success(st.session_state["msg_sucesso_proposta"])
        del st.session_state["msg_sucesso_proposta"]
    st.caption("Analise o potencial do cliente em **todas as construtoras** disponíveis.")

    usuario_logado = st.session_state.get("usuario_logado")

    # 1. Planilhas
    df_total, resumo = carregar_todas_planilhas(CONSTRUTORAS)
    renderizar_sidebar_resumo(CONSTRUTORAS)

    if df_total is None or df_total.empty:
        st.warning("⚠️ Nenhuma planilha em cache. Peça ao gerente para subir planilhas.")
        return

    st.info(f"📦 {len(resumo)} produto(s) • {len(df_total)} unidades totais em cache")

    # 2. Cliente
    renderizar_area_cliente(df_total, usuario_logado, USUARIOS)

    # 3. Resultados
    if st.session_state.get("simulacao_ativa"):
        sim = st.session_state.simulacao_ativa

        st.markdown("---")
        top_refinado = renderizar_refinamento()
        sim["top_recomendacoes"] = top_refinado

        idx_escolhido = renderizar_seletor_proposta(top_refinado)
        st.session_state.unidade_escolhida_idx = idx_escolhido

        plano = None
        if idx_escolhido is not None and top_refinado is not None and not top_refinado.empty:
            top_para_pdf = top_refinado.loc[[idx_escolhido]]
            num_pre = st.session_state.get(f"plano_pre_{idx_escolhido}", 0)
            num_pos = st.session_state.get(f"plano_pos_{idx_escolhido}", 0)
            inter_list = st.session_state.get(f"inter_list_{idx_escolhido}", [])

            row = top_para_pdf.iloc[0]
            valor_base = float(row.get("valor_base", 0) or 0)
            construtora = str(row.get("_construtora", ""))
            renda = float(sim.get("renda", 0) or 0)
            entrada = float(sim.get("entrada", 0) or 0)

            regra = obter_regra_construtora(construtora)
            plano = calcular_plano_entrada(
                entrada, renda, regra,
                valor_final_imovel=valor_base,
                num_pre=int(num_pre), num_pos=int(num_pos),
                intermediarias=inter_list,
            )
        else:
            top_para_pdf = top_refinado

        # Compartilhar
        st.markdown("---")
        st.markdown("### 📤 Compartilhar Simulação")
        dados_pdf = _montar_dados_pdf(sim, usuario_logado, USUARIOS, top_para_pdf, plano)
        resumo_texto = _montar_resumo_texto(sim, usuario_logado, USUARIOS, top_para_pdf, plano)
        botoes_compartilhar(resumo_texto, sim["nome_cliente"], dados_pdf)

        # Cards
        st.markdown("---")
        renderizar_cards(
            top_refinado, sim["desconto_acordado"], sim["tipo_desconto"],
            sim["coluna_base"], sim["preco_col"], sim["nome_cliente"],
        )

        # =========================================================
        # ENVIAR PROPOSTA (COM LGPD E UPLOAD)
        # =========================================================
        if idx_escolhido is not None:
            st.markdown("---")
            st.info("💡 **Revise o plano de entrada** no card acima antes de enviar.")
            
            feedback = st.text_area("📝 Feedback para o Gerente", placeholder="Ex: Cliente tem FGTS alto e urgência na mudança.", key="feedback_proposta")
            
            st.markdown("### 📎 Documentos do Cliente (LGPD)")
            
            token_key = f"lgpd_token_{sim['nome_cliente']}"
            token_atual = st.session_state.get(token_key)
            status_lgpd = "pendente"
            
            if not token_atual:
                if st.button("🔗 Gerar Link de Consentimento LGPD"):
                    with st.spinner("Gerando link..."):
                        token_atual = criar_token_consentimento(sim["nome_cliente"])
                        st.session_state[token_key] = token_atual
                        st.rerun()
            else:
                status_lgpd = verificar_consentimento(token_atual)
                
                if status_lgpd == "pendente":
                    st.warning("⏳ Aguardando o cliente clicar no link de autorização.")
                    
                    try:
                        base_url = st.secrets.get("APP_BASE_URL", "http://localhost:8080")
                    except:
                        base_url = "http://localhost:8080"
                    link = f"{base_url}/?consentimento={token_atual}"
                    
                    st.code(link, language="text")
                    st.caption("Envie este link para o cliente via WhatsApp:")
                    
                    texto_wa = f"Olá {sim['nome_cliente']}, para darmos andamento na sua proposta, por favor autorize o uso dos seus documentos neste link: {link}"
                    link_wa = f"https://wa.me/?text={urllib.parse.quote(texto_wa)}"
                    st.markdown(f'<a href="{link_wa}" target="_blank" style="display:block; background-color:#25D366; color:white; text-align:center; padding:8px; border-radius:8px; text-decoration:none; font-weight:600;">📱 Enviar Link no WhatsApp</a>', unsafe_allow_html=True)
                    
                    if st.button("🔄 Verificar se o cliente autorizou"):
                        st.rerun()
                        
                elif status_lgpd == "autorizado":
                    st.success("✅ Cliente autorizou o uso dos documentos!")
            
            arquivos = None
            if status_lgpd == "autorizado":
                arquivos = st.file_uploader("Anexe RG, CPF e Comprovante de Renda", accept_multiple_files=True, type=["pdf", "png", "jpg", "jpeg"])
            
            if st.button("📤 Enviar Proposta ao Gerente", use_container_width=True, type="primary"):
                if status_lgpd != "autorizado":
                    st.error("⚠️ O cliente precisa autorizar o uso dos documentos (LGPD).")
                else:
                    with st.spinner("Enviando proposta..."):
                        try:
                            caminhos_docs = []
                            if arquivos:
                                for arq in arquivos:
                                    # Tenta fazer o upload
                                    path = upload_documento(arq, sim["nome_cliente"], tipo_doc=arq.name)
                                    if path:
                                        caminhos_docs.append(path)
                                        
                            num_pre = st.session_state.get(f"plano_pre_{idx_escolhido}", 0)
                            num_pos = st.session_state.get(f"plano_pos_{idx_escolhido}", 0)
                            
                            _salvar_proposta(
                                sim, top_refinado, idx_escolhido, usuario_logado, USUARIOS,
                                num_pre=num_pre, num_pos=num_pos, 
                                feedback_corretor=feedback,
                                documentos_paths=caminhos_docs,
                                lgpd_token=token_atual
                            )
                            
                            # Se deu tudo certo, salva a mensagem e limpa o token
                            st.session_state["msg_sucesso_proposta"] = "✅ Proposta enviada ao Gerente com sucesso!"
                            if token_key in st.session_state:
                                del st.session_state[token_key]
                            st.rerun()
                            
                        except Exception as e:
                            # Se o upload falhar, chama a tela de erro persistente
                            from src.utils import mostrar_erro_persistente
                            mostrar_erro_persistente(f"Erro ao enviar documentos ou salvar proposta: {str(e)}", chave="upload_proposta")

        st.markdown("---")
        renderizar_ajuste_global(df_total, "PREÇO")

    st.markdown("---")
    if st.button("💬 Perguntar à BIA (IA Imobiliária)", use_container_width=True):
        st.session_state.pagina = "ChatIA"
        st.rerun()


# =========================================================
# FUNÇÕES AUXILIARES E DE SALVAMENTO
# =========================================================
def _montar_dados_pdf(sim, usuario_logado, USUARIOS, top_filtrado, plano=None):
    oportunidades = []
    if top_filtrado is not None and not top_filtrado.empty:
        for _, row in top_filtrado.iterrows():
            item = {}
            for col in row.index:
                col_str = str(col)
                val = row[col]
                if hasattr(val, "item"): val = val.item()
                if isinstance(val, float) and (val != val): val = ""
                item[col_str] = val
            oportunidades.append(item)

    nome_gerente = USUARIOS[usuario_logado].get("nome", "") if usuario_logado in USUARIOS else ""
    return {
        "nome_cliente": sim.get("nome_cliente", ""), "data_nascimento": sim.get("data_nascimento", ""),
        "renda": sim.get("renda", 0), "entrada": sim.get("entrada", 0), "fgts": sim.get("fgts", 0),
        "subsidio": sim.get("subsidio", 0), "financiamento_caixa": sim.get("financiamento_caixa", 0),
        "parcela_morando": sim.get("parcela_morando", 0), "documentacao_paga": sim.get("documentacao_paga", False),
        "bairro": "", "origem": "", "desconto": sim.get("desconto_acordado", 0), "tipo_desconto": "MISTO",
        "nome_gerente": nome_gerente, "oportunidades": oportunidades, "plano_entrada": plano,
    }

def _montar_resumo_texto(sim, usuario_logado, USUARIOS, top_filtrado, plano=None):
    from src.compartilhar import gerar_resumo
    nome_gerente = USUARIOS[usuario_logado].get("nome", "") if usuario_logado in USUARIOS else ""
    return gerar_resumo(
        nome_cliente=sim.get("nome_cliente", ""), renda=sim.get("renda", 0), entrada=sim.get("entrada", 0),
        bairro="", top_imoveis=top_filtrado, nome_gerente=nome_gerente, desconto=sim.get("desconto_acordado", 0),
        tipo_desconto="MISTO", origem="", fgts=sim.get("fgts", 0), subsidio=sim.get("subsidio", 0),
        financiamento_caixa=sim.get("financiamento_caixa", 0), parcela_morando=sim.get("parcela_morando", 0),
        data_nascimento=sim.get("data_nascimento", ""), documentacao_paga=sim.get("documentacao_paga", False),
        plano_entrada=plano,
    )

def _salvar_proposta(sim, top, idx_escolhido, usuario_logado, USUARIOS,
                     num_pre=0, num_pos=0, feedback_corretor="", documentos_paths=None, lgpd_token=""):
    from src.simulacoes_storage import salvar_simulacao
    from src.unidades_status_storage import marcar_unidade

    if documentos_paths is None: documentos_paths = []

    top_unit = top.loc[[idx_escolhido]]
    nome_gerente = USUARIOS[usuario_logado]["nome"] if usuario_logado in USUARIOS else ""
    row = top_unit.iloc[0]
    
    valor_base = float(row.get("valor_base", 0) or 0)
    construtora = str(row.get("_construtora", ""))
    produto = str(row.get("_produto", ""))
    unidade = str(row.get("UNIDADE", ""))
    renda = float(sim.get("renda", 0) or 0)
    entrada = float(sim.get("entrada", 0) or 0)

    regra = obter_regra_construtora(construtora)
    inter_list = st.session_state.get(f"inter_list_{idx_escolhido}", [])
    plano = calcular_plano_entrada(
        entrada, renda, regra, valor_final_imovel=valor_base,
        num_pre=int(num_pre), num_pos=int(num_pos), intermediarias=inter_list,
    )

    top_unit = top_unit.copy()
    top_unit["num_pre"] = num_pre
    top_unit["num_pos"] = num_pos

    dados_extra = {
        "data_nascimento": sim.get("data_nascimento", ""), "fgts": sim.get("fgts", 0),
        "subsidio": sim.get("subsidio", 0), "parcela_morando": sim.get("parcela_morando", 0),
        "financiamento_caixa": sim.get("financiamento_caixa", 0), "documentacao_paga": sim.get("documentacao_paga", False),
        "plano_entrada": _serializar_plano(plano), "feedback_corretor": feedback_corretor,
        "documentos": documentos_paths, "lgpd_token": lgpd_token,
    }

    if "lead_para_simular" in st.session_state:
        dados_extra["lead_id"] = st.session_state["lead_para_simular"]["id"]

    sim_id = salvar_simulacao(
        nome_cliente=sim["nome_cliente"], renda=renda, entrada=entrada, bairro="", origem="",
        desconto=sim.get("desconto_acordado", 0), tipo_desconto="MISTO", gerente=nome_gerente,
        top_recomendacoes=top_unit, status_proposta="pendente", dados_extra=dados_extra,
    )

    marcar_unidade(
        construtora=construtora, produto=produto, unidade=unidade, status="em_processo",
        proposta_id=sim_id, cliente=sim.get("nome_cliente", ""), corretor=nome_gerente,
    )

    if "lead_para_simular" in st.session_state:
        from src.crm.leads_storage import atualizar_status_lead
        lead_id = st.session_state["lead_para_simular"]["id"]
        atualizar_status_lead(lead_id, "aprovacao")
        del st.session_state["lead_para_simular"]
        st.toast("🤝 Lead atualizado no CRM!")

def _serializar_plano(plano):
    if not isinstance(plano, dict): return {}
    resultado = {}
    for k, v in plano.items():
        if isinstance(v, (str, int, float, bool)) or v is None:
            resultado[k] = v
        elif isinstance(v, list):
            resultado[k] = [str(x) for x in v]
        else:
            resultado[k] = str(v)
    return resultado