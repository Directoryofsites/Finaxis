
import sys
from app.core.database import SessionLocal
from app.services import plan_cuenta

def test_saldo():
    db = SessionLocal()
    try:
        # Assuming empresa_id=1 for testing
        empresa_id = 1
        cuentas = plan_cuenta.get_plan_cuentas_flat(db, empresa_id=empresa_id)
        
        print(f"Total cuentas encontradas: {len(cuentas)}")
        
        has_saldo = False
        for cuenta in cuentas:
            if hasattr(cuenta, 'saldo'):
                has_saldo = True
                if cuenta.saldo != 0.0:
                    print(f"Cuenta {cuenta.codigo} - {cuenta.nombre} tiene saldo: {cuenta.saldo}")
        
        if has_saldo:
            print("VERIFICACIÓN EXITOSA: El campo 'saldo' está presente en los objetos.")
        else:
            print("ERROR: El campo 'saldo' NO se encontró en los objetos.")
            
    except Exception as e:
        print(f"Error durante la prueba: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    test_saldo()
