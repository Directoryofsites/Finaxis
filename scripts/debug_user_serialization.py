# scripts/debug_user_serialization.py
import sys
import os
from sqlalchemy.orm import Session

sys.path.append(os.getcwd())

from app.core.database import SessionLocal
from app.models.usuario import Usuario
from app.models.empresa import Empresa
from app.schemas.usuario import User as UserSchema

def debug_user(empresa_id):
    db = SessionLocal()
    try:
        # 1. Buscar usuario de la empresa
        user = db.query(Usuario).filter(Usuario.empresa_id == empresa_id).first()
        if not user:
            print(f"No user found for company {empresa_id}")
            # Buscar el owner
            empresa = db.query(Empresa).filter(Empresa.id == empresa_id).first()
            if empresa and empresa.owner_id:
                user = db.query(Usuario).filter(Usuario.id == empresa.owner_id).first()
                print(f"Found owner: {user.email}")
            else:
                return

        print(f"User found: {user.email}")
        
        # 2. Simular get_current_user context switch logic
        user.empresa_id = empresa_id
        empresa_context = db.query(Empresa).filter(Empresa.id == empresa_id).first()
        user.empresa = empresa_context
        
        print(f"Empresa context: {empresa_context.razon_social}")
        print(f"Is Lite Mode (DB): {empresa_context.is_lite_mode}")
        
        # 3. Serializar con Pydantic
        user_pydantic = UserSchema.from_orm(user)
        print("--- SERIALIZED DATA ---")
        print(user_pydantic.model_dump_json(indent=2))
        
        # Verificar campo
        if user_pydantic.empresa and user_pydantic.empresa.is_lite_mode:
             print("\nSUCCESS: is_lite_mode is TRUE in serialization.")
        else:
             print("\nFAILURE: is_lite_mode is False/None in serialization.")

    except Exception as e:
        print(f"ERROR: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    debug_user(132) # ID de empresa "Pruebas" convertida
