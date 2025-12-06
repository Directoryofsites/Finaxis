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
    
    debitos_inventario_por_cuenta: Dict[int, float] = {}
    impuestos_descontables_por_cuenta: Dict[int, float] = {}

    if not compra.items:
        raise HTTPException(status_code=400, detail="La factura de compra no tiene items.")

    for item in compra.items:
        producto_db = db.query(models_producto.Producto).options(
            joinedload(models_producto.Producto.grupo_inventario),
            joinedload(models_producto.Producto.impuesto_iva)
        ).filter(
            models_producto.Producto.id == item.producto_id,
            models_producto.Producto.empresa_id == empresa_id
        ).first()

        if not producto_db:
            raise HTTPException(status_code=404, detail=f"Producto con ID {item.producto_id} no encontrado.")

        if not producto_db.grupo_inventario or not producto_db.grupo_inventario.cuenta_inventario_id:
            grupo_nombre = producto_db.grupo_inventario.nombre if producto_db.grupo_inventario else "N/A"
            raise HTTPException(status_code=409, detail=f"El producto '{producto_db.nombre}' (grupo '{grupo_nombre}') no tiene una cuenta de inventario configurada.")
        
        if producto_db.impuesto_iva and not producto_db.impuesto_iva.cuenta_iva_descontable_id:
            raise HTTPException(status_code=409, detail=f"La tasa de impuesto '{producto_db.impuesto_iva.nombre}' no tiene una cuenta de IVA Descontable configurada.")
        
        subtotal_item = item.cantidad * item.costo_unitario
        valor_iva = 0

        if producto_db.impuesto_iva and producto_db.impuesto_iva.tasa > 0:
            valor_iva = subtotal_item * producto_db.impuesto_iva.tasa
            cuenta_iva_id = producto_db.impuesto_iva.cuenta_iva_descontable_id
            impuestos_descontables_por_cuenta[cuenta_iva_id] = impuestos_descontables_por_cuenta.get(cuenta_iva_id, 0) + valor_iva

        total_compra += subtotal_item + valor_iva
        
        cuenta_inventario_id = producto_db.grupo_inventario.cuenta_inventario_id
        debitos_inventario_por_cuenta[cuenta_inventario_id] = debitos_inventario_por_cuenta.get(cuenta_inventario_id, 0) + subtotal_item

    if total_compra > 0:
        for cuenta_id, total_cuenta in debitos_inventario_por_cuenta.items():
            movimientos_contables.append(schemas_doc.MovimientoContableCreate(
                cuenta_id=cuenta_id, concepto="Compra de mercancía", debito=total_cuenta, credito=0
            ))
        
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
        movimientos=movimientos_contables,
        aplicaciones=None 
    )

    try:
        with db.begin_nested():
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
                        bodega_id=compra.bodega_id, # <--- ¡CAMBIO CRÍTICO!
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
        raise HTTPException(status_code=500, detail=f"Error interno del servidor al crear la factura de compra: {e}")