import streamlit as st
import pandas as pd
from src.drive_sync import listar_planilhas_drive, baixar_planilha_bruta, verificar_hash_arquivo, registrar_importacao

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
                if f"df_bruto_{arq['id']}" in st.session_state:
                    df_bruto = st.session_state[f"df_bruto_{arq['id']}"]
                    
                    st.markdown("#### 🧠 Verificação da BIA (Preview dos Dados)")
                    st.write("Veja como a planilha foi lida. Identifique a linha onde estão os **títulos das colunas** (ex: Bloco, Unidade, Preço):")
                    
                    # Mostra a tabela com os índices das linhas do Excel visíveis
                    st.dataframe(df_bruto, use_container_width=True)
                    
                    # Pergunta ao gerente qual é a linha do cabeçalho
                    linha_cabecalho = st.number_input(
                        "Em qual linha do Excel estão os títulos das colunas?", 
                        min_value=1, max_value=15, value=7, 
                        help="Na sua foto, os títulos (BLOCO, UNIDADE...) estão na linha 7 do Excel, que no Pandas é o índice 6.",
                        key=f"header_{arq['id']}"
                    )
                    
                    if st.button("✅ Confirmar Cabeçalho e Processar", key=f"proc_{arq['id']}"):
                        # Re-lê o arquivo, agora dizendo para o Pandas pular as linhas anteriores e usar a linha escolhida como cabeçalho
                        with st.spinner("Processando dados reais..."):
                            try:
                                # Aqui a gente baixa de novo, mas passando o 'skiprows'
                                from src.drive_sync import get_drive_service
                                import io
                                from googleapiclient.http import MediaIoBaseDownload
                                
                                service = get_drive_service()
                                request = service.files().get_media(fileId=arq['id']) if arq['mimeType'] != 'application/vnd.google-apps.spreadsheet' else service.files().export_media(fileId=arq['id'], mimeType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                                
                                fh = io.BytesIO()
                                downloader = MediaIoBaseDownload(fh, request)
                                done = False
                                while done is False:
                                    status, done = downloader.next_chunk()
                                fh.seek(0)
                                
                                # O PULO DO GATO: Pula até a linha do cabeçalho escolhida
                                df_final = pd.read_excel(fh, skiprows=linha_cabecalho - 1)
                                
                                st.success("✅ Planilha estruturada com sucesso!")
                                st.dataframe(df_final.head(10))
                                
                                # === A BIA PORTEIRA (Agora com as colunas certas) ===
                                colunas = [str(c).upper() for c in df_final.columns]
                                tem_construtora = any("CONSTRUTORA" in c or "INCORPORAÇÃO" in c for c in colunas)
                                tem_produto = any("PRODUTO" in c or "EMPREENDIMENTO" in c or "TABELA" in c for c in colunas)
                                
                                if tem_construtora and tem_produto:
                                    st.info("A BIA identificou as colunas. O que deseja fazer?")
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        if st.button("🔄 Atualizar Produto Existente", key=f"up_{arq['id']}"):
                                            registrar_importacao(arq.get("md5Checksum", ""), arq['name'], "atualizado")
                                            st.success("Produto atualizado no sistema!")
                                    with col2:
                                        if st.button("🆕 Criar Novo Produto", key=f"new_{arq['id']}"):
                                            registrar_importacao(arq.get("md5Checksum", ""), arq['name'], "novo")
                                            st.success("Novo produto criado no sistema!")
                                else:
                                    st.warning("A BIA não encontrou as colunas de Construtora/Produto. Você pode mapear manualmente depois.")
                                    
                            except Exception as e:
                                st.error(f"Erro ao processar: {e}")