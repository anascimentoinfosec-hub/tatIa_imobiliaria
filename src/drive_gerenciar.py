import streamlit as st
from src.drive_sync import listar_planilhas_drive, baixar_e_ler_planilha, verificar_hash_arquivo, registrar_importacao

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
            with st.expander(f"📄 {arq['name']}"):
                st.caption(f"Última modificação: {arq.get('modifiedTime', 'Desconhecida')}")
                
                if st.button(f"Processar {arq['name']}", key=f"btn_{arq['id']}"):
                    # 1. Verifica Hash (antiduplicidade)
                    file_hash = arq.get("md5Checksum", "")
                    if file_hash and verificar_hash_arquivo(file_hash):
                        st.warning("⚠️ Esta planilha já foi importada anteriormente (arquivo idêntico).")
                    else:
                        with st.spinner("Lendo planilha..."):
                            try:
                                df = baixar_e_ler_planilha(arq['id'], arq['mimeType'])
                                st.success("✅ Planilha lida com sucesso!")
                                st.dataframe(df.head(5))
                                
                                # === AQUI ENTRA A BIA PORTEIRA ===
                                st.markdown("### 🧠 Verificação da BIA")
                                
                                # Exemplo simples de detecção (você pode melhorar com IA depois)
                                colunas = [c.upper() for c in df.columns]
                                tem_construtora = any("CONSTRUTORA" in c for c in colunas)
                                tem_produto = any("PRODUTO" in c for c in colunas) or any("EMPREENDIMENTO" in c for c in colunas)
                                
                                if tem_construtora and tem_produto:
                                    st.info("A BIA identificou colunas de Construtora e Produto. O que deseja fazer?")
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        if st.button("🔄 Atualizar Produto Existente"):
                                            # Lógica de atualizar
                                            registrar_importacao(file_hash, arq['name'], "atualizado")
                                            st.success("Produto atualizado no sistema!")
                                    with col2:
                                        if st.button("🆕 Criar Novo Produto"):
                                            # Lógica de criar novo
                                            registrar_importacao(file_hash, arq['name'], "novo")
                                            st.success("Novo produto criado no sistema!")
                                else:
                                    st.error("A BIA não conseguiu identificar as colunas necessárias (Construtora/Produto). Verifique o padrão da planilha.")
                                    
                            except Exception as e:
                                st.error(f"Erro ao ler arquivo: {e}")