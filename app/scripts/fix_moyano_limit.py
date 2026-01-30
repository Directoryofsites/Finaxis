from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.empresa import Empresa

def fix_moyano():
    db: Session = SessionLocal()
    try:
        # Buscar por NIT (del screenshot del usuario)
        nit_moyano = "4548878787" 
        empresa = db.query(Empresa).filter(Empresa.nit == nit_moyano).first()
        
        if empresa:
            print(f"Empresa encontrada: {empresa.razon_social} (ID: {empresa.id})")
            print(f"Límite actual: {empresa.limite_registros_mensual}")
            
            # Actualizamos ambos por seguridad
            empresa.limite_registros = 5000
            empresa.limite_registros_mensual = 5000
            db.add(empresa)
            db.commit()
            print("✅ Límite actualizado exitosamente a 5000.")
        else:
            print("❌ No se encontró la empresa con NIT 4548878787.")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    fix_moyano()
