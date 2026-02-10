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


def get_reporte_gestion_ventas(db: Session, empresa_id: int, filtros: schemas_ventas.GestionVentasFiltros) -> schemas_ventas.GestionVentasResponse:
    """
    Genera una lista ligera de documentos que aplican al reporte de ventas (CxC)
    FILTRANDO POR LA CONSTANTE ESCALABLE (CARTERA_CLIENTE) y AFECTA_INVENTARIO.
    """
    
    # 1. Definición de filtros y cuentas
    fecha_inicio_dt = datetime.combine(filtros.fecha_inicio, datetime.min.time())
    fecha_fin_dt = datetime.combine(filtros.fecha_fin, datetime.max.time())
    
    cxc_account_ids = _get_cxc_accounts(db, empresa_id)
    
    if not cxc_account_ids:
        # Si no hay cuentas de cartera, devolvemos un reporte vacío
        return schemas_ventas.GestionVentasResponse(kpis=schemas_ventas.GestionVentasKPIs(total_facturado=0.0, total_cobrado=0.0, saldo_pendiente=0.0, cartera_vencida=0.0), items=[])


    # OBTENER EL VALOR TOTAL DE LA FACTURA (solo la suma de DÉBITOS a CxC)
    sq_valor_total = db.query(
        models_mov.documento_id.label("documento_id"),
        func.coalesce(func.sum(models_mov.debito), Decimal('0.0')).label("valor_total_cxc")
    ).filter(
        models_mov.documento_id == models_doc.id, 
        models_mov.cuenta_id.in_(cxc_account_ids) 
    ).group_by(models_mov.documento_id).subquery()


    # 2. Consulta Principal de Documentos (Facturas de Venta)
    query = db.query(
        models_doc.id,
        models_doc.fecha,
        models_doc.numero,
        models_doc.fecha_vencimiento,
        TipoDocumentoModel.codigo.label("tipo_documento"),
        models_tercero.razon_social.label("beneficiario_nombre"),
        func.coalesce(sq_valor_total.c.valor_total_cxc, Decimal('0.0')).label("valor_total_cxc_final")
    ).select_from(models_doc)\
     .join(TipoDocumentoModel, models_doc.tipo_documento_id == TipoDocumentoModel.id)\
     .join(models_tercero, models_doc.beneficiario_id == models_tercero.id)\
     .outerjoin(sq_valor_total, models_doc.id == sq_valor_total.c.documento_id)\
     .filter(
        models_doc.empresa_id == empresa_id,
        models_doc.anulado == False,
        # FILTRO CRÍTICO FINAL: USO DE LA CONSTANTE EN LUGAR DE LA CADENA MÁGICA
        and_(
             TipoDocumentoModel.funcion_especial == FuncionEspecial.CARTERA_CLIENTE,
             TipoDocumentoModel.afecta_inventario == True
        ),
        models_doc.fecha.between(fecha_inicio_dt, fecha_fin_dt),
    )

    # Aplicar filtros adicionales
    if filtros.cliente_id:
        query = query.filter(models_doc.beneficiario_id == filtros.cliente_id)

    # 3. Ejecución y construcción de respuesta
    documentos_db = query.all()
    
    items_reporte: List[schemas_ventas.GestionVentasItem] = []
    
    # Devolvemos KPIs en cero, ya que el reporte se enfoca en rentabilidad
    kpis_cero = schemas_ventas.GestionVentasKPIs(total_facturado=0.0, total_cobrado=0.0, saldo_pendiente=0.0, cartera_vencida=0.0)

    for doc in documentos_db:
        # Se usa el valor renombrado y coalescido
        valor_total_dec = Decimal(str(doc.valor_total_cxc_final))
            
        items_reporte.append(schemas_ventas.GestionVentasItem(
            id=doc.id,
            fecha=doc.fecha,
            tipo_documento=doc.tipo_documento,
            numero=doc.numero,
            beneficiario_nombre=doc.beneficiario_nombre,
            fecha_vencimiento=doc.fecha_vencimiento,
            estado="N/A", 
            # Se usa el valor para cumplir con el schema
            total=float(valor_total_dec.quantize(Decimal("0.01"), ROUND_HALF_UP)),
            saldo_pendiente=0.0,
        ))

    return schemas_ventas.GestionVentasResponse(kpis=kpis_cero, items=items_reporte)


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