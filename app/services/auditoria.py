from sqlalchemy.orm import Session, aliased
from sqlalchemy import and_, func, case, union_all, select, literal_column, cast
from sqlalchemy.dialects import postgresql
from sqlalchemy.types import Date, String, Integer, Numeric
from fastapi import HTTPException
from typing import Optional, List, Dict, Any
from datetime import date, timedelta, datetime

from ..models import (
    Documento as models_doc,
    DocumentoEliminado as models_doc_elim,
    TipoDocumento as models_tipo,
    Tercero as models_tercero,
    Usuario as models_usuario,
    LogOperacion as models_log,
    Empresa as models_empresa,
    MovimientoContable as models_mov # <-- IMPORTACIÓN CORREGIDA Y AÑADIDA
)
from ..schemas import documento as schemas_doc
from ..schemas import auditoria as schemas_auditoria


def get_log_operaciones(
    db: Session,
    empresa_id: int,
    fecha_inicio: Optional[date],
    fecha_fin: Optional[date]
):
    query = db.query(models_log).filter(
        models_log.empresa_id == empresa_id
    )
    filter_conditions = []
    if fecha_inicio:
        filter_conditions.append(models_log.fecha_operacion >= fecha_inicio)
    if fecha_fin:
        fecha_fin_ajustada = fecha_fin + timedelta(days=1)
        filter_conditions.append(models_log.fecha_operacion < fecha_fin_ajustada)

    if filter_conditions:
        query = query.filter(and_(*filter_conditions))

    return query.order_by(models_log.fecha_operacion.desc()).all()

def _safe_parse_json_date(log_entry):
    try:
        detalle_json = log_entry.detalle_documento_json
        if isinstance(detalle_json, list) and detalle_json:
            fecha_str = detalle_json[0].get('fecha')
            return datetime.strptime(fecha_str, '%Y-%m-%d').date()
        return date.min
    except (TypeError, ValueError, AttributeError, KeyError):
        return date.min

def get_ultimas_operaciones_global(db: Session, request: schemas_auditoria.UltimasOperacionesRequest) -> List[dict]:


    # --- INICIO: SONDA DE DIAGNÓSTICO ---
    print("--- SONDA DE DATOS ENTRANTE EN SERVICIO 'auditoria.py' ---")
    try:
        # Usamos model_dump() para una representación limpia de los datos de Pydantic
        print(f"Request recibido: {request.model_dump()}")
    except Exception as e:
        print(f"No se pudo dumpear el request. Contenido bruto: {request}")
        print(f"Error al dumpear: {e}")
    print("---------------------------------------------------------")
    # --- FIN: SONDA DE DIAGNÓSTICO ---


    # --- Subconsulta para Documentos Creados/Anulados ---
    UsuarioCreador = aliased(models_usuario, name="creador")
    
    docs_creados = select(
        models_doc.id.label("id_operacion"),
        models_empresa.razon_social.label("empresa_razon_social"),
        models_doc.fecha_operacion.label("fecha_evento"),
        models_doc.fecha.label("fecha_documento"),
        UsuarioCreador.email.label("email_usuario"),
        case(
            (models_doc.anulado == True, 'ANULACIÓN'),
            else_='CREACIÓN'
        ).label("tipo_operacion"),
        (models_tipo.nombre + ' #' + cast(models_doc.numero, String)).label("detalle")
    ).select_from(models_doc) \
    .join(models_empresa, models_doc.empresa_id == models_empresa.id) \
    .join(models_tipo, models_doc.tipo_documento_id == models_tipo.id) \
    .outerjoin(UsuarioCreador, models_doc.usuario_creador_id == UsuarioCreador.id)

    # --- Subconsulta para Documentos Eliminados ---
    UsuarioEliminador = aliased(models_usuario, name="eliminador")

    docs_eliminados = select(
        models_doc_elim.id.label("id_operacion"),
        models_empresa.razon_social.label("empresa_razon_social"),
        models_doc_elim.fecha_eliminacion.label("fecha_evento"),
        models_doc_elim.fecha.label("fecha_documento"),
        UsuarioEliminador.email.label("email_usuario"),
        literal_column("'ELIMINACIÓN'").label("tipo_operacion"),
        (models_tipo.nombre + ' #' + cast(models_doc_elim.numero, String)).label("detalle")
    ).select_from(models_doc_elim) \
    .join(models_empresa, models_doc_elim.empresa_id == models_empresa.id) \
    .join(models_tipo, models_doc_elim.tipo_documento_id == models_tipo.id) \
    .outerjoin(UsuarioEliminador, models_doc_elim.usuario_eliminacion_id == UsuarioEliminador.id)

    # --- INICIO: MOTOR DE FILTRADO DINÁMICO ---

    # Filtro por Empresas
    if request.empresaIds:
        docs_creados = docs_creados.where(models_doc.empresa_id.in_(request.empresaIds))
        docs_eliminados = docs_eliminados.where(models_doc_elim.empresa_id.in_(request.empresaIds))

    # Filtro por Fecha de Creación/Evento del Registro
    if request.fecha_creacion_inicio:
        docs_creados = docs_creados.where(models_doc.fecha_operacion >= request.fecha_creacion_inicio)
        docs_eliminados = docs_eliminados.where(models_doc_elim.fecha_eliminacion >= request.fecha_creacion_inicio)
    if request.fecha_creacion_fin:
        fecha_fin_ajustada = request.fecha_creacion_fin.replace(hour=23, minute=59, second=59)
        docs_creados = docs_creados.where(models_doc.fecha_operacion <= fecha_fin_ajustada)
        docs_eliminados = docs_eliminados.where(models_doc_elim.fecha_eliminacion <= fecha_fin_ajustada)

    # Filtro por Fecha del Documento (fecha transaccional)
    if request.fecha_documento_inicio:
        docs_creados = docs_creados.where(models_doc.fecha >= request.fecha_documento_inicio.date())
        docs_eliminados = docs_eliminados.where(models_doc_elim.fecha >= request.fecha_documento_inicio.date())
    if request.fecha_documento_fin:
        docs_creados = docs_creados.where(models_doc.fecha <= request.fecha_documento_fin.date())
        docs_eliminados = docs_eliminados.where(models_doc_elim.fecha <= request.fecha_documento_fin.date())
    
    # --- FIN: MOTOR DE FILTRADO DINÁMICO ---

    # --- Unificar las consultas ---
    unified_query = union_all(docs_creados, docs_eliminados).alias('operaciones')

    # --- Construir la consulta final, ordenar y limitar ---
    query_base = select(unified_query)

    # --- INICIO DE LA CORRECCIÓN: Lógica de Ordenamiento Dinámico ---
    if request.orderBy == 'fecha_documento':
        # Si el frontend pide ordenar por la fecha interna del documento
        query_ordenada = query_base.order_by(unified_query.c.fecha_documento.desc().nullslast())
    else:
        # Por defecto, o si se pide explícitamente, se ordena por la fecha de creación del registro
        query_ordenada = query_base.order_by(unified_query.c.fecha_evento.desc().nullslast())
    # --- FIN DE LA CORRECCIÓN ---

    # Finalmente, aplicamos el límite a la consulta ya ordenada
    final_query = query_ordenada.limit(request.limit)
    
    resultados = db.execute(final_query).mappings().all()

   # Mapear a la estructura de respuesta esperada
    response_data = [
        {
            "id": res.id_operacion,
            "empresa_razon_social": res.empresa_razon_social,
            "fecha_operacion": res.fecha_evento,
            # --- INICIO DE LA MEJORA ---
            # Añadimos el campo que faltaba a la respuesta.
            "fecha_documento": res.fecha_documento,
            # --- FIN DE LA MEJORA ---
            "email_usuario": res.email_usuario,
            "tipo_operacion": res.tipo_operacion,
            "detalle_documento": res.detalle,
            "razon": ""
        } for res in resultados
    ]

    return response_data

