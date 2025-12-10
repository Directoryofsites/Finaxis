from sqlalchemy.orm import Session, selectinload
from sqlalchemy import func
from fastapi import HTTPException
from datetime import datetime, date

from ..models import produccion as models_prod
from ..models import documento as models_doc
from ..models import producto as models_inv
from ..models import grupo_inventario as models_grupo
from ..models import bodega as models_bodega
from ..models import tercero as models_tercero
from ..schemas import produccion as schemas_prod
from ..schemas import documento as schemas_doc
from app.services.produccion_configuracion import get_configuracion # Importar config service

from . import inventario as service_inventario
from . import documento as service_documento
from . import tipo_documento as service_tipo_documento

# --- CRUD RECETAS ---

def create_receta(db: Session, receta: schemas_prod.RecetaCreate, empresa_id: int):
    db_receta = models_prod.Receta(
        empresa_id=empresa_id,
        producto_id=receta.producto_id,
        nombre=receta.nombre,
        descripcion=receta.descripcion,
        cantidad_base=receta.cantidad_base,
        activa=receta.activa
    )
    db.add(db_receta)
    db.flush() # Obtener ID

    for det in receta.detalles:
        db_detalle = models_prod.RecetaDetalle(
            receta_id=db_receta.id,
            insumo_id=det.insumo_id,
            cantidad=det.cantidad
        )
        db.add(db_detalle)
    
    if receta.recursos:
        for rec in receta.recursos:
            db_recurso = models_prod.RecetaRecurso(
                receta_id=db_receta.id,
                descripcion=rec.descripcion,
                tipo=rec.tipo,
                costo_estimado=rec.costo_estimado,
                cuenta_contable_id=rec.cuenta_contable_id
            )
            db.add(db_recurso)
    
    db.commit()
    db.refresh(db_receta)
    return db_receta

def get_recetas(db: Session, empresa_id: int):
    return db.query(models_prod.Receta).filter(models_prod.Receta.empresa_id == empresa_id).all()

def get_receta_by_id(db: Session, receta_id: int, empresa_id: int):
    return db.query(models_prod.Receta).options(
        selectinload(models_prod.Receta.detalles).selectinload(models_prod.RecetaDetalle.insumo),
        selectinload(models_prod.Receta.recursos),
        selectinload(models_prod.Receta.producto)
    ).filter(models_prod.Receta.id == receta_id, models_prod.Receta.empresa_id == empresa_id).first()

def update_receta(db: Session, receta_id: int, receta_update: schemas_prod.RecetaUpdate, empresa_id: int):
    db_receta = get_receta_by_id(db, receta_id, empresa_id)
    if not db_receta:
        return None

    # Actualizar campos básicos
    if receta_update.nombre is not None:
        db_receta.nombre = receta_update.nombre
    if receta_update.descripcion is not None:
        db_receta.descripcion = receta_update.descripcion
    if receta_update.cantidad_base is not None:
        db_receta.cantidad_base = receta_update.cantidad_base
    if receta_update.activa is not None:
        db_receta.activa = receta_update.activa

    # Actualizar Detalles (Reemplazo completo si se envía la lista)
    if receta_update.detalles is not None:
        # Eliminar anteriores
        for det in db_receta.detalles:
            db.delete(det)
        
        # Crear nuevos
        for det_in in receta_update.detalles:
            new_det = models_prod.RecetaDetalle(
                receta_id=db_receta.id,
                insumo_id=det_in.insumo_id,
                cantidad=det_in.cantidad
            )
            db.add(new_det)

    # Actualizar Recursos (Reemplazo completo si se envía la lista)
    if receta_update.recursos is not None:
        # Eliminar anteriores
        for rec in db_receta.recursos:
            db.delete(rec)
        
        # Crear nuevos
        for rec_in in receta_update.recursos:
            new_rec = models_prod.RecetaRecurso(
                receta_id=db_receta.id,
                descripcion=rec_in.descripcion,
                tipo=rec_in.tipo,
                costo_estimado=rec_in.costo_estimado,
                cuenta_contable_id=rec_in.cuenta_contable_id
            )
            db.add(new_rec)

    db.commit()
    db.refresh(db_receta)
    return db_receta

# --- ORDENES DE PRODUCCION ---

def create_orden(db: Session, orden: schemas_prod.OrdenProduccionCreate, empresa_id: int, user_id: int):
    # Generar consecutivo simple (TODO: Usar secuencia real si se requiere)
    count = db.query(models_prod.OrdenProduccion).filter(models_prod.OrdenProduccion.empresa_id == empresa_id).count()
    numero_orden = f"OP-{count + 1:04d}"

    db_orden = models_prod.OrdenProduccion(
        empresa_id=empresa_id,
        numero_orden=numero_orden,
        producto_id=orden.producto_id,
        receta_id=orden.receta_id,
        bodega_destino_id=orden.bodega_destino_id,
        cantidad_planeada=orden.cantidad_planeada,
        cantidad_real=0,
        estado=models_prod.EstadoOrdenProduccion.PLANIFICADA,
        fecha_inicio=orden.fecha_inicio or date.today(),
        observaciones=orden.observaciones
    )
    db.add(db_orden)
    db.flush() # Obtener ID

    # Copiar Recursos de la Receta (Presupuestado)
    if orden.receta_id:
        receta = get_receta_by_id(db, orden.receta_id, empresa_id)
        if receta and receta.recursos:
            factor = orden.cantidad_planeada / (receta.cantidad_base or 1)
            total_mod = 0.0
            total_cif = 0.0

            for rec in receta.recursos:
                valor_calculado = rec.costo_estimado * factor
                
                new_op_rec = models_prod.OrdenProduccionRecurso(
                    orden_id=db_orden.id,
                    descripcion=rec.descripcion,
                    tipo=rec.tipo,
                    valor=valor_calculado
                )
                db.add(new_op_rec)

                if rec.tipo == 'MANO_OBRA_DIRECTA':
                    total_mod += valor_calculado
                elif rec.tipo == 'COSTO_INDIRECTO_FABRICACION':
                    total_cif += valor_calculado
            
            # Actualizar totales estimados en la Orden
            db_orden.costo_total_mod = total_mod
            db_orden.costo_total_cif = total_cif

    db.commit()
    db.refresh(db_orden)
    return db_orden

def get_ordenes(db: Session, empresa_id: int):
    return db.query(models_prod.OrdenProduccion).options(
        selectinload(models_prod.OrdenProduccion.producto),
        selectinload(models_prod.OrdenProduccion.receta)
    ).filter(models_prod.OrdenProduccion.empresa_id == empresa_id).order_by(models_prod.OrdenProduccion.id.desc()).all()

def get_orden_by_id(db: Session, orden_id: int, empresa_id: int):
    return db.query(models_prod.OrdenProduccion).options(
        selectinload(models_prod.OrdenProduccion.producto),
        selectinload(models_prod.OrdenProduccion.bodega_destino),
        selectinload(models_prod.OrdenProduccion.receta),
        selectinload(models_prod.OrdenProduccion.insumos).selectinload(models_prod.OrdenProduccionInsumo.insumo),
        selectinload(models_prod.OrdenProduccion.recursos)
    ).filter(models_prod.OrdenProduccion.id == orden_id, models_prod.OrdenProduccion.empresa_id == empresa_id).first()


# --- PROCESO: CONSUMO DE MATERIA PRIMA (BATCH) ---

def procesar_consumo_mp(db: Session, orden_id: int, items_consumo: list[schemas_prod.RecetaDetalleCreate], bodega_origen_id: int, empresa_id: int, user_id: int):
    """
    Registra el consumo de materias primas.
    1. Crea un Documento Contable (Tipo: 'CONSUMO_PRODUCCION').
    2. Genera asientos contables: Crédito 14 (Inventario) vs Débito 71 (Costo MP).
    3. Descarga inventario (Kardex).
    4. Registra los insumos en la Orden de Producción.
    """
    orden = get_orden_by_id(db, orden_id, empresa_id)
    if not orden: raise HTTPException(status_code=404, detail="Orden no encontrada")
    if orden.estado == models_prod.EstadoOrdenProduccion.CERRADA:
         raise HTTPException(status_code=400, detail="Orden ya cerrada")

    # A. Buscar Tipo Documento para Producción (Debe existir o crearse)
    # Buscamos por función especial 'produccion_consumo' o similar. Si no existe, usamos un genérico.
    # Por ahora, asumimos que existe un tipo con función 'SALIDA_PRODUCCION'
    # TODO: Parametrizar esto correctamente. 
    tipo_doc = db.query(models_doc.TipoDocumento).filter(
        models_doc.TipoDocumento.empresa_id == empresa_id,
        # models_doc.TipoDocumento.funcion_especial == 'salida_produccion' # Ideal
        models_doc.TipoDocumento.nombre.ilike('%CONSUMO%') # Fallback temporal
    ).first()
    
    if not tipo_doc:
        # Fallback de emergencia, usar Nota Contable o similar
        raise HTTPException(status_code=400, detail="No existe Tipo de Documento para Consumo de Producción configurado.")

    movimientos_contables = []
    total_costo_lote = 0.0

    # B. Preparar Movimientos
    for item in items_consumo:
        producto = service_inventario.get_producto_by_id(db, item.insumo_id, empresa_id)
        costo_unitario = producto.costo_promedio or 0.0
        costo_total_linea = costo_unitario * item.cantidad
        
        grupo = producto.grupo_inventario
        if not grupo or not grupo.cuenta_inventario_id or not grupo.cuenta_costo_produccion_id:
             raise HTTPException(status_code=400, detail=f"Producto {producto.nombre} no tiene cuentas configuradas (Inv/CostoProd) en su grupo.")

        # 1. CRÉDITO a INVENTARIO (14) - Salida de Bodega
        movimientos_contables.append(schemas_doc.MovimientoContableCreate(
            cuenta_id=grupo.cuenta_inventario_id,
            centro_costo_id=None, # Opcional: Asignar al CC de Producción
            concepto=f"Consumo MP Orden #{orden.numero_orden} - {producto.nombre}",
            debito=0,
            credito=costo_total_linea
        ))

        # 2. DÉBITO a COSTO (71) - Costo Materia Prima
        movimientos_contables.append(schemas_doc.MovimientoContableCreate(
            cuenta_id=grupo.cuenta_costo_produccion_id,
            centro_costo_id=None,
            concepto=f"Costo MP Orden #{orden.numero_orden} - {producto.nombre}",
            debito=costo_total_linea,
            credito=0
        ))
        
        total_costo_lote += costo_total_linea

        # Registrar en la Orden (Tabla auxiliar)
        op_insumo = models_prod.OrdenProduccionInsumo(
            orden_id=orden.id,
            insumo_id=producto.id,
            bodega_origen_id=bodega_origen_id,
            cantidad=item.cantidad,
            costo_unitario_historico=costo_unitario,
            costo_total=costo_total_linea,
            fecha_despacho=datetime.now()
        )
        db.add(op_insumo)

    # C. Crear Documento
    doc_create = schemas_doc.DocumentoCreate(
        empresa_id=empresa_id,
        tipo_documento_id=tipo_doc.id,
        fecha=date.today(),
        fecha_vencimiento=date.today(),
        observaciones=f"Consumo MP para Orden {orden.numero_orden}",
        movimientos=movimientos_contables,
        aplicaciones=[]
    )
    
    documento = service_documento.create_documento(db, doc_create, user_id, commit=False)

    # D. Registrar en Kardex (Vinculado al Documento)
    for item in items_consumo:
         # IMPORTANTE: Re-leer costo unitario para ser consistentes con el movimiento contable
         producto = service_inventario.get_producto_by_id(db, item.insumo_id, empresa_id)
         service_inventario.registrar_movimiento_inventario(
             db=db,
             producto_id=item.insumo_id,
             bodega_id=bodega_origen_id,
             tipo_movimiento='SALIDA_PRODUCCION',
             cantidad=item.cantidad,
             costo_unitario=producto.costo_promedio, # El costo que se usó para el cálculo
             fecha=datetime.now(),
             documento_id=documento.id
         )

    # Actualizar Costo en Orden
    orden.costo_total_mp += total_costo_lote
    if orden.estado == models_prod.EstadoOrdenProduccion.PLANIFICADA:
        orden.estado = models_prod.EstadoOrdenProduccion.EN_PROCESO

    db.commit()
    return orden

