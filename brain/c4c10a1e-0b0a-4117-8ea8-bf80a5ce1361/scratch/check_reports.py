from app.core.database import SessionLocal
from app.services.documento import generate_auxiliar_por_facturas, generate_estado_cuenta_cliente_report
from datetime import date

db = SessionLocal()
empresa_id = 134
tercero_id = 2326

# Verificar Auxiliar
print("--- VERIFICANDO AUXILIAR DE CARTERA ---")
res_aux = generate_auxiliar_por_facturas(db, empresa_id, tercero_id, date(2026,4,1), date(2026,4,17))
print(f"Total Facturas/Notas: {len(res_aux['facturas'])}")
for f in res_aux['facturas']:
    print(f"  - {f['documento']} | Valor: {f['valor_original']} | Saldo: {f['saldo_factura']}")

# Verificar Estado de Cuenta
print("\n--- VERIFICANDO ESTADO DE CUENTA CLIENTE ---")
res_est = generate_estado_cuenta_cliente_report(db, empresa_id, tercero_id, date(2026,4,17))
print(f"Total Items: {len(res_est['facturas'])}")
for f in res_est['facturas']:
    print(f"  - {f['tipo_documento']} #{f['numero']} | Saldo: {f['abonos']}") # abonos is actually saldo in the struct? Wait, I need to check the struct.

db.close()
