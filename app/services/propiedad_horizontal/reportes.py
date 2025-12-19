from sqlalchemy.orm import Session, joinedload
from sqlalchemy import text
from typing import List, Optional
from datetime import date
from app.models.documento import Documento
from app.models.movimiento_contable import MovimientoContable
from app.models.propiedad_horizontal.unidad import PHUnidad
from app.models.propiedad_horizontal.concepto import PHConcepto
from app.models.tercero import Tercero
from app.models.tipo_documento import TipoDocumento

def get_movimientos_ph_report(
    db: Session,
    empresa_id: int,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
    unidad_id: Optional[int] = None,
    propietario_id: Optional[int] = None,
    tipo_documento_id: Optional[int] = None,
    concepto_id: Optional[int] = None,
    numero_doc: Optional[str] = None,
    tipo_movimiento: Optional[str] = None # 'FACTURAS', 'RECIBOS', 'TODOS'
):
    """
    Genera un reporte detallado de movimientos para PH.
    Permite filtrar por múltiples criterios.
    """
    from app.models.propiedad_horizontal.configuracion import PHConfiguracion
    
    # Base Query: Movimientos Contables enlazados a Documentos
    # Seleccionamos campos relevantes
    query = db.query(
        Documento.fecha,
        TipoDocumento.codigo.label("tipo_doc"),
        Documento.numero,
        PHUnidad.codigo.label("unidad"),
        Tercero.razon_social.label("propietario"),
        MovimientoContable.concepto.label("detalle"),
        MovimientoContable.debito,
        MovimientoContable.credito,
        Documento.observaciones
    ).join(Documento, MovimientoContable.documento_id == Documento.id)\
     .join(TipoDocumento, Documento.tipo_documento_id == TipoDocumento.id)\
     .outerjoin(PHUnidad, Documento.unidad_ph_id == PHUnidad.id)\
     .outerjoin(Tercero, Documento.beneficiario_id == Tercero.id)

    # Filtros Obligatorios
    query = query.filter(Documento.empresa_id == empresa_id)
    query = query.filter(Documento.estado.in_(['ACTIVO', 'PROCESADO']))
    # --- CORRECCIÓN: Filtrar solo documentos de PH (vinculados a una unidad) ---
    query = query.filter(Documento.unidad_ph_id != None)

    # Filtros Opcionales
    if fecha_desde:
        query = query.filter(Documento.fecha >= fecha_desde)
    if fecha_hasta:
        query = query.filter(Documento.fecha <= fecha_hasta)
    
    if unidad_id:
        query = query.filter(Documento.unidad_ph_id == unidad_id)
    
    if propietario_id:
        query = query.filter(Documento.beneficiario_id == propietario_id)
    
    if tipo_documento_id:
        query = query.filter(Documento.tipo_documento_id == tipo_documento_id)
    
    if numero_doc:
        from sqlalchemy import cast, String
        query = query.filter(cast(Documento.numero, String).ilike(f"%{numero_doc}%"))

    # Filtro por Tipo de Movimiento (Facturas vs Recibos)
    if tipo_movimiento and tipo_movimiento in ['FACTURAS', 'RECIBOS']:
        config = db.query(PHConfiguracion).filter(PHConfiguracion.empresa_id == empresa_id).first()
        
        if config:
            if tipo_movimiento == 'FACTURAS':
                if config.tipo_documento_factura_id:
                    query = query.filter(Documento.tipo_documento_id == config.tipo_documento_factura_id)
            elif tipo_movimiento == 'RECIBOS':
                if config.tipo_documento_recibo_id:
                    query = query.filter(Documento.tipo_documento_id == config.tipo_documento_recibo_id)

    # Filtro Especial por Concepto de PH
    # Si se selecciona un concepto PH, buscamos movimientos que afecten a la cuenta de ingreso asociada.
    if concepto_id:
        ph_concepto = db.query(PHConcepto).filter(
            PHConcepto.id == concepto_id, 
            PHConcepto.empresa_id == empresa_id
        ).first()
        
        if ph_concepto and ph_concepto.cuenta_ingreso_id:
            query = query.filter(MovimientoContable.cuenta_id == ph_concepto.cuenta_ingreso_id)

    # Ordenamiento
    query = query.order_by(Documento.fecha.desc(), Documento.id.desc())

    results = query.all()

    # Formatear salida
    reporte = []
    for row in results:
        reporte.append({
            "fecha": row.fecha,
            "tipo_doc": row.tipo_doc,
            "numero": row.numero,
            "unidad": row.unidad or "N/A",
            "propietario": row.propietario or "N/A",
            "detalle": row.detalle,  # Concepto del movimiento
            "observaciones": row.observaciones, # Observaciones del documento general
            "debito": float(row.debito or 0),
            "credito": float(row.credito or 0)
        })
    
    return reporte
