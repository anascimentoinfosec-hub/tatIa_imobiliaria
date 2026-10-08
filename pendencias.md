# 🐛 Pendências e Backlog

## 🔴 Bugs Conhecidos

### #001 — Formulário de vendas não limpa após registrar
- **Status:** Resolvido parcialmente (limpar_form_venda funciona)
- **Prioridade:** 🟢 Baixa

---

## 🟡 Melhorias Planejadas

### #003 — Supabase (persistência na nuvem)
- Migrar dados de JSON local para PostgreSQL
- Resolve: Streamlit Cloud apagar dados a cada deploy
- Liberta o app do PC ligado (fim do ngrok)
- **Prioridade:** 🟡 Alta

### #004 — Aprovação de descontos com log
- Corretor cria desconto → gerente aprova/rejeita
- **Prioridade:** 🟢 Baixa (fluxo atual já funciona)

### #005 — Módulo Financeiro (comissões, contas)
- Cálculo de comissão por venda
- **Prioridade:** 🟡 Média (Fase 3)

### #006 — Ambiente do Diretor
- Dashboard executivo consolidado
- **Prioridade:** 🟡 Média (Fase 2)

### #007 — BIA: memória persistente entre sessões
- Salvar histórico no JSON para lembrar entre dias
- **Prioridade:** 🟢 Baixa

### #010 — Simulação do gerente não aparece em Vendas
- **Status:** Resolvido com botão "Confirmar Venda"
- **Prioridade:** ✅ Concluído

### #014 — Regras de entrada por construtora
- **Status:** ✅ Concluído (Parte 1 + 2)
- **Prioridade:** ✅ Concluído

### #017 — BIA analisa planilha automaticamente
- **Status:** ✅ Concluído (com botão no form)
- **Prioridade:** ✅ Concluído

### #019 — Bloquear salvamento sem mapeamento
- **Status:** ✅ Concluído
- **Prioridade:** ✅ Concluído

### #020 — Encoding corrompido no JSON
- **Status:** ✅ Concluído
- **Prioridade:** ✅ Concluído

### #021 — Unificar upload (evitar 2 uploads)
- **Status:** ✅ Concluído
- **Prioridade:** ✅ Concluído

### #022 — Refinamento: filtro de Cidade
- Funciona em MRV (via `CIDADE`), mas não detecta em outras
- **Prioridade:** 🟢 Baixa

### #023 — Botão de excluir construtora
- **Status:** ✅ Concluído
- **Prioridade:** ✅ Concluído

### #024 — Redesign do simulador (cliente primeiro)
- **Status:** ✅ Concluído
- **Prioridade:** ✅ Concluído

### #025 — Corretor vê só suas vendas
- **Status:** ✅ Concluído
- **Prioridade:** ✅ Concluído

### #026 — Corretor vê só seu histórico
- **Status:** ✅ Concluído
- **Prioridade:** ✅ Concluído

### #027 — BIA operacional independente
- **Status:** ✅ Concluído
- **Prioridade:** ✅ Concluído

### #028 — Campo FGTS e Subsídio
- **Status:** ✅ Concluído
- **Prioridade:** ✅ Concluído

### #029 — Campo Data de Nascimento
- **Status:** ✅ Concluído
- **Prioridade:** ✅ Concluído

### #030 — Exibir parcela morando
- **Status:** ✅ Concluído
- **Prioridade:** ✅ Concluído

### #031 — Intermediárias editáveis
- **Status:** ✅ Concluído (com agendamento por parcela)
- **Prioridade:** ✅ Concluído

### #032 — Flag "documentação paga"
- **Status:** ✅ Concluído
- **Prioridade:** ✅ Concluído

### #033 — Tela de Proposta completa
- **Status:** ✅ Concluído (dados completos no histórico)
- **Prioridade:** ✅ Concluído

### #034 — 7 status do funil de venda
- **Status:** ✅ Concluído
- **Prioridade:** ✅ Concluído

### #035 — Botões de ação do gerente
- **Status:** ✅ Concluído
- **Prioridade:** ✅ Concluído

### #036 — Motivo de rejeição
- **Status:** ✅ Concluído
- **Prioridade:** ✅ Concluído

### #037 — Ato editável (não apenas o mínimo)
- Cliente pode dar mais no ato
- **Prioridade:** 🟡 Média (aguardando feedback)

### #038 — Incluir intermediárias e cronograma no PDF
- **Status:** 🟡 Aguardando validação da gerente
- A gerente precisa decidir: o PDF deve mostrar a lista completa com as parcelas ajustadas?
- Se sim: criar tabela "Parcela | Normal | Intermediária | Total" no PDF
- **Prioridade:** 🟡 Alta (aguardando resposta)

### #039 — Notificação WhatsApp para o gerente
- Quando o corretor envia proposta → gerente recebe WhatsApp
- Também pode notificar em outros status (aprovação, contrato enviado)
- Opções: Z-API (R$ 99/mês), Twilio, Evolution API (self-host), Watidy
- Precisa: campo `telefone` em usuários + chave de API
- **Prioridade:** 🟡 Alta (após validar valor com a gerente)
- **Decisão:** alinhar com a gerente qual serviço contratar
---

## ✅ Concluídos Recentemente

- ✅ Intermediárias agendadas (por parcela/fase)
- ✅ Cronograma de pagamento visual
- ✅ Compartilhar antes de Enviar Proposta
- ✅ Botão Confirmar Venda cria venda real
- ✅ Campos novos: FGTS, Subsídio, Data Nascimento, Parcela Morando
- ✅ Teto de parcelamento por construtora (15%)
- ✅ 7 status do funil