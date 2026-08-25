import streamlit as st
import pandas as pd
import io
import pdfplumber
import re
import json
import os
import hashlib
from datetime import datetime
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import requests

# CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Simulador de Crédito", layout="wide")

# --- ARQUIVOS DE CONFIGURAÇÃO ---
ARQUIVO_CONFIG = "construtoras.json"
ARQUIVO_USUARIOS = "usuarios.json"

# --- FUNÇÕES DE HASH ---
def hash_senha(senha: str) -> str:
    return hashlib.sha256(senha.encode()).hexdigest()

def verificar_login(usuario: str, senha: str, usuarios: dict) -> bool:
    hash_digitado = hash_senha(senha)
    if usuario not in usuarios:
        return False
    return usuarios[usuario]["hash"] == hash_digitado and usuarios[usuario]["ativo"]

# --- FUNÇÕES DE USUÁRIOS ---
def carregar_usuarios():
    try:
        if os.path.exists(ARQUIVO_USUARIOS):
            with open(ARQUIVO_USUARIOS, 'r', encoding='utf-8') as f:
                return json.load(f)
    except:
        pass
    return {
        "gerente": {
            "nome": "Gerente Geral",
            "hash": hash_senha("gerente2026"),
            "perfil": "gerente",
            "ativo": True,
            "criado_em": datetime.now().isoformat()
        }
    }

def salvar_usuarios(usuarios):
    with open(ARQUIVO_USUARIOS, 'w', encoding='utf-8') as f:
        json.dump(usuarios, f, indent=2, ensure_ascii=False)

# --- FUNÇÕES DE CONSTRUTORAS ---
def carregar_construtoras():
    try:
        if os.path.exists(ARQUIVO_CONFIG):
            with open(ARQUIVO_CONFIG, 'r', encoding='utf-8') as f:
                return json.load(f)
    except:
        pass
    return {
        "Oásis II": {
            "skiprows": 2,
            "mapeamento": {
                "0": "UNIDADE", "1": "PAVTO", "2": "COLUNA", "3": "M²",
                "4": "TIPOLOGIA", "5": "VAGA", "6": "SOL",
                "8": "1ª AVALIAÇÃO OÁSIS II", "10": "DESCONTO", "12": "PREÇO", "13": "DISPONIBILIDADE"
            },
            "colunas_ordem": ["UNIDADE", "PAVTO", "COLUNA", "M²", "TIPOLOGIA", "VAGA", "SOL", "1ª AVALIAÇÃO OÁSIS II", "DESCONTO", "PREÇO", "DISPONIBILIDADE"],
            "colunas_para_converter": ["PREÇO", "1ª AVALIAÇÃO OÁSIS II", "DESCONTO", "M²", "PAVTO"]
        }
    }

def salvar_construtoras(construtoras):
    with open(ARQUIVO_CONFIG, 'w', encoding='utf-8') as f:
        json.dump(construtoras, f, indent=2, ensure_ascii=False)

# --- FUNÇÃO DE CONVERSÃO ---
def converter_para_float(valor):
    if valor is None or pd.isna(valor):
        return 0.0
    if isinstance(valor, (int, float)):
        return float(valor)
    
    valor_str = str(valor).strip()
    valor_str = re.sub(r'R\$\s*', '', valor_str)
    
    if '.' in valor_str and ',' in valor_str:
        valor_str = valor_str.replace('.', '').replace(',', '.')
    elif ',' in valor_str:
        partes = valor_str.split(',')
        if len(partes) == 2 and len(partes[1]) <= 2:
            valor_str = valor_str.replace(',', '.')
        else:
            valor_str = valor_str.replace(',', '')
    
    valor_str = re.sub(r'[^0-9.]', '', valor_str)
    
    try:
        return float(valor_str)
    except:
        return 0.0

# --- FUNÇÃO PARA LER PLANILHA ---
def ler_planilha(uploaded_file, config):
    try:
        if uploaded_file.name.endswith('.pdf'):
            with pdfplumber.open(io.BytesIO(uploaded_file.read())) as pdf:
                all_tables = []
                for page in pdf.pages:
                    tables = page.extract_tables()
                    for table in tables:
                        if table and len(table) > 1:
                            all_tables.append(table)
                if all_tables:
                    table_data = all_tables[0]
                    header_row = None
                    for i, row in enumerate(table_data):
                        if row:
                            row_text = ' '.join([str(cell).upper() for cell in row if cell])
                            if 'UNIDADE' in row_text:
                                header_row = i
                                break
                    if header_row is not None:
                        columns = [str(col).strip() if col else f'col_{i}' for i, col in enumerate(table_data[header_row])]
                        df = pd.DataFrame(table_data[header_row + 1:], columns=columns)
                        df = df.dropna(how='all')
                        df = df[~df.iloc[:, 0].astype(str).str.strip().eq('')]
                        return df
                    else:
                        return None
                else:
                    return None
        elif uploaded_file.name.endswith('.csv'):
            return pd.read_csv(uploaded_file)
        else:
            df_raw = pd.read_excel(uploaded_file, header=None)
            
            linha_cabecalho = None
            for i, row in df_raw.iterrows():
                row_text = ' '.join([str(cell).upper() for cell in row if pd.notna(cell)])
                if 'UNIDADE' in row_text:
                    linha_cabecalho = i
                    break
            
            if linha_cabecalho is None:
                return None
            
            dados = df_raw.iloc[linha_cabecalho + 1:].reset_index(drop=True)
            
            mapeamento = config.get("mapeamento", {})
            df = pd.DataFrame()
            for idx_str, nome_novo in mapeamento.items():
                idx = int(idx_str)
                if idx < len(dados.columns):
                    df[nome_novo] = dados.iloc[:, idx]
            
            df = df.dropna(how='all')
            if 'UNIDADE' in df.columns:
                df = df[df['UNIDADE'].notna() & (df['UNIDADE'].astype(str).str.strip() != '')]
            
            return df
    except:
        return None

# --- AUTENTICAÇÃO GOOGLE OAUTH 2.0 ---
def autenticar_google_drive_oauth():
    """Autentica com OAuth 2.0 usando a conta do gerente"""
    
    # Se já tem token na sessão, usa
    if "google_token" in st.session_state:
        try:
            creds = Credentials(token=st.session_state.google_token)
            return build('drive', 'v3', credentials=creds)
        except:
            st.session_state.google_token = None
    
    # Verifica se tem as credenciais nos secrets
    if not all(k in st.secrets for k in ["GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET"]):
        st.warning("⚠️ Configure as credenciais OAuth nos Secrets do Streamlit")
        return None
    
    # Configura o fluxo OAuth
    client_config = {
        "web": {
            "client_id": st.secrets["GOOGLE_CLIENT_ID"],
            "client_secret": st.secrets["GOOGLE_CLIENT_SECRET"],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [st.secrets.get("GOOGLE_REDIRECT_URI", "https://simulador-credito.streamlit.app/_stcore/oauth2-redirect")]
        }
    }
    
    flow = Flow.from_client_config(
        client_config,
        scopes=['https://www.googleapis.com/auth/drive.readonly', 
                'https://www.googleapis.com/auth/drive.file']
    )
    
    # Verifica se tem código de autorização na URL
    query_params = st.query_params
    
    if 'code' not in query_params:
        # Gera URL de autorização
        auth_url, state = flow.authorization_url(prompt='consent')
        st.session_state['oauth_state'] = state
        
        # Exibe botão para autorizar
        st.info("### 🔑 Autorize o acesso ao Google Drive")
        st.markdown("""
        O app precisa acessar suas planilhas no Google Drive.
        Clique no botão abaixo para autorizar:
        """)
        
        # Botão estilizado
        st.markdown(f"""
        <div style="display: flex; justify-content: center; margin: 20px 0;">
            <a href="{auth_url}" target="_blank" style="
                background-color: #4285F4;
                color: white;
                padding: 14px 28px;
                text-decoration: none;
                border-radius: 8px;
                font-weight: bold;
                font-size: 18px;
                display: inline-block;
                box-shadow: 0 2px 5px rgba(0,0,0,0.2);
            ">
                🔐 Autorizar Google Drive
            </a>
        </div>
        """, unsafe_allow_html=True)
        
        st.caption("Você será redirecionado para fazer login na sua conta Google e autorizar o acesso.")
        return None
    
    # Troca o código por token
    try:
        flow.fetch_token(code=query_params['code'])
        creds = flow.credentials
        
        # Salva o token na sessão
        st.session_state.google_token = creds.token
        
        # Limpa o código da URL
        st.query_params.clear()
        
        st.success("✅ Autenticado com sucesso!")
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ Erro na autenticação: {str(e)}")
        return None

# --- FUNÇÃO PARA BUSCAR PLANILHA DO DRIVE ---
def buscar_planilha_drive(service, nome_arquivo=None):
    """Busca a planilha mais recente no Drive do gerente"""
    try:
        if nome_arquivo:
            # Busca por nome específico
            query = f"name='{nome_arquivo}' and mimeType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' and trashed=false"
        else:
            # Busca a mais recente
            query = "mimeType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' and trashed=false"
        
        results = service.files().list(
            q=query,
            orderBy="modifiedTime desc",
            pageSize=5
        ).execute()
        
        files = results.get('files', [])
        return files
    
    except Exception as e:
        st.error(f"❌ Erro ao buscar arquivos: {str(e)}")
        return []

# --- FUNÇÃO PARA BAIXAR PLANILHA DO DRIVE ---
def baixar_planilha_drive(service, file_id):
    """Baixa uma planilha do Drive"""
    try:
        request = service.files().get_media(fileId=file_id)
        file_data = request.execute()
        return io.BytesIO(file_data)
    except Exception as e:
        st.error(f"❌ Erro ao baixar arquivo: {str(e)}")
        return None

# --- FUNÇÃO PARA EXIBIR O SIMULADOR ---
def pagina_simulador(CONSTRUTORAS, USUARIOS, perfil_atual):
    st.title("📊 Simulador de Crédito")
    
    with st.sidebar:
        st.header("⚙️ Configurações")
        
        # Para o gerente: opção de usar o Drive
        if perfil_atual == "gerente":
            usar_drive = st.checkbox("☁️ Buscar planilha do Google Drive")
            if usar_drive:
                st.markdown("---")
                st.markdown("### 📁 Google Drive")
                
                drive_service = autenticar_google_drive_oauth()
                
                if drive_service:
                    # Busca os arquivos
                    arquivos = buscar_planilha_drive(drive_service)
                    
                    if arquivos:
                        # Seleciona um arquivo
                        opcoes = {f"{f['name']} ({f['modifiedTime']})": f['id'] for f in arquivos}
                        arquivo_selecionado = st.selectbox(
                            "Selecione a planilha:",
                            options=list(opcoes.keys())
                        )
                        
                        if st.button("📥 Carregar do Drive", use_container_width=True):
                            file_id = opcoes[arquivo_selecionado]
                            file_data = baixar_planilha_drive(drive_service, file_id)
                            if file_data:
                                st.session_state['drive_file_data'] = file_data
                                st.session_state['drive_file_name'] = arquivo_selecionado
                                st.success(f"✅ Planilha carregada: {arquivo_selecionado}")
                                st.rerun()
                        
                        if 'drive_file_data' in st.session_state:
                            st.info(f"📄 Planilha atual: {st.session_state.get('drive_file_name', '')}")
                    else:
                        st.warning("⚠️ Nenhuma planilha encontrada no Drive")
                else:
                    st.info("🔑 Autorize o acesso ao Drive para carregar planilhas")
                
                st.markdown("---")
        
        # Upload tradicional
        if not perfil_atual == "gerente" or not usar_drive:
            construtora_selecionada = st.selectbox(
                "🏗️ Selecione a construtora",
                options=list(CONSTRUTORAS.keys())
            )
            
            st.markdown("---")
            
            uploaded_file = st.file_uploader(
                "📤 Envie a planilha",
                type=['xlsx', 'xls', 'csv', 'pdf']
            )
        else:
            # Se está usando Drive, usa a construtora selecionada abaixo
            construtora_selecionada = st.selectbox(
                "🏗️ Selecione a construtora",
                options=list(CONSTRUTORAS.keys())
            )
            uploaded_file = None
            
            if 'drive_file_data' in st.session_state:
                # Cria um objeto parecido com uploaded_file
                class DriveFile:
                    def _init_(self, data, name):
                        self._data = data
                        self.name = name
                    def read(self):
                        return self._data.getvalue() if hasattr(self._data, 'getvalue') else self._data
                
                uploaded_file = DriveFile(
                    st.session_state['drive_file_data'],
                    st.session_state.get('drive_file_name', 'planilha_drive.xlsx')
                )
        
        st.markdown("---")
        st.caption("Versão 2.0")
    
    # --- PROCESSAMENTO DA PLANILHA ---
    if uploaded_file is not None:
        try:
            config = CONSTRUTORAS[construtora_selecionada]
            df = ler_planilha(uploaded_file, config)
            
            if df is None:
                st.error("❌ Não foi possível ler a planilha. Verifique o formato e o mapeamento.")
                st.stop()
            
            for col in config.get("colunas_para_converter", []):
                if col in df.columns:
                    df[col] = df[col].apply(converter_para_float)
            
            st.markdown("---")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                colunas_tipo = ['TIPOLOGIA', 'QUARTOS', 'DORMITÓRIOS', 'TIPO']
                tipo_col = None
                for c in colunas_tipo:
                    if c in df.columns:
                        tipo_col = c
                        break
                
                if tipo_col:
                    tipos = ['Todas'] + sorted(df[tipo_col].dropna().unique().tolist())
                    tipo_selecionado = st.selectbox("🏠 Tipo", tipos)
                else:
                    tipo_selecionado = 'Todas'
            
            with col2:
                colunas_andar = ['PAVTO', 'ANDAR']
                andar_col = None
                for c in colunas_andar:
                    if c in df.columns:
                        andar_col = c
                        break
                
                if andar_col:
                    andar_min = st.number_input("📌 Andar mínimo", min_value=0, value=0, step=1)
                else:
                    andar_min = 0
            
            with col3:
                colunas_preco = ['PREÇO', 'VALOR']
                preco_col = None
                for c in colunas_preco:
                    if c in df.columns:
                        preco_col = c
                        break
                
                if preco_col and not df[preco_col].isna().all():
                    preco_max = st.number_input(
                        "💰 Preço máximo (R$)",
                        min_value=0,
                        value=int(df[preco_col].max()) if df[preco_col].max() > 0 else 1000000,
                        step=50000,
                        format="%d"
                    )
                else:
                    preco_max = 1000000
            
            with col4:
                colunas_status = ['DISPONIBILIDADE', 'STATUS', 'SITUAÇÃO']
                status_col = None
                for c in colunas_status:
                    if c in df.columns:
                        status_col = c
                        break
                
                if status_col:
                    status_opcoes = ['Todas'] + sorted(df[status_col].dropna().unique().tolist())
                    status_selecionado = st.selectbox("🔑 Disponibilidade", status_opcoes)
                else:
                    status_selecionado = 'Todas'
            
            resultado = df.copy()
            
            if tipo_selecionado != 'Todas' and tipo_col:
                resultado = resultado[resultado[tipo_col] == tipo_selecionado]
            
            if andar_min > 0 and andar_col:
                resultado = resultado[resultado[andar_col] >= andar_min]
            
            if preco_col and preco_col in df.columns:
                resultado = resultado[resultado[preco_col] <= preco_max]
            
            if status_selecionado != 'Todas' and status_col:
                resultado = resultado[resultado[status_col] == status_selecionado]
            
            if not resultado.empty:
                colunas_area = ['M²', 'AREA_M2', 'AREA']
                area_col = None
                for c in colunas_area:
                    if c in resultado.columns:
                        area_col = c
                        break
                
                if preco_col and area_col:
                    resultado['R$/m²'] = (resultado[preco_col] / resultado[area_col]).round(2)
            
            colunas_ordem = config.get("colunas_ordem", list(df.columns)).copy()
            if 'R$/m²' in resultado.columns:
                colunas_ordem.append('R$/m²')
            
            colunas_ordem = [c for c in colunas_ordem if c in resultado.columns]
            
            st.subheader(f"🔍 Resultados: {len(resultado)} imóveis encontrados - {construtora_selecionada}")
            
            if not resultado.empty:
                if 'R$/m²' in resultado.columns:
                    resultado_ordenado = resultado.sort_values('R$/m²')
                else:
                    resultado_ordenado = resultado
                
                st.dataframe(
                    resultado_ordenado[colunas_ordem],
                    use_container_width=True,
                    height=400
                )
                
                st.markdown("---")
                st.subheader("🤖 Recomendação da IA")
                
                melhor = resultado_ordenado.iloc[0]
                
                col_a, col_b = st.columns([2, 1])
                
                with col_a:
                    st.success(f"*Melhor custo-benefício:* Unidade {melhor['UNIDADE']}")
                    if preco_col and preco_col in melhor:
                        st.write(f"- *Preço:* R$ {melhor[preco_col]:,.2f}")
                    if 'R$/m²' in melhor:
                        st.write(f"- *R$/m²:* R$ {melhor['R$/m²']:.2f}")
                    if '1ª AVALIAÇÃO OÁSIS II' in melhor:
                        st.write(f"- *Avaliação:* R$ {melhor['1ª AVALIAÇÃO OÁSIS II']:,.2f}")
                    if 'DESCONTO' in melhor:
                        st.write(f"- *Desconto:* R$ {melhor['DESCONTO']:,.2f}")
                    if tipo_col and tipo_col in melhor:
                        st.write(f"- *Tipo:* {melhor[tipo_col]}")
                
                with col_b:
                    if preco_col and preco_col in melhor and melhor[preco_col] > 0:
                        valor = melhor[preco_col]
                        entrada_percentual = st.slider("Entrada (%)", 20, 50, 30)
                        entrada = valor * (entrada_percentual / 100)
                        financiado = valor - entrada
                        juros = 0.10
                        prazo_meses = 420
                        parcela_media = financiado * (1 + juros/12) / prazo_meses
                        
                        st.info(f"*Simulação - Unidade {melhor['UNIDADE']}*")
                        st.write(f"Valor total: R$ {valor:,.2f}")
                        st.write(f"Entrada ({entrada_percentual}%): R$ {entrada:,.2f}")
                        st.write(f"Financiado: R$ {financiado:,.2f}")
                        st.write(f"Parcela estimada: R$ {parcela_media:,.2f}")
                        st.caption(f"Prazo: {prazo_meses} meses (35 anos), juros: {juros*100}% a.a. (SAC)")
                    else:
                        st.warning("⚠️ Valor do imóvel não disponível para simulação.")
            else:
                st.warning("⚠️ Nenhum imóvel encontrado com os filtros atuais.")
        
        except Exception as e:
            st.error(f"❌ Erro ao ler a planilha: {str(e)}")
            st.info("Verifique o formato do arquivo (XLSX, CSV ou PDF).")
    
    else:
        st.info("👈 Selecione a construtora e envie a planilha no menu lateral para começar")
        st.markdown("""
        ### Como usar:
        1. Selecione a *construtora* no menu lateral
        2. Envie a planilha da construtora (XLSX, CSV ou PDF) ou use o Google Drive
        3. Ajuste os filtros disponíveis
        4. A IA recomenda o melhor imóvel
        """)