def get_auditoria_consecutivos(db: Session, empresa_id: int, tipo_documento_id: int) -> schemas_doc.AuditoriaConsecutivosResponse:
    tipo_doc = db.query(
        models_tipo.nombre,
        models_tipo.consecutivo_actual
    ).filter(
        models_tipo.id == tipo_documento_id,
        models_tipo.empresa_id == empresa_id
    ).first()

    if not tipo_doc:
        raise HTTPException(status_code=404, detail="Tipo de documento no encontrado para esta empresa.")

    UsuarioCreador = aliased(models_usuario)
    UsuarioEliminador = aliased(models_usuario)
    TerceroActivo = aliased(models_tercero)
    TerceroEliminado = aliased(models_tercero)
    LogAnulacion = aliased(models_log)

    subquery_total_activo = db.query(
        models_mov.documento_id,
        func.sum(models_mov.debito).label("total_documento")
    ).group_by(models_mov.documento_id).subquery()

    query_activos_anulados = select(
        case((models_doc.anulado == True, 'ANULADO'), else_='ACTIVO').label('estado'),
        models_doc.numero,
        # --- INICIO: CORRECCIÓN DE FECHAS ---
        models_doc.fecha.label('fecha_documento'),
        models_doc.fecha_operacion.label('fecha_operacion'),
        # --- FIN: CORRECCIÓN DE FECHAS ---
        TerceroActivo.razon_social.label('beneficiario_nombre'),
        subquery_total_activo.c.total_documento,
        UsuarioCreador.nombre_completo.label('usuario_operacion'),
        LogAnulacion.razon.label('razon_operacion')
    ).select_from(models_doc) \
    .join(subquery_total_activo, models_doc.id == subquery_total_activo.c.documento_id) \
    .outerjoin(UsuarioCreador, models_doc.usuario_creador_id == UsuarioCreador.id) \
    .outerjoin(TerceroActivo, models_doc.beneficiario_id == TerceroActivo.id) \
    .outerjoin(
        LogAnulacion,
        and_(
            cast(cast(LogAnulacion.detalle_documento_json[0]['id'], String), Integer) == models_doc.id,
            LogAnulacion.tipo_operacion == 'ANULACION',
            LogAnulacion.empresa_id == empresa_id
        )
    ) \
    .where(
        models_doc.empresa_id == empresa_id,
        models_doc.tipo_documento_id == tipo_documento_id
    )

    query_eliminados = select(
        literal_column("'ELIMINADO'").cast(String).label('estado'),
        models_doc_elim.numero.cast(Integer).label('numero'),
        # --- INICIO: CORRECCIÓN DE FECHAS ---
        models_doc_elim.fecha.label('fecha_documento'),
        models_doc_elim.fecha_eliminacion.cast(Date).label('fecha_operacion'),
        # --- FIN: CORRECIÓN DE FECHAS ---
        TerceroEliminado.razon_social.label('beneficiario_nombre'),
        literal_column("0").cast(Numeric).label('total_documento'),
        UsuarioEliminador.nombre_completo.label('usuario_operacion'),
        models_log.razon.label('razon_operacion')
    ).select_from(models_doc_elim) \
    .outerjoin(UsuarioEliminador, models_doc_elim.usuario_eliminacion_id == UsuarioEliminador.id) \
    .outerjoin(TerceroEliminado, models_doc_elim.beneficiario_id == TerceroEliminado.id) \
    .outerjoin(models_log, models_doc_elim.log_eliminacion_id == models_log.id) \
    .where(
        models_doc_elim.empresa_id == empresa_id,
        models_doc_elim.tipo_documento_id == tipo_documento_id
    )

    unified_query = union_all(query_activos_anulados, query_eliminados).alias('unified')
    final_query = select(unified_query).order_by(unified_query.c.numero)

    documentos_encontrados = db.execute(final_query).mappings().all()
    
    # El resto de la lógica para detectar huecos no necesita cambios y sigue aquí...
    resultados_finales = []
    huecos_count = 0
    expected_numero = 1

    for doc in documentos_encontrados:
        numero_actual = int(doc.numero)
        if numero_actual > expected_numero:
            gap = schemas_doc.AuditoriaConsecutivoGap(
                numero_faltante_inicio=expected_numero,
                numero_faltante_fin=numero_actual - 1,
                cantidad_faltante=(numero_actual - expected_numero)
            )
            resultados_finales.append(gap)
            huecos_count += 1

        # El mapeo ahora funcionará porque los nombres de las columnas coinciden con el schema
        item = schemas_doc.AuditoriaConsecutivoItem(**doc)
        resultados_finales.append(item)
        expected_numero = numero_actual + 1

    ultimo_consecutivo = int(tipo_doc.consecutivo_actual) if tipo_doc.consecutivo_actual is not None else 0
    if ultimo_consecutivo >= expected_numero:
        gap = schemas_doc.AuditoriaConsecutivoGap(
            numero_faltante_inicio=expected_numero,
            numero_faltante_fin=ultimo_consecutivo,
            cantidad_faltante=(ultimo_consecutivo - expected_numero + 1)
        )
        resultados_finales.append(gap)
        huecos_count += 1
    
    return schemas_doc.AuditoriaConsecutivosResponse(
        tipo_documento_nombre=tipo_doc.nombre,
        ultimo_consecutivo_registrado=ultimo_consecutivo,
        total_documentos_encontrados=len(documentos_encontrados),
        total_huecos_encontrados=huecos_count,
        resultados=resultados_finales
    )