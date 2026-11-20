import streamlit as st
import pandas as pd
import io
import uuid
import json
from googleapiclient.http import MediaIoBaseDownload
from src.drive_sync import listar_planilhas_drive, baixar_planilha_bruta, verificar_hash_arquivo, registrar_importacao, get_drive_service

def renderizar_drive_sync():
    st.title("📂 Sincronização Google Drive")

    # === CONFIGURAÇÃO DA PASTA DO DRIVE ===
    from src.configuracoes_storage import obter_configuracao, salvar_configuracao
    
    with st.expander("⚙️ Configurar Pasta do Google Drive", expanded=False):
        st.caption("Cole o link da pasta do Google Drive onde estão as planilhas.")
        
        link_atual = obter_configuracao("drive_folder_link", "")
        novo_link = st.text_input("Link da Pasta do Drive:", value=link_atual, placeholder="https://drive.google.com/drive/folders/...")
        
        if st.button("💾 Salvar Pasta do Drive"):
            if "drive.google.com" in novo_link:
                # Extrai o ID da pasta do link (o código entre a última '/' e o '?')
                try:
                    if "/folders/" in novo_link:
                        folder_id = novo_link.split("/folders/")[1].split("?")[0]
                    else:
                        folder_id = novo_link # Se o cara colar só o ID
                        
                    salvar_configuracao("drive_folder_id", folder_id)
                    st.success(f"✅ Pasta configurada com sucesso! ID: {folder_id}")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Link inválido. Erro: {e}")
            else:
                st.error("❌ Por favor, cole um link válido do Google Drive.")

    st.markdown("---")
    
    # Exibe a mensagem de sucesso se ela existir na memória
    if "msg_sucesso_drive" in st.session_state:
        st.success(st.session_state["msg_sucesso_drive"])
        st.info("👉 **Próximo passo:** O produto já está disponível no Simulador e na Gestão de Construtoras.")
        del st.session_state["msg_sucesso_drive"]

    st.markdown("Monitore a pasta de planilhas das construtoras e importe os dados.")
    
    if st.button("🔄 Buscar Planilhas no Drive"):
        with st.spinner("Conectando ao Google Drive..."):
            try:
                arquivos = listar_planilhas_drive()
                st.session_state["arquivos_drive"] = arquivos
            except Exception as e:
                st.error(f"Erro ao acessar o Drive: {e}")
                
    if "arquivos_drive" in st.session_state:
        arquivos = st.session_state["arquivos_drive"]
        
        if not arquivos:
            st.info("Nenhuma planilha encontrada na pasta configurada.")
            return
            
        st.write(f"Encontramos **{len(arquivos)}** planilhas na pasta.")
        
        for arq in arquivos:
            with st.expander(f"📄 {arq['name']}", expanded=True):
                st.caption(f"Última modificação: {arq.get('modifiedTime', 'Desconhecida')}")
                
                if st.button(f"Ler {arq['name']}", key=f"btn_{arq['id']}"):
                    with st.spinner("Lendo as primeiras linhas..."):
                        try:
                            df_bruto = baixar_planilha_bruta(arq['id'], arq['mimeType'])
                            st.session_state[f"df_bruto_{arq['id']}"] = df_bruto
                        except Exception as e:
                            st.error(f"Erro ao ler arquivo: {e}")
                
                # Se o arquivo foi lido, mostra o preview e a interação
                if f"df_bruto_{arq['id']}" in st.session_state:
                    df_bruto = st.session_state[f"df_bruto_{arq['id']}"]
                    
                    st.markdown("#### 🧠 Verificação da BIA (Preview dos Dados)")
                    st.write("Veja como a planilha foi lida. Identifique a linha onde estão os **títulos das colunas**:")
                    
                    st.dataframe(df_bruto, use_container_width=True)
                    
                    linha_cabecalho = st.number_input(
                        "Em qual linha do Excel estão os títulos das colunas?", 
                        min_value=1, max_value=30, value=6, 
                        key=f"header_{arq['id']}"
                    )
                    
                    if st.button("✅ Confirmar Cabeçalho e Processar", key=f"proc_{arq['id']}"):
                        with st.spinner("Processando dados reais..."):
                            try:
                                service = get_drive_service()
                                if arq['mimeType'] == 'application/vnd.google-apps.spreadsheet':
                                    request = service.files().export_media(fileId=arq['id'], mimeType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                                else:
                                    request = service.files().get_media(fileId=arq['id'])
                                
                                fh = io.BytesIO()
                                downloader = MediaIoBaseDownload(fh, request)
                                done = False
                                while done is False:
                                    status, done = downloader.next_chunk()
                                fh.seek(0)
                                
                                # 1. Lê o arquivo cru (sem cabeçalho)
                                df_cru = pd.read_excel(fh, header=None)
                                
                                # 2. Usa o número EXATO que o gerente digitou na tela
                                idx_cabecalho = int(linha_cabecalho) 
                                
                                # 3. Pega os nomes das colunas daquela linha
                                nomes_colunas = df_cru.iloc[idx_cabecalho].tolist()
                                
                                # 4. Pega os dados que vêm DEPOIS da linha do cabeçalho
                                df_dados = df_cru.iloc[idx_cabecalho + 1:].copy()
                                
                                # 5. Limpa os nomes das colunas (remove 'nan' e duplicados)
                                nomes_limpos = []
                                contador = {}
                                for col in nomes_colunas:
                                    col_str = str(col).strip()
                                    if col_str.lower() == "nan" or col_str == "":
                                        continue
                                    
                                    if col_str in contador:
                                        contador[col_str] += 1
                                        nomes_limpos.append(f"{col_str}_{contador[col_str]}")
                                    else:
                                        contador[col_str] = 1
                                        nomes_limpos.append(col_str)
                                
                                # 6. Filtra o DataFrame para as colunas válidas
                                df_dados = df_dados.iloc[:, :len(nomes_limpos)]
                                df_dados.columns = nomes_limpos
                                
                                # 7. Remove linhas vazias e formata
                                df_final = df_dados.dropna(how='all').reset_index(drop=True)
                                
                                # 8. Salva na memória para a próxima etapa
                                st.session_state[f"df_final_{arq['id']}"] = df_final
                                st.rerun()
                                
                            except Exception as e:
                                st.error(f"Erro ao processar: {e}")

                    # === MOSTRA A ETAPA DA BIA SE A PLANILHA JÁ FOI PROCESSADA ===
                    if f"df_final_{arq['id']}" in st.session_state:
                        df_final = st.session_state[f"df_final_{arq['id']}"]
                        
                        st.success("✅ Planilha estruturada com sucesso!")
                        st.dataframe(df_final.head(5))
                        
                        st.markdown("### 🧠 Verificação da BIA")
                        
                        colunas = [str(c).upper() for c in df_final.columns]
                        tem_construtora = any("CONSTRUTORA" in c or "INCORPORAÇÃO" in c for c in colunas)
                        tem_produto = any("PRODUTO" in c or "EMPREENDIMENTO" in c or "TABELA" in c for c in colunas)
                        
                        if not (tem_construtora and tem_produto):
                            st.info("🤖 A BIA não encontrou a Construtora/Produto na planilha. Me ajude a identificar:")
                            
                            from src.construtoras_storage import carregar_construtoras
                            dados_banco = carregar_construtoras()
                            construtoras_existentes = list(dados_banco.keys())
                            
                            # A MÁGICA DA PREVENÇÃO DE DUPLICIDADE
                            opcoes_construtora = ["➕ Criar Nova Construtora"] + construtoras_existentes
                            
                            construtora_selecionada = st.selectbox(
                                "🏗️ Selecione a Construtora:", 
                                opcoes_construtora, 
                                key=f"sel_const_{arq['id']}"
                            )
                            
                            # Se ele escolher criar nova, mostra o campo de texto
                            if construtora_selecionada == "➕ Criar Nova Construtora":
                                nome_construtora = st.text_input("Digite o nome da Nova Construtora:", key=f"new_const_{arq['id']}")
                            else:
                                nome_construtora = construtora_selecionada
                                st.caption(f"✅ Usando construtora existente: **{nome_construtora}**")
                            
                            key_prod = f"prod_{arq['id']}"
                            key_cid = f"cid_{arq['id']}"

                            st.text_input("📦 Nome do Produto:", key=key_prod)
                            st.text_input("📍 Cidade (Opcional):", key=key_cid)
                            
                            if st.button("💾 Salvar e Criar Produto", key=f"salvar_{arq['id']}"):
                                nome_produto = st.session_state.get(key_prod, "")
                                cidade = st.session_state.get(key_cid, "")

                                if not nome_construtora or not nome_produto:
                                    st.warning("⚠️ Preencha o nome da Construtora e do Produto.")
                                else:
                                    with st.spinner("Salvando no banco e preparando o Simulador..."):
                                        from src.construtoras_storage import carregar_construtoras, salvar_construtoras
                                        from src.planilha_cache import salvar_planilha_cache
                                        
                                        try:
                                            # 1. SALVA NO CACHE
                                            df_limpo = df_final.replace({float('nan'): None})
                                            sucesso_cache = salvar_planilha_cache(nome_construtora, df_limpo, nome_produto)
                                            
                                            if not sucesso_cache:
                                                st.error("Erro ao salvar a planilha no cache do Simulador.")
                                                st.stop()

                                            # 2. SALVA NA GESTÃO DE CONSTRUTORAS
                                            dados_atuais = carregar_construtoras()
                                            
                                            if nome_construtora not in dados_atuais:
                                                dados_atuais[nome_construtora] = {
                                                    "tipo_desconto": "AVALIAÇÃO",
                                                    "produtos": {}
                                                }
                                            
                                            colunas_excel = [str(c) for c in df_final.columns]
                                            
                                            dados_atuais[nome_construtora]["produtos"][nome_produto] = {
                                                "cidade": cidade,
                                                "skiprows": linha_cabecalho,
                                                "mapeamento": {str(i): col for i, col in enumerate(colunas_excel)},
                                                "colunas_ordem": colunas_excel,
                                                "colunas_para_converter": []
                                            }
                                            
                                            salvar_construtoras(dados_atuais)
                                            
                                            registrar_importacao(arq.get("md5Checksum", ""), arq['name'], "novo")
                                            
                                            st.session_state["msg_sucesso_drive"] = f"✅ Produto '{nome_produto}' da '{nome_construtora}' sincronizado com sucesso!"
                                            
                                            del st.session_state[key_prod]
                                            del st.session_state[key_cid]
                                            del st.session_state[f"df_final_{arq['id']}"]
                                            del st.session_state[f"df_bruto_{arq['id']}"]
                                            if "arquivos_drive" in st.session_state:
                                                del st.session_state["arquivos_drive"]
                                                
                                            st.rerun()
                                            
                                        except Exception as e:
                                            st.error(f"Erro ao salvar no banco: {e}")
                        else:
                            st.info("✅ A BIA identificou as colunas! O que deseja fazer?")
                            col1, col2 = st.columns(2)
                            with col1:
                                if st.button("🔄 Atualizar Produto Existente", key=f"up_{arq['id']}"):
                                    registrar_importacao(arq.get("md5Checksum", ""), arq['name'], "atualizado")
                                    st.success("Produto atualizado no sistema!")
                            with col2:
                                if st.button("🆕 Criar Novo Produto", key=f"new_{arq['id']}"):
                                    registrar_importacao(arq.get("md5Checksum", ""), arq['name'], "novo")
                                    st.success("Novo produto criado no sistema!")
                        