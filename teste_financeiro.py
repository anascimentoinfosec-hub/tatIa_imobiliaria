from src.regras.financeiro import calcular_parcela_price, calcular_parcela_sac

# Simulação: 217.000 financiado, 10% a.a., 420 meses
print("Price:", calcular_parcela_price(217000, 0.10, 420))
print("SAC:", calcular_parcela_sac(217000, 0.10, 420))