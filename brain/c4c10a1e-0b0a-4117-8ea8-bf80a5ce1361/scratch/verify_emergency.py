import os
import sys

sys.path.append(os.path.abspath('c:/ContaPY2'))
from app.core.database import SessionLocal
from app.services.cartera import get_facturas_pendientes_por_tercero
from app.models.documento import Documento

db = SessionLocal()
emp_id = 134
tercero_id = 2326

print(f"--- VERIFICACIÓN DE EMERGENCIA PARA TERCERO {tercero_id} (Empresa {emp_id}) ---")
pendientes = get_facturas_pendientes_por_tercero(db, tercero_id, emp_id)

print(f"Total encontrados: {len(pendientes)}")
for p in pendientes:
    # EL KEY ES 'tipo_documento'
    print(f"Doc: {p['tipo_documento']} #{p['numero']} | Valor: {p['valor_total']} | Aplicado: {p['total_aplicado']} | Saldo: {p['saldo_pendiente']}")

db.close()
