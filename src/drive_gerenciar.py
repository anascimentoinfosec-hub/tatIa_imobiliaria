import streamlit as st
import pandas as pd
import io
from googleapiclient.http import MediaIoBaseDownload
from src.drive_sync import listar_planilhas_drive, baixar_planilha_bruta, verificar_hash_arquivo, registrar_importacao, get_drive_service

def renderizar_drive_sync():
    st.title("📂 Sincronização Google Drive")
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
                # Se o arquivo foi lido, mostra o preview e a interação
                if f"df_bruto_{arq['id']}" in st.session_state:
                    df_bruto = st.session_state[f"df_bruto_{arq['id']}"]
                    
                    st.markdown("#### 🧠 Verificação da BIA (Preview dos Dados)")
                    st.write("Veja como a planilha foi lida. Identifique a linha onde estão os **títulos das colunas**:")
                    
                    st.dataframe(df_bruto, use_container_width=True)
                    
                    linha_cabecalho = st.number_input(
                        "Em qual linha do Excel estão os títulos das colunas?", 
                        min_value=1, max_value=20, value=6, 
                        key=f"header_{arq['id']}"
                    )
                    
                    if st.button("✅ Confirmar Cabeçalho e Processar", key=f"proc_{arq['id']}"):
                        with st.spinner("Processando dados reais..."):
                            try:
                                # ... (código de download do arquivo igual ao anterior) ...
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
                                
                                df_final = pd.read_excel(fh, skiprows=linha_cabecalho - 1)
                                
                                # SALVA NA MEMÓRIA PARA NÃO ZERAR A TELA
                                st.session_state[f"df_final_{arq['id']}"] = df_final
                                st.rerun() # Recarrega a tela para mostrar a próxima etapa
                                
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
                            
                            key_const = f"const_{arq['id']}"
                            key_prod = f"prod_{arq['id']}"
                            key_cid = f"cid_{arq['id']}"

                            st.text_input("🏗️ Nome da Construtora:", key=key_const)
                            st.text_input("📦 Nome do Produto:", key=key_prod)
                            st.text_input("📍 Cidade (Opcional):", key=key_cid)
                            
                            if st.button("💾 Salvar e Criar Produto", key=f"salvar_{arq['id']}"):
                                nome_construtora = st.session_state.get(key_const, "")
                                nome_produto = st.session_state.get(key_prod, "")
                                cidade = st.session_state.get(key_cid, "")

                                if not nome_construtora or not nome_produto:
                                    st.warning("⚠️ Preencha o nome da Construtora e do Produto.")
                                else:
                                    with st.spinner("Salvando no banco..."):
                                        from src.db import get_client
                                        client = get_client()
                                        
                                        try:
                                            # Como o seu banco não tem coluna 'cidade' nessa tabela, 
                                            # vamos salvar apenas o que ele conhece.
                                            client.table("planilhas_cache").insert({
                                                "construtora": nome_construtora,
                                                "produto": nome_produto
                                            }).execute()
                                            
                                            # Registra o hash para não duplicar
                                            registrar_importacao(arq.get("md5Checksum", ""), arq['name'], "novo")
                                            
                                            st.success(f"✅ Produto '{nome_produto}' da construtora '{nome_construtora}' criado com sucesso!")
                                            st.balloons()
                                            
                                            # Limpa os campos após salvar
                                            del st.session_state[key_const]
                                            del st.session_state[key_prod]
                                            del st.session_state[key_cid]
                                            del st.session_state[f"df_final_{arq['id']}"]
                                            st.rerun()
                                        except Exception as e:
                                            st.error(f"Erro ao salvar no banco: {e}")