import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal, engine
from sqlalchemy import text
from app.models.propiedad_horizontal.campo_personalizado import PHCampoPersonalizado

def run_migration():
    print("🚀 Iniciando migración de Metadatos Dinámicos...")
    
    with engine.connect() as conn:
        # 1. Agregar columna a ph_unidades
        try:
            print("1. Intentando añadir columna 'metadatos_extra' a 'ph_unidades'...")
            conn.execute(text("ALTER TABLE ph_unidades ADD COLUMN IF NOT EXISTS metadatos_extra JSONB DEFAULT '{}'::jsonb;"))
            conn.commit()
            print("   ✅ Columna 'metadatos_extra' lista.")
        except Exception as e:
            print(f"   ⚠️ Nota: {e}")

        # 2. Crear tabla de campos personalizados
        try:
            print("2. Creando tabla 'ph_campos_personalizados'...")
            PHCampoPersonalizado.__table__.create(engine, checkfirst=True)
            print("   ✅ Tabla 'ph_campos_personalizados' lista.")
        except Exception as e:
            print(f"   ❌ Error creando tabla: {e}")

    print("\n✨ Migración completada exitosamente.")

if __name__ == "__main__":
    run_migration()
