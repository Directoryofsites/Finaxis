# app/services/tercero.py (Versión con manejo de lista_precio_id)

from sqlalchemy.orm import Session
from sqlalchemy import or_, func, distinct
from typing import List, Optional, Dict, Any
from fastapi import HTTPException, status

# Modelos
from app.models import tercero as models_tercero
from app.models.documento import Documento, DocumentoEliminado # Añadido DocumentoEliminado
from app.models.plantilla_maestra import PlantillaMaestra
from app.models.lista_precio import ListaPrecio # Necesario para validación

# Schemas
from app.schemas import tercero as schemas

def create_tercero(db: Session, tercero: schemas.TerceroCreate, user_id: int):
    # --- INICIO VALIDACIÓN LISTA PRECIO ---
    # Validamos que si se envía un lista_precio_id, este exista y pertenezca a la empresa
    if tercero.lista_precio_id:
        lista_precio_db = db.query(ListaPrecio).filter(
            ListaPrecio.id == tercero.lista_precio_id,
            ListaPrecio.empresa_id == tercero.empresa_id # empresa_id ya viene en TerceroCreate
        ).first()
        if not lista_precio_db:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"La Lista de Precios con ID {tercero.lista_precio_id} no existe o no pertenece a esta empresa."
            )
    # --- FIN VALIDACIÓN LISTA PRECIO ---

    db_tercero = models_tercero.Tercero(**tercero.model_dump())
    db_tercero.created_by = user_id
    db_tercero.updated_by = user_id
    db.add(db_tercero)
    db.commit()
    db.refresh(db_tercero)
    return db_tercero

def update_tercero(db: Session, tercero_id: int, tercero_update: schemas.TerceroUpdate, empresa_id: int, user_id: int):
    db_tercero = get_tercero(db, tercero_id=tercero_id, empresa_id=empresa_id)
    if not db_tercero:
        return None # La ruta manejará el 404

    # --- INICIO VALIDACIÓN LISTA PRECIO ---
    # Validamos si se está intentando actualizar lista_precio_id
    if tercero_update.lista_precio_id is not None:
         # Si se envía 0 o un ID negativo, se interpreta como quitar la lista
         if tercero_update.lista_precio_id <= 0:
             tercero_update.lista_precio_id = None # Guardamos NULL en la DB
         else:
             lista_precio_db = db.query(ListaPrecio).filter(
                 ListaPrecio.id == tercero_update.lista_precio_id,
                 ListaPrecio.empresa_id == empresa_id
             ).first()
             if not lista_precio_db:
                 raise HTTPException(
                     status_code=status.HTTP_404_NOT_FOUND,
                     detail=f"La Lista de Precios con ID {tercero_update.lista_precio_id} no existe o no pertenece a esta empresa."
                 )
    # --- FIN VALIDACIÓN LISTA PRECIO ---

    update_data = tercero_update.model_dump(exclude_unset=True)

    # Si lista_precio_id se estableció explícitamente a None (porque se envió <= 0)
    # nos aseguramos de que se incluya en la actualización para poner NULL en la DB
    if 'lista_precio_id' in tercero_update.model_fields_set and tercero_update.lista_precio_id is None:
         update_data['lista_precio_id'] = None

    for key, value in update_data.items():
        setattr(db_tercero, key, value)
    db_tercero.updated_by = user_id
    # db.add(db_tercero) # No es necesario db.add() para actualizar un objeto existente
    db.commit()
    db.refresh(db_tercero)
    return db_tercero

def delete_tercero(db: Session, tercero_id: int, empresa_id: int):
    db_tercero = get_tercero(db, tercero_id=tercero_id, empresa_id=empresa_id)
    if not db_tercero:
        return None # La ruta manejará el 404

    # --- REVISIÓN VALIDACIÓN DE DEPENDENCIAS ---
    # La lógica actual ya es bastante robusta, verificando Documentos y Plantillas.
    # Vamos a asegurar que también revise la tabla de documentos eliminados si es necesario.
    dependencies = []

    # Verificar Documentos ACTIVOS o ANULADOS
    documento_activo_en_uso = db.query(Documento).filter(
        Documento.beneficiario_id == tercero_id,
        Documento.empresa_id == empresa_id
    ).first()
    if documento_activo_en_uso:
        dependencies.append("Documentos Contables (Activos/Anulados)")

    # Verificar Documentos ELIMINADOS (Opcional pero recomendado para integridad total)
    documento_eliminado_en_uso = db.query(DocumentoEliminado).filter(
         DocumentoEliminado.beneficiario_id == tercero_id,
         DocumentoEliminado.empresa_id == empresa_id
    ).first()
    if documento_eliminado_en_uso:
        dependencies.append("Documentos en Papelera")


    # Verificar Plantillas
    plantilla_en_uso = db.query(PlantillaMaestra).filter(
        PlantillaMaestra.beneficiario_id_sugerido == tercero_id,
        PlantillaMaestra.empresa_id == empresa_id
    ).first()
    if plantilla_en_uso:
        dependencies.append("Plantillas de Documentos")
    # --- FIN REVISIÓN VALIDACIÓN DE DEPENDENCIAS ---

    if dependencies:
        error_message = f"No se puede eliminar. El tercero está en uso en: {', '.join(dependencies)}."
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=error_message
        )

    db.delete(db_tercero)
    db.commit()
    # No necesitamos retornar el objeto eliminado, la ruta devuelve 204
    return {"ok": True} # Cambiado para devolver un simple OK

