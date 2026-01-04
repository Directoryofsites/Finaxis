import sys
import os
sys.path.append(os.getcwd())

from app.core.database import SessionLocal
from app.models.plan_cuenta import PlanCuenta

def create_cash_accounts():
    db = SessionLocal()
    empresa_id = 1
    
    print("--- CREANDO CUENTAS DEL GRUPO 11 ---")
    
    # Lista de cuentas mínimas requeridas
    cuentas_a_crear = [
        {"codigo": "1105", "nombre": "CAJA", "nivel": 2, "padre": None},
        {"codigo": "110505", "nombre": "CAJA GENERAL", "nivel": 4, "padre": "1105"},
        {"codigo": "1110", "nombre": "BANCOS", "nivel": 2, "padre": None},
        {"codigo": "111005", "nombre": "MONEDA NACIONAL", "nivel": 4, "padre": "1110"},
    ]

    for data in cuentas_a_crear:
        existe = db.query(PlanCuenta).filter_by(
            empresa_id=empresa_id, 
            codigo=data["codigo"]
        ).first()
        
        if not existe:
            print(f"Creando cuenta: {data['codigo']} - {data['nombre']}")
            nueva_cuenta = PlanCuenta(
                empresa_id=empresa_id,
                codigo=data["codigo"],
                nombre=data["nombre"],
                nivel=data["nivel"],
                permite_movimiento=(len(data["codigo"]) > 4), # Solo las de 6+ dígitos
                es_cuenta_de_ingresos=False,
                is_bank_reconciliation_account=True if data["codigo"].startswith("1110") else False
            )
            db.add(nueva_cuenta)
        else:
            print(f"Cuenta ya existe: {data['codigo']}")
    
    db.commit()
    print("Proceso finalizado. Cuentas creadas exitosamente.")

if __name__ == "__main__":
    create_cash_accounts()
