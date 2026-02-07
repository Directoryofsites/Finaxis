
import sys
sys.path.append('c:\\ContaPY2')
from sqlalchemy import text
from app.core.database import SessionLocal

def migrate_db():
    session = SessionLocal()
    try:
        print("Iniciando migración de esquema para Descuentos...")
        
        # 1. Movimientos Contables (Descuento por Línea)
        # Agregamos descuento_tasa (0-100) y descuento_valor (absoluto)
        try:
            session.execute(text("ALTER TABLE movimientos_contables ADD COLUMN IF NOT EXISTS descuento_tasa NUMERIC(5, 2) DEFAULT 0"))
            session.execute(text("ALTER TABLE movimientos_contables ADD COLUMN IF NOT EXISTS descuento_valor NUMERIC(15, 2) DEFAULT 0"))
            print("Tabla movimientos_contables actualizada.")
        except Exception as e:
            print(f"Error alterando movimientos_contables (quizas ya existen): {e}")

        # 2. Documentos (Cabecera Global)
        # Agregamos descuento_global_valor y cargos_globales_valor (recargos)
        try:
            session.execute(text("ALTER TABLE documentos ADD COLUMN IF NOT EXISTS descuento_global_valor NUMERIC(15, 2) DEFAULT 0"))
            session.execute(text("ALTER TABLE documentos ADD COLUMN IF NOT EXISTS cargos_globales_valor NUMERIC(15, 2) DEFAULT 0"))
            print("Tabla documentos actualizada.")
        except Exception as e:
             print(f"Error alterando documentos (quizas ya existen): {e}")
             
        session.commit()
        print("Migracion finalizada exitosamente.")

    except Exception as e:
        session.rollback()
        print(f"Error CRITICO en migracion: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    migrate_db()