# --- FUNÇÃO PARA EXIBIR GESTÃO DE USUÁRIOS ---
def pagina_gestao_usuarios(USUARIOS):
    st.title("👥 Gestão de Usuários")
    
    tabs = st.tabs(["📋 Listar", "➕ Adicionar", "✏️ Editar"])
    
    with tabs[0]:
        st.markdown("### Usuários cadastrados:")
        if USUARIOS:
            dados_tabela = []
            for login, dados in USUARIOS.items():
                dados_tabela.append({
                    "Login": login,
                    "Nome": dados["nome"],
                    "Perfil": "👑 Gerente" if dados["perfil"] == "gerente" else "👤 Corretor",
                    "Status": "✅ Ativo" if dados["ativo"] else "❌ Inativo"
                })
            st.dataframe(pd.DataFrame(dados_tabela), use_container_width=True)
        else:
            st.info("Nenhum usuário cadastrado.")
    
    with tabs[1]:
        with st.form("form_novo_usuario"):
            col1, col2 = st.columns(2)
            with col1:
                novo_login = st.text_input("Login (usuário)")
                novo_nome = st.text_input("Nome completo")
            with col2:
                nova_senha = st.text_input("Senha", type="password")
                novo_perfil = st.selectbox("Perfil", ["corretor", "gerente"])
                novo_ativo = st.checkbox("Ativo", value=True)
            
            if st.form_submit_button("➕ Adicionar Usuário", use_container_width=True):
                if novo_login and novo_nome and nova_senha:
                    if novo_login in USUARIOS:
                        st.error("❌ Usuário já existe!")
                    else:
                        USUARIOS[novo_login] = {
                            "nome": novo_nome,
                            "hash": hash_senha(nova_senha),
                            "perfil": novo_perfil,
                            "ativo": novo_ativo,
                            "criado_em": datetime.now().isoformat()
                        }
                        salvar_usuarios(USUARIOS)
                        st.success(f"✅ Usuário '{novo_login}' adicionado com sucesso!")
                        st.rerun()
                else:
                    st.error("❌ Preencha todos os campos!")
    
    with tabs[2]:
        usuarios_lista = list(USUARIOS.keys())
        if usuarios_lista:
            usuario_editar = st.selectbox("Selecione o usuário", usuarios_lista)
            
            if usuario_editar:
                dados = USUARIOS[usuario_editar]
                
                with st.form("form_editar_usuario"):
                    col1, col2 = st.columns(2)
                    with col1:
                        novo_nome = st.text_input("Nome", value=dados["nome"])
                        novo_perfil = st.selectbox(
                            "Perfil", 
                            ["corretor", "gerente"], 
                            index=0 if dados["perfil"] == "corretor" else 1
                        )
                    with col2:
                        nova_senha = st.text_input("Nova senha (deixe em branco para manter)", type="password")
                        novo_ativo = st.checkbox("Ativo", value=dados["ativo"])
                    
                    col_btn1, col_btn2 = st.columns(2)
                    with col_btn1:
                        if st.form_submit_button("💾 Salvar", use_container_width=True):
                            dados["nome"] = novo_nome
                            if nova_senha:
                                dados["hash"] = hash_senha(nova_senha)
                            dados["perfil"] = novo_perfil
                            dados["ativo"] = novo_ativo
                            salvar_usuarios(USUARIOS)
                            st.success("✅ Usuário atualizado com sucesso!")
                            st.rerun()
                    
                    with col_btn2:
                        if st.form_submit_button("🗑️ Excluir", use_container_width=True):
                            if usuario_editar == "gerente":
                                st.error("❌ Não é possível excluir o gerente principal!")
                            else:
                                del USUARIOS[usuario_editar]
                                salvar_usuarios(USUARIOS)
                                st.success(f"✅ Usuário '{usuario_editar}' excluído!")
                                st.rerun()
        else:
            st.warning("Nenhum usuário cadastrado.")

# --- FUNÇÃO PARA EXIBIR GESTÃO DE CONSTRUTORAS ---
def pagina_gestao_construtoras(CONSTRUTORAS):
    st.title("🏗️ Gestão de Construtoras")
    
    with st.expander("➕ Adicionar Nova Construtora", expanded=True):
        with st.form("form_nova_construtora"):
            col1, col2 = st.columns(2)
            with col1:
                nome = st.text_input("Nome da Construtora")
                skiprows = st.number_input("Linhas para pular (skiprows)", min_value=0, value=0, step=1)
            with col2:
                st.markdown("*Colunas para exibir*")
                st.caption("Ex: UNIDADE, PAVTO, PREÇO")
                colunas_ordem_str = st.text_input(
                    "Colunas (separadas por vírgula)",
                    placeholder="UNIDADE, PAVTO, PREÇO"
                )
                
                st.markdown("*Colunas numéricas*")
                st.caption("Ex: PREÇO, M², ANDAR")
                colunas_numericas_str = st.text_input(
                    "Colunas numéricas (separadas por vírgula)",
                    placeholder="PREÇO, M², ANDAR"
                )
            
            st.markdown("*Mapeamento de colunas (índice: nome)*")
            st.caption('Ex: {"0": "UNIDADE", "1": "PAVTO", "2": "PREÇO"}')
            mapeamento_str = st.text_area(
                "Digite o mapeamento",
                placeholder='{"0": "UNIDADE", "1": "PAVTO", "2": "PREÇO"}',
                height=80
            )
            
            if st.form_submit_button("➕ Adicionar Construtora", use_container_width=True):
                if nome:
                    try:
                        mapeamento = json.loads(mapeamento_str) if mapeamento_str else {}
                        colunas_ordem = [c.strip() for c in colunas_ordem_str.split(',') if c.strip()]
                        colunas_numericas = [c.strip() for c in colunas_numericas_str.split(',') if c.strip()]
                        
                        CONSTRUTORAS[nome] = {
                            "skiprows": skiprows,
                            "mapeamento": {str(k): v for k, v in mapeamento.items()},
                            "colunas_ordem": colunas_ordem,
                            "colunas_para_converter": colunas_numericas
                        }
                        
                        salvar_construtoras(CONSTRUTORAS)
                        st.success(f"✅ Construtora '{nome}' adicionada com sucesso!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Erro ao adicionar: {str(e)}")
    
    st.markdown("---")
    st.markdown("### 📋 Construtoras Cadastradas")
    
    if CONSTRUTORAS:
        for nome, config in CONSTRUTORAS.items():
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
                with col1:
                    st.write(f"*{nome}*")
                with col2:
                    st.write(f"{len(config.get('colunas_ordem', []))} colunas")
                with col3:
                    if st.button(f"✏️ Editar", key=f"edit_{nome}"):
                        st.session_state['editando'] = nome
                with col4:
                    if st.button(f"🗑️ Excluir", key=f"del_{nome}"):
                        del CONSTRUTORAS[nome]
                        salvar_construtoras(CONSTRUTORAS)
                        st.rerun()
                
                if st.session_state.get('editando') == nome:
                    with st.form(f"form_edit_{nome}"):
                        col1, col2 = st.columns(2)
                        with col1:
                            novo_nome = st.text_input("Novo nome", value=nome)
                            novo_skiprows = st.number_input("Skiprows", value=config.get("skiprows", 0), step=1)
                        with col2:
                            novo_colunas_ordem = st.text_input(
                                "Colunas para exibir",
                                value=", ".join(config.get("colunas_ordem", []))
                            )
                            novo_colunas_numericas = st.text_input(
                                "Colunas numéricas",
                                value=", ".join(config.get("colunas_para_converter", []))
                            )
                        
                        novo_mapeamento = st.text_area(
                            "Mapeamento",
                            value=json.dumps(config.get("mapeamento", {}), indent=2, ensure_ascii=False),
                            height=100
                        )
                        
                        col_btn1, col_btn2 = st.columns(2)
                        with col_btn1:
                            if st.form_submit_button("💾 Salvar", use_container_width=True):
                                try:
                                    del CONSTRUTORAS[nome]
                                    CONSTRUTORAS[novo_nome] = {
                                        "skiprows": novo_skiprows,
                                        "mapeamento": json.loads(novo_mapeamento),
                                        "colunas_ordem": [c.strip() for c in novo_colunas_ordem.split(',') if c.strip()],
                                        "colunas_para_converter": [c.strip() for c in novo_colunas_numericas.split(',') if c.strip()]
                                    }
                                    salvar_construtoras(CONSTRUTORAS)
                                    st.session_state['editando'] = None
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"❌ Erro: {str(e)}")
                        with col_btn2:
                            if st.form_submit_button("❌ Cancelar", use_container_width=True):
                                st.session_state['editando'] = None
                                st.rerun()
                
                st.markdown("---")
    else:
        st.info("Nenhuma construtora cadastrada. Adicione a primeira!")