def get_tercero(db: Session, tercero_id: int, empresa_id: int):
    # Esta función ya está bien
    return db.query(models_tercero.Tercero).filter(
        models_tercero.Tercero.id == tercero_id,
        models_tercero.Tercero.empresa_id == empresa_id
    ).first()

def get_tercero_by_nit(db: Session, nit: str, empresa_id: int):
     # Esta función ya está bien
    return db.query(models_tercero.Tercero).filter(
        models_tercero.Tercero.nit == nit,
        models_tercero.Tercero.empresa_id == empresa_id
    ).first()

def get_tercero_by_razon_social(db: Session, razon_social: str, empresa_id: int):
     # Esta función ya está bien
    return db.query(models_tercero.Tercero).filter(
        func.lower(models_tercero.Tercero.razon_social) == func.lower(razon_social),
        models_tercero.Tercero.empresa_id == empresa_id
    ).first()

def get_terceros(db: Session, empresa_id: int, filtro: Optional[str] = None, skip: int = 0, limit: int = 100):
    # --- MEJORA: Incluir datos de la lista de precios ---
    query = db.query(
            models_tercero.Tercero,
            ListaPrecio.nombre.label('lista_precio_nombre') # Incluimos el nombre
        ).outerjoin(ListaPrecio, models_tercero.Tercero.lista_precio_id == ListaPrecio.id)\
        .filter(models_tercero.Tercero.empresa_id == empresa_id)
    # --- FIN MEJORA ---

    if filtro:
        # Asegurarse que el filtro busca en las columnas correctas del modelo Tercero
        query = query.filter(or_(
            models_tercero.Tercero.razon_social.ilike(f"%{filtro}%"),
            models_tercero.Tercero.nit.ilike(f"%{filtro}%")
        ))

    # Aplicar ordenamiento, offset y limit al query final
    results = query.order_by(models_tercero.Tercero.razon_social).offset(skip).limit(limit).all()

    # --- MEJORA: Construir la respuesta incluyendo el nombre de la lista ---
    terceros_list = []
    for db_tercero, lista_nombre in results:
        tercero_dict = db_tercero.__dict__ # Convertir a dict
        tercero_dict['lista_precio_nombre'] = lista_nombre # Añadir el nombre
        terceros_list.append(schemas.Tercero.model_validate(tercero_dict)) # Validar con Pydantic
    # --- FIN MEJORA ---

    return terceros_list


def get_cuentas_asociadas_tercero(
    db: Session,
    empresa_id: int,
    tercero_id: int
) -> List[Dict[str, Any]]:
    # Esta función ya está bien
    from app.models.movimiento_contable import MovimientoContable
    from app.models.plan_cuenta import PlanCuenta

    tercero_exists = get_tercero(db, tercero_id=tercero_id, empresa_id=empresa_id)
    if not tercero_exists:
        raise HTTPException(status_code=404, detail="Tercero no encontrado o no pertenece a la empresa.")

    cuenta_ids_with_tercero = db.query(distinct(MovimientoContable.cuenta_id)).join(
        Documento, MovimientoContable.documento_id == Documento.id
    ).filter(
        Documento.empresa_id == empresa_id,
        Documento.beneficiario_id == tercero_id,
        Documento.anulado == False
    ).all()

    cuenta_ids = [id_tuple[0] for id_tuple in cuenta_ids_with_tercero]

    if not cuenta_ids:
        return []

    cuentas = db.query(PlanCuenta).filter(
        PlanCuenta.id.in_(cuenta_ids),
        PlanCuenta.empresa_id == empresa_id
    ).order_by(PlanCuenta.codigo).all()

    return [{"id": cuenta.id, "codigo": cuenta.codigo, "nombre": cuenta.nombre} for cuenta in cuentas]

def fusionar_terceros(db: Session, origen_id: int, destino_id: int, empresa_id: int):
    # Esta función ya está bien
    try:
        # 1. Verificar que ambos terceros existen
        tercero_origen = get_tercero(db, tercero_id=origen_id, empresa_id=empresa_id)
        if not tercero_origen:
            raise HTTPException(status_code=404, detail="El tercero de origen no fue encontrado.")

        tercero_destino = get_tercero(db, tercero_id=destino_id, empresa_id=empresa_id)
        if not tercero_destino:
            raise HTTPException(status_code=404, detail="El tercero de destino no fue encontrado.")

        # 2. Contar y reasignar documentos
        documentos_a_mover = db.query(Documento).filter(
            Documento.beneficiario_id == origen_id,
            Documento.empresa_id == empresa_id
        )
        count_documentos = documentos_a_mover.count()
        documentos_a_mover.update(
            {"beneficiario_id": destino_id},
            synchronize_session=False
        )

        # 3. Eliminar el tercero de origen
        db.delete(tercero_origen)

        # 4. Confirmar explícitamente la transacción
        db.commit()

        return {"message": "Fusión completada con éxito.", "documentosMovidos": count_documentos}

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ocurrió un error durante la fusión: {str(e)}"
        )