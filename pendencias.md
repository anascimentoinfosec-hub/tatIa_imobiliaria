# 🐛 Pendências e Backlog

Arquivo de controle das pendências do projeto. Atualizar conforme forem sendo resolvidas.

---

## 🔴 Bugs Conhecidos

### #001 — Formulário de vendas não limpa após registrar
- **Data:** 26/09/2026
- **Tela:** 💼 Vendas → ➕ Adicionar
- **Comportamento atual:** Após clicar em "Registrar venda", os campos continuam preenchidos
- **Tentativa 1:** Limpeza via `session_state` + flag `limpar_form_venda` → ❌ não funcionou
- **Próxima tentativa sugerida:** Investigar cache do `st.form` ou usar `key` dinâmica baseada em timestamp
- **Impacto:** Médio (UX ruim, mas não bloqueia)
- **Prioridade:** 🟡 Média (após testes da gerente)

---

## 🟡 Melhorias Planejadas

### #002 — Coluna STATUS nas planilhas de construtora
- Cards de "Disponíveis / Reservados / Vendidos" no Dashboard só aparecem se a planilha tiver coluna STATUS
- **Alternativa:** Adicionar coluna automaticamente, ou permitir cadastro manual

Data:27/09
### #009 - nos campos de valores incluir o ponto do milhar
    - priorizar
    
### #010 - No módulo de Gerente ao criar uma nova simulação está não aparecendo no modo Gestão de Vendas

#### #011 - O valor de entrada não pode ter referência com as tabelas da regra de financiamento. 
        *Qualquer valor de entrada tem que estar liberado

#### #012 - O simulador deve ser somente e somente só a simulação de Entrada
        * Por isso bloquear a área de regra de financiamento e não gerar calculo com essa regras(Temporiamente)

### # 013 - Trocar do lado diretio no botão simulador para ser simulador de Entrada de Construtora
        Pois é somente isso que ele deve fazer e não simular o que os bancos fariam

### #014 Cada construtura tem uma regra de negócio para a entrada diferente
    
    1 - Cliente na mesa dados(cpf, renda brut....)
2- Simulação com caixa Corretor simula na caixa
3 - conforme o valor financiado. corretor identifica o imóvel: neste caso 380.900 
   Dor:
  ****- O Corretor na tela do simulador olhou um a um para saber o valor do imóvel
   Pílula:  
*** Aqui o ideal é que a busca traga os imóveis conforme preferências
    O corretor vai realizando perguntas: Localização, andar, sol, vaga, quartos, lazer....
	
4 - Conforme a renda o banco financia ex.:297.600 ********
5 - Corretor localiza imóvel conforme o valor do imóvel da tabela da construtora: neste caso 380.900 - O Corretor na tela do simulador olhou um a um para saber o valor do imóvel

Ex.: Jeronimo da veiga
6 - A construtora ta dando (Desconto acordado: R$ 80000) isso é de momento e varia 
7 - 3 Regras do Conceito( *Validar regras de outras construtoras)
8 - Regras do Pré-chaves
  - Regra1: Ato Mínimo: R$1000,00
  - Regra2: Se o corretor quiser receber na cabeça 4,2%. O cliente tem que dar os 4.2% +1000
  - Regra3: A parcela antes das chaves(Pré-chaves) só pode comprometer 30% da renda bruta do cliente
  - Regra3: As intermediarias Pré-chaves pode comprometer até 80% da renda bruta do cliente
8 - Regras do Pós-Chaves
   Regra1 - Parcela pós chaves não pode comprometar 5% da renda bruta do cliente
   Regra2 - As intermediarias no pós chaves não pode comprometer _+ de 30% da renda bruta

9 - Somando-se as regras de pré e pós chaves não pode comprometer 60x de parcelas


    Obs.: Essa simulação poderá ser feita tanto pelo gerente quanto pelo corredor

#### #  #015 - Na simulação do cliente é necessário ter um campo vagas. 
    - Poist o Cliente pode necessitar e as oportunidades deverão buscar somente unidades com vagas

#### # 016 Ajuste na lista de Oportunidades
    Ao localizar as melhores oportunidades o corretor poderá ajustar campos importante tais como localização

#### # Na área do cliente tem que aparecer um área chamada Lazer onde o corretor poderá marcar uma ou mais opções e com isto o filtro de oportunidades ser mais assertivo
   Opções:
       - Complexo Aquatico
       - Salão de Festas
       - Academia
       - Cobertura
       - Churrasqueira
       - Quadra Poliesportiva,
        - Quadra de Beach Tennis
        - Playground
        - Pet place
        - Mini Mercado,
        - Redário,
        - Horta
        - Espaço Piquinique
        - Fitness
        - Car Wash
        - Futmesa
     
### #003 — Supabase (persistência na nuvem)
- Migrar dados de JSON local para banco PostgreSQL
- Resolve: Streamlit Cloud apagar dados a cada deploy
- Liberta o app do PC ligado (fim do ngrok)

### #004 — Aprovação de descontos com log
- Corretor cria desconto → gerente aprova/rejeita
- Registra quem aprovou, quando e por quê
- Prepara base para o Diretor

### #005 — Módulo Financeiro (comissões, contas)
- Cálculo de comissão por venda
- Contas a pagar/receber
- Fluxo de caixa

### #006 — Ambiente do Diretor
- Dashboard executivo consolidado
- Metas, performance, VGV geral

### #007 — BIA: memória persistente entre sessões
- Hoje a BIA lembra só durante a sessão (session_state)
- Salvar histórico no JSON para lembrar entre dias

### #008 — Migrar dados antigos dos JSONs para Supabase
- Só quando #003 estiver concluída
- Opcional se dados antigos não forem relevantes

---

## ✅ Concluídos Recentemente

- ✅ Módulo de Vendas (CRUD + Kanban + Dashboard VGV)
- ✅ Monitor de taxas via BIA (Tavily)
- ✅ Regras de financiamento configuráveis
- ✅ Reorganização por perfil (corretor/gerente/superadmin)
- ✅ Cálculo correto Price/SAC + Diagnóstico financeiro
- ✅ Export PDF + Proposta única
- ✅ Histórico de simulações
- ✅ Dashboard com gráficos

---

## 📝 Como usar

1. Adicione novas pendências no topo da seção apropriada
2. Ao resolver, mova para "Concluídos Recentemente"
3. Numere sequencialmente (#001, #002, ...)
4. Após ~5 concluídos, limpe a lista antiga