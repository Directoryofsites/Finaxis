import sys
import os

# Add the parent directory to sys.path to allow imports from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.propiedad_horizontal.unidad import PHUnidad
from app.models.propiedad_horizontal.configuracion import PHConfiguracion
from app.models.documento import Documento
from app.models.tipo_documento import TipoDocumento
from app.services.documento import eliminar_documento

def reset_ph_data():
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        print(" -> Buscando documentos de Propiedad Horizontal para eliminar...")
        
        # 1. Identificar Documentos de PH (Con unidad_ph_id o Tipo PH)
        
        # A. Obtener Tipos de Documento Configurados en PH
        config_ph = db.query(PHConfiguracion).first()
        tipos_ph_ids = []
        if config_ph:
            if config_ph.tipo_documento_factura_id: tipos_ph_ids.append(config_ph.tipo_documento_factura_id)
            if config_ph.tipo_documento_recibo_id: tipos_ph_ids.append(config_ph.tipo_documento_recibo_id)
        
        print(f" -> Buscando por Tipos PH: {tipos_ph_ids} o Unidad PH Asignada...")

        # B. Query Mixto (Por Unidad O Por Tipo Configurado)
        query = db.query(Documento).filter(
            (Documento.unidad_ph_id.isnot(None)) |
            (Documento.tipo_documento_id.in_(tipos_ph_ids) if tipos_ph_ids else False)
        )
        
        docs_to_delete = query.all()
        
        count = len(docs_to_delete)
        print(f" -> Se encontraron {count} documentos para eliminar.")

        if count == 0:
            print(" -> No hay documentos para eliminar.")
            return

        # 2. Get unique Document Types affected to reset consecutives later
        tipos_afectados_ids = set(doc.tipo_documento_id for doc in docs_to_delete)

        # 3. Eliminar Documentos
        print(" - Eliminando documentos...")
        
        # Obtener un usuario valido (Admin)
        from app.models.usuario import Usuario
        admin_user = db.query(Usuario).first()
        if not admin_user:
            print(" [ERROR] No hay usuarios en el sistema para registrar la eliminacion.")
            return

        user_id = admin_user.id
        razon = "Reset de Pruebas PH"

        for doc in docs_to_delete:
            try:
                # Llamamos al servicio 'eliminar_documento' que ya maneja la lógica de contabilidad/log
                eliminar_documento(db, doc.id, doc.empresa_id, user_id, razon)
                print(f"   - Eliminado Doc ID {doc.id} (Numero {doc.numero})")
            except Exception as e:
                print(f"   ERROR eliminando Doc {doc.id}: {e}")

        # 4. Resetear Consecutivos (Opcional pero recomendado para pruebas)
        print(" - Reseteando consecutivos de Tipos de Documento...")
        tipos = db.query(TipoDocumento).filter(TipoDocumento.id.in_(tipos_afectados_ids)).all()
        for tipo in tipos:
            print(f"   - Tipo {tipo.codigo}: Consecutivo actual {tipo.consecutivo_actual} -> 0")
            tipo.consecutivo_actual = 0
            db.add(tipo)
        
        db.commit()
        print("\n [OK] Limpieza completada con exito.")

    except Exception as e:
        print(f"\n [ERROR] General: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("INICIO PROCESO DE LIMPIEZA PH")
    confirm = input("ESTAS SEGURO DE ELIMINAR TODOS LOS DOCUMENTOS DE PH? (s/n): ")
    if confirm.lower() == 's':
        reset_ph_data()
    else:
        print("Operación cancelada.")
