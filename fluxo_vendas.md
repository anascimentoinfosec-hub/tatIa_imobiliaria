# 📋 Fluxo Completo de Vendas

> Documento de referência do negócio real da imobiliária.
> Última atualização: 04/10/2026

---

## 🎯 PARTE 1 — SIMULAÇÃO (Corretor)

### 1. Planilha da construtora tem:
- ✅ **Valor de Avaliação** (base para a Caixa)
- ✅ **Valor de Preço** (valor na tabela)
- ⚠️ Ambos devem aparecer na simulação → diferença = **barganha de desconto**

### 2. Corretor simula na Caixa
- Usa o **VALOR DE AVALIAÇÃO** como base
- Ex: Avaliação = R$ 400.000

### 3. Caixa define o financiamento
- Teto = **80%** da avaliação
- Ex: 80% × 400k = **R$ 320.000**

### 4. Valor final do imóvel
- Valor de Preço (tabela): R$ 420.000
- **Desconto da construtora**: R$ 80.000 (variável por construtora)
- **Valor final**: R$ 340.000

### 5. Regra da construtora
- Ex: 15% do valor final deve ser parcelado
- 15% × 340k = **R$ 51.000**

### 6. Cálculo da ENTRADA
- Valor final − Financiamento Caixa = Entrada
- R$ 340.000 − R$ 320.000 = **R$ 20.000**

### 7. Ato mínimo
- Cliente paga **ATO** para segurar o imóvel (ex: R$ 1.000 via PIX)
- Entrada restante a parcelar = R$ 20.000 − R$ 1.000 = **R$ 19.000**

### 8. Parcelamento da entrada (R$ 19.000)
Dividida em:
- **Pré-chaves** (durante a obra): máx **30% da renda**
  - Intermediárias pré: máx **80% da renda**
- **Pós-chaves** (após entrega): máx **5% da renda**
  - Intermediárias pós: máx **30% da renda**

**Exemplo com renda R$ 8.000:**
- Pré máx: R$ 2.400
- Intermediária pré máx: R$ 6.400
- Pós máx: R$ 400
- Intermediária pós máx: R$ 2.400

### ⚠️ Importante — Intermediárias
- Corretor/gerente pode **aumentar a intermediária** de pré-chaves
- Objetivo: **antecipar** o pagamento antes do fim da obra
- Sistema precisa permitir **editar o valor da intermediária** manualmente

### ⚠️ Documentação e taxa Caixa
- Algumas construtoras exigem que cliente pague:
  - Documentação do imóvel
  - Taxa da Caixa
- → Campo flag por construtora/produto

---

## 📤 PARTE 2 — PROPOSTA (Corretor → Cliente)

### 9. Simulação apresentada ao cliente
Deve mostrar **todos** os campos:
- Valor do imóvel (Avaliação)
- Nome, Renda, Data de nascimento
- Produto, Unidade
- Valor de venda
- Desconto
- Valor final
- Financiamento (Caixa)
- **FGTS** (novo campo)
- **Subsídio** (novo campo)
- Parcela "morando" (do financiamento Caixa)
- Valor pré-chaves + valor intermediária
- Valor pós-chaves + valor intermediária
- Ato do cliente
- Documentação paga? (Sim/Não)

---

## ✅ PARTE 3 — APROVAÇÃO (Gerente + Construtora)

### 10. Cliente aceita → Corretor informa Gerente
### 11. Gerente envia docs para **Acessoria de Crédito** da construtora
   - Validação: minutos a dias
### 12. Acessoria aprova/rejeita
   - Se rejeitar: **pasta permanece** no sistema com motivo
### 13. Gerente informa cliente da aprovação
### 14. Gerente cadastra cliente no sistema da construtora
   - Status nosso: **"Aguardando validação da construtora"**
### 15. Construtora aprova no sistema dela
   - Status nosso: **"Aprovado pela construtora"**
### 16. Construtora gera contrato e envia ao cliente
   - Status nosso: **"Contrato enviado (aguardando assinatura)"**
### 17. Cliente paga ATO + Assina contrato
   - Status nosso: **"Assinado"**
### 18. 🎉 **Venda realizada com sucesso!**

---

## 🔄 Status do Funil (propostos)

| Status | O que significa | Quem move |
|---|---|---|
| `pendente` | Simulação aprovada pelo cliente | Corretor |
| `em_analise` | Enviado à acessoria da construtora | Gerente |
| `aprovada` | Acessoria aprovou | Gerente |
| `aguardando_construtora` | Cadastrado no sistema da construtora | Gerente |
| `contrato_enviado` | Contrato enviado ao cliente | Gerente |
| `venda_confirmada` | ATO pago + contrato assinado | Gerente |
| `rejeitada` | Acessoria negou | Gerente |