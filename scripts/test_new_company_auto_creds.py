
import sys
sys.path.append('c:\\ContaPY2')

from app.core.database import SessionLocal
from app.services.empresa import create_empresa_con_usuarios
from app.schemas.empresa import EmpresaConUsuariosCreate
from app.schemas.usuario import UserCreateInCompany
import uuid

def test_auto_creds():
    db = SessionLocal()
    try:
        # Datos de prueba únicos
        random_str = str(uuid.uuid4())[:8]
        nit_fake = f"999{random_str}" # NIT único
        email_fake = f"test_{random_str}@demo.com"
        
        print(f"--- Iniciando Prueba de Creación Automática ---")
        print(f"Creando empresa 'Empresa Test {random_str}' NIT {nit_fake}...")
        
        # Payload de creación (Schema)
        empresa_in = EmpresaConUsuariosCreate(
            razon_social=f"Empresa Test {random_str}",
            nit=nit_fake,
            email=email_fake,
            modo_operacion="STANDARD",
            usuarios=[
                UserCreateInCompany(email=email_fake, password="Password123!", nombre="Test User", roles_ids=[1])
            ]
        )
        
        # Llamar al servicio modificado
        nueva_empresa = create_empresa_con_usuarios(db=db, empresa_data=empresa_in)
        print(f"Empresa creada con ID: {nueva_empresa.id}")
        
        # VERIFICACIÓN
        config = db.query(ConfiguracionFE).filter_by(empresa_id=nueva_empresa.id).first()
        
        if config:
            print("✅ ÉXITO: ConfiguracionFE se creó automáticamente.")
            print(f"   Ambiente: {config.ambiente}")
            print(f"   Habilitado: {config.habilitado}")
            if config.api_token and "sandbox" in config.api_token:
                print("✅ ÉXITO: El token contiene credenciales de Sandbox.")
            else:
                print("❌ FALLO: El token NO parece ser de Sandbox.")
        else:
            print("❌ FALLO: No se creó ConfiguracionFE automáticamente.")
            
    except Exception as e:
        print(f"❌ Excepción durante la prueba: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    test_auto_creds()