# --- SIDEBAR COM LOGIN E NAVEGAÇÃO ---
with st.sidebar:
    st.markdown("### 🏢 Simulador de Crédito")
    st.markdown("---")
    
    USUARIOS = carregar_usuarios()
    CONSTRUTORAS = carregar_construtoras()
    
    if "usuario_logado" not in st.session_state:
        st.session_state.usuario_logado = None
    
    if st.session_state.usuario_logado is None:
        st.markdown("### 🔑 Login")
        usuario = st.text_input("Usuário")
        senha = st.text_input("Senha", type="password")
        if st.button("Entrar", use_container_width=True):
            if verificar_login(usuario, senha, USUARIOS):
                st.session_state.usuario_logado = usuario
                st.success(f"✅ Bem-vindo, {USUARIOS[usuario]['nome']}!")
                st.rerun()
            else:
                st.error("❌ Usuário ou senha inválidos!")
        st.stop()
    
    usuario_atual = st.session_state.usuario_logado
    perfil_atual = USUARIOS[usuario_atual]["perfil"]
    
    st.write(f"👤 *{USUARIOS[usuario_atual]['nome']}*")
    st.caption(f"Perfil: {perfil_atual}")
    
    if st.button("🚪 Sair", use_container_width=True):
        st.session_state.usuario_logado = None
        if "google_token" in st.session_state:
            del st.session_state.google_token
        st.rerun()
    
    st.markdown("---")
    
    if "pagina" not in st.session_state:
        st.session_state.pagina = "Simulador"
    
    if st.button("📊 Simulador", use_container_width=True):
        st.session_state.pagina = "Simulador"
        st.rerun()
    
    if perfil_atual == "gerente":
        if st.button("👥 Gestão de Usuários", use_container_width=True):
            st.session_state.pagina = "Usuários"
            st.rerun()
        
        if st.button("🏗️ Gestão de Construtoras", use_container_width=True):
            st.session_state.pagina = "Construtoras"
            st.rerun()
    
    st.markdown("---")
    st.caption("Versão 2.0")

# --- RENDERIZAÇÃO DA PÁGINA SELECIONADA ---
# Se for corretor, SEMPRE vai para o simulador
if perfil_atual == "corretor":
    pagina_simulador(CONSTRUTORAS, USUARIOS, perfil_atual)
else:
    # Gerente: usa a navegação normal
    pagina = st.session_state.get("pagina", "Simulador")
    
    if pagina == "Simulador":
        pagina_simulador(CONSTRUTORAS, USUARIOS, perfil_atual)
    elif pagina == "Usuários":
        pagina_gestao_usuarios(USUARIOS)
    elif pagina == "Construtoras":
        pagina_gestao_construtoras(CONSTRUTORAS)
    else:
        pagina_simulador(CONSTRUTORAS, USUARIOS, perfil_atual)
