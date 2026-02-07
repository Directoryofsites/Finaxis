
import sys
import json
sys.path.append('c:\\ContaPY2')

from app.core.database import SessionLocal
from app.models.configuracion_fe import ConfiguracionFE
from app.models.empresa import Empresa

def apply_sandbox_to_all():
    session = SessionLocal()
    try:
        empresas = session.query(Empresa).all()
        print(f"Encontradas {len(empresas)} empresas. Aplicando credenciales Sandbox...")

        creds_sandbox = {
            "client_id": "a1003ed4-93cc-4980-89ab-1a181b031918",
            "client_secret": "iO7V0w287m87yGZ3JOlWgR5ytGsFSXaIkGcOMaJd",
            "username": "sandbox@factus.com.co",
            "password": "sandbox2024%"
        }
        creds_json = json.dumps(creds_sandbox)

        count = 0
        for emp in empresas:
            config = session.query(ConfiguracionFE).filter_by(empresa_id=emp.id).first()
            
            if not config:
                config = ConfiguracionFE(
                    empresa_id=emp.id,
                    proveedor='FACTUS',
                    ambiente='PRUEBAS',
                    habilitado=True,
                    api_token=creds_json
                )
                session.add(config)
                count += 1
            else:
                # Solo sobrescribimos si no tiene token o si es explícitamente una empresa de prueba
                # Para este caso "bruto", sobrescribimos si está vacío o si queremos forzar.
                # El usuario dijo: "¿Y si necesitas hacer pruebas con otras empresas? ... todas son de prueba"
                # Así que forzaremos Sandbox en TODAS para asegurar.
                config.ambiente = 'PRUEBAS'
                config.habilitado = True
                config.api_token = creds_json
                count += 1
        
        session.commit()
        print(f"✅ Se actualizaron/crearon credenciales Sandbox para {count} empresas.")

    except Exception as e:
        print(f"❌ Error: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    apply_sandbox_to_all()
