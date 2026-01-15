from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime
from sqlalchemy import func, desc, asc, or_, and_

from app.core.database import get_db
from app.core.security import get_current_user
from app.schemas.consumo import ResumenConsumo, PlanMensualRead, BolsaItemRead, RecargaItemRead, HistorialConsumoRead, HistorialConsumoPage
from app.models.consumo_registros import ControlPlanMensual, BolsaExcedente, RecargaAdicional, HistorialConsumo, EstadoPlan, EstadoBolsa, EstadoRecarga, TipoFuenteConsumo, TipoOperacionConsumo
from app.models.empresa import Empresa
from app.models.configuracion_sistema import ConfiguracionSistema
from app.services.consumo_service import _get_or_create_plan_mensual, PAQUETES_RECARGA, comprar_recarga
from pydantic import BaseModel

router = APIRouter()

@router.get("/precio-unitario")
def get_precio_unitario(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """Retorna el precio unitario configurado para recargas personalizadas."""
    # Prioridad 1: Precio personalizado de la empresa
    if current_user.empresa and current_user.empresa.precio_por_registro is not None:
        return {"precio": current_user.empresa.precio_por_registro}

    # Prioridad 2: Precio global del sistema
    config = db.query(ConfiguracionSistema).filter_by(clave="PRECIO_POR_REGISTRO").first()
    return {"precio": int(config.valor) if config else 150}

@router.get("/resumen", response_model=ResumenConsumo)
def get_resumen_consumo(
    mes: int = Query(None, ge=1, le=12, description="Mes a consultar (1-12)"),
    anio: int = Query(None, ge=2000, description="Año a consultar"),
    empresa_id: int = Query(None, description="ID de empresa (Solo Soporte/Admin)"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
) -> Any:
    """
    Obtiene el estado actual del cupo de registros para el periodo especificado:
    - Plan Mensual del mes/año solicitado.
    - Bolsas de excedentes vigentes EN ese periodo.
    - Recargas adicionales vigentes EN ese periodo.
    """
    # Lógica de Seguridad para Override
    target_empresa_id = current_user.empresa_id
    
    if empresa_id and empresa_id != current_user.empresa_id:
        # Verificar permisos elevados
        roles_permitidos = ['soporte', 'administrador', 'super_admin', 'dev']
        tiene_permiso = any(r.nombre.lower() in roles_permitidos for r in current_user.roles)
        
        if tiene_permiso:
            target_empresa_id = empresa_id
        # Si no tiene permiso, falla silenciosamente y usa su propia empresa (o podría lanzar 403)
    
    now = datetime.now()
    
    # Defaults si no se especifican
    query_mes = mes if mes else now.month
    query_anio = anio if anio else now.year
    
    # Fecha de referencia para el periodo consultado (Primer día del mes)
    
    # Construir fecha arbitraria para el servicio (día 1)
    fecha_consulta = datetime(query_anio, query_mes, 1)
    
    # Usar el servicio para obtener O CREAR (y sincronizar) el plan
    plan = _get_or_create_plan_mensual(db, target_empresa_id, fecha_consulta)
    try:
        db.commit() # Persistir la creación/sync del plan si era nuevo
    except:
        db.rollback()
    
    # Recargar para asegurar data fresca tras commit
    db.refresh(plan)
    
    # Asignar el plan para la respuesta
    plan_schema = plan

    # 2. Bolsas Vigentes (Ordenadas por vencimiento, FIFO visual)
    periodo_ref = datetime(query_anio, query_mes, 1)
    
    bolsas = db.query(BolsaExcedente).filter(
        BolsaExcedente.empresa_id == target_empresa_id,
        BolsaExcedente.estado == EstadoBolsa.VIGENTE,
        BolsaExcedente.fecha_vencimiento >= periodo_ref
    ).order_by(asc(BolsaExcedente.fecha_vencimiento)).all()
    
    # 3. Recargas y Compras del Periodo
    from sqlalchemy import or_

    recargas = db.query(RecargaAdicional).filter(
        RecargaAdicional.empresa_id == target_empresa_id,
        or_(
            RecargaAdicional.estado == EstadoRecarga.VIGENTE,
            (RecargaAdicional.mes == query_mes) & (RecargaAdicional.anio == query_anio)
        )
    ).order_by(asc(RecargaAdicional.fecha_compra)).all()
    
    # Calculo Total DISPONIBLE (Solo sumamos lo disponible real, no lo comprado histórico)
    total = (plan.cantidad_disponible if plan and plan.estado == EstadoPlan.ABIERTO else 0) + \
            sum(b.cantidad_disponible for b in bolsas) + \
            sum(r.cantidad_disponible for r in recargas) # cantidad_disponible será 0 si está agotada
            
    return {
        "plan_actual": plan_schema,
        "bolsas_vigentes": bolsas,
        "recargas_vigentes": recargas,
        "total_disponible": total
    }

# ... (lines 16-121 remain unchanged, so I don't include them in replacement)

@router.get("/historial", response_model=HistorialConsumoPage)
@router.get("/historial", response_model=HistorialConsumoPage)
def get_historial_consumo(
    skip: int = 0,
    limit: int = 50,
    fecha_inicio: str = Query(None, description="Fecha inicio YYYY-MM-DD"),
    fecha_fin: str = Query(None, description="Fecha fin YYYY-MM-DD"),
    tipo_operacion: str = Query(None, description="Tipo de operación"),
    filtro_fecha_doc: bool = Query(False, description="Usar fecha del documento contable si existe"),
    empresa_id: int = Query(None, description="ID de empresa (Solo Soporte/Admin)"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
) -> Any:
    return _get_historial_paginated(db, current_user, skip, limit, fecha_inicio, fecha_fin, tipo_operacion, filtro_fecha_doc, empresa_id_override=empresa_id)


def get_historial_query(db, empresa_id, filtro_fecha_doc, fecha_inicio, fecha_fin, tipo_operacion):
    from app.models.documento import Documento
    
    query = db.query(HistorialConsumo).outerjoin(
        Documento, HistorialConsumo.documento_id == Documento.id
    ).filter(
        HistorialConsumo.empresa_id == empresa_id
    )

    if filtro_fecha_doc:
        fecha_efectiva = func.coalesce(Documento.fecha, HistorialConsumo.fecha)
    else:
        fecha_efectiva = HistorialConsumo.fecha

    if fecha_inicio:
        try:
            dt_inicio = datetime.strptime(fecha_inicio, "%Y-%m-%d")
            query = query.filter(fecha_efectiva >= dt_inicio)
        except ValueError:
            pass 

    if fecha_fin:
        try:
            dt_fin = datetime.strptime(fecha_fin, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
            query = query.filter(fecha_efectiva <= dt_fin)
        except ValueError:
            pass

    if tipo_operacion and tipo_operacion != "TODOS":
        query = query.filter(HistorialConsumo.tipo_operacion == tipo_operacion)
        
    # FIX: Excluir consumos huérfanos (Documentos eliminados)
    # Si es CONSUMO, debe tener un documento asociado.
    # Si el usuario pide REVERSION, COMPRA, etc, esos pueden no tener doc.
    if tipo_operacion == 'CONSUMO' or not tipo_operacion or tipo_operacion == 'TODOS':
         query = query.filter(
             or_(
                 HistorialConsumo.tipo_operacion != 'CONSUMO',
                 and_(
                     HistorialConsumo.tipo_operacion == 'CONSUMO',
                     HistorialConsumo.documento_id.isnot(None)
                 )
             )
         )

    # FIX: Excluir Documentos ANULADOS (Política de "Cero Ruido")
    # Tratamos los anulados igual que los eliminados: No deben aparecer en el historial.
    # Se mantienen registros que NO tienen documento (Recargas, Cierres) o que tienen documento NO anulado.
    query = query.filter(
        or_(
            Documento.id.is_(None),       # Operaciones sin documento (ej. Compra Recarga)
            Documento.anulado.is_(False)  # Documentos Activos
        )
    )

    # FIX: Excluir Documentos con REVERSIONES (Política "Net Zero" / "Anti-Confusion")
    # 1. Si tienen documento, y ese documento tiene reversiones, ocultar TODO.
    subquery_revertidos = db.query(HistorialConsumo.documento_id).filter(
        HistorialConsumo.tipo_operacion == 'REVERSION',
        HistorialConsumo.documento_id.isnot(None),
        HistorialConsumo.empresa_id == empresa_id
    ).subquery()

    query = query.filter(
        or_(
            # Caso 1: Sin documento...
            and_(
                HistorialConsumo.documento_id.is_(None),
                # PERO ocultar si es REVERSION o CONSUMO huérfano (ruido)
                HistorialConsumo.tipo_operacion != 'REVERSION',
                HistorialConsumo.tipo_operacion != 'CONSUMO'
            ),
            # Caso 2: Con documento...
            and_(
                HistorialConsumo.documento_id.isnot(None),
                ~HistorialConsumo.documento_id.in_(subquery_revertidos) # Excluir docs revertidos
            )
        )
    )

    return query


def _get_historial_paginated(db, current_user, skip, limit, fecha_inicio, fecha_fin, tipo_operacion, filtro_fecha_doc, empresa_id_override=None):
    from app.models.documento import Documento
    from app.models.consumo_registros import BolsaExcedente
    
    # Determinar Empresa ID
    target_empresa_id = current_user.empresa_id
    if empresa_id_override and empresa_id_override != current_user.empresa_id:
        roles_permitidos = ['soporte', 'administrador', 'super_admin', 'dev']
        tiene_permiso = any(r.nombre.lower() in roles_permitidos for r in current_user.roles)
        if tiene_permiso:
            target_empresa_id = empresa_id_override

    # Query base: Join LEFT con Documento
    query = get_historial_query(db, target_empresa_id, filtro_fecha_doc, fecha_inicio, fecha_fin, tipo_operacion)

    # Calcular total de cantidad (suma de impactos en el filtro actual)
    # SUM(cantidad)
    total_cantidad = query.with_entities(func.sum(HistorialConsumo.cantidad)).scalar() or 0

    # Query proyectada: Traemos el modelo Historial entero + el consecutivo del documento + Datos de Bolsa (si es cierre)
    # JOIN con BolsaExcedente para obtener origen
    query = query.outerjoin(BolsaExcedente, HistorialConsumo.fuente_id == BolsaExcedente.id)
    
    # Redefinir fecha_efectiva para el ordenamiento en este scope
    if filtro_fecha_doc:
        fecha_efectiva = func.coalesce(Documento.fecha, HistorialConsumo.fecha)
    else:
        fecha_efectiva = HistorialConsumo.fecha
    
    results = query.add_columns(
        Documento.numero,
        Documento.fecha.label('doc_fecha'), # Traemos también la fecha doc para uso en frontend si se requiere
        BolsaExcedente.mes_origen,
        BolsaExcedente.anio_origen
    ).order_by(desc(fecha_efectiva), desc(Documento.numero)).offset(skip).limit(limit).all()
    
    items = []
    for historial_model, doc_nro, doc_fecha, mes_origen, anio_origen in results:
        # Inyectar atributos 'virtuales' al modelo para Pydantic
        setattr(historial_model, "documento_numero", doc_nro)
        
        # Inyectar origen de bolsa si aplica
        if mes_origen and anio_origen:
             setattr(historial_model, "bolsa_origen", f"{mes_origen}/{anio_origen}")
             setattr(historial_model, "bolsa_mes", mes_origen)
             setattr(historial_model, "bolsa_anio", anio_origen)
        
        
        # Opcional: Si estamos en modo "historial contable", tal vez queramos que el campo .fecha 
        # del item refleje la fecha del documento en lugar de la fecha de creación.
        # El usuario pidió: "Historial... fecha de creación, no de fecha de consulta o fecha actual"
        # Wait, user said: "No es actividad reciente, sino historial historial... fecha de creación [del doc]"
        if filtro_fecha_doc and doc_fecha:
             # Hack visual: sobrescribimos la fecha del objeto con la fecha del documento
             # para que el frontend la muestre en la columna "FECHA"
             # Convertimos date a datetime min
             if isinstance(doc_fecha, datetime):
                 historial_model.fecha = doc_fecha
             else:
                 # Es date
                 historial_model.fecha = datetime(doc_fecha.year, doc_fecha.month, doc_fecha.day)

        items.append(historial_model)

    return {"items": items, "total_cantidad": total_cantidad}

    return {"items": items, "total_cantidad": total_cantidad}


@router.get("/reporte/pdf")
def generar_reporte_pdf(
    fecha_inicio: str = Query(None),
    fecha_fin: str = Query(None),
    tipo_operacion: str = Query(None),
    filtro_fecha_doc: bool = Query(True),
    empresa_id: int = Query(None, description="ID de empresa (Solo Soporte/Admin)"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    # 1. Obtener Datos (Reusando lógica de filtros, sin paginación)
    from app.models.documento import Documento
    
    # Determinar Empresa ID (Lógica Segura)
    target_empresa_id = current_user.empresa_id
    if empresa_id and empresa_id != current_user.empresa_id:
        roles_permitidos = ['soporte', 'administrador', 'super_admin', 'dev']
        tiene_permiso = any(r.nombre.lower() in roles_permitidos for r in current_user.roles)
        if tiene_permiso:
            target_empresa_id = empresa_id

    query = get_historial_query(db, target_empresa_id, filtro_fecha_doc, fecha_inicio, fecha_fin, tipo_operacion)
    
    # Calcular total impacto
    total_cantidad = query.with_entities(func.sum(HistorialConsumo.cantidad)).scalar() or 0
    
    # Definir ordenamiento
    if filtro_fecha_doc:
        fecha_efectiva = func.coalesce(Documento.fecha, HistorialConsumo.fecha)
    else:
        fecha_efectiva = HistorialConsumo.fecha
        
    query = query.outerjoin(BolsaExcedente, HistorialConsumo.fuente_id == BolsaExcedente.id)
    
    from sqlalchemy import case, asc, desc
    
    # Definir prioridad de fuente para el ordenamiento (Plan -> Bolsa -> Recarga)
    # 1: PLAN, 2: BOLSA, 3: RECARGA
    # Esto asegura que si un documento consume de todos, se vea el flujo lógico.
    prioridad_fuente = case(
        (HistorialConsumo.fuente_tipo == 'PLAN', 1),
        (HistorialConsumo.fuente_tipo == 'BOLSA', 2),
        (HistorialConsumo.fuente_tipo == 'RECARGA', 3),
        else_=4
    )
    
    # Ordenamiento Ascendente (Cronológico: Lo más viejo primero)
    # Usuario pidió explícitamente: "fecha inferior a la fecha superior"
    results = query.add_columns(
        Documento.numero,
        Documento.fecha.label('doc_fecha'),
        BolsaExcedente.mes_origen,
        BolsaExcedente.anio_origen
    ).order_by(
        asc(fecha_efectiva), 
        asc(Documento.numero),
        prioridad_fuente
    ).limit(5000).all()

    # Procesar items
    items = []
    for historial_model, doc_nro, doc_fecha, mes_origen, anio_origen in results:
        # Clonar/usar objeto serializable ligero o dict 
        # (El objeto SQLAlchemy puede dar problemas con Jinja si se desconecta)
        
        real_date = historial_model.fecha
        if filtro_fecha_doc and doc_fecha:
             if isinstance(doc_fecha, datetime):
                 real_date = doc_fecha
             else:
                 real_date = datetime(doc_fecha.year, doc_fecha.month, doc_fecha.day)
        
        item_dict = {
            "fecha": real_date,
            "tipo_operacion": historial_model.tipo_operacion,
            "fuente_tipo": historial_model.fuente_tipo,
            "cantidad": historial_model.cantidad,
            "documento_numero": doc_nro,
            "bolsa_origen": f"{mes_origen}/{anio_origen}" if mes_origen else None
        }
        items.append(item_dict)

    # 2. Renderizar Template
    from jinja2 import Environment, FileSystemLoader
    from weasyprint import HTML
    import os

    template_dir = os.path.join(os.getcwd(), 'app/templates')
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template('reports/historial_consumo_report.html')
    
    empresa = current_user.empresa
    
    html_content = template.render(
        empresa=empresa,
        items=items,
        total_cantidad=total_cantidad,
        filtros={
            "fecha_inicio": fecha_inicio,
            "fecha_fin": fecha_fin,
            "tipo_operacion": tipo_operacion
        },
        fecha_generacion=datetime.now().strftime("%d/%m/%Y %H:%M")
    )
    
    # 3. Generar PDF
    pdf_bytes = HTML(string=html_content).write_pdf()
    
    from fastapi.responses import Response
    return Response(
        content=pdf_bytes, 
        media_type="application/pdf", 
        headers={"Content-Disposition": "attachment; filename=historial_consumo.pdf"}
    )

# --- NUEVOS ENDPOINTS DE RECARGAS ---

@router.get("/paquetes")
def get_paquetes_recarga(
    current_user = Depends(get_current_user)
):
    """Retorna la lista de paquetes de recarga disponibles y sus precios."""
    # Convertimos dict a lista para facil consumo en frontend
    return [
        {"id": k, **v} 
        for k, v in PAQUETES_RECARGA.items()
    ]

class CompraRecargaRequest(BaseModel):
    paquete_id: str = None
    cantidad_custom: int = None
    mes: int = None
    anio: int = None

@router.post("/recargas")
def comprar_paquete_recarga(
    data: CompraRecargaRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Procesa la compra de un paquete o recarga personalizada.
    """
    try:
        if not data.paquete_id and not data.cantidad_custom:
            raise ValueError("Debe especificar un paquete o una cantidad personalizada.")

        # Se pasa mes y año si vienen en el request (para recargas retroactivas)
        recarga = comprar_recarga(
            db, 
            current_user.empresa_id, 
            paquete_id=data.paquete_id,
            cantidad_custom=data.cantidad_custom,
            mes=data.mes,
            anio=data.anio
        )
        return {"status": "success", "message": "Recarga exitosa", "recarga_id": recarga.id}
    except ValueError as e:
        # Re-raise as HTTP 400
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class MarcarPagadaRequest(BaseModel):
    pagado: bool = True

@router.put("/recargas/{recarga_id}/pago")
def marcar_recarga_pagada(
    recarga_id: int,
    data: MarcarPagadaRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Marca una recarga como pagada (facturada=True) o pendiente.
    Esto permite 'dar de baja' el saldo pendiente por cobrar en el dashboard de soporte.
    """
    # En un sistema real, validaríamos que current_user.es_admin o similar.
    # Por ahora asumimos que solo soporte accede a esto.
    
    recarga = db.query(RecargaAdicional).filter(RecargaAdicional.id == recarga_id).first()
    if not recarga:
        raise HTTPException(status_code=404, detail="Recarga no encontrada")
        
    recarga.facturado = data.pagado
    if data.pagado:
        recarga.fecha_facturacion = datetime.now()
    else:
        recarga.fecha_facturacion = None
        
    db.commit()
    return {"status": "success", "message": "Estado de pago actualizado"}
        

@router.delete("/reset-factory")
def reset_consumo_factory(
    empresa_id: int = Query(..., description="ID de la empresa a reiniciar"),
    borrar_historial: bool = Query(True, description="Borrar historial de consumos y reversiones"),
    borrar_recargas: bool = Query(True, description="Borrar recargas adicionales"),
    borrar_bolsas: bool = Query(True, description="Borrar bolsas de excedentes"),
    reset_plan: bool = Query(True, description="Reiniciar Plan Mensual"),
    db: Session = Depends(get_db),
    # current_user = Depends(get_current_admin) # Solo SuperAdmin debería poder hacer esto
):
    """
    DANGER: Reinicia todos los datos de consumo de una empresa.
    Solo para entornos de desarrollo/pruebas o reparaciones críticas.
    """
    # 1. Verificar Empresa
    empresa = db.query(Empresa).get(empresa_id)
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")

    try:
        # 2. ELIMINAR TABLAS (Orden crítico por FKs)
        detalles = []

        # A. Historial Consumo
        if borrar_historial:
            db.query(HistorialConsumo).filter(HistorialConsumo.empresa_id == empresa_id).delete(synchronize_session=False)
            detalles.append("Historial")
        
        # B. Bolsas Excedentes
        if borrar_bolsas:
            db.query(BolsaExcedente).filter(BolsaExcedente.empresa_id == empresa_id).delete(synchronize_session=False)
            detalles.append("Bolsas")

        # C. Recargas Adicionales
        if borrar_recargas:
            # Limpieza inteligente: Borrar historial de GESTIÓN (Compra/Expiración) de las recargas a borrar
            # pero MANTENER el de CONSUMO para justificar el gasto histórico.
            db.query(HistorialConsumo).filter(
                HistorialConsumo.empresa_id == empresa_id,
                HistorialConsumo.fuente_tipo == TipoFuenteConsumo.RECARGA.value,
                HistorialConsumo.tipo_operacion.in_([
                    TipoOperacionConsumo.COMPRA.value, 
                    TipoOperacionConsumo.EXPIRACION.value,
                    # Opcional: TipoOperacionConsumo.ANULACION.value si existiera y fuera ruido
                ])
            ).delete(synchronize_session=False)

            db.query(RecargaAdicional).filter(RecargaAdicional.empresa_id == empresa_id).delete(synchronize_session=False)
            detalles.append("Recargas")

        # D. Planes Mensuales
        if reset_plan:
            db.query(ControlPlanMensual).filter(ControlPlanMensual.empresa_id == empresa_id).delete(synchronize_session=False)
            detalles.append("Plan Mensual")

        db.commit()
        
        # Forzar regeneración del plan actual inmediato si se reseteó
        if reset_plan:
            try:
               now = datetime.now()
               _get_or_create_plan_mensual(db, empresa_id, now)
               db.commit()
            except:
                pass # Si falla la regeneración inmediata, se hará en la próxima consulta

        return {"status": "success", "message": f"Reset completado para {empresa.razon_social}. Eliminado: {', '.join(detalles)}"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

