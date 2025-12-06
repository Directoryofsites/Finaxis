# app/services/ajuste_inventario.py (Versión con AttributeError CORREGIDO)

from sqlalchemy.orm import Session, selectinload # Añadir selectinload
from fastapi import HTTPException, status
from datetime import date, datetime, time # Asegurar time

# Importar modelos y schemas usando alias consistentes
from .. import models
from .. import schemas
# Importar servicios
from ..services import documento as documento_service
from ..services import inventario as inventario_service

def crear_ajuste_inventario(db: Session, ajuste_data: schemas.inventario.AjusteInventarioCreate, empresa_id: int, user_id: int):
    """
    Servicio orquestador para crear un ajuste de inventario.
    CORREGIDO: Usa ajuste_data.bodega_id al registrar movimiento.
    """
    try:
        # Buscar el tipo de documento 'AI'
        tipo_doc_ajuste = db.query(models.TipoDocumento).filter(
            models.TipoDocumento.empresa_id == empresa_id,
            models.TipoDocumento.codigo == 'AI' # Usar código es más robusto que función especial a veces
        ).first()

        if not tipo_doc_ajuste:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tipo de documento 'AI' (Ajuste Inventario) no configurado.")

        # Validar bodega una sola vez
        bodega_db = db.query(models.Bodega).filter(
            models.Bodega.id == ajuste_data.bodega_id,
            models.Bodega.empresa_id == empresa_id
        ).first()
        if not bodega_db:
             raise HTTPException(status_code=400, detail=f"La bodega ID {ajuste_data.bodega_id} no es válida.")


        movimientos_contables = []
        # Filtrar items sin diferencia significativa ANTES de la transacción
        items_con_diferencia = [item for item in ajuste_data.items if abs(item.diferencia) > 1e-6]

        if not items_con_diferencia:
             raise HTTPException(status_code=400, detail="No hay items con diferencias significativas para ajustar.")

        # --- INICIO TRANSACCIÓN ATÓMICA ---
        with db.begin_nested():

            # Preparar movimientos contables
            for item in items_con_diferencia:
                # Usar selectinload para cargar grupo eficientemente
                producto = db.query(models.Producto).options(
                    selectinload(models.Producto.grupo_inventario) # Cargar grupo relacionado
                ).filter(models.Producto.id == item.producto_id).first()

                # Validaciones cruciales de configuración de cuentas
                if not producto or not producto.grupo_inventario:
                    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Producto ID {item.producto_id} no encontrado o sin grupo.")

                grupo = producto.grupo_inventario
                # Asegurar que costo_promedio no sea None
                costo_promedio_usar = item.costo_promedio if item.costo_promedio is not None else (producto.costo_promedio or 0.0)
                valor_ajuste = abs(item.diferencia * costo_promedio_usar)

                # Añadir producto_id a los movimientos contables
                if item.diferencia > 0: # Sobrante
                    if not grupo.cuenta_inventario_id or not grupo.cuenta_ajuste_sobrante_id:
                        raise HTTPException(status_code=400, detail=f"Grupo '{grupo.nombre}' sin cuentas de inventario y/o ajuste sobrante.")
                    movimientos_contables.append(schemas.documento.MovimientoContableCreate(cuenta_id=grupo.cuenta_inventario_id, debito=valor_ajuste, credito=0, concepto=ajuste_data.concepto, producto_id=item.producto_id)) # Añadido producto_id
                    movimientos_contables.append(schemas.documento.MovimientoContableCreate(cuenta_id=grupo.cuenta_ajuste_sobrante_id, debito=0, credito=valor_ajuste, concepto=ajuste_data.concepto, producto_id=item.producto_id)) # Añadido producto_id
                else: # Faltante
                    if not grupo.cuenta_inventario_id or not grupo.cuenta_ajuste_faltante_id:
                        raise HTTPException(status_code=400, detail=f"Grupo '{grupo.nombre}' sin cuentas de inventario y/o ajuste faltante.")
                    movimientos_contables.append(schemas.documento.MovimientoContableCreate(cuenta_id=grupo.cuenta_ajuste_faltante_id, debito=valor_ajuste, credito=0, concepto=ajuste_data.concepto, producto_id=item.producto_id)) # Añadido producto_id
                    movimientos_contables.append(schemas.documento.MovimientoContableCreate(cuenta_id=grupo.cuenta_inventario_id, debito=0, credito=valor_ajuste, concepto=ajuste_data.concepto, producto_id=item.producto_id)) # Añadido producto_id

            # Crear el documento contable "padre"
            documento_a_crear = schemas.documento.DocumentoCreate(
                empresa_id=empresa_id,
                tipo_documento_id=tipo_doc_ajuste.id,
                fecha=ajuste_data.fecha,
                # No necesita beneficiario ni centro costo usualmente, a menos que lo requieras
                # Añadir concepto general del ajuste al documento padre si se desea
                # concepto=ajuste_data.concepto, # Descomentar si el modelo Documento tiene 'concepto'
                movimientos=movimientos_contables
            )

            # Usar el servicio create_documento que maneja límites, fecha inicio, etc.
            db_documento = documento_service.create_documento(
                db=db, documento=documento_a_crear, user_id=user_id, commit=False # commit=False crucial para atomicidad
            )

            # Registrar movimientos de inventario (Kardex)
            for item in items_con_diferencia:
                tipo_movimiento = 'ENTRADA_AJUSTE' if item.diferencia > 0 else 'SALIDA_AJUSTE'
                cantidad_ajuste = abs(item.diferencia)
                producto_costo = item.costo_promedio # Usar el costo enviado por el frontend
                # Fallback robusto por si costo_promedio es None
                if producto_costo is None:
                     prod_db_cost = db.query(models.Producto.costo_promedio).filter(models.Producto.id == item.producto_id).scalar()
                     producto_costo = prod_db_cost or 0.0

                inventario_service.registrar_movimiento_inventario(
                    db=db,
                    producto_id=item.producto_id,
                    # --- INICIO CORRECCIÓN ---
                    bodega_id=ajuste_data.bodega_id, # Usar la bodega del ajuste general
                    # --- FIN CORRECCIÓN ---
                    tipo_movimiento=tipo_movimiento,
                    cantidad=cantidad_ajuste,
                    costo_unitario=float(producto_costo), # Asegurar float
                    # Combinar fecha con hora actual para ordenamiento preciso en Kardex
                    fecha=datetime.combine(ajuste_data.fecha, datetime.now().time()),
                    documento_id=db_documento.id
                )

        # Si todo OK, la sub-transacción (begin_nested) se completa
        db.commit() # Commit final de la transacción principal
        db.refresh(db_documento)
        return db_documento

    except Exception as e:
        db.rollback() # Revierte todo si algo falla
        print(f"ERROR DETALLADO en crear_ajuste_inventario: {e}") # Log para nosotros
        import traceback
        traceback.print_exc() # Ver traceback completo
        if isinstance(e, HTTPException):
            raise e # Re-lanzar errores HTTP conocidos
        # Error genérico para el usuario
        raise HTTPException(status_code=500, detail=f"Error interno del servidor al crear el ajuste.")