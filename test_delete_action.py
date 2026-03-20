import sys
import os

sys.path.insert(0, r"C:\ContaPY2")

from app.core.database import SessionLocal
from app.models.plan_cuenta import PlanCuenta
from app.services.plan_cuenta import ejecutar_depuracion_jerarquica
from fastapi import HTTPException

def test_deletion():
    db = SessionLocal()
    try:
        from app.models.empresa import Empresa
        empresa = db.query(Empresa).first()
        if not empresa: return
        empresa_id = empresa.id
        
        # 1. Crear cuentas dummy
        c1 = PlanCuenta(empresa_id=empresa_id, codigo="9999", nombre="Test 1", nivel=1)
        db.add(c1)
        db.commit()
        db.refresh(c1)
        
        c2 = PlanCuenta(empresa_id=empresa_id, codigo="999905", nombre="Test 2", nivel=2, cuenta_padre_id=c1.id)
        db.add(c2)
        db.commit()
        db.refresh(c2)
        
        ids_a_eliminar = [c1.id, c2.id]
        print(f"Borrando IDs: {ids_a_eliminar}")
        
        try:
            res = ejecutar_depuracion_jerarquica(db, ids_a_eliminar, empresa_id)
            print("Resultado:", res)
        except Exception as e:
            print("Error al borrar:", e)
            
    finally:
        db.close()

if __name__ == "__main__":
    test_deletion()
