# app/services/reportes_financieros.py

from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.models import (
    movimiento_contable as models_mov,
    documento as models_doc,
    tipo_documento as models_tipo_doc,
    producto as models_prod,
    grupo_inventario as models_grupo
)
from app.schemas.reporte_rentabilidad import (
    RentabilidadProductoFiltros,
    RentabilidadProductoResponse,
    RentabilidadProductoItem
)

def get_reporte_rentabilidad_producto(db: Session, filtros: RentabilidadProductoFiltros, empresa_id: int) -> RentabilidadProductoResponse:
    """
    Calcula la rentabilidad de un producto específico en un rango de fechas.
    Versión final con corrección de tipos de datos y filtro de producto preciso.
    """

    query_items = (
        db.query(
            models_doc.Documento.fecha,
            func.concat(models_tipo_doc.TipoDocumento.codigo, '-', models_doc.Documento.numero).label('documento_ref'),
            models_prod.MovimientoInventario.cantidad,
            models_mov.MovimientoContable.credito.label('venta_total'),
            models_prod.MovimientoInventario.costo_unitario.label('costo_unitario_promedio')
        )
        .join(models_doc.Documento, models_prod.MovimientoInventario.documento_id == models_doc.Documento.id)
        .join(models_tipo_doc.TipoDocumento, models_doc.Documento.tipo_documento_id == models_tipo_doc.TipoDocumento.id)
        .join(models_prod.Producto, models_prod.MovimientoInventario.producto_id == models_prod.Producto.id)
        .join(models_grupo.GrupoInventario, models_prod.Producto.grupo_id == models_grupo.GrupoInventario.id)
        # --- INICIO DE LA CIRUGÍA ---
        # Se corrige el JOIN para que el movimiento contable también esté ligado al producto específico.
        .join(models_mov.MovimientoContable, and_(
            models_mov.MovimientoContable.documento_id == models_doc.Documento.id,
            models_mov.MovimientoContable.producto_id == models_prod.MovimientoInventario.producto_id, # <-- EL ESLABÓN QUE FALTABA
            models_mov.MovimientoContable.cuenta_id == models_grupo.GrupoInventario.cuenta_ingreso_id,
            models_mov.MovimientoContable.credito > 0
        ))
        # --- FIN DE LA CIRUGÍA ---
        .where(
            models_doc.Documento.empresa_id == empresa_id,
            models_prod.MovimientoInventario.producto_id == filtros.producto_id, # Este filtro ahora funcionará con precisión
            models_prod.MovimientoInventario.tipo_movimiento == 'SALIDA_VENTA',
            models_doc.Documento.fecha.between(filtros.fecha_inicio, filtros.fecha_fin),
            models_doc.Documento.anulado == False
        )
        .order_by(models_doc.Documento.fecha.asc())
    )

    resultados_db = query_items.all()

    items_finales = []
    total_venta = 0.0
    total_costo = 0.0

    for r in resultados_db:
        venta_total_float = float(r.venta_total)
        
        venta_unitaria_calculada = (venta_total_float / r.cantidad) if r.cantidad != 0 else 0
        costo_total_item = r.cantidad * r.costo_unitario_promedio
        utilidad_bruta_item = venta_total_float - costo_total_item
        margen_item = (utilidad_bruta_item / venta_total_float) if venta_total_float != 0 else 0

        items_finales.append(
            RentabilidadProductoItem(
                fecha=r.fecha,
                documento_ref=r.documento_ref,
                cantidad=r.cantidad,
                venta_unitaria=venta_unitaria_calculada,
                venta_total=venta_total_float,
                costo_unitario_promedio=r.costo_unitario_promedio,
                costo_total=costo_total_item,
                utilidad_bruta=utilidad_bruta_item,
                margen_rentabilidad=margen_item
            )
        )
        total_venta += venta_total_float
        total_costo += costo_total_item

    total_utilidad = total_venta - total_costo
    margen_total_porcentaje = (total_utilidad / total_venta) * 100 if total_venta != 0 else 0

    return RentabilidadProductoResponse(
        items=items_finales,
        total_venta=total_venta,
        total_costo=total_costo,
        total_utilidad=total_utilidad,
        margen_total_porcentaje=margen_total_porcentaje
    )