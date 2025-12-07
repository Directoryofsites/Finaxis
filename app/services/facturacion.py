# app/services/facturacion.py (VERSIÓN CORREGIDA: FECHA VENCIMIENTO MANUAL OBLIGATORIA)

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from fastapi import HTTPException, status
from typing import List, Dict
from datetime import datetime, time

from ..models import tipo_documento as models_tipo
from ..models import producto as models_producto
from ..models import grupo_inventario as models_grupo
from ..models import impuesto as models_impuesto
from ..models import bodega as models_bodega
from ..models import documento as models_doc
from ..models import tercero as models_tercero 

from ..schemas import facturacion as schemas_facturacion
from ..schemas import documento as schemas_doc

from . import documento as service_documento
from . import inventario as service_inventario

def crear_factura_venta(db: Session, factura: schemas_facturacion.FacturaCreate, user_id: int, empresa_id: int):
    """
    Servicio orquestador para crear una factura de venta.
    Logica de Vencimiento: Manual y Obligatoria para Crédito.
    """
    # 1. Obtener Tipo de Documento
    tipo_doc = db.query(models_tipo.TipoDocumento).filter(
        models_tipo.TipoDocumento.id == factura.tipo_documento_id,
        models_tipo.TipoDocumento.empresa_id == empresa_id
    ).first()

    if not tipo_doc:
        raise HTTPException(status_code=404, detail="Tipo de documento no encontrado.")

    # 2. Validar Bodega (si aplica)
    bodega_db = None
    if tipo_doc.afecta_inventario:
        if not factura.bodega_id:
             raise HTTPException(status_code=400, detail="Debe seleccionar una bodega para la salida de inventario.")
        bodega_db = db.query(models_bodega.Bodega).filter(
            models_bodega.Bodega.id == factura.bodega_id,
            models_bodega.Bodega.empresa_id == empresa_id
        ).first()
        if not bodega_db:
            raise HTTPException(status_code=400, detail=f"La bodega con ID {factura.bodega_id} no es válida o no pertenece a su empresa.")

    # 3. Validar Cliente
    cliente = db.query(models_tercero.Tercero).filter(
        models_tercero.Tercero.id == factura.beneficiario_id,
        models_tercero.Tercero.empresa_id == empresa_id
    ).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado.")

    # --- LOGICA DE VENCIMIENTO CORREGIDA (MANUAL) ---
    fecha_vencimiento_final = factura.fecha # Por defecto igual a la fecha (Contado)
    
    if factura.condicion_pago == 'Crédito':
        # Si es crédito, la fecha de vencimiento es OBLIGATORIA y viene del frontend
        if not factura.fecha_vencimiento:
             raise HTTPException(status_code=400, detail="Para ventas a Crédito, debe especificar la Fecha de Vencimiento manualmente.")
        
        if factura.fecha_vencimiento < factura.fecha:
             raise HTTPException(status_code=400, detail="La fecha de vencimiento no puede ser anterior a la fecha de la factura.")
             
        fecha_vencimiento_final = factura.fecha_vencimiento
    # ------------------------------------------------

    movimientos_contables = []
    total_factura = 0
    impuestos_generados_por_cuenta: Dict[int, float] = {}

    if not factura.items:
        raise HTTPException(status_code=400, detail="La factura de venta no tiene items.")

    # Convertir fecha a datetime
    if not isinstance(factura.fecha, datetime):
        fecha_factura_dt = datetime.combine(factura.fecha, time.min)
    else:
        fecha_factura_dt = factura.fecha

    # Pre-cargar productos
    productos_ids = [item.producto_id for item in factura.items]
    productos_db = db.query(models_producto.Producto).options(
        joinedload(models_producto.Producto.grupo_inventario),
        joinedload(models_producto.Producto.impuesto_iva)
    ).filter(
        models_producto.Producto.id.in_(productos_ids),
        models_producto.Producto.empresa_id == empresa_id
    ).all()
    productos_map = {p.id: p for p in productos_db}

    try:
        with db.begin_nested():
            for item in factura.items:
                producto_db = productos_map.get(item.producto_id)
                if not producto_db:
                    raise HTTPException(status_code=404, detail=f"Producto ID {item.producto_id} no encontrado.")

                # Validaciones contables
                if not producto_db.grupo_inventario or not producto_db.grupo_inventario.cuenta_ingreso_id:
                    raise HTTPException(status_code=409, detail=f"Producto '{producto_db.nombre}': Falta cuenta de Ingresos en Grupo.")
                if not producto_db.es_servicio:
                    if not producto_db.grupo_inventario.cuenta_costo_venta_id: raise HTTPException(status_code=409, detail=f"Producto '{producto_db.nombre}': Falta cuenta Costo Venta en Grupo.")
                    if not producto_db.grupo_inventario.cuenta_inventario_id: raise HTTPException(status_code=409, detail=f"Producto '{producto_db.nombre}': Falta cuenta Inventario en Grupo.")
                if producto_db.impuesto_iva and not producto_db.impuesto_iva.cuenta_id: raise HTTPException(status_code=409, detail=f"Impuesto '{producto_db.impuesto_iva.nombre}': Falta cuenta IVA Generado.")

                # Validación de Stock (con bloqueo)
                if tipo_doc.afecta_inventario and bodega_db and not producto_db.es_servicio:
                    stock_bodega_actual = db.query(models_producto.StockBodega).filter(
                        models_producto.StockBodega.producto_id == item.producto_id,
                        models_producto.StockBodega.bodega_id == factura.bodega_id
                    ).with_for_update().first()

                    stock_fisico = stock_bodega_actual.stock_actual if stock_bodega_actual else 0.0
                    stock_comprometido = stock_bodega_actual.stock_comprometido if stock_bodega_actual else 0.0
                    
                    # LOGICA DE DISPONIBILIDAD (FIX REMISIONES)
                    # Si NO es una facturación de remisión, debemos respetar el stock comprometido.
                    # Si ES una facturación de remisión, asumimos que estamos consumiendo nuestra propia reserva (validamos contra físico).
                    stock_disponible = stock_fisico
                    if not factura.remision_id:
                        stock_disponible = stock_fisico - stock_comprometido

                    if stock_disponible < item.cantidad:
                        msg_stock = f"Stock insuficiente para '{producto_db.nombre}'."
                        if not factura.remision_id:
                            msg_stock += f" Físico: {stock_fisico:.2f}, Comprometido: {stock_comprometido:.2f}, Disp: {stock_disponible:.2f}"
                        else:
                            msg_stock += f" Físico: {stock_fisico:.2f}"
                        raise HTTPException(status_code=409, detail=f"{msg_stock}, Req: {item.cantidad:.2f}")

                # Cálculos
                subtotal_item = item.cantidad * item.precio_unitario
                valor_iva = 0
                if producto_db.impuesto_iva and producto_db.impuesto_iva.tasa > 0:
                    valor_iva = subtotal_item * producto_db.impuesto_iva.tasa
                    cuenta_iva_id = producto_db.impuesto_iva.cuenta_id
                    impuestos_generados_por_cuenta[cuenta_iva_id] = impuestos_generados_por_cuenta.get(cuenta_iva_id, 0) + valor_iva
                total_factura += subtotal_item + valor_iva

                # Asientos Ingreso
                movimientos_contables.append(schemas_doc.MovimientoContableCreate(
                    cuenta_id=producto_db.grupo_inventario.cuenta_ingreso_id,
                    producto_id=item.producto_id,
                    concepto=f"Venta: {producto_db.nombre}",
                    debito=0, credito=subtotal_item
                ))
                
                # Asientos Costo
                if not producto_db.es_servicio:
                    costo_total_item = item.cantidad * (producto_db.costo_promedio or 0.0)
                    if costo_total_item > 0:
                        movimientos_contables.append(schemas_doc.MovimientoContableCreate(
                            cuenta_id=producto_db.grupo_inventario.cuenta_costo_venta_id,
                            producto_id=item.producto_id,
                            concepto=f"Costo Venta: {producto_db.nombre}",
                            debito=costo_total_item, credito=0
                        ))
                        movimientos_contables.append(schemas_doc.MovimientoContableCreate(
                            cuenta_id=producto_db.grupo_inventario.cuenta_inventario_id,
                            producto_id=item.producto_id,
                            concepto=f"Salida Inv: {producto_db.nombre}",
                            debito=0, credito=costo_total_item
                        ))

            # Asientos Consolidados
            if total_factura > 0:
                cuenta_debito_id = None
                if factura.condicion_pago == 'Crédito': cuenta_debito_id = tipo_doc.cuenta_debito_cxc_id
                elif factura.condicion_pago == 'Contado': cuenta_debito_id = tipo_doc.cuenta_caja_id
                
                if not cuenta_debito_id: raise HTTPException(status_code=400, detail=f"Falta configurar cuenta para pago '{factura.condicion_pago}' en Tipo Doc.")
                
                movimientos_contables.append(schemas_doc.MovimientoContableCreate(
                    cuenta_id=cuenta_debito_id,
                    concepto="Causación Factura Venta",
                    debito=total_factura, credito=0
                ))
                
                for cuenta_iva, valor in impuestos_generados_por_cuenta.items():
                    movimientos_contables.append(schemas_doc.MovimientoContableCreate(
                        cuenta_id=cuenta_iva,
                        concepto="IVA Generado",
                        debito=0, credito=valor
                    ))

            # Crear Documento
            documento_payload = schemas_doc.DocumentoCreate(
                tipo_documento_id=factura.tipo_documento_id,
                numero=None,
                empresa_id=empresa_id,
                beneficiario_id=factura.beneficiario_id,
                fecha=factura.fecha,
                fecha_vencimiento=fecha_vencimiento_final, # Guardamos la fecha manual
                centro_costo_id=factura.centro_costo_id,
                movimientos=movimientos_contables,
                aplicaciones=None
            )

            nuevo_documento = service_documento.create_documento(
                db=db, documento=documento_payload, user_id=user_id, commit=False
            )

            # Kardex
            if tipo_doc.afecta_inventario and bodega_db:
                for item in factura.items:
                    p_db = productos_map.get(item.producto_id)
                    if p_db and not p_db.es_servicio:
                        service_inventario.registrar_movimiento_inventario(
                            db=db,
                            producto_id=item.producto_id,
                            bodega_id=factura.bodega_id,
                            tipo_movimiento='SALIDA_VENTA',
                            cantidad=item.cantidad,
                            costo_unitario=(p_db.costo_promedio or 0.0),
                            documento_id=nuevo_documento.id,
                            fecha=fecha_factura_dt
                        )

            # --- INTEGRACIÓN REMISIONES ---
            if factura.remision_id:
                from . import remision as service_remision
                service_remision.procesar_facturacion_remision(db, factura.remision_id, factura.items)
            
            # --- INTEGRACIÓN COTIZACIONES ---
            if factura.cotizacion_id:
                from . import cotizacion as service_cotizacion
                service_cotizacion.procesar_facturacion_cotizacion(db, factura.cotizacion_id, factura.items)
            # --------------------------------

        db.commit()
        db.refresh(nuevo_documento)
        return nuevo_documento

    except Exception as e:
        db.rollback()
        if isinstance(e, HTTPException): raise e
        print(f"ERROR FACTURACION: {e}")
        raise HTTPException(status_code=500, detail="Error interno al crear factura.")