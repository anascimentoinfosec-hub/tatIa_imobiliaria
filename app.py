#ATUALIZADO EM 25/08/2026
import streamlit as st
import pandas as pd
import io
import pdfplumber
import re
import json
import os
import hashlib
from datetime import datetime, timedelta
import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
import random

# CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Simulador de Crédito", layout="wide")

# --- ARQUIVOS DE CONFIGURAÇÃO ---
ARQUIVO_CONFIG = "construtoras.json"
ARQUIVO_USUARIOS = "usuarios.json"
ARQUIVO_RECUPERACAO = "recuperacao.json"

# --- FUNÇÕES DE HASH ---
def hash_senha(senha: str) -> str:
    return hashlib.sha256(senha.encode()).hexdigest()

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
            "email": "gerente@email.com",
            "criado_em": datetime.now().isoformat()
        }
    }

def salvar_usuarios(usuarios):
    with open(ARQUIVO_USUARIOS, 'w', encoding='utf-8') as f:
        json.dump(usuarios, f, indent=2, ensure_ascii=False)

def verificar_login(usuario: str, senha: str, usuarios: dict) -> bool:
    hash_digitado = hash_senha(senha)
    if usuario not in usuarios:
        return False
    return usuarios[usuario]["hash"] == hash_digitado and usuarios[usuario]["ativo"]

# --- FUNÇÕES DE RECUPERAÇÃO DE SENHA ---
def gerar_token_recuperacao():
    return ''.join(secrets.choice('0123456789') for _ in range(6))

def salvar_token_recuperacao(email, token):
    recuperacao = {}
    try:
        if os.path.exists(ARQUIVO_RECUPERACAO):
            with open(ARQUIVO_RECUPERACAO, 'r', encoding='utf-8') as f:
                recuperacao = json.load(f)
    except:
        pass
    
    recuperacao[email] = {
        "token": token,
        "criado_em": datetime.now().isoformat()
    }
    
    with open(ARQUIVO_RECUPERACAO, 'w', encoding='utf-8') as f:
        json.dump(recuperacao, f, indent=2, ensure_ascii=False)

def validar_token_recuperacao(email, token):
    try:
        if not os.path.exists(ARQUIVO_RECUPERACAO):
            return False
        
        with open(ARQUIVO_RECUPERACAO, 'r', encoding='utf-8') as f:
            recuperacao = json.load(f)
        
        if email not in recuperacao:
            return False
        
        dados = recuperacao[email]
        if dados["token"] != token:
            return False
        
        criado_em = datetime.fromisoformat(dados["criado_em"])
        if datetime.now() - criado_em > timedelta(minutes=15):
            return False
        
        return True
    except:
        return False

def remover_token_recuperacao(email):
    try:
        if os.path.exists(ARQUIVO_RECUPERACAO):
            with open(ARQUIVO_RECUPERACAO, 'r', encoding='utf-8') as f:
                recuperacao = json.load(f)
            
            if email in recuperacao:
                del recuperacao[email]
            
            with open(ARQUIVO_RECUPERACAO, 'w', encoding='utf-8') as f:
                json.dump(recuperacao, f, indent=2, ensure_ascii=False)
    except:
        pass

def enviar_email_recuperacao(email, token):
    try:
        if "EMAIL_SENDER" not in st.secrets or "EMAIL_PASSWORD" not in st.secrets:
            st.warning(f"⚠️ Configure EMAIL_SENDER e EMAIL_PASSWORD nos Secrets do Streamlit")
            st.info(f"💡 Token gerado: *{token}* (copie e cole)")
            return True
        
        remetente = st.secrets["EMAIL_SENDER"]
        senha = st.secrets["EMAIL_PASSWORD"]
        
        msg = MIMEMultipart()
        msg['From'] = remetente
        msg['To'] = email
        msg['Subject'] = "🔐 Código de recuperação - Simulador de Crédito"
        
        corpo = f"""
        Olá!
        
        Você solicitou a recuperação de senha do Simulador de Crédito.
        
        Seu código de verificação é: *{token}*
        
        Digite este código no app para criar uma nova senha.
        
        Este código é válido por 15 minutos.
        
        Se você não solicitou esta recuperação, ignore este e-mail.
        
        Atenciosamente,
        Equipe Simulador de Crédito
        """
        
        msg.attach(MIMEText(corpo, 'plain'))
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(remetente, senha)
        server.send_message(msg)
        server.quit()
        
        return True
    except Exception as e:
        st.error(f"❌ Erro ao enviar e-mail: {str(e)}")
        return False

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

# --- FUNÇÃO PARA EXIBIR O SIMULADOR ---
def pagina_simulador(CONSTRUTORAS, USUARIOS, perfil_atual):
    st.title("📊 Simulador de Crédito")
    
    with st.sidebar:
        st.header("⚙️ Configurações")
        
        construtora_selecionada = st.selectbox(
            "🏗️ Selecione a construtora",
            options=list(CONSTRUTORAS.keys())
        )
        
        st.markdown("---")
        
        uploaded_file = st.file_uploader(
            "📤 Envie a planilha",
            type=['xlsx', 'xls', 'csv', 'pdf']
        )
        
        st.markdown("---")
        st.caption("Versão 2.0")
    
    # --- CORPO PRINCIPAL ---
    if uploaded_file is None:
        # --- CSS CORRIGIDO ---
        st.markdown("""
        <style>
        .hero {
            background: linear-gradient(135deg, #1a237e, #0d47a1, #1565c0);
            padding: 50px 30px;
            border-radius: 16px;
            color: white;
            text-shadow: 2px 2px 8px rgba(0,0,0,0.8);
            margin-bottom: 30px;
            border-bottom: 6px solid #ff6f00;
        }
        .hero h1 {
            font-size: 38px;
            font-weight: 700;
            margin: 0;
        }
        .hero p {
            font-size: 18px;
            opacity: 0.9;
            margin: 8px 0 0 0;
        }
        .card-info {
            background-color: #f0f4ff;
            padding: 16px 20px;
            border-radius: 12px;
            border-left: 6px solid #0066cc;
            margin-bottom: 12px;
        }
        .card-info h4 {
            margin: 0 0 4px 0;
            color: #0066cc;
            font-size: 14px;
        }
        .card-info p {
            margin: 0;
            color: #333;
            font-weight: 600;
            font-size: 16px;
        }
        .dica-card {
            background: linear-gradient(135deg, #1a2a6c, #b21f1f, #fdbb2d);
            padding: 20px;
            border-radius: 12px;
            color: white;
            text-align: center;
            margin-top: 16px;
        }
        .dica-card p {
            font-size: 17px;
            font-style: italic;
            margin: 0;
        }
        .clima-card {
            background-color: #e8f4fd;
            padding: 16px 20px;
            border-radius: 12px;
            display: flex;
            align-items: center;
            gap: 16px;
        }
        .clima-card .temp {
            font-size: 28px;
            font-weight: 700;
        }
        .empreendimento-card {
            background: linear-gradient(135deg, #1a237e, #0d47a1);
            padding: 20px;
            border-radius: 12px;
            color: white;
            text-align: center;
            margin-top: 12px;
        }
        .empreendimento-card h3 {
            margin: 0;
        }
        .empreendimento-card p {
            margin: 4px 0;
            opacity: 0.9;
        }
        </style>
        """, unsafe_allow_html=True)

        # --- HERO (sem imagem, apenas gradiente) ---
        st.markdown("""
        <div class="hero">
            <h1>🏢 Simulador de Crédito Imobiliário</h1>
            <p>Rio de Janeiro • Oásis II e outras construtoras</p>
        </div>
        """, unsafe_allow_html=True)

        col_esq, col_dir = st.columns([2, 1])

        with col_esq:
            st.markdown("### 📊 Mercado Imobiliário")
            
            mercado = {
                "Taxa Selic": "10,50%",
                "Taxa de Juros (SFH)": "9,50% a.a.",
                "TR (referência)": "1,50% a.a.",
                "Valor médio m² (RJ)": "R$ 12.800",
                "Média de entrada": "20% a 30%",
                "Prazo máximo": "420 meses (35 anos)"
            }
            
            for titulo, valor in mercado.items():
                st.markdown(f"""
                <div class="card-info">
                    <h4>{titulo}</h4>
                    <p>{valor}</p>
                </div>
                """, unsafe_allow_html=True)

        with col_dir:
            st.markdown("### 🌤️ Clima no Rio")
            
            try:
                if "OPENWEATHER_API_KEY" in st.secrets:
                    api_key = st.secrets["OPENWEATHER_API_KEY"]
                    url = f"https://api.openweathermap.org/data/2.5/weather?q=Rio de Janeiro,BR&units=metric&lang=pt_br&appid={api_key}"
                    response = requests.get(url, timeout=5)
                    if response.status_code == 200:
                        dados = response.json()
                        temp = dados['main']['temp']
                        desc = dados['weather'][0]['description']
                        umidade = dados['main']['humidity']
                        vento = dados['wind']['speed']
                        
                        st.markdown(f"""
                        <div class="clima-card">
                            <div>
                                <div class="temp">{temp:.1f}°C</div>
                                <div style="text-transform: capitalize;">{desc}</div>
                            </div>
                            <div style="margin-left: auto; text-align: right; font-size: 14px;">
                                🌧️ Umidade: {umidade}%<br>
                                💨 Vento: {vento} km/h
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.info("🌤️ Clima: 28°C, Ensolarado")
                else:
                    st.info("🌤️ Configure a chave OpenWeather para clima em tempo real!")
            except:
                st.info("🌤️ Clima: 28°C, Ensolarado")

            st.markdown("---")
            st.markdown("### 🏗️ Empreendimento em Destaque")
            st.markdown("""
            <div class="empreendimento-card">
                <h3>Oásis II</h3>
                <p>📍 Barra da Tijuca - Rio de Janeiro</p>
                <p>🏢 18 andares • 115 unidades • 2 e 3 quartos</p>
                <p>💰 Preços a partir de R$ 384.950</p>
            </div>
            """, unsafe_allow_html=True)

        # --- DICA DO DIA ---
        dicas = [
            "💡 'A melhor época para comprar imóvel é sempre aquela em que você está preparado financeiramente.'",
            "💡 'Clientes valorizam corretores que entendem de financiamento, não só de imóveis.'",
            "💡 'Um bom corretor não vende um imóvel, ele realiza um sonho.'",
            "💡 'Conhecer as taxas de juros é tão importante quanto conhecer a planta do imóvel.'",
            "💡 'A confiança se constrói com transparência. Mostre todas as opções de financiamento.'",
            "💡 'O cliente não compra o imóvel, compra a segurança de ter um lar.'",
            "💡 'A simulação é o primeiro passo. O segundo é acreditar que é possível.'",
            "💡 'Imóvel é o único investimento que você pode usar enquanto ele valoriza.'"
        ]
        
        dia = datetime.now().day
        dica = dicas[dia % len(dicas)]
        
        st.markdown(f"""
        <div class="dica-card">
            <p>{dica}</p>
        </div>
        """, unsafe_allow_html=True)

        # --- INSTRUÇÕES ---
        st.markdown("---")
        st.markdown("### 📌 Como usar o Simulador")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            *1. Selecione a construtora*
            No menu lateral, escolha a construtora desejada.
            """)
        
        with col2:
            st.markdown("""
            *2. Envie a planilha*
            Faça upload da planilha da construtora (XLSX ou PDF).
            """)
        
        with col3:
            st.markdown("""
            *3. Simule e compare*
            A IA recomenda o melhor imóvel com base em custo-benefício.
            """)
        
        return
    
    # --- PROCESSAMENTO DA PLANILHA ---
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
                            "email": "",
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
                        novo_email = st.text_input("E-mail", value=dados.get("email", ""))
                    
                    col_btn1, col_btn2 = st.columns(2)
                    with col_btn1:
                        if st.form_submit_button("💾 Salvar", use_container_width=True):
                            dados["nome"] = novo_nome
                            if nova_senha:
                                dados["hash"] = hash_senha(nova_senha)
                            dados["perfil"] = novo_perfil
                            dados["ativo"] = novo_ativo
                            dados["email"] = novo_email
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
        
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("Entrar", use_container_width=True):
                if verificar_login(usuario, senha, USUARIOS):
                    st.session_state.usuario_logado = usuario
                    st.success(f"✅ Bem-vindo, {USUARIOS[usuario]['nome']}!")
                    st.rerun()
                else:
                    st.error("❌ Usuário ou senha inválidos!")
        
        with col2:
            if st.button("🔑 Esqueci a senha", use_container_width=True):
                st.session_state['recuperando_senha'] = True
                st.rerun()
        
        if st.session_state.get('recuperando_senha', False):
            st.markdown("---")
            st.markdown("### 🔐 Recuperar senha")
            
            email = st.text_input("E-mail cadastrado")
            
            if st.button("📧 Enviar código", use_container_width=True):
                if email:
                    email_existe = False
                    for user, dados in USUARIOS.items():
                        if dados.get("email") == email:
                            email_existe = True
                            break
                    
                    if not email_existe:
                        st.warning("⚠️ E-mail não encontrado. Verifique ou contate o administrador.")
                    else:
                        token = gerar_token_recuperacao()
                        salvar_token_recuperacao(email, token)
                        
                        if enviar_email_recuperacao(email, token):
                            st.success("✅ Código enviado para seu e-mail!")
                            st.session_state['token_enviado'] = True
                        else:
                            st.error("❌ Erro ao enviar e-mail")
            
            if st.session_state.get('token_enviado', False):
                codigo = st.text_input("Código de verificação")
                nova_senha = st.text_input("Nova senha", type="password")
                confirmar_senha = st.text_input("Confirmar nova senha", type="password")
                
                if st.button("✅ Alterar senha", use_container_width=True):
                    if codigo and nova_senha and confirmar_senha:
                        if nova_senha != confirmar_senha:
                            st.error("❌ As senhas não coincidem!")
                        elif len(nova_senha) < 6:
                            st.error("❌ A senha deve ter pelo menos 6 caracteres!")
                        else:
                            if validar_token_recuperacao(email, codigo):
                                for user, dados in USUARIOS.items():
                                    if dados.get("email") == email:
                                        dados["hash"] = hash_senha(nova_senha)
                                        salvar_usuarios(USUARIOS)
                                        remover_token_recuperacao(email)
                                        st.success("✅ Senha alterada com sucesso!")
                                        st.session_state['recuperando_senha'] = False
                                        st.session_state['token_enviado'] = False
                                        st.rerun()
                                        break
                            else:
                                st.error("❌ Código inválido ou expirado!")
                    else:
                        st.error("❌ Preencha todos os campos!")
            
            if st.button("🔙 Voltar ao login"):
                st.session_state['recuperando_senha'] = False
                st.session_state['token_enviado'] = False
                st.rerun()
        
        st.stop()
    
    usuario_atual = st.session_state.usuario_logado
    perfil_atual = USUARIOS[usuario_atual]["perfil"]
    
    st.write(f"👤 *{USUARIOS[usuario_atual]['nome']}*")
    st.caption(f"Perfil: {perfil_atual}")
    
    if st.button("🚪 Sair", use_container_width=True):
        st.session_state.usuario_logado = None
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
if perfil_atual == "corretor":
    pagina_simulador(CONSTRUTORAS, USUARIOS, perfil_atual)
else:
    pagina = st.session_state.get("pagina", "Simulador")
    
    if pagina == "Simulador":
        pagina_simulador(CONSTRUTORAS, USUARIOS, perfil_atual)
    elif pagina == "Usuários":
        pagina_gestao_usuarios(USUARIOS)
    elif pagina == "Construtoras":
        pagina_gestao_construtoras(CONSTRUTORAS)
    else:
        pagina_simulador(CONSTRUTORAS, USUARIOS, perfil_atual)
