import os
import sys

sys.path.append(os.path.abspath('c:/ContaPY2'))
from app.core.database import SessionLocal
from app.services.cartera import get_facturas_pendientes_por_tercero
from app.models.documento import Documento

db = SessionLocal()
tercero_id = 2326
empresa_id = 134

print(f"--- VERIFICACIÓN FINAL: NOTA DÉBITO EN REPORTE ---")
pendientes = get_facturas_pendientes_por_tercero(db, tercero_id, empresa_id)

encontrado = False
for p in pendientes:
    if "NOTA DEBITO" in p['numero'].upper():
        print(f"ENCONTRADA: {p['numero']} | Saldo: {p['saldo_pendiente']}")
        encontrado = True

if not encontrado:
    print("No se encontró ninguna Nota Débito en el reporte de pendientes.")
    # Ver todos por si acaso
    print(f"Total pendientes: {len(pendientes)}")
    for p in pendientes[:5]:
        print(f"  - {p['numero']} | {p['saldo_pendiente']}")

db.close()
