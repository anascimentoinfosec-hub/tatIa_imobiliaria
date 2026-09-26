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