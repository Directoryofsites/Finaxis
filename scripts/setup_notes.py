import sys
import os
sys.path.append(os.getcwd())

from app.core.database import SessionLocal
from app.models.tipo_documento import TipoDocumento
from app.models.empresa import Empresa

def setup_note_types():
    db = SessionLocal()
    try:
        # 1. Obtener Empresa (Asumimos ID 1 o la primera que encontremos para este script de setup)
        # Idealmente esto debería correrse para cada empresa o ser parte de un seed general.
        empresas = db.query(Empresa).all()
        if not empresas:
            print("No hay empresas registradas.")
            return

        for empresa in empresas:
            print(f"Configurando tipos de documento para empresa: {empresa.razon_social} (ID: {empresa.id})")
            
            # NOTA CRÉDITO
            nc_exists = db.query(TipoDocumento).filter_by(empresa_id=empresa.id, codigo='91').first()
            if not nc_exists:
                nc = TipoDocumento(
                    empresa_id=empresa.id,
                    codigo='91',
                    nombre='NOTA CREDITO',
                    consecutivo_actual=0,
                    numeracion_manual=False,
                    funcion_especial=None, # O 'nota_credito' si decides usar flags explícitos
                    afecta_inventario=False,
                    es_venta=True
                )
                db.add(nc)
                print(" -> Creado Tipo: NOTA CREDITO (91)")
            else:
                print(" -> Ya existe: NOTA CREDITO")

            # NOTA DÉBITO
            nd_exists = db.query(TipoDocumento).filter_by(empresa_id=empresa.id, codigo='92').first()
            if not nd_exists:
                nd = TipoDocumento(
                    empresa_id=empresa.id,
                    codigo='92',
                    nombre='NOTA DEBITO',
                    consecutivo_actual=0,
                    numeracion_manual=False,
                    funcion_especial=None,
                    afecta_inventario=False,
                    es_venta=True
                )
                db.add(nd)
                print(" -> Creado Tipo: NOTA DEBITO (92)")
            else:
                print(" -> Ya existe: NOTA DEBITO")

        db.commit()
        print("Configuración completada exitosamente.")

    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    setup_note_types()
