from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.services import empresa as empresa_service
from app.services import usuario as usuario_service
from app.models import empresa as empresa_model
from app.models import usuario as usuario_model
from sqlalchemy import or_, text

def remove_anomaly():
    db: Session = SessionLocal()
    try:
        print("--- BORRADO QUIRURGICO DE ANOMALIAS (INTENTO 6) ---")
        
        target_empresa_id = 145
        target_user_id = 31

        # PASO 1: DESVINCULAR OWNER
        if target_empresa_id:
            print(f"1. Desvinculando Owner de Empresa {target_empresa_id}...")
            try:
                db.execute(text("UPDATE empresas SET owner_id = NULL WHERE id = :eid"), {"eid": target_empresa_id})
                db.commit()
            except Exception as e:
                db.rollback()
                print(f"   [WARN] Falló desvincular owner: {e}")

        # PASO 2: DESVINCULAR USUARIOS (Antes de borrar tablas que puedan referenciarlos)
        if target_empresa_id:
            print(f"2. Desvinculando Usuarios de Empresa {target_empresa_id}...")
            try:
                db.execute(text("UPDATE usuarios SET empresa_id = NULL WHERE empresa_id = :eid"), {"eid": target_empresa_id})
                db.commit()
            except Exception as e:
                db.rollback()
                print(f"   [WARN] Falló desvincular usuarios: {e}")

        # PASO 3: LIMPIEZA MANUAL DE DEPENDENCIAS
        if target_empresa_id:
            print(f"3. Limpiando dependencias de Empresa {target_empresa_id}...")
            
            tables = [
                "productos", 
                "tasas_impuesto",
                "usuario_empresas", 
                "usuario_roles",
                "plan_cuentas", 
                "terceros",
                "centros_costo", 
                "tipos_documento",
                "periodos_contables_cerrados",
                "log_operaciones", 
                "documentos", 
                "documentos_eliminados"
            ]
            
            for t in tables:
                try:
                    db.execute(text(f"DELETE FROM {t} WHERE empresa_id = :eid"), {"eid": target_empresa_id})
                    db.commit() # Commit parcial para aislar errores
                    print(f"   - {t} limpiado.")
                except Exception as e:
                    db.rollback()
                    # Algunos fallarán si no tienen columna empresa_id, es normal
                    print(f"   [INFO] Saltando {t}: {e}")
            
            # PASO 4: BORRAR EMPRESA
            print(f"4. Borrando Empresa {target_empresa_id}...")
            try:
                db.execute(text("DELETE FROM empresas WHERE id = :eid"), {"eid": target_empresa_id})
                db.commit()
                print("   [OK] Empresa borrada.")
            except Exception as e:
                db.rollback()
                print(f"   [ERROR] Falló borrar empresa: {e}")

        # PASO 5: BORRAR USUARIO
        if target_user_id:
            print(f"5. Borrando Usuario {target_user_id}...")
            try:
                # Limpiezas previas para el user
                db.execute(text("DELETE FROM usuario_roles WHERE usuario_id = :uid"), {"uid": target_user_id})
                db.execute(text("DELETE FROM usuario_empresas WHERE usuario_id = :uid"), {"uid": target_user_id})
                db.execute(text("UPDATE plan_cuentas SET created_by = NULL WHERE created_by = :uid"), {"uid": target_user_id})
                db.commit()
                
                # Borrar user
                db.execute(text("DELETE FROM usuarios WHERE id = :uid"), {"uid": target_user_id})
                db.commit()
                print("   [OK] Usuario borrado.")
            except Exception as e:
                db.rollback()
                print(f"   [ERROR] Falló borrar usuario: {e}")
                
    except Exception as e:
        print(f"Error general: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    remove_anomaly()
