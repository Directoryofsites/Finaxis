
import os
import sys
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from app.models.documento import Documento
from app.models.movimiento_contable import MovimientoContable
from app.models.propiedad_horizontal import PHUnidad
from app.models.tipo_documento import TipoDocumento

DATABASE_URL = "sqlite:///./contapy.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

def debug_unit():
    unidad_codigo = "b 2 / 101"
    unidad = db.query(PHUnidad).filter(PHUnidad.codigo == unidad_codigo).first()
    if not unidad:
        print(f"Unidad {unidad_codigo} no encontrada")
        return

    print(f"DEBUG UNIDAD: {unidad.codigo} (ID: {unidad.id})")
    print(f"PROPIETARIO ID: {unidad.propietario_principal_id}")

    docs = db.query(Documento).filter(
        Documento.unidad_ph_id == unidad.id,
        Documento.anulado == False
    ).all()

    print("\nDOCUMENTOS ASOCIADOS A LA UNIDAD:")
    for d in docs:
        tipo = db.query(TipoDocumento).filter(TipoDocumento.id == d.tipo_documento_id).first()
        print(f"ID: {d.id} | {tipo.codigo}-{d.numero} | Fecha: {d.fecha} | Estado: {d.estado}")
        for m in d.movimientos:
            print(f"  - Cuenta: {m.cuenta_id} | Concepto: {m.concepto} | D: {m.debito} | C: {m.credito}")

    # Buscar documentos por beneficiario que NO tengan unidad_id pero que sean de este dueño
    docs_owner = db.query(Documento).filter(
        Documento.beneficiario_id == unidad.propietario_principal_id,
        Documento.unidad_ph_id == None,
        Documento.anulado == False
    ).all()

    if docs_owner:
        print("\nDOCUMENTOS DEL PROPIETARIO SIN UNIDAD ASIGNADA:")
        for d in docs_owner:
            tipo = db.query(TipoDocumento).filter(TipoDocumento.id == d.tipo_documento_id).first()
            print(f"ID: {d.id} | {tipo.codigo}-{d.numero} | Fecha: {d.fecha} | Estado: {d.estado}")
            for m in d.movimientos:
                print(f"  - Cuenta: {m.cuenta_id} | Concepto: {m.concepto} | D: {m.debito} | C: {m.credito}")

    db.close()

if __name__ == "__main__":
    debug_unit()
