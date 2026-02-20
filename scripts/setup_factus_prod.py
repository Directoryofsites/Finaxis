
import sys
import json
import os

# Ajustar path para importar módulos de la app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.database import SessionLocal
from app.models.configuracion_fe import ConfiguracionFE
from app.models.empresa import Empresa

def configure_factus_prod(empresa_id, client_id, client_secret, username, password):
    session = SessionLocal()
    try:
        print(f"Configurando Factus PRODUCCIÓN para Empresa ID {empresa_id}...")
        
        empresa = session.query(Empresa).get(empresa_id)
        if not empresa:
            print(f"Error: No existe la empresa con ID {empresa_id}")
            return
            
        config = session.query(ConfiguracionFE).filter_by(empresa_id=empresa_id).first()
        if not config:
            print("Creando nuevo registro de configuración FE...")
            config = ConfiguracionFE(empresa_id=empresa_id)
            session.add(config)
            
        # Almacenar credenciales en api_token como JSON
        creds = {
            "client_id": client_id,
            "client_secret": client_secret,
            "username": username,
            "password": password
        }
        
        config.proveedor = 'FACTUS'
        config.ambiente = 'PRODUCCION' # IMPORTANTE: Cambiar a producción
        config.api_token = json.dumps(creds)
        config.habilitado = True
        
        # Seteamos URLs de Factus Producción si no están (FactusProvider las maneja internamente, pero por si acaso)
        config.api_url = "https://api.factus.com.co"
        
        session.commit()
        print(f"✅ Éxito: Empresa '{empresa.razon_social}' configurada para Factus Producción.")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    print("--- ASISTENTE DE CONFIGURACIÓN FACTUS PRODUCCIÓN ---")
    emp_id = input("ID de la Empresa (ej: 140 para la Iglesia): ").strip()
    c_id = input("Factus Client ID: ").strip()
    c_secret = input("Factus Client Secret: ").strip()
    u_name = input("Factus Username (Email): ").strip()
    passw = input("Factus Password: ").strip()
    
    if all([emp_id, c_id, c_secret, u_name, passw]):
        configure_factus_prod(int(emp_id), c_id, c_secret, u_name, passw)
    else:
        print("Datos incompletos. Abortando.")
