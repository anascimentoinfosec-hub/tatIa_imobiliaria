\# 🚀 Como Rodar o App (Local + ngrok)



\## 📋 Pré-requisitos (já instalados)



\- Python 3.14

\- Streamlit

\- ngrok configurado com authtoken em `C:\\Users\\User\\AppData\\Local\\ngrok\\ngrok.yml`

\- Domínio fixo: `predefine-endeared-protector.ngrok-free.dev`



\---



\## 🎬 Passo a passo (toda vez)



\### 1️⃣ Terminal 1 — Rodar o Streamlit



Abra o PowerShell e rode:



```powershell

cd $env:USERPROFILE\\Documents\\tatIa\_imobiliaria

py -3.14 -m streamlit run app.py --server.port 8080

```



✅ Deixe esse terminal aberto.



\---



\### 2️⃣ Terminal 2 — Rodar o ngrok



Abra \*\*outro\*\* PowerShell e rode:



```powershell

cd $env:USERPROFILE\\Downloads

.\\ngrok http 8080 --domain=predefine-endeared-protector.ngrok-free.dev

```



✅ Deixe esse terminal aberto também.



\---



\### 3️⃣ Compartilhar o link



O link público (sempre o mesmo) é:



```

https://predefine-endeared-protector.ngrok-free.dev

```



Envie esse link para a gerente (ou qualquer pessoa autorizada).



\---



\## ⚠️ Regras importantes



\- \*\*Os dois terminais precisam ficar abertos.\*\* Se fechar algum, o link cai.

\- \*\*A máquina precisa estar ligada e com internet.\*\*

\- \*\*As planilhas e usuários ficam no seu PC\*\* (persistem entre sessões).

\- \*\*Para encerrar:\*\* aperte `Ctrl+C` nos dois terminais.



\---



\## 🔄 Fluxo resumido



```

\[Seu PC]                          \[Internet]                        \[Gerente]

Streamlit :8080  →  ngrok tunnel  →  https://predefine-...dev  →  Navegador dela

```



\---



\## 💡 Dicas extras



\- Se a porta 8080 estiver ocupada, use 8081 ou outra (ajuste nos dois comandos).

\- Se o authtoken expirar, rode de novo:

&#x20; ```powershell

&#x20; .\\ngrok config add-authtoken SEU\_TOKEN

&#x20; ```

\- Para ver o painel de monitoramento do ngrok: acesse `http://localhost:4040` no navegador (enquanto o ngrok estiver rodando).

