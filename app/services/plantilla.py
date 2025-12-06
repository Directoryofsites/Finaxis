from sqlalchemy.orm import Session, joinedload
from typing import List
from fastapi import HTTPException
from datetime import datetime

from ..models import plantilla_maestra as models_maestra
from ..models import plantilla_detalle as models_detalle
from ..models import documento as models_documento # <-- IMPORTACIÓN AÑADIDA
from ..schemas import plantilla as schemas

def _validate_balance(detalles: List[schemas.PlantillaDetalleCreate]):
    total_debito = sum(d.debito for d in detalles)
    total_credito = sum(d.credito for d in detalles)
    if abs(total_debito - total_credito) > 0.01:
        raise HTTPException(
            status_code=400,
            detail="Los débitos y créditos de la plantilla no están balanceados."
        )

def get_plantillas_by_empresa(db: Session, empresa_id: int):
    return db.query(models_maestra.PlantillaMaestra).filter(
        models_maestra.PlantillaMaestra.empresa_id == empresa_id
    ).order_by(models_maestra.PlantillaMaestra.nombre_plantilla).all()

def get_plantilla(db: Session, plantilla_id: int):
    return db.query(models_maestra.PlantillaMaestra).filter(
        models_maestra.PlantillaMaestra.id == plantilla_id
    ).first()

def create_plantilla(db: Session, plantilla: schemas.PlantillaMaestraCreate, user_id: int, empresa_id: int):
    _validate_balance(plantilla.detalles)

    db_maestra = models_maestra.PlantillaMaestra(
        empresa_id=empresa_id,
        nombre_plantilla=plantilla.nombre_plantilla,
        tipo_documento_id_sugerido=plantilla.tipo_documento_id_sugerido,
        beneficiario_id_sugerido=plantilla.beneficiario_id_sugerido,
        centro_costo_id_sugerido=plantilla.centro_costo_id_sugerido,
        created_at=datetime.utcnow(),
        created_by=user_id,
        updated_by=user_id
    )
    for detalle_in in plantilla.detalles:
        db_detalle = models_detalle.PlantillaDetalle(**detalle_in.model_dump())
        db_maestra.detalles.append(db_detalle)

    try:
        db.add(db_maestra)
        db.commit()
        db.refresh(db_maestra)
        return db_maestra
    except Exception as e:
        db.rollback()
        raise e

def update_plantilla(db: Session, plantilla_id: int, plantilla_update: schemas.PlantillaMaestraUpdate, user_id: int):
    _validate_balance(plantilla_update.detalles)

    db_maestra = get_plantilla(db, plantilla_id=plantilla_id)
    if not db_maestra:
        return None

    try:
        update_data = plantilla_update.model_dump(exclude={'detalles'})
        for key, value in update_data.items():
            setattr(db_maestra, key, value)

        db_maestra.updated_by = user_id

        db_maestra.detalles.clear()
        for detalle_in in plantilla_update.detalles:
            db_detalle = models_detalle.PlantillaDetalle(**detalle_in.model_dump())
            db_maestra.detalles.append(db_detalle)

        db.commit()
        db.refresh(db_maestra)
        return db_maestra
    except Exception as e:
        db.rollback()
        raise e

def delete_plantilla(db: Session, plantilla_id: int, empresa_id: int):
    db_maestra = db.query(models_maestra.PlantillaMaestra).filter(
        models_maestra.PlantillaMaestra.id == plantilla_id,
        models_maestra.PlantillaMaestra.empresa_id == empresa_id
    ).first()

    if not db_maestra:
        return None

    db.delete(db_maestra)
    db.commit()
    return db_maestra

# --- INICIO DE LA NUEVA FUNCIÓN ---

def create_template_from_document(db: Session, documento_id: int, nombre_plantilla: str, user_id: int):
    """
    Crea una nueva plantilla de contabilidad a partir de un documento existente.
    """
    # Paso 1: Buscar el documento de origen y sus movimientos.
    # Usamos joinedload para cargar los movimientos en la misma consulta y ser más eficientes.
    source_doc = db.query(models_documento.Documento).options(
        joinedload(models_documento.Documento.movimientos)
    ).filter(models_documento.Documento.id == documento_id).first()

    if not source_doc:
        raise HTTPException(status_code=404, detail="El documento de origen no fue encontrado.")

    # Paso 2: Verificar que no exista ya una plantilla con el mismo nombre para esta empresa.
    existing_template = db.query(models_maestra.PlantillaMaestra).filter(
        models_maestra.PlantillaMaestra.empresa_id == source_doc.empresa_id,
        models_maestra.PlantillaMaestra.nombre_plantilla == nombre_plantilla
    ).first()

    if existing_template:
        raise HTTPException(status_code=409, detail=f"Ya existe una plantilla con el nombre '{nombre_plantilla}'.")

    # Paso 3: Crear el registro maestro de la nueva plantilla.
    db_maestra = models_maestra.PlantillaMaestra(
        empresa_id=source_doc.empresa_id,
        nombre_plantilla=nombre_plantilla,
        tipo_documento_id_sugerido=source_doc.tipo_documento_id,
        beneficiario_id_sugerido=source_doc.beneficiario_id,
        centro_costo_id_sugerido=source_doc.centro_costo_id,
        created_at=datetime.utcnow(),
        created_by=user_id,
        updated_by=user_id
    )

    # Paso 4: Iterar sobre los movimientos del documento y crear los detalles de la plantilla.
    for movimiento in source_doc.movimientos:
        db_detalle = models_detalle.PlantillaDetalle(
            cuenta_id=movimiento.cuenta_id,
            concepto=movimiento.concepto,
            debito=movimiento.debito,
            credito=movimiento.credito
        )
        db_maestra.detalles.append(db_detalle)

    # Paso 5: Guardar todo en la base de datos de forma atómica.
    try:
        db.add(db_maestra)
        db.commit()
        db.refresh(db_maestra)
        return db_maestra
    except Exception as e:
        db.rollback()
        # En un entorno de producción, registraríamos el error 'e' en un log.
        raise HTTPException(status_code=500, detail="Ocurrió un error al guardar la plantilla.")

# --- FIN DE LA NUEVA FUNCIÓN ---