from app.core.database import SessionLocal
from app.models.empresa import Empresa
from app.services.consumo_service import verificar_disponibilidad, registrar_consumo, SaldoInsuficienteException
from datetime import datetime

def verify():
    db = SessionLocal()
    try:
        print("--- VERIFICACIÓN DE CONSUMO PELAEZ HERMANOS ---")
        emp = db.query(Empresa).filter(Empresa.nit == '5456748787').first()
        
        if not emp:
            print("ERROR: Empresa no encontrada")
            return

        print(f"Empresa: {emp.razon_social} (ID: {emp.id})")
        print(f"Created At: {emp.created_at}")
        print(f"Fecha Inicio Operaciones: {emp.fecha_inicio_operaciones}")
        
        # 1. Verificar Disponibilidad
        print("\n[TEST 1] Verificar Disponibilidad (1 registro)...")
        try:
            res = verificar_disponibilidad(db, emp.id, 1)
            print(f"RESULTADO: {'OK (Disponible)' if res else 'FAIL (No disponible)'}")
        except Exception as e:
            print(f"RESULTADO: EXCEPTION - {e}")

        # 2. Simular Consumo Real
        print("\n[TEST 2] Simular Consumo (1 registro)...")
        try:
            # Usamos un doc ID ficticio o None si lo permite la lógica (aunque registrar_consumo pide doc_id)
            # Pasamos None y fecha actual
            registrar_consumo(db, emp.id, 1, documento_id=999999, fecha_doc=datetime.now())
            print("RESULTADO: OK (Consumo registrado sin error)")
        except SaldoInsuficienteException as e:
            print(f"RESULTADO: FALLO - Saldo Insuficiente: {e}")
        except Exception as e:
            print(f"RESULTADO: ERROR CRITICO - {e}")
            
    except Exception as e:
        print(f"Global Error: {e}")
    finally:
        db.rollback() # Siempre rollback para no afectar datos reales
        db.close()
        print("\n--- FIN DEL TEST (Rollback aplicado) ---")

if __name__ == "__main__":
    verify()
