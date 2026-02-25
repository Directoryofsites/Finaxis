import os
import sys

# Agregar la raíz del proyecto para importaciones
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.core.database import SessionLocal, engine
from app.models.empresa import Empresa # Ensure models are loaded

def add_ia_columns():
    db = SessionLocal()
    try:
        print("Iniciando migración manual para campos de cuotas de Inteligencia Artificial...")
        
        # 1. limite_mensajes_ia_mensual
        try:
            db.execute(text("ALTER TABLE empresas ADD COLUMN limite_mensajes_ia_mensual INTEGER NOT NULL DEFAULT 0;"))
            print("[\u2713] Columna 'limite_mensajes_ia_mensual' agregada correctamente.")
        except Exception as e:
            print(f"[-] Omitiendo 'limite_mensajes_ia_mensual': Ya existe o error ({str(e).splitlines()[0]})")
            db.rollback()
            
        # 2. consumo_mensajes_ia_actual
        try:
            db.execute(text("ALTER TABLE empresas ADD COLUMN consumo_mensajes_ia_actual INTEGER NOT NULL DEFAULT 0;"))
            print("[\u2713] Columna 'consumo_mensajes_ia_actual' agregada correctamente.")
        except Exception as e:
            print(f"[-] Omitiendo 'consumo_mensajes_ia_actual': Ya existe o error ({str(e).splitlines()[0]})")
            db.rollback()

        # 3. fecha_reinicio_cuota_ia
        try:
            db.execute(text("ALTER TABLE empresas ADD COLUMN fecha_reinicio_cuota_ia DATE;"))
            print("[\u2713] Columna 'fecha_reinicio_cuota_ia' agregada correctamente.")
        except Exception as e:
            print(f"[-] Omitiendo 'fecha_reinicio_cuota_ia': Ya existe o error ({str(e).splitlines()[0]})")
            db.rollback()

        db.commit()
        print("\n\u2728 Migración de BD para Cuotas de IA finalizada exitosamente.")
        
    except Exception as e:
        print(f"\n\u274c Error crítico durante la migración: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    add_ia_columns()
