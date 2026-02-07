import sys
import os
from sqlalchemy import text

# Add project root to path
sys.path.append(os.getcwd())

from app.core.database import SessionLocal
from app.models.empresa import Empresa
from app.models.consumo_registros import ControlPlanMensual, BolsaExcedente, RecargaAdicional, HistorialConsumo
from app.models.documento import Documento
from app.models.movimiento_contable import MovimientoContable
from app.models.periodo_contable_cerrado import PeriodoContableCerrado
from passlib.context import CryptContext
import app.models.nomina

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def reset_test_data():
    db = SessionLocal()
    try:
        print("--- STARTING CLEAN SLATE RESET ---")

        # 1. DELETE OLD CORRUPT COMPANIES (176, 177, 205)
        # Delete Children First (205 -> 177 -> 176) to satisfy padre_id FK
        target_ids = [205, 177, 176]
        
        for cid in target_ids:
            print(f"Deleting data for Company {cid}...")
            # Order matters due to FKs
            # MovimientoContable does not have empresa_id, linked via Documento
            subquery_docs = db.query(Documento.id).filter(Documento.empresa_id == cid)
            db.query(MovimientoContable).filter(MovimientoContable.documento_id.in_(subquery_docs)).delete(synchronize_session=False)
            # Delete Documents (Requires cascade or manual delete of children like Retenciones etc if present, 
            # assuming Cascade is set on DB level for basic tables, otherwise might fail. 
            # Safest is to try delete company and let cascade work if configured, or manual delete.)
            
            # Manual cleanup of key tables just in case
            # Delete dependent tables
            # Historial Consumo (Must be deleted before Documento because it references Documento)
            # CAUTION: History might belong to Parent Company checking Child Docs. 
            # Delete any history referencing these docs unique to this company.
            subquery_docs = db.query(Documento.id).filter(Documento.empresa_id == cid)
            db.query(HistorialConsumo).filter(HistorialConsumo.documento_id.in_(subquery_docs)).delete(synchronize_session=False)

            db.query(PeriodoContableCerrado).filter(PeriodoContableCerrado.empresa_id == cid).delete()
            db.query(BolsaExcedente).filter(BolsaExcedente.empresa_id == cid).delete()
            db.query(RecargaAdicional).filter(RecargaAdicional.empresa_id == cid).delete()
            db.query(ControlPlanMensual).filter(ControlPlanMensual.empresa_id == cid).delete()
            
            # Delete Plantillas Maestras (References Terceros)
            db.execute(text("DELETE FROM plantillas_maestras WHERE empresa_id = :cid"), {"cid": cid})
            
            # Documents
            db.query(Documento).filter(Documento.empresa_id == cid).delete()
            
            # Users linked to company
            # Need to import Usuario inside loop or top level, I'll add top level.
            # Assuming I will fix imports in next block.
            # Using raw SQL string for safety if model import fails or just strict model usage.
            # Let's import Usuario.
            from app.models.usuario import Usuario
            from app.models.tercero import Tercero
            
            # Delete Terceros (Clean up references to created_by)
            db.query(Tercero).filter(Tercero.empresa_id == cid).delete()

            # Delete Roles first (Raw SQL to avoid model import hell)
            db.execute(text("DELETE FROM usuario_roles WHERE usuario_id IN (SELECT id FROM usuarios WHERE empresa_id = :cid)"), {"cid": cid})
            
            # Update created_by and updated_by to NULL for any Tercero
            db.execute(text("UPDATE terceros SET created_by = NULL WHERE created_by IN (SELECT id FROM usuarios WHERE empresa_id = :cid)"), {"cid": cid})
            db.execute(text("UPDATE terceros SET updated_by = NULL WHERE updated_by IN (SELECT id FROM usuarios WHERE empresa_id = :cid)"), {"cid": cid})
            
            # Update conceptos_favoritos cleanup
            db.execute(text("UPDATE conceptos_favoritos SET created_by = NULL WHERE created_by IN (SELECT id FROM usuarios WHERE empresa_id = :cid)"), {"cid": cid})
            db.execute(text("UPDATE conceptos_favoritos SET updated_by = NULL WHERE updated_by IN (SELECT id FROM usuarios WHERE empresa_id = :cid)"), {"cid": cid})
            
            # Update plantillas_maestras cleanup
            db.execute(text("UPDATE plantillas_maestras SET created_by = NULL WHERE created_by IN (SELECT id FROM usuarios WHERE empresa_id = :cid)"), {"cid": cid})
            db.execute(text("UPDATE plantillas_maestras SET updated_by = NULL WHERE updated_by IN (SELECT id FROM usuarios WHERE empresa_id = :cid)"), {"cid": cid})
            
            # Update documentos cleanup (for documents in OTHER companies created by these users)
            db.execute(text("UPDATE documentos SET usuario_creador_id = NULL WHERE usuario_creador_id IN (SELECT id FROM usuarios WHERE empresa_id = :cid)"), {"cid": cid})
            
            # Update documentos_eliminados cleanup
            db.execute(text("UPDATE documentos_eliminados SET usuario_creador_id = NULL, usuario_eliminacion_id = NULL WHERE usuario_creador_id IN (SELECT id FROM usuarios WHERE empresa_id = :cid) OR usuario_eliminacion_id IN (SELECT id FROM usuarios WHERE empresa_id = :cid)"), {"cid": cid})
            
            # Update log_operaciones cleanup
            db.execute(text("UPDATE log_operaciones SET usuario_id = NULL WHERE usuario_id IN (SELECT id FROM usuarios WHERE empresa_id = :cid)"), {"cid": cid})
            
            # Delete usuario_empresas (User-Company ManyToMany)
            db.execute(text("DELETE FROM usuario_empresas WHERE usuario_id IN (SELECT id FROM usuarios WHERE empresa_id = :cid)"), {"cid": cid})
            db.execute(text("DELETE FROM usuario_empresas WHERE empresa_id = :cid"), {"cid": cid})
            
            # Update empresas owner_id cleanup (Unlink user from company usage)
            db.execute(text("UPDATE empresas SET owner_id = NULL WHERE owner_id IN (SELECT id FROM usuarios WHERE empresa_id = :cid)"), {"cid": cid})
            
            db.query(Usuario).filter(Usuario.empresa_id == cid).delete()

            # Finally the Company
            db.query(Empresa).filter(Empresa.id == cid).delete()
            
        db.commit()
        print("Old companies deleted.")

        # 2. CREATE NEW STRUCTURE
        print("Creating new clean structure...")
        
        # 2.1 PARENT (Accountant)
        padre = Empresa(
            razon_social="CONTADOR TEST (PADRE)",
            nit="900000001",
            dv="1",
            direccion="Calle Test 123",
            telefono="5550001",
            email="contador@test.com",
            limite_registros_mensual=200, # CRITICAL: Parent has the limit
            es_contador=True, # Flag as accountant
            padre_id=None # Top level
        )
        db.add(padre)
        db.flush()
        print(f"Created Parent: {padre.razon_social} (ID: {padre.id})")

        # 2.2 CHILDREN
        hija_a = Empresa(
            razon_social="HIJA A (CLIENTE)",
            nit="900000002",
            dv="2",
            direccion="Calle Hija 1",
            telefono="5550002",
            email="hija_a@test.com",
            limite_registros_mensual=0, # Children have 0 (consume from parent)
            es_contador=False,
            padre_id=padre.id
        )
        db.add(hija_a)

        hija_b = Empresa(
            razon_social="HIJA B (CLIENTE)",
            nit="900000003",
            dv="3",
            direccion="Calle Hija 2",
            telefono="5550003",
            email="hija_b@test.com",
            limite_registros_mensual=0,
            es_contador=False,
            padre_id=padre.id
        )
        db.add(hija_b)
        
        db.commit()
        print(f"Created Children linked to Parent ID {padre.id}")
        print("--- RESET COMPLETE ---")
        
        return padre.id, hija_a.id, hija_b.id

    except Exception as e:
        db.rollback()
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    reset_test_data()
