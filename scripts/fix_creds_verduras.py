
import sys
import json
sys.path.append('c:\\ContaPY2')

from app.core.database import SessionLocal
from app.models.configuracion_fe import ConfiguracionFE
from app.models.empresa import Empresa

def fix_creds():
    session = SessionLocal()
    try:
        empresa_id = 134 # Verduras la 21
        print(f"Reparando credenciales para Empresa ID {empresa_id}...")
        
        config = session.query(ConfiguracionFE).filter_by(empresa_id=empresa_id).first()
        if not config:
            print("Creando registro ConfiguracionFE...")
            config = ConfiguracionFE(empresa_id=empresa_id, proveedor='FACTUS', ambiente='PRUEBAS', habilitado=True)
            session.add(config)
        
        # Credenciales Sandbox
        creds = {
            "client_id": "a1003ed4-93cc-4980-89ab-1a181b031918",
            "client_secret": "iO7V0w287m87yGZ3JOlWgR5ytGsFSXaIkGcOMaJd",
            "username": "sandbox@factus.com.co",
            "password": "sandbox2024%"
        }
        
        config.api_token = json.dumps(creds)
        config.ambiente = 'PRUEBAS'
        config.habilitado = True
        
        session.commit()
        print("[OK] Credenciales Sandbox inyectadas correctamente en ID 134.")
        
    except Exception as e:
        print(f"[ERROR] {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    fix_creds()
