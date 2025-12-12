import sys
import os

# Permitir importaciones desde la raíz del proyecto
sys.path.append(os.getcwd())

from app.core.database import SessionLocal, engine
from app.models.empresa import Empresa
from sqlalchemy import text

def clean_duplicates():
    db = SessionLocal()
    try:
        print("--- BUSCANDO DUPLICADOS DE EMPRESA DEMO ---")
        
        # Buscar todas las empresas con el NIT de demostración
        nit_demo = "800000001-1"
        empresas = db.query(Empresa).filter(Empresa.nit == nit_demo).order_by(Empresa.id.asc()).all()
        
        count = len(empresas)
        print(f"Encontradas {count} 'Empresas de Demostración'.")
        
        if count <= 1:
            print("No hay duplicados que eliminar.")
            return

        # La primera (la más vieja) es la original que conservaremos
        original = empresas[0]
        print(f"Conservando ORIGINAL: ID {original.id} - {original.razon_social}")
        
        # Las demás se eliminan
        duplicados = empresas[1:]
        
        for dup in duplicados:
            print(f"Eliminando DUPLICADO: ID {dup.id}...")
            
            # 1. Eliminar Usuarios asociados
            db.execute(text("DELETE FROM usuarios WHERE empresa_id = :emp_id"), {"emp_id": dup.id})
            print(f"   - Usuarios eliminados.")

            # 2. Eliminar PUC (Cuentas) asociadas
            db.execute(text("DELETE FROM cuentas WHERE empresa_id = :emp_id"), {"emp_id": dup.id})
            print(f"   - PUC eliminado.")

            # 3. Eliminar Terceros asociados (por si acaso)
            try:
                db.execute(text("DELETE FROM terceros WHERE empresa_id = :emp_id"), {"emp_id": dup.id})
            except:
                pass # Puede que no exista la tabla o no tenga datos

            # 4. Finalmente eliminar la empresa
            db.delete(dup)
            print(f"   - Empresa eliminada.")
            
        db.commit()
        print("Limpieza completada exitosamente.")
        
    except Exception as e:
        print(f"Error al limpiar: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    clean_duplicates()
