import sys
import os
import traceback

sys.path.insert(0, r"C:\ContaPY2")

from app.core.database import SessionLocal
from app.models.plan_cuenta import PlanCuenta
from app.services.plan_cuenta import ejecutar_depuracion_jerarquica

def test_deletion_5177():
    db = SessionLocal()
    try:
        from app.models.empresa import Empresa
        
        cuenta = db.query(PlanCuenta).filter(
            PlanCuenta.codigo.like("5177%")
        ).first()
        
        if not cuenta:
            print("No hay 5177")
            return
            
        empresa_id = cuenta.empresa_id
        
        # Obtenemos _identificar_cuentas_borrables
        from app.services.plan_cuenta import _identificar_cuentas_borrables
        ids_a_eliminar, ids_a_conservar = _identificar_cuentas_borrables(db, cuenta.id, empresa_id)
        
        print(f"Borrando IDs: {ids_a_eliminar}")
        if not ids_a_eliminar:
            print("nada para borrar")
            return
            
        try:
            res = ejecutar_depuracion_jerarquica(db, list(ids_a_eliminar), empresa_id)
            print("Resultado:", res)
        except Exception as e:
            print("Error al borrar:")
            traceback.print_exc()
            
    finally:
        db.close()

if __name__ == "__main__":
    test_deletion_5177()
