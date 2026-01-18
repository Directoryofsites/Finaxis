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

    # --- FILTRO MAESTRO: SOLO CUENTAS POR COBRAR (CARTERA) ---
    # Para el "Extracto de Cuenta", solo nos interesan los movimientos de las cuentas 13xx (Cartera)
    # Obtenemos las cuentas configuradas en PHConfiguracion y/o las cuentas de CXC de los Tipos Doc.
    
    config = db.query(PHConfiguracion).filter(PHConfiguracion.empresa_id == empresa_id).first()
    ids_cartera = set()
    
    if config:
        if config.cuenta_cartera_id: ids_cartera.add(config.cuenta_cartera_id)
        # if config.cuenta_intereses_id: ids_cartera.add(config.cuenta_intereses_id) # ELIMINADO: Campo no existe
        
        # Tambien buscamos cuentas cxc de los tipos de documento usados en PH
        if config.tipo_documento_factura_id:
             td = db.query(TipoDocumento).filter(TipoDocumento.id == config.tipo_documento_factura_id).first()
             if td and td.cuenta_debito_cxc_id: ids_cartera.add(td.cuenta_debito_cxc_id)
             
    # Si no hay cuentas configuradas, intentamos fallback genérico a cuentas que empiecen por '13'
    # pero es mas seguro usar las configuradas para no traer ruido.
    
    # Para asegurar que traemos TODO lo de cartera, vamos a filtrar donde la cuenta sea de tipo "Deudores" (13)
    # OJO: Esto requiere joinear con PlanCuenta.
    
    from app.models.plan_cuenta import PlanCuenta
    query = query.join(PlanCuenta, MovimientoContable.cuenta_id == PlanCuenta.id)
    query = query.filter(PlanCuenta.codigo.like("13%")) # Convención estándar Colombia
    
    # ---------------------------------------------------------

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
        
        if config:
            if tipo_movimiento == 'FACTURAS':
                if config.tipo_documento_factura_id:
                    query = query.filter(Documento.tipo_documento_id == config.tipo_documento_factura_id)
            elif tipo_movimiento == 'RECIBOS':
                # Nota: Recibos no siempre tienen ID unico en config, podria ser cualquier comprobante
                # Mejor filtrar por naturaleza: Facturas (Debito > 0), Recibos (Credito > 0) dentro de Cartera
                if tipo_movimiento == 'FACTURAS':
                     query = query.filter(MovimientoContable.debito > 0)
                elif tipo_movimiento == 'RECIBOS':
                     query = query.filter(MovimientoContable.credito > 0)


    # Filtro Especial por Concepto de PH -> AHORA FILTRA POR DETALLE DE TEXTO O CONCEPTOS
    if concepto_id:
        # Si el usuario filtra por concepto, buscamos en el texto del movimiento
        # ya que ahora estamos filtrando solo cuentas de cartera.
        ph_concepto = db.query(PHConcepto).filter(PHConcepto.id == concepto_id).first()
        if ph_concepto:
             query = query.filter(MovimientoContable.concepto.ilike(f"%{ph_concepto.nombre}%"))

    # Ordenamiento: Ascendente para poder calcular saldos correctamente (opcional)
    # Pero el usuario pidió ver historial, usualmente Descendente. 
    # Para saldos acumulados en frontend, es mejor Ascendente y luego reversear, o hacerlo desc desde saldo final.
    # Mantendremos DESC como estaba.
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
