
import sys
import os
import json

sys.path.append('c:\\ContaPY2')

from app.core.database import SessionLocal
from app.models.configuracion_fe import ConfiguracionFE
from app.models.empresa import Empresa

def setup_creds():
    session = SessionLocal()
    try:
        # Buscar empresa Moyano o la que estemos usando
        # En el output anterior vimos "Moyano"
        empresa = session.query(Empresa).filter(Empresa.razon_social.ilike('%Moyano%')).first()
        
        if not empresa:
            print("No encontré la empresa Moyano. Buscando ID 146...")
            empresa = session.query(Empresa).get(146)
            
        if not empresa:
            print("No encontré empresa para configurar.")
            return

        print(f"Configurando para: {empresa.razon_social} (ID: {empresa.id})")
        
        config = session.query(ConfiguracionFE).filter_by(empresa_id=empresa.id).first()
        if not config:
            print("No existe ConfiguracionFE. Creando...")
            config = ConfiguracionFE(empresa_id=empresa.id, proveedor='FACTUS', ambiente='PRUEBAS', habilitado=True)
            session.add(config)
        
        # CREDENCIALES SANDBOX (Tomadas del historial)
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
        print("✅ Credenciales Sandbox guardadas en api_token.")
        
    except Exception as e:
        print(f"Error: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    setup_creds()
