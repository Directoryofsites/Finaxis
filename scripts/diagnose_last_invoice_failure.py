
import sys
import os
from sqlalchemy import text

sys.path.append('c:\\ContaPY2')

from app.core.database import SessionLocal
from app.models.documento import Documento
from app.models.empresa import Empresa
from app.models.configuracion_fe import ConfiguracionFE

def diagnose():
    session = SessionLocal()
    try:
        # 1. Buscar el último documento creado
        last_doc = session.query(Documento).order_by(Documento.id.desc()).first()
        
        if not last_doc:
            print("No se encontraron documentos en el sistema.")
            return

        print(f"--- Último Documento ID: {last_doc.id} ---")
        print(f"Número: {last_doc.numero}")
        print(f"Empresa ID: {last_doc.empresa_id}")
        print(f"Tercero: {last_doc.beneficiario_id} (NIT: {last_doc.beneficiario.nit if last_doc.beneficiario else 'N/A'})")
        print(f"Estado DIAN: {last_doc.dian_estado}")
        print(f"Error DIAN: {last_doc.dian_error}")
        
        # 2. Verificar Empresa
        empresa = session.query(Empresa).get(last_doc.empresa_id)
        if empresa:
            print(f"Nombre Empresa: {empresa.razon_social}")
        else:
            print("❌ La empresa asociada al documento no existe.")
            
        # 3. Verificar Configuración FE
        config = session.query(ConfiguracionFE).filter_by(empresa_id=last_doc.empresa_id).first()
        
        if not config:
            print("❌ NO existe registro en tabla 'configuracion_fe' para esta empresa.")
        else:
            print(f"✅ Existe registro Configuración FE (ID: {config.id})")
            print(f"   Habilitado: {config.habilitado}")
            print(f"   Ambiente: {config.ambiente}")
            
            if not config.api_token:
                print("❌ ERROR: El campo 'api_token' está VACÍO o NULO.")
            else:
                print(f"✅ api_token presente: {config.api_token[:20]}...")

    except Exception as e:
        print(f"Excepción: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    diagnose()
