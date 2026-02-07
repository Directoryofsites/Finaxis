from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException, status
from typing import List, Dict
from datetime import datetime

# Importamos los modelos y schemas necesarios
from ..models import tipo_documento as models_tipo
from ..models import producto as models_producto
from ..models import grupo_inventario as models_grupo
from ..models import impuesto as models_impuesto
from ..models import bodega as models_bodega # <--- NUEVA IMPORTACIÓN
from ..schemas import compras as schemas_compras
from ..schemas import documento as schemas_doc

# Importamos los servicios que vamos a orquestar
from . import documento as service_documento
from . import inventario as service_inventario

def crear_factura_compra(db: Session, compra: schemas_compras.CompraCreate, user_id: int, empresa_id: int):
    """
    Servicio orquestador para crear una factura de compra (versión final).
    Ahora acepta un bodega_id dinámico y lo valida.
    """
    
    tipo_doc = db.query(models_tipo.TipoDocumento).filter(
        models_tipo.TipoDocumento.id == compra.tipo_documento_id,
        models_tipo.TipoDocumento.empresa_id == empresa_id
    ).first()

    if not tipo_doc:
        raise HTTPException(status_code=404, detail="Tipo de documento no encontrado.")

    movimientos_contables = []
    total_compra = 0
    
    debitos_inventario_por_cuenta = {} # DEPRECATED: Se usa movimiento detallado
    impuestos_descontables_por_cuenta: Dict[int, float] = {}

    # --- LÓGICA DE PRORRATEO COMPRAS (DOBLE PASADA) ---
    items_procesados = []
    total_base_para_prorrateo = 0.0
    
    # Cargar Productos
    productos_ids = [item.producto_id for item in compra.items]
    productos_db = db.query(models_producto.Producto).options(
        joinedload(models_producto.Producto.grupo_inventario),
        joinedload(models_producto.Producto.impuesto_iva)
    ).filter(
        models_producto.Producto.id.in_(productos_ids),
        models_producto.Producto.empresa_id == empresa_id
    ).all()
    productos_map = {p.id: p for p in productos_db}

    # Paso 1: Validaciones y Bases
    for item in compra.items:
        producto_db = productos_map.get(item.producto_id)
        if not producto_db:
             raise HTTPException(status_code=404, detail=f"Producto con ID {item.producto_id} no encontrado.")

        if not producto_db.grupo_inventario or not producto_db.grupo_inventario.cuenta_inventario_id:
            grupo_nombre = producto_db.grupo_inventario.nombre if producto_db.grupo_inventario else "N/A"
            raise HTTPException(status_code=409, detail=f"El producto '{producto_db.nombre}' (grupo '{grupo_nombre}') no tiene una cuenta de inventario configurada.")
        
        if producto_db.impuesto_iva and not producto_db.impuesto_iva.cuenta_iva_descontable_id:
            raise HTTPException(status_code=409, detail=f"La tasa de impuesto '{producto_db.impuesto_iva.nombre}' no tiene una cuenta de IVA Descontable configurada.")

        # Cálculos de Línea
        costo_base = float(item.costo_unitario)
        tasa_desc = float(item.descuento_tasa or 0)
        subtotal_bruto = float(item.cantidad) * costo_base
        valor_desc_linea = subtotal_bruto * (tasa_desc / 100.0)
        subtotal_neto_linea = subtotal_bruto - valor_desc_linea
        
        total_base_para_prorrateo += subtotal_neto_linea
        
        items_procesados.append({
            "item_input": item,
            "producto_db": producto_db,
            "subtotal_neto_linea": subtotal_neto_linea,
            "valor_desc_linea": valor_desc_linea
        })

    # Paso 2: Generación
    desc_global_val = float(compra.descuento_global_valor or 0)
    cargo_global_val = float(compra.cargos_globales_valor or 0)
    
    for procesado in items_procesados:
        item = procesado["item_input"]
        producto_db = procesado["producto_db"]
        subtotal_neto = procesado["subtotal_neto_linea"]
        
        # Prorrateo
        participacion = 0.0
        if total_base_para_prorrateo > 0:
            participacion = subtotal_neto / total_base_para_prorrateo
            
        dist_desc_global = participacion * desc_global_val
        dist_cargo_global = participacion * cargo_global_val
        
        base_contable_final = subtotal_neto - dist_desc_global + dist_cargo_global
        total_descuento_acumulado = procesado["valor_desc_linea"] + dist_desc_global # Para registro
        
        # IVA (Descontable)
        valor_iva = 0
        if producto_db.impuesto_iva and producto_db.impuesto_iva.tasa > 0:
            valor_iva = base_contable_final * float(producto_db.impuesto_iva.tasa)
            cuenta_iva_id = producto_db.impuesto_iva.cuenta_iva_descontable_id
            impuestos_descontables_por_cuenta[cuenta_iva_id] = impuestos_descontables_por_cuenta.get(cuenta_iva_id, 0) + valor_iva

        total_compra += base_contable_final + valor_iva
        
        cuenta_inventario_id = producto_db.grupo_inventario.cuenta_inventario_id
        
        # Movimiento Inventario (Debito)
        movimientos_contables.append(schemas_doc.MovimientoContableCreate(
            cuenta_id=cuenta_inventario_id,
            producto_id=item.producto_id,
            cantidad=item.cantidad,
            concepto=f"Compra: {producto_db.nombre}",
            debito=base_contable_final, 
            credito=0,
            descuento_tasa=item.descuento_tasa,
            descuento_valor=total_descuento_acumulado
        ))

    if total_compra > 0:
        # Impuestos acumulados
        for cuenta_id, total_cuenta in impuestos_descontables_por_cuenta.items():
            movimientos_contables.append(schemas_doc.MovimientoContableCreate(
                cuenta_id=cuenta_id, concepto="IVA Descontable en compra", debito=total_cuenta, credito=0
            ))
        
        if not tipo_doc.cuenta_credito_cxp_id:
             raise HTTPException(status_code=409, detail="El tipo de documento no tiene configurada una cuenta de Proveedores (crédito).")
        
        movimientos_contables.append(schemas_doc.MovimientoContableCreate(
            cuenta_id=tipo_doc.cuenta_credito_cxp_id, concepto="Compra de mercancía", debito=0, credito=total_compra
        ))

    documento_payload = schemas_doc.DocumentoCreate(
        tipo_documento_id=compra.tipo_documento_id,
        numero=compra.numero,
        empresa_id=empresa_id,
        beneficiario_id=compra.beneficiario_id,
        fecha=compra.fecha,
        fecha_vencimiento=compra.fecha_vencimiento,
        centro_costo_id=compra.centro_costo_id,
        
        # --- NUEVO: Pasar valores ---
        descuento_global_valor=compra.descuento_global_valor,
        cargos_globales_valor=compra.cargos_globales_valor,
        # ----------------------------

        movimientos=movimientos_contables,
        aplicaciones=None 
    )

    try:
        # Eliminamos el begin_nested() que causaba conflictos con el commit manual
        # y simplificamos el manejo de transacciones.
        
        nuevo_documento = service_documento.create_documento(
            db=db, documento=documento_payload, user_id=user_id, commit=False
        )

        # --- INICIO DE LA CIRUGÍA FINAL ---
        if tipo_doc.afecta_inventario:
            # 1. Validación de Seguridad: Verificamos que la bodega exista y pertenezca a la empresa.
            bodega_db = db.query(models_bodega.Bodega).filter(
                models_bodega.Bodega.id == compra.bodega_id,
                models_bodega.Bodega.empresa_id == empresa_id
            ).first()
            if not bodega_db:
                raise HTTPException(status_code=400, detail=f"La bodega con ID {compra.bodega_id} no es válida o no pertenece a su empresa.")

            for item in compra.items:
                # 2. Uso del Valor Dinámico: Reemplazamos el '1' por el ID verificado.
                service_inventario.registrar_movimiento_inventario(
                    db=db,
                    producto_id=item.producto_id,
                    bodega_id=compra.bodega_id,
                    tipo_movimiento='ENTRADA_COMPRA',
                    cantidad=item.cantidad,
                    costo_unitario=item.costo_unitario,
                    documento_id=nuevo_documento.id,
                    fecha=compra.fecha
                )
        # --- FIN DE LA CIRUGÍA FINAL ---

        db.commit()
        db.refresh(nuevo_documento)
        return nuevo_documento
    except Exception as e:
        db.rollback()
        if isinstance(e, HTTPException): raise e
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error interno del servidor al crear la factura de compra: {e}")