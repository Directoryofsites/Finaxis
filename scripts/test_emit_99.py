import sys
import os
import json
import uuid

sys.path.append('c:\\ContaPY2')

from app.core.database import SessionLocal
from app.models.documento import Documento
from app.services.factura_electronica_service import factura_electronica_service

def test_emit_number_99():
    session = SessionLocal()
    try:
        # Usar el documento 12254 (el que falló con No 24) pero cambiarle el número temporalmente para la prueba
        doc = session.query(Documento).get(12254)
        if not doc:
            print("No se encontró doc 12254")
            return
            
        original_num = doc.numero
        doc.numero = 99 # Probar con 99
        session.commit()
        
        print(f"Intentando emitir documento {doc.id} con número {doc.numero}...")
        res = factura_electronica_service.emitir_factura(session, doc.id, 1) # usuario 1
        
        print("Resultado Emisión:")
        print(json.dumps(res, indent=2))
        
        # Restaurar número original para no dañar la DB
        doc.numero = original_num
        session.commit()
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    test_emit_number_99()
