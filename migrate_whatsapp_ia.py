from sqlalchemy import text
from app.core.database import engine

def upgrade():
    with engine.begin() as conn:
        print("--- Iniciando migracion de base de datos ---")
        
        try:
            # 1. Tabla Usuarios: Columna whatsapp_number
            result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='usuarios' AND column_name='whatsapp_number';"))
            if not result.fetchone():
                conn.execute(text("ALTER TABLE usuarios ADD COLUMN whatsapp_number VARCHAR(50);"))
                conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ux_usuarios_whatsapp_number ON usuarios (whatsapp_number);"))
                print("OK: Columna 'whatsapp_number' agregada a 'usuarios'.")
            else:
                print("INFO: La columna 'whatsapp_number' ya existe.")

            # 2. Tabla Empresas: Columnas de IA
            columns_to_add = [
                ("limite_mensajes_ia_mensual", "INTEGER DEFAULT 0"),
                ("consumo_mensajes_ia_actual", "INTEGER DEFAULT 0"),
                ("fecha_reinicio_cuota_ia", "DATE")
            ]
            
            for col_name, col_type in columns_to_add:
                result = conn.execute(text(f"SELECT column_name FROM information_schema.columns WHERE table_name='empresas' AND column_name='{col_name}';"))
                if not result.fetchone():
                    conn.execute(text(f"ALTER TABLE empresas ADD COLUMN {col_name} {col_type};"))
                    print(f"OK: Columna '{col_name}' agregada a 'empresas'.")
                else:
                    print(f"INFO: La columna '{col_name}' ya existe.")

            print("\n!!! Migracion completada con exito !!!")
            
        except Exception as e:
            print(f"❌ Error durante la migración: {e}")

if __name__ == "__main__":
    upgrade()