# --- PROCESO: REGISTRAR RECURSO (MOD/CIF) ---

def agregar_recurso(db: Session, orden_id: int, recurso: schemas_prod.OrdenProduccionRecursoCreate, empresa_id: int):
    orden = get_orden_by_id(db, orden_id, empresa_id)
    if not orden: raise HTTPException(status_code=404, detail="Orden no encontrada")
    
    nuevo_recurso = models_prod.OrdenProduccionRecurso(
        orden_id=orden.id,
        descripcion=recurso.descripcion,
        tipo=recurso.tipo,
        valor=recurso.valor
    )
    db.add(nuevo_recurso)
    
    if recurso.tipo == models_prod.TipoRecurso.MANO_OBRA:
        orden.costo_total_mod += recurso.valor
    else:
        orden.costo_total_cif += recurso.valor
        
    db.commit()
    db.refresh(orden)
    return orden

# --- PROCESO: CIERRE DE ORDEN (ENTRADA PT) ---

def cerrar_orden(db: Session, orden_id: int, cantidad_real_obtenida: float, empresa_id: int, user_id: int):
    orden = get_orden_by_id(db, orden_id, empresa_id)
    if not orden: raise HTTPException(status_code=404, detail="Orden no encontrada")
    if orden.estado == models_prod.EstadoOrdenProduccion.CERRADA:
         raise HTTPException(status_code=400, detail="Orden ya cerrada")

    producto_pt = service_inventario.get_producto_by_id(db, orden.producto_id, empresa_id)
    grupo_pt = producto_pt.grupo_inventario
    
    # Validar Cuentas
    if not grupo_pt or not grupo_pt.cuenta_inventario_id or not grupo_pt.cuenta_costo_produccion_id:
         raise HTTPException(status_code=400, detail="Producto terminado no tiene cuentas configuradas.")

    # 1. Calcular Costos Totales
    costo_total_orden = orden.costo_total_mp + orden.costo_total_mod + orden.costo_total_cif
    if cantidad_real_obtenida <= 0:
        raise HTTPException(status_code=400, detail="Cantidad obtenida debe ser mayor a 0")
    
    costo_unitario_final = costo_total_orden / cantidad_real_obtenida
    
    # 2. Crear Documento de Entrada PT (Tipo: 'ENTRADA_PRODUCCION')
    tipo_doc = db.query(models_doc.TipoDocumento).filter(
        models_doc.TipoDocumento.empresa_id == empresa_id,
        models_doc.TipoDocumento.nombre.ilike('%ENTRADA%PROD%') 
    ).first()
    
    if not tipo_doc:
        # Fallback, buscar cualquier entrada o nota
        raise HTTPException(status_code=400, detail="No existe Tipo de Documento para Entrada de Producción.")

    movimientos_contables = []
    
    # A. DÉBITO a INVENTARIO (14) - Entrada PT
    movimientos_contables.append(schemas_doc.MovimientoContableCreate(
        cuenta_id=grupo_pt.cuenta_inventario_id,
        concepto=f"Entrada PT Orden #{orden.numero_orden} - {producto_pt.nombre}",
        debito=costo_total_orden,
        credito=0
    ))
    
    # B. CRÉDITO a COSTO (71/72/73) - Contrapartida (Descarga de Producción en Proceso)
    # Aquí hay una simplificación: Acreditamos todo a la cuenta de costo de producción del PT.
    # En un sistema más complejo, acreditaríamos 71, 72 y 73 proporcionalmente.
    # Para este MVP, usaremos la `cuenta_costo_produccion_id` del grupo del PT como la cuenta "Bridge" o de cierre de costos.
    movimientos_contables.append(schemas_doc.MovimientoContableCreate(
        cuenta_id=grupo_pt.cuenta_costo_produccion_id,
        concepto=f"Cierre Costos Orden #{orden.numero_orden}",
        debito=0,
        credito=costo_total_orden
    ))

    doc_create = schemas_doc.DocumentoCreate(
        empresa_id=empresa_id,
        tipo_documento_id=tipo_doc.id,
        fecha=date.today(),
        fecha_vencimiento=date.today(),
        observaciones=f"Cierre Orden Producción {orden.numero_orden}. Cantidad: {cantidad_real_obtenida}",
        movimientos=movimientos_contables,
        aplicaciones=[]
    )
    
    documento = service_documento.create_documento(db, doc_create, user_id, commit=False)

    # 3. Registrar en Kardex
    service_inventario.registrar_movimiento_inventario(
        db=db,
        producto_id=orden.producto_id,
        bodega_id=orden.bodega_destino_id,
        tipo_movimiento='ENTRADA_PRODUCCION',
        cantidad=cantidad_real_obtenida,
        costo_unitario=costo_unitario_final,
        fecha=datetime.now(),
        documento_id=documento.id
    )

    # 4. Actualizar Orden
    orden.cantidad_real = cantidad_real_obtenida
    orden.costo_unitario_final = costo_unitario_final
    orden.fecha_fin = date.today()
    orden.estado = models_prod.EstadoOrdenProduccion.CERRADA
    
    db.commit()
    db.refresh(orden)
    return orden

