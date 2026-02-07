
import sys
sys.path.append('c:\\ContaPY2')

from app.core.database import SessionLocal
from app.models.configuracion_fe import ConfiguracionFE
import json

def fix_company_218():
    session = SessionLocal()
    try:
        empresa_id = 218
        print(f"Reparando configuración FE para empresa {empresa_id}...")
        
        config = session.query(ConfiguracionFE).filter_by(empresa_id=empresa_id).first()
        
        creds_sandbox = {
            "client_id": "a1003ed4-93cc-4980-89ab-1a181b031918",
            "client_secret": "iO7V0w287m87yGZ3JOlWgR5ytGsFSXaIkGcOMaJd",
            "username": "sandbox@factus.com.co",
            "password": "sandbox2024%"
        }
        
        if not config:
            print("Configuración no encontrada. Creando nueva...")
            new_config = ConfiguracionFE(
                empresa_id=empresa_id,
                proveedor='FACTUS',
                ambiente='PRUEBAS',
                habilitado=True,
                api_token=json.dumps(creds_sandbox)
            )
            session.add(new_config)
        else:
            print("Configuración existente encontrada. Actualizando...")
            config.proveedor = 'FACTUS'
            config.ambiente = 'PRUEBAS'
            config.habilitado = True
            config.api_token = json.dumps(creds_sandbox)
            
        session.commit()
        print("✅ Reparación completada exitosamente.")

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    fix_company_218()
