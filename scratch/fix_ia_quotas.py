from app.core.database import SessionLocal
from app.models.empresa import Empresa

def fix_quota():
    db = SessionLocal()
    try:
        # Buscamos la empresa 222 o cualquier empresa que no tenga cuota
        empresas = db.query(Empresa).all()
        for emp in empresas:
            if emp.limite_mensajes_ia_mensual is None or emp.limite_mensajes_ia_mensual <= 0:
                print(f"Habilitando cuota IA para {emp.razon_social} (ID: {emp.id})")
                emp.limite_mensajes_ia_mensual = 100
                emp.consumo_mensajes_ia_actual = 0
        
        db.commit()
        print("Cuotas actualizadas correctamente.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    fix_quota()