# --- LIFECYCLE MANAGEMENT ---

def anular_orden(db: Session, orden_id: int, motivo: str, empresa_id: int, user_id: int):
    """
    Anula una orden de producción.
    - Si está EN_PROCESO: Reversa consumo de insumos (Entrada a Bodega).
    - Si está CERRADA: Reversa consumo de insumos (Entrada) Y reversa producto terminado (Salida).
    - Genera documento contable de anulación.
    """
    orden = get_orden_by_id(db, orden_id, empresa_id)
    if not orden:
        raise HTTPException(status_code=404, detail="Orden no encontrada")
    
    if orden.estado == models_prod.EstadoOrdenProduccion.ANULADA:
        raise HTTPException(status_code=400, detail="La orden ya está anulada")
    
    if orden.estado not in [models_prod.EstadoOrdenProduccion.EN_PROCESO, models_prod.EstadoOrdenProduccion.CERRADA]:
        raise HTTPException(status_code=400, detail="Solo se pueden anular órdenes en proceso o cerradas. Para borradores, usa eliminar.")

    # Obtener configuración para Tipo de Documento
    config_prod = get_configuracion(db, empresa_id)
    if not config_prod or not config_prod.tipo_documento_anulacion_id:
        raise HTTPException(status_code=400, detail="No está configurado el Tipo de Documento para Anulaciones de Producción.")
    
    tipo_doc_id = config_prod.tipo_documento_anulacion_id
    
    # --- INICIO TRANSACCIÓN ---
    movimientos_contables = []
    
    # 1. Reversar Insumos (ENTRADA a Bodega Origen)
    for consumo in orden.insumos:
        cantidad_devolver = consumo.cantidad
        costo_unitario = consumo.costo_unitario_historico
        costo_total = cantidad_devolver * costo_unitario
        
        insumo_obj = consumo.insumo
        grupo = insumo_obj.grupo_inventario
        
        # Debito Inventario (Vuelve a entrar)
        movimientos_contables.append(schemas_doc.MovimientoContableCreate(
            cuenta_id=grupo.cuenta_inventario_id,
            debito=costo_total,
            credito=0,
            concepto=f"Reversión Insumo OP-{orden.numero_orden}",
            producto_id=insumo_obj.id
        ))
        # Credito Costo (Se anula el gasto)
        movimientos_contables.append(schemas_doc.MovimientoContableCreate(
            cuenta_id=grupo.cuenta_costo_id, 
            debito=0,
            credito=costo_total,
            concepto=f"Reversión Costo OP-{orden.numero_orden}",
            producto_id=insumo_obj.id
        ))
    
    # 2. Si estaba CERRADA, reversar Producto Terminado (SALIDA de Bodega Destino)
    if orden.estado == models_prod.EstadoOrdenProduccion.CERRADA:
        cant_pt = orden.cantidad_real
        costo_unitario_pt = orden.costo_unitario_final
        total_pt = cant_pt * costo_unitario_pt
        
        pt_obj = orden.producto
        grupo_pt = pt_obj.grupo_inventario
        
        # Credito Inventario (Sale)
        movimientos_contables.append(schemas_doc.MovimientoContableCreate(
            cuenta_id=grupo_pt.cuenta_inventario_id,
            debito=0,
            credito=total_pt,
            concepto=f"Reversión PT OP-{orden.numero_orden}",
            producto_id=pt_obj.id
        ))
        
        # Debito Costo/Bridge (Se reversa el ingreso a inventario)
        movimientos_contables.append(schemas_doc.MovimientoContableCreate(
            cuenta_id=grupo_pt.cuenta_costo_produccion_id, 
            debito=total_pt,
            credito=0,
            concepto=f"Reversión Cierre OP-{orden.numero_orden}",
            producto_id=pt_obj.id
        ))

    # Crear Documento Contable
    doc_anulacion = schemas_doc.DocumentoCreate(
        empresa_id=empresa_id,
        tipo_documento_id=tipo_doc_id,
        fecha=date.today(),
        concepto=f"ANULACIÓN OP-{orden.numero_orden}: {motivo}",
        movimientos=movimientos_contables
    )
    
    db_doc = service_documento.create_documento(db, doc_anulacion, user_id, commit=False)
    
    # 3. Aplicar Movimientos de Inventario (Kardex)
    # 3.1 MP (Entradas)
    for consumo in orden.insumos:
        service_inventario.registrar_movimiento_inventario(
            db, consumo.insumo_id, consumo.bodega_origen_id,
            'ENTRADA_AJUSTE', consumo.cantidad, consumo.costo_unitario_historico, # Usando Ajuste como proxy de devolucion
            datetime.now(), db_doc.id
        )
    
    # 3.2 PT (Salida) - Solo si Cerrada
    if orden.estado == models_prod.EstadoOrdenProduccion.CERRADA:
         service_inventario.registrar_movimiento_inventario(
            db, orden.producto_id, orden.bodega_destino_id,
            'SALIDA_AJUSTE', orden.cantidad_real, orden.costo_unitario_final,
            datetime.now(), db_doc.id
        )

    # 4. Actualizar estado de la orden
    orden.estado = models_prod.EstadoOrdenProduccion.ANULADA
    orden.motivo_anulacion = motivo
    
    db.commit()
    return orden

def archivar_orden(db: Session, orden_id: int, archivar: bool, empresa_id: int):
    orden = get_orden_by_id(db, orden_id, empresa_id)
    if not orden:
        raise HTTPException(status_code=404, detail="Orden no encontrada")
    
    orden.archivada = archivar
    db.commit()
    return orden

def delete_orden(db: Session, orden_id: int, empresa_id: int):
    orden = get_orden_by_id(db, orden_id, empresa_id)
    if not orden:
        raise HTTPException(status_code=404, detail="Orden no encontrada")
        
    if orden.estado != models_prod.EstadoOrdenProduccion.PLANIFICADA:
         raise HTTPException(status_code=400, detail="Solo se pueden eliminar órdenes en estado PLANIFICADA (Borrador). Si ya tiene movimientos, usa Anular.")
    
    db.delete(orden)
    db.commit()
    return True
