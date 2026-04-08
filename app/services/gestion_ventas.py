# app/services/gestion_ventas.py (VERSIÓN FINAL Y ESCALABLE: USO DE CONSTANTE)

from sqlalchemy.orm import Session, aliased, joinedload
from sqlalchemy import func, and_, or_, select, case, cast, String as SAString, Date as SADate
from decimal import Decimal, ROUND_HALF_UP
from datetime import date, datetime, timedelta
from typing import List, Optional, Dict, Any

from fastapi import HTTPException, status
import os 
import locale 
import json 
from pydantic import ValidationError 
import traceback

# Importación de la CONSTANTE
from app.core.constants import FuncionEspecial 

# Importaciones del Core
from app.core.security import create_signed_token, validate_signed_token

# Modelos
from app.models import Documento as models_doc
from app.models import MovimientoContable as models_mov
from app.models import Tercero as models_tercero
from app.models import AplicacionPago as models_aplica
from app.models import Empresa as models_empresa
from app.models.plan_cuenta import PlanCuenta as models_plan_cuenta 
from app.models.tipo_documento import TipoDocumento as models_tipo_doc_raw 

# Renombramos el modelo TipoDocumento para usarlo de forma no ambigua
TipoDocumentoModel = models_tipo_doc_raw 


# Esquemas
from app.schemas import gestion_ventas as schemas_ventas
from app.schemas import documento as schemas_doc
from app.schemas import token as schemas_token 

# --- CONSTANTES ---
ESTADOS_REPORTE = ['Pagada', 'Pendiente', 'Vencida', 'Anulada']

# --- FUNCIONES AUXILIARES CRÍTICAS ---

def _get_cxc_accounts(db: Session, empresa_id: int) -> List[int]:
    """Obtiene los IDs de las cuentas de Cartera (Clase 13)."""
    cxc_accounts = db.query(models_plan_cuenta.id)\
                     .filter(
                         models_plan_cuenta.empresa_id == empresa_id,
                         models_plan_cuenta.codigo.startswith('13')
                     ).all()
    return [id_[0] for id_ in cxc_accounts]

def _get_costo_accounts(db: Session, empresa_id: int) -> List[int]:
    """Obtiene los IDs de las cuentas de Costo de Ventas (Clase 6)."""
    costo_accounts = db.query(models_plan_cuenta.id)\
                       .filter(
                           models_plan_cuenta.empresa_id == empresa_id,
                           models_plan_cuenta.codigo.startswith('6')
                       ).all()
    return [id_[0] for id_ in costo_accounts]


def get_reporte_gestion_ventas(db: Session, empresa_id: int, filtros: schemas_ventas.GestionVentasFiltros) -> schemas_ventas.GestionVentasResponse:
    """
    Genera un reporte gerencial de ventas con KPIs, gráficas y listado detallado.
    """
    # 1. Preparación de filtros
    fecha_inicio_dt = datetime.combine(filtros.fecha_inicio, datetime.min.time())
    fecha_fin_dt = datetime.combine(filtros.fecha_fin, datetime.max.time())
    
    cxc_account_ids = _get_cxc_accounts(db, empresa_id)
    costo_account_ids = _get_costo_accounts(db, empresa_id)
    
    if not cxc_account_ids:
        return schemas_ventas.GestionVentasResponse(
            kpis=schemas_ventas.GestionVentasKPIs(
                total_facturado=0, total_utilidad=0, margen_promedio=0, 
                cantidad_facturas=0, ticket_promedio=0, total_cobrado=0, 
                saldo_pendiente=0, cartera_vencida=0
            ),
            graficos=schemas_ventas.GestionVentasGraficos(ventas_por_dia=[], top_clientes=[], top_productos=[]),
            items=[]
        )

    # 2. Subconsultas de Totales por Documento (CxC y Costo)
    sq_valor_total = db.query(
        models_mov.documento_id.label("documento_id"),
        func.coalesce(func.sum(models_mov.debito), Decimal('0.0')).label("valor_total_cxc")
    ).filter(models_mov.cuenta_id.in_(cxc_account_ids)).group_by(models_mov.documento_id).subquery()

    sq_costo_total = db.query(
        models_mov.documento_id.label("documento_id"),
        func.coalesce(func.sum(models_mov.debito), Decimal('0.0')).label("valor_costo")
    ).filter(models_mov.cuenta_id.in_(costo_account_ids)).group_by(models_mov.documento_id).subquery()

    # 3. Consulta Base de Documentos
    docs_query = db.query(
        models_doc.id,
        models_doc.fecha,
        models_doc.numero,
        models_doc.fecha_vencimiento,
        TipoDocumentoModel.codigo.label("tipo_documento"),
        models_tercero.razon_social.label("beneficiario_nombre"),
        models_doc.beneficiario_id,
        func.coalesce(sq_valor_total.c.valor_total_cxc, Decimal('0.0')).label("total_factura"),
        func.coalesce(sq_costo_total.c.valor_costo, Decimal('0.0')).label("total_costo")
    ).select_from(models_doc)\
     .join(TipoDocumentoModel, models_doc.tipo_documento_id == TipoDocumentoModel.id)\
     .join(models_tercero, models_doc.beneficiario_id == models_tercero.id)\
     .outerjoin(sq_valor_total, models_doc.id == sq_valor_total.c.documento_id)\
     .outerjoin(sq_costo_total, models_doc.id == sq_costo_total.c.documento_id)\
     .filter(
        models_doc.empresa_id == empresa_id,
        models_doc.anulado == False,
        TipoDocumentoModel.funcion_especial == FuncionEspecial.CARTERA_CLIENTE,
        TipoDocumentoModel.afecta_inventario == True,
        models_doc.fecha.between(fecha_inicio_dt, fecha_fin_dt)
    )

    if filtros.cliente_id:
        docs_query = docs_query.filter(models_doc.beneficiario_id == filtros.cliente_id)

    documentos = docs_query.order_by(models_doc.fecha.desc()).all()

    # 4. Cálculos de KPIs
    total_vta = sum(d.total_factura for d in documentos)
    total_cst = sum(d.total_costo for d in documentos)
    total_utl = total_vta - total_cst
    cant_fact = len(documentos)
    
    # NUEVOS KPIs: Clientes Únicos y Frecuencia
    unique_clients = set(d.beneficiario_id for d in documentos)
    cant_clientes = len(unique_clients)
    frec_compra = (float(cant_fact) / cant_clientes) if cant_clientes > 0 else 0

    mrg_prom = (float(total_utl) / float(total_vta) * 100) if total_vta > 0 else 0
    tkt_prom = (float(total_vta) / cant_fact) if cant_fact > 0 else 0

    kpis = schemas_ventas.GestionVentasKPIs(
        total_facturado=float(total_vta),
        total_utilidad=float(total_utl),
        margen_promedio=round(mrg_prom, 2),
        cantidad_facturas=cant_fact,
        cantidad_clientes_unicos=cant_clientes,
        frecuencia_compra=round(frec_compra, 2),
        ticket_promedio=round(tkt_prom, 2),
        total_cobrado=0.0,
        saldo_pendiente=0.0,
        cartera_vencida=0.0
    )

    # 5. Datos para Gráficas
    # Ventas por Día
    ventas_dia_dict = {}
    for d in documentos:
        fecha_str = d.fecha.strftime("%Y-%m-%d")
        ventas_dia_dict[fecha_str] = ventas_dia_dict.get(fecha_str, 0) + float(d.total_factura)
    ventas_por_dia = [schemas_ventas.ChartDataPoint(label=k, value=v) for k, v in sorted(ventas_dia_dict.items())]

    # Top Clientes (basado en los documentos ya filtrados)
    clientes_dict = {}
    for d in documentos:
        clientes_dict[d.beneficiario_nombre] = clientes_dict.get(d.beneficiario_nombre, 0) + float(d.total_factura)
    top_clientes = sorted(
        [schemas_ventas.ChartDataPoint(label=k, value=v) for k, v in clientes_dict.items()],
        key=lambda x: x.value, reverse=True
    )[:5]

    # Top Productos (requiere query adicional sobre movimientos)
    doc_ids = [d.id for d in documentos]
    top_productos = []
    if doc_ids:
        from app.models.producto import Producto
        productos_query = db.query(
            Producto.nombre,
            func.sum(models_mov.debito).label("venta_total")
        ).join(models_mov, Producto.id == models_mov.producto_id)\
         .filter(models_mov.documento_id.in_(doc_ids))\
         .group_by(Producto.nombre)\
         .order_by(func.sum(models_mov.debito).desc())\
         .limit(5).all()
        top_productos = [schemas_ventas.ChartDataPoint(label=p.nombre, value=float(p.venta_total)) for p in productos_query]

    graficos = schemas_ventas.GestionVentasGraficos(
        ventas_por_dia=ventas_por_dia,
        top_clientes=top_clientes,
        top_productos=top_productos
    )

    # 6. Mapeo de Items
    items = [
        schemas_ventas.GestionVentasItem(
            id=d.id, fecha=d.fecha, tipo_documento=d.tipo_documento,
            numero=d.numero, beneficiario_nombre=d.beneficiario_nombre,
            fecha_vencimiento=d.fecha_vencimiento, estado="Activo",
            total=float(d.total_factura), saldo_pendiente=0.0
        ) for d in documentos
    ]

    return schemas_ventas.GestionVentasResponse(kpis=kpis, graficos=graficos, items=items)


# 2. Servicio para Generación de URL Firmada 

def generar_url_firmada_reporte_gestion_ventas(db: Session, empresa_id: int, user_id: int, filtros: schemas_ventas.GestionVentasFiltros) -> str:
    """
    Crea un token con los filtros de reporte y la información de la empresa para la descarga segura.
    (Esta función no se toca, ya que solo genera el token).
    """
    try:
        # 1. Construir el payload que incluye los filtros y la info de seguridad
        payload_data = schemas_ventas.GestionVentasPDFPayload(
            filtros=filtros,
            emp_id=empresa_id,
            user_id=user_id
        )
        token_payload_str = payload_data.model_dump_json()

        # 2. Generar el token firmado de corta duración (TTL: 600 segundos = 10 minutos)
        token = create_signed_token(token_payload_str, salt='pdf-gestion-ventas-v1', max_age=600)

        # 3. Construir la URL pública de descarga (usando os.environ.get o config)
        from app.core.config import settings
        backend_base_url = settings.BASE_URL # Usa la configuración centralizada que ya arreglamos
        if backend_base_url.endswith('/'):
            backend_base_url = backend_base_url[:-1] # Remove trailing slash if present 
        download_url = f"{backend_base_url}/api/gestion-ventas/pdf-descarga/{token}"
        
        return download_url

    except Exception as e:
        print(f"Error al crear token JWT para PDF Gestión Ventas: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Fallo en el motor de firma de tokens para PDF.")