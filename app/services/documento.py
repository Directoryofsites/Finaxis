# -*- coding: utf-8 -*-
from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy import func, and_, or_
from fastapi import HTTPException
from datetime import date
from app.core.config import settings

from fastapi import HTTPException, status
from app.core.security import create_print_token

from datetime import date, datetime
from dateutil.relativedelta import relativedelta
import json
from weasyprint import HTML
# Se añade la importación del servicio de cartera para el recálculo
from app.services import cartera as cartera_service

# Importamos el guardián de periodos
from app.services import periodo as periodo_service

import os



# --- INICIO: ARQUITECTURA DE PLANTILLAS REFACTORIZADA ---
# 1. Importamos el nuevo diccionario con las plantillas pre-compiladas.
from app.services._templates_empaquetados import TEMPLATES_EMPAQUETADOS

# 2. Importamos las librerías necesarias para filtros complejos de Jinja2.
from jinja2 import Environment, select_autoescape
import itertools
import operator

# --- INICIO: NUEVA CONSTANTE CENTRALIZADA ---
from app.core.constants import FuncionEspecial
# --- FIN: NUEVA CONSTANTE CENTRALIZADA ---

from app.utils.numero_a_letras import numero_a_letras

from app.models.cupo_adicional import CupoAdicional # <--- AGREGAR ESTO

# 3. Creamos UNA ÚNICA instancia del entorno de Jinja2 para todo el módulo.
#    Ya no cargará desde el sistema de archivos (loader=None).
#    Le pre-cargamos los filtros que sabemos que se usan en las plantillas.
GLOBAL_JINJA_ENV = Environment(loader=None, autoescape=select_autoescape(['html', 'xml']))
GLOBAL_JINJA_ENV.filters['slice'] = lambda value, start, end: value[start:end]
GLOBAL_JINJA_ENV.filters['groupby'] = lambda value, attribute: itertools.groupby(sorted(value, key=operator.itemgetter(attribute)), operator.itemgetter(attribute))

GLOBAL_JINJA_ENV.globals['list'] = list
# --- FIN: ARQUITECTURA DE PLANTILLAS REFACTORIZADA ---

# Importamos el nuevo servicio de centro de costo para usar el motor jerárquico
from app.services import centro_costo as centro_costo_service
from typing import List, Optional, Dict, Any

from app.models import (
    Documento as models_doc,
    MovimientoContable as models_mov,
    TipoDocumento as models_tipo,
    PeriodoContableCerrado as models_periodo,
    Empresa as models_empresa,
    LogOperacion as models_log,
    Tercero as models_tercero,
    PlanCuenta as models_plan,
    DocumentoEliminado as models_doc_elim,
    MovimientoEliminado as models_mov_elim,
    FormatoImpresion as models_formato,
    AplicacionPago as models_aplica,
    CentroCosto as models_centro_costo,
    Usuario as models_usuario,
    Producto as models_producto,
    MovimientoInventario as models_mov_inv
)

from app.models.grupo_inventario import GrupoInventario as models_grupo

from app.schemas import documento as schemas_doc

# --- INICIO: FUNCIONES AUXILIARES DE LÓGICA CONTABLE (REPLICADAS DE CARTERA.PY) ---

def _get_cuentas_especiales_ids(db: Session, empresa_id: int, tipo: str) -> List[int]:
    """
    Obtiene dinámicamente los IDs de las cuentas parametrizadas para Cartera (cxc) o Proveedores (cxp).
    """
    cuentas_ids = set()
    query = db.query(
        models_tipo.cuenta_debito_cxc_id,
        models_tipo.cuenta_credito_cxc_id,
        models_tipo.cuenta_debito_cxp_id,
        models_tipo.cuenta_credito_cxp_id
    ).filter(models_tipo.empresa_id == empresa_id).distinct()

    if tipo == 'cxc':
        for row in query.all():
            if row.cuenta_debito_cxc_id: cuentas_ids.add(row.cuenta_debito_cxc_id)
            if row.cuenta_credito_cxc_id: cuentas_ids.add(row.cuenta_credito_cxc_id)
    elif tipo == 'cxp':
        for row in query.all():
            if row.cuenta_debito_cxp_id: cuentas_ids.add(row.cuenta_debito_cxp_id)
            if row.cuenta_credito_cxp_id: cuentas_ids.add(row.cuenta_credito_cxp_id)

    return list(cuentas_ids)

def _documento_afecta_cuentas(db: Session, documento_id: int, cuentas_ids: List[int]) -> bool:
    """
    Verifica si un documento tiene al menos un movimiento que afecte a la lista de cuentas proporcionada.
    """
    if not cuentas_ids:
        return False

    movimiento_existente = db.query(models_mov.id).filter(
        models_mov.documento_id == documento_id,
        models_mov.cuenta_id.in_(cuentas_ids)
    ).first()
    return movimiento_existente is not None

# --- FIN: FUNCIONES AUXILIARES ---

# Dentro de app/services/documento.py

def create_documento(db: Session, documento: schemas_doc.DocumentoCreate, user_id: int, commit: bool = True):
    try:
        # 1. BLINDAJE CONTABLE: Validar período cerrado
        periodo_service.validar_periodo_abierto(db, documento.empresa_id, documento.fecha)
        
        # 2. Obtener datos de la empresa
        # Nota: Usamos la consulta completa para tener acceso a todos los campos si es necesario
        empresa_info = db.query(models_empresa).filter(models_empresa.id == documento.empresa_id).first()
        
        if not empresa_info:
            raise HTTPException(status_code=404, detail="La empresa especificada no existe.")
        

        # ==============================================================================
        # 3. VALIDACIÓN DE LÍMITE DE REGISTROS (MODELO MENSUAL ESTRICTO)
        # ==============================================================================
        
        # Importamos calendar aquí
        import calendar
        
        # A. Definir el mes del documento
        fecha_doc = documento.fecha
        anio_doc = fecha_doc.year
        mes_doc = fecha_doc.month
        
        inicio_mes = fecha_doc.replace(day=1)
        ultimo_dia = calendar.monthrange(anio_doc, mes_doc)[1]
        fin_mes = fecha_doc.replace(day=ultimo_dia)

        
        # B. DETERMINAR EL LÍMITE EFECTIVO
        # 1. Buscamos si hay excepción para este mes
        cupo_mensual_especifico = db.query(CupoAdicional).filter(
            CupoAdicional.empresa_id == documento.empresa_id,
            CupoAdicional.anio == anio_doc,
            CupoAdicional.mes == mes_doc
        ).first()

        limite_efectivo = 0
        usando_excepcion = False

        # LÓGICA CORREGIDA:
        # Si existe un registro de excepción, miramos su valor.
        if cupo_mensual_especifico:
            # Si el valor es mayor a 0, es un límite específico (ej: 50).
            if cupo_mensual_especifico.cantidad_adicional > 0:
                limite_efectivo = cupo_mensual_especifico.cantidad_adicional
                usando_excepcion = True
            else:
                # Si el valor es 0, interpretamos "Quitar límite específico" -> Usar Plan Base
                # (Esta es la corrección que pediste: 0 en el mes = volver al defecto)
                limite_efectivo = empresa_info.limite_registros or 0
        else:
            # Si no hay registro, usamos el Plan Base
            limite_efectivo = empresa_info.limite_registros or 0

        # Validación final
        # Si limite_efectivo es 0 aquí, significa que el Plan Base también es 0 (Ilimitado globalmente)
        
        if limite_efectivo > 0:
            # C. Contar consumo del mes
            conteo_mes = db.query(func.count(models_mov.id))\
                .join(models_doc, models_mov.documento_id == models_doc.id)\
                .filter(
                    models_doc.empresa_id == documento.empresa_id,
                    models_doc.anulado == False,
                    models_doc.fecha >= inicio_mes,
                    models_doc.fecha <= fin_mes
                ).scalar() or 0
            
            # D. Proyección
            nuevos_movimientos = len(documento.movimientos)
            conteo_total_proyectado = conteo_mes + nuevos_movimientos
            
            print(f"\n📊 [CONTROL CUPO {anio_doc}-{mes_doc}]")
            print(f"Fuente: {'EXCEPCIÓN MENSUAL' if usando_excepcion else 'PLAN BASE'}")
            print(f"Límite Efectivo: {limite_efectivo}")
            print(f"Consumo: {conteo_mes} + {nuevos_movimientos}")

            if conteo_total_proyectado > limite_efectivo:
                raise HTTPException(
                    status_code=409, 
                    detail=f"⛔ LÍMITE EXCEDIDO ({'Excepción Mes' if usando_excepcion else 'Plan Base'}): Cupo de {limite_efectivo}. Consumido: {conteo_mes}. Intenta crear: {nuevos_movimientos}."
                )
        # ==============================================================================


        # 4. Validación de Fecha de Inicio de Operaciones
        if empresa_info.fecha_inicio_operaciones and documento.fecha < empresa_info.fecha_inicio_operaciones:
            raise HTTPException(
                status_code=403,
                detail=f"La fecha del documento no puede ser anterior al inicio de operaciones."
            )
        
        # ... (Resto de la lógica de creación: validación de partida doble, asignación de número, etc.) ...
        total_debito = sum(mov.debito for mov in documento.movimientos)
        total_credito = sum(mov.credito for mov in documento.movimientos)
        if abs(total_debito - total_credito) > 0.001:
            raise HTTPException(status_code=400, detail="Error de partida doble.")
        
        tipo_doc = db.query(models_tipo).filter(models_tipo.id == documento.tipo_documento_id).with_for_update().first()
        if not tipo_doc:
            raise HTTPException(status_code=404, detail="El tipo de documento no existe.")

        if not tipo_doc.numeracion_manual:
            numero_a_asignar = (tipo_doc.consecutivo_actual or 0) + 1
            documento.numero = numero_a_asignar

        db_documento = models_doc(
            empresa_id=documento.empresa_id,
            tipo_documento_id=documento.tipo_documento_id,
            numero=documento.numero,
            fecha=documento.fecha,
            fecha_operacion=datetime.utcnow(),
            fecha_vencimiento=documento.fecha_vencimiento,
            beneficiario_id=documento.beneficiario_id,
            centro_costo_id=documento.centro_costo_id,
            usuario_creador_id=user_id,
            unidad_ph_id=documento.unidad_ph_id # Added for PH Module
        )

        for mov_in in documento.movimientos:
            mov_data = mov_in.model_dump()
            if mov_data.get('centro_costo_id') is None and documento.centro_costo_id is not None:
                mov_data['centro_costo_id'] = documento.centro_costo_id
            db_movimiento = models_mov(**mov_data)
            db_documento.movimientos.append(db_movimiento)

        if not tipo_doc.numeracion_manual:
            tipo_doc.consecutivo_actual = documento.numero

        db.add(db_documento)
        
        if commit:
            db.commit()
            db.refresh(db_documento)
        else:
            db.flush()
            db.refresh(db_documento)
        
        funciones_relevantes = [
            FuncionEspecial.RC_CLIENTE, 
            FuncionEspecial.PAGO_PROVEEDOR, 
            FuncionEspecial.CARTERA_CLIENTE, 
            FuncionEspecial.CXP_PROVEEDOR
        ]

        if tipo_doc.funcion_especial in funciones_relevantes and db_documento.beneficiario_id:
            cartera_service.recalcular_aplicaciones_tercero(
                db,
                tercero_id=db_documento.beneficiario_id,
                empresa_id=db_documento.empresa_id
            )
            if commit:
                db.commit()

        return db_documento
    except Exception as e:
        if commit:
            db.rollback()
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")


def anular_documento(db: Session, documento_id: int, empresa_id: int, user_id: int, user_email: str, razon: str):
    # 1. Buscamos el documento (Solo lectura inicial)
    db_documento = db.query(models_doc).filter(
        models_doc.id == documento_id,
        models_doc.empresa_id == empresa_id
    ).first()

    if not db_documento:
        raise HTTPException(status_code=404, detail="Documento no encontrado o no pertenece a la empresa.")

    # 2. BLINDAJE: Validamos ANTES de abrir cualquier transacción de escritura
    periodo_service.validar_periodo_abierto(db, empresa_id, db_documento.fecha)

    # 3. Validaciones de negocio
    if db_documento.anulado:
        raise HTTPException(status_code=409, detail="El documento ya se encuentra anulado.")

    try:
        # 4. Ahora sí, iniciamos la lógica transaccional
        # Recargamos con bloqueo para garantizar atomicidad
        db_documento = db.query(models_doc).filter(models_doc.id == documento_id).with_for_update().first()
        
        movimientos_snapshot = []
        for mov in db_documento.movimientos:
            movimientos_snapshot.append({
                "cuenta_codigo": mov.cuenta.codigo,
                "cuenta_nombre": mov.cuenta.nombre,
                "concepto": mov.concepto,
                "debito": float(mov.debito),
                "credito": float(mov.credito)
            })

        documento_snapshot = {
            "id": db_documento.id,
            "tipo_documento": db_documento.tipo_documento.nombre,
            "numero": db_documento.numero,
            "fecha": db_documento.fecha.isoformat(),
            "beneficiario": db_documento.beneficiario.razon_social if db_documento.beneficiario else None,
            "movimientos": movimientos_snapshot
        }

        log_entry = models_log(
            empresa_id=empresa_id,
            usuario_id=user_id,
            documento_id_asociado=documento_id,
            email_usuario=user_email,
            razon=razon,
            tipo_operacion='ANULACION',
            detalle_documento_json=[documento_snapshot]
        )

        db.add(log_entry)
        db_documento.anulado = True
        db_documento.estado = 'ANULADO'

        # Reversión de Inventario
        if db_documento.tipo_documento and db_documento.tipo_documento.afecta_inventario:
            movimientos_inventario_originales = db.query(models_producto.MovimientoInventario).filter(
                models_producto.MovimientoInventario.documento_id == db_documento.id
            ).all()

            for mov_inv in movimientos_inventario_originales:
                tipo_movimiento_reverso = ''
                if mov_inv.tipo_movimiento.startswith('SALIDA'):
                    tipo_movimiento_reverso = 'ENTRADA_ANULACION'
                elif mov_inv.tipo_movimiento.startswith('ENTRADA'):
                    tipo_movimiento_reverso = 'SALIDA_ANULACION'

                if tipo_movimiento_reverso:
                    service_inventario.registrar_movimiento_inventario(
                        db=db,
                        producto_id=mov_inv.producto_id,
                        bodega_id=mov_inv.bodega_id,
                        tipo_movimiento=tipo_movimiento_reverso,
                        cantidad=mov_inv.cantidad,
                        costo_unitario=mov_inv.costo_unitario,
                        fecha=datetime.utcnow(),
                        documento_id=db_documento.id
                    )
        
        db.commit()
        db.refresh(db_documento)

        # Recálculo de Cartera
        funciones_relevantes = [
            FuncionEspecial.CARTERA_CLIENTE, 
            FuncionEspecial.RC_CLIENTE, 
            FuncionEspecial.CXP_PROVEEDOR, 
            FuncionEspecial.PAGO_PROVEEDOR
        ]
        if db_documento.tipo_documento and db_documento.tipo_documento.funcion_especial in funciones_relevantes:
            if db_documento.beneficiario_id:
                cartera_service.recalcular_aplicaciones_tercero(db, tercero_id=db_documento.beneficiario_id, empresa_id=empresa_id)
                db.commit()

        return db_documento

    except HTTPException as e:
        db.rollback()
        raise e
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error interno del servidor durante la anulación: {str(e)}")
    


# REEMPLAZO PARA app/services/documento.py (Función eliminar_documento)

def eliminar_documento(db: Session, documento_id: int, empresa_id: int, user_id: int, razon: str):
    # 1. Buscamos el documento (Lectura simple)
    # Usamos query directa para no cargar relaciones pesadas si va a fallar
    db_documento_check = db.query(models_doc).filter(
        models_doc.id == documento_id, 
        models_doc.empresa_id == empresa_id
    ).first()
    
    if not db_documento_check:
        raise HTTPException(status_code=404, detail="Documento no encontrado en esta empresa.")

    # 2. BLINDAJE: Validamos ANTES de proceder
    periodo_service.validar_periodo_abierto(db, empresa_id, db_documento_check.fecha)

    try:
        # 3. Carga completa para eliminación
        db_documento = get_documento_by_id(db, documento_id=documento_id, empresa_id=empresa_id)

        # LINK ADJUSTMENT REVERSAL (HOOK)
        if db_documento.reconciliation_reference and db_documento.reconciliation_reference.startswith("BM-"):
            try:
                bm_id = int(db_documento.reconciliation_reference.split("-")[1])
                from app.models.conciliacion_bancaria import BankMovement
                
                # Buscar y liberar el movimiento bancario
                bank_move = db.query(BankMovement).filter(BankMovement.id == bm_id).first()
                if bank_move:
                    bank_move.status = "PENDING"
                    # Nota: No hacemos commit aquí, se hará junto con la eliminación abajo
                    
            except Exception as e:
                print(f"Error revirtiendo estado bancario: {e}")
                # No bloqueamos la eliminación, pero logueamos el error
        
        movimientos_a_eliminar = db_documento.movimientos[:]

        movimientos_para_log = [{
            "cuenta": mov.cuenta.codigo, "concepto": mov.concepto,
            "debito": float(mov.debito), "credito": float(mov.credito)
        } for mov in movimientos_a_eliminar]

        detalle_json_log = {
            "tipo_doc": db_documento.tipo_documento.codigo, "numero": db_documento.numero,
            "fecha": db_documento.fecha.isoformat(),
            "beneficiario": db_documento.beneficiario.razon_social if db_documento.beneficiario else None,
            "movimientos": movimientos_para_log
        }

        log_entry = models_log(
            empresa_id=empresa_id, usuario_id=user_id,
            tipo_operacion='ELIMINACION', razon=razon,
            detalle_documento_json=detalle_json_log
        )
        db.add(log_entry)
        db.flush()

        doc_eliminado_data = {
            "id_original": db_documento.id,
            "empresa_id": db_documento.empresa_id,
            "tipo_documento_id": db_documento.tipo_documento_id,
            "numero": db_documento.numero,
            "fecha": db_documento.fecha,
            "fecha_vencimiento": db_documento.fecha_vencimiento,
            "beneficiario_id": db_documento.beneficiario_id,
            "centro_costo_id": db_documento.centro_costo_id,
            "usuario_creador_id": db_documento.usuario_creador_id,
            "usuario_eliminacion_id": user_id,
            "log_eliminacion_id": log_entry.id
        }
        
        doc_eliminado = models_doc_elim(**doc_eliminado_data)
        db.add(doc_eliminado)
        db.flush()

        for mov in movimientos_a_eliminar:
            mov_eliminado = models_mov_elim(
                id_original=mov.id,
                documento_eliminado_id=doc_eliminado.id,
                documento_id_original=mov.documento_id,
                cuenta_id=mov.cuenta_id,
                centro_costo_id=mov.centro_costo_id,
                concepto=mov.concepto,
                debito=mov.debito,
                credito=mov.credito
            )
            db.add(mov_eliminado)

        db.query(models_mov).filter(models_mov.documento_id == documento_id).delete(synchronize_session=False)
        db.delete(db_documento)
        
        # Commit final se maneja usualmente en el router o aquí si no hay transacción externa
        # db.commit() # Descomentar si la ruta no hace commit
        
        return {"message": "Documento preparado para mover a la papelera."}

    except HTTPException as e:
        # No hacemos rollback global aquí porque no iniciamos la transacción, 
        # pero propagamos el error para que FastAPI lo maneje
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al eliminar: {str(e)}")
    


def get_documento_by_id(db: Session, documento_id: int, empresa_id: int):
    """
    Obtiene un único documento por su ID, asegurando que pertenezca a la empresa.
    Carga de forma anticipada las relaciones para que el detalle de productos funcione.
    """
    return db.query(models_doc).options(
        # Estrategia de carga explícita y anidada:
        # 1. Carga los movimientos del documento.
        # 2. PARA CADA movimiento, carga su cuenta Y su producto.
        selectinload(models_doc.movimientos).options(
            joinedload(models_mov.cuenta),
            joinedload(models_mov.producto)
        ),
        joinedload(models_doc.beneficiario),
        joinedload(models_doc.tipo_documento)
    ).filter(
        models_doc.id == documento_id,
        models_doc.empresa_id == empresa_id
    ).first()

def get_documentos(db: Session, empresa_id: int, filtros: dict, skip: int = 0, limit: int = 100):
    subquery = db.query(
        models_mov.documento_id,
        func.sum(models_mov.debito).label("total_debito")
    ).group_by(models_mov.documento_id).subquery()

    query = db.query(
        models_doc.id,
        models_doc.fecha,
        models_doc.numero,
        models_doc.anulado,
        models_doc.estado,
        models_doc.observaciones,
        models_tipo.codigo.label("tipo_documento_codigo"),
        models_tipo.nombre.label("tipo_documento_nombre"),
        models_tercero.razon_social.label("beneficiario_nombre"),
        subquery.c.total_debito
    ).join(
        subquery, models_doc.id == subquery.c.documento_id
    ).outerjoin(
        models_tipo, models_doc.tipo_documento_id == models_tipo.id
    ).outerjoin(
        models_tercero, models_doc.beneficiario_id == models_tercero.id
    ).filter(models_doc.empresa_id == empresa_id)

    if filtros:
        filter_conditions = []
        
        # 1. Filtro de Fechas
        if filtros.get("fecha_inicio") and filtros.get("fecha_fin"):
            filter_conditions.append(models_doc.fecha.between(filtros["fecha_inicio"], filtros["fecha_fin"]))

        # 2. CORRECCIÓN: Filtro de Tipo de Documento (Soporta ambos nombres)
        tipo_id = filtros.get("tipo_documento_id") or filtros.get("tipo_doc_id")
        if tipo_id:
            filter_conditions.append(models_doc.tipo_documento_id == tipo_id)

        # 3. Filtro de Número
        if filtros.get("numero"):
            filter_conditions.append(models_doc.numero == filtros["numero"])
            
        # 4. Filtro de Tercero
        if filtros.get("tercero_id"):
            filter_conditions.append(models_doc.beneficiario_id == filtros["tercero_id"])
            
        # 5. NUEVO: Filtro por Observaciones
        if filtros.get("observaciones"):
            filter_conditions.append(models_doc.observaciones.ilike(f"%{filtros['observaciones']}%"))

        # Aplicar todos los filtros acumulados
        if filter_conditions:
            query = query.filter(and_(*filter_conditions))

    total_records = query.count()
    documentos = query.order_by(models_doc.fecha.desc(), models_doc.numero.desc()).offset(skip).limit(limit).all()
    

    return {"total": total_records, "documentos": documentos}


def reactivar_documento(db: Session, documento_id: int, empresa_id: int):
    try:
        db_documento = db.query(models_doc).filter(
            models_doc.id == documento_id,
            models_doc.empresa_id == empresa_id
        ).with_for_update().first()

        if not db_documento:
            raise HTTPException(status_code=404, detail="Documento no encontrado o no pertenece a la empresa.")
        
        # --- NUEVO: Validar período cerrado ---
        periodo_service.validar_periodo_abierto(db, empresa_id, db_documento.fecha)
        # --------------------------------------

        if not db_documento.anulado:
            raise HTTPException(status_code=409, detail="El documento no se encuentra anulado, no se puede reactivar.")

        conflicto = db.query(models_doc).filter(
            models_doc.empresa_id == empresa_id,
            models_doc.tipo_documento_id == db_documento.tipo_documento_id,
            models_doc.numero == db_documento.numero,
            models_doc.anulado == False,
            models_doc.id != documento_id
        ).first()

        if conflicto:
            raise HTTPException(status_code=409, detail=f"No se puede reactivar. Ya existe otro documento activo con el mismo tipo y número ({db_documento.numero}).")

        db_documento.anulado = False
        db_documento.estado = 'ACTIVO'
        db.commit()
        db.refresh(db_documento)
        return db_documento
    except HTTPException as e:
        db.rollback()
        raise e
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error interno del servidor durante la reactivación: {str(e)}")


# EN app/services/documento.py

# EN app/services/documento.py

def generar_pdf_documento(db: Session, documento_id: int, empresa_id: int):
    """
    Genera el PDF visual.
    VERSIÓN ROBUSTA: Para Compras, lee directamente de MovimientoInventario
    para garantizar cantidades y costos unitarios reales, ignorando cruces contables fallidos.
    """
    # 1. Obtener documento
    db_doc = get_documento_by_id(db, documento_id, empresa_id)
    if not db_doc:
        raise HTTPException(status_code=404, detail="Documento no encontrado.")

    # 2. Plantilla
    plantilla = db.query(models_formato).filter(
        models_formato.empresa_id == empresa_id, 
        models_formato.tipo_documento_id == db_doc.tipo_documento_id
    ).first()
    html_content = plantilla.contenido_html if plantilla else "<html><body>Sin Formato</body></html>"
    
    # 3. Empresa
    empresa = db.query(models_empresa).filter(models_empresa.id == empresa_id).first()
    
    # 4. LÓGICA
    items_facturables = []
    subtotal_acumulado = 0
    impuestos_acumulados = 0
    
    # Acumuladores Contables
    suma_debito_total = 0
    suma_credito_total = 0
    
    # --- DETECCIÓN DEL MODO ---
    modo_operacion = 'GENERAL' 
    func_especial = db_doc.tipo_documento.funcion_especial
    
    funcs_venta = ['FACTURA_VENTA', 'cartera_cliente']
    funcs_compra = ['FACTURA_COMPRA', 'cxp_proveedor', 'compras', 'pago_proveedor'] # Agregado pago por si acaso
    
    try:
        if hasattr(FuncionEspecial, 'CARTERA_CLIENTE'): funcs_venta.append(FuncionEspecial.CARTERA_CLIENTE)
        if hasattr(FuncionEspecial, 'CXP_PROVEEDOR'): funcs_compra.append(FuncionEspecial.CXP_PROVEEDOR)
        if hasattr(FuncionEspecial, 'FACTURA_COMPRA'): funcs_compra.append(FuncionEspecial.FACTURA_COMPRA)
    except: pass

    if func_especial in funcs_venta: modo_operacion = 'VENTA'
    elif func_especial in funcs_compra: modo_operacion = 'COMPRA'
    
    # Detección por cuentas si no hay función especial
    if modo_operacion == 'GENERAL':
        if any(getattr(m.cuenta, 'codigo', '').startswith('4') for m in db_doc.movimientos):
            modo_operacion = 'VENTA'
        # Si toca inventario (14) o costo (6) al débito
        elif any(getattr(m.cuenta, 'codigo', '').startswith(('14', '6')) and m.debito > 0 for m in db_doc.movimientos):
            modo_operacion = 'COMPRA'

    # --- PROCESAMIENTO ---
    
    if modo_operacion == 'VENTA':
        # RUTA A: VENTA
        query_comercial = db.query(
            models_producto.Producto.codigo.label("codigo"),
            models_producto.Producto.nombre.label("nombre"),
            models_producto.MovimientoInventario.cantidad.label("cantidad_real"),
            models_mov.credito.label("valor_total")
        ).join(models_doc, models_producto.MovimientoInventario.documento_id == models_doc.id)\
         .join(models_producto.Producto, models_producto.MovimientoInventario.producto_id == models_producto.Producto.id)\
         .join(models_grupo, models_producto.Producto.grupo_id == models_grupo.id)\
         .join(models_mov, and_(
             models_mov.documento_id == models_doc.id,
             models_mov.cuenta_id == models_grupo.cuenta_ingreso_id, 
             models_mov.producto_id == models_producto.Producto.id
         ))\
         .filter(models_doc.id == documento_id, models_producto.MovimientoInventario.tipo_movimiento == 'SALIDA_VENTA').all()

        if query_comercial:
            for item in query_comercial:
                cant = float(item.cantidad_real)
                val = float(item.valor_total)
                unit = val / cant if cant > 0 else 0
                items_facturables.append({
                    "producto_codigo": item.codigo, "producto_nombre": item.nombre,
                    "cantidad": f"{cant:,.2f}", "precio_unitario": f"$ {unit:,.0f}", "subtotal": f"$ {val:,.0f}",
                    "debito_fmt": "0", "credito_fmt": f"$ {val:,.0f}"
                })
                subtotal_acumulado += val
        else:
            # Fallback Venta
            for mov in db_doc.movimientos:
                if getattr(mov.cuenta, 'codigo', '').startswith('4') and mov.credito > 0:
                    val = float(mov.credito)
                    items_facturables.append({
                        "producto_codigo": getattr(mov.cuenta, 'codigo', ''), "producto_nombre": mov.concepto,
                        "cantidad": "1.00", "precio_unitario": f"$ {val:,.0f}", "subtotal": f"$ {val:,.0f}",
                        "debito_fmt": "0", "credito_fmt": f"$ {val:,.0f}"
                    })
                    subtotal_acumulado += val

    elif modo_operacion == 'COMPRA':
        # RUTA B: COMPRA (DIRECTO A INVENTARIO - CORRECCIÓN)
        # No cruzamos con contabilidad para evitar fallos. Leemos directo del Kardex.
        query_kardex = db.query(
            models_producto.Producto.codigo.label("codigo"),
            models_producto.Producto.nombre.label("nombre"),
            models_producto.MovimientoInventario.cantidad.label("cantidad"),
            models_producto.MovimientoInventario.costo_unitario.label("costo_u"),
            models_producto.MovimientoInventario.costo_total.label("costo_t")
        ).join(models_producto.Producto, models_producto.MovimientoInventario.producto_id == models_producto.Producto.id)\
         .filter(
             models_producto.MovimientoInventario.documento_id == documento_id,
             # Aceptamos cualquier entrada (Compra, Ajuste, Inicial) para ser flexibles
             models_producto.MovimientoInventario.tipo_movimiento.like('ENTRADA%')
         ).all()

        if query_kardex:
            for item in query_kardex:
                cant = float(item.cantidad)
                unit = float(item.costo_u) # El costo unitario real de compra
                val = float(item.costo_t)  # El total de la línea
                
                items_facturables.append({
                    "producto_codigo": item.codigo, 
                    "producto_nombre": item.nombre,
                    "cantidad": f"{cant:,.2f}", # Cantidad Real
                    "precio_unitario": f"$ {unit:,.0f}", # Costo Unitario Real
                    "subtotal": f"$ {val:,.0f}",
                    "debito_fmt": f"$ {val:,.0f}", "credito_fmt": "0"
                })
                subtotal_acumulado += val
        else:
            # Fallback Compra (ej: Gastos/Servicios que no van al Kardex)
            # Buscamos débitos a Gasto(5), Costo(6) o Inventario(14) si falló el kardex
            for mov in db_doc.movimientos:
                cod = getattr(mov.cuenta, 'codigo', '')
                # Excluimos impuestos (24) y retenciones (23) de esta lista de items principal
                if (cod.startswith(('14', '5', '6', '15', '16'))) and mov.debito > 0:
                    val = float(mov.debito)
                    items_facturables.append({
                        "producto_codigo": cod, "producto_nombre": mov.concepto,
                        "cantidad": "1.00", "precio_unitario": f"$ {val:,.0f}", "subtotal": f"$ {val:,.0f}",
                        "debito_fmt": f"$ {val:,.0f}", "credito_fmt": "0"
                    })
                    subtotal_acumulado += val

    else:
        # RUTA C: GENERAL
        for mov in db_doc.movimientos:
            deb = float(mov.debito or 0)
            cred = float(mov.credito or 0)
            val_linea = deb if deb > 0 else cred
            
            items_facturables.append({
                "producto_codigo": getattr(mov.cuenta, 'codigo', ''), 
                "producto_nombre": mov.concepto,
                "cantidad": "1.00", 
                "precio_unitario": f"$ {val_linea:,.0f}", 
                "subtotal": f"$ {val_linea:,.0f}",
                "debito_fmt": f"$ {deb:,.0f}" if deb > 0 else "0",
                "credito_fmt": f"$ {cred:,.0f}" if cred > 0 else "0"
            })

    # --- CÁLCULO DE TOTALES E IMPUESTOS ---
    # Los impuestos se calculan siempre desde contabilidad para ser exactos
    for mov in db_doc.movimientos:
        suma_debito_total += float(mov.debito or 0)
        suma_credito_total += float(mov.credito or 0)
        
        cod = getattr(mov.cuenta, 'codigo', '')
        if cod.startswith('24'):
            # En ventas es crédito, en compras es débito (IVA descontable)
            if modo_operacion == 'VENTA' and mov.credito > 0:
                impuestos_acumulados += float(mov.credito)
            elif modo_operacion == 'COMPRA' and mov.debito > 0:
                impuestos_acumulados += float(mov.debito)

    if modo_operacion != 'GENERAL':
        total_general = subtotal_acumulado + impuestos_acumulados
    else:
        total_general = suma_credito_total

    # Valor en Letras
    from app.utils.numero_a_letras import numero_a_letras
    total_redondeado = round(total_general)
    valor_letras = numero_a_letras(total_redondeado)

    # 5. Contexto
    beneficiario = db_doc.beneficiario
    context = {
        "empresa": {
            "razon_social": getattr(empresa, 'razon_social', 'Empresa'),
            "nit": getattr(empresa, 'nit', ''),
            "direccion": getattr(empresa, 'direccion', ""),
            "telefono": getattr(empresa, 'telefono', ""),
            "email": getattr(empresa, 'email', ""),
            "logo_url": getattr(empresa, 'logo_url', "")
        },
        "documento": {
            "tipo_nombre": db_doc.tipo_documento.nombre.upper() if db_doc.tipo_documento else "DOCUMENTO",
            "consecutivo": db_doc.numero,
            "fecha_emision": db_doc.fecha.strftime('%d/%m/%Y'),
            "fecha_vencimiento": db_doc.fecha_vencimiento.strftime('%d/%m/%Y') if getattr(db_doc, 'fecha_vencimiento', None) else "",
            "observaciones": getattr(db_doc, 'observaciones', "")
        },
        "tercero": {
            "razon_social": getattr(beneficiario, 'razon_social', "Varios") if beneficiario else "Varios",
            "nit": getattr(beneficiario, 'nit', "") if beneficiario else "",
            "direccion": getattr(beneficiario, 'direccion', "") if beneficiario else "",
            "telefono": getattr(beneficiario, 'telefono', "") if beneficiario else ""
        },
        "items": items_facturables,
        "totales": {
            "subtotal": f"$ {subtotal_acumulado:,.0f}",
            "impuestos": f"$ {impuestos_acumulados:,.0f}",
            "total": f"$ {total_redondeado:,.0f}",
            "total_debito": f"$ {suma_debito_total:,.0f}",
            "total_credito": f"$ {suma_credito_total:,.0f}",
            "valor_letras": valor_letras
        }
    }

    # 6. Render
    try:
        template = GLOBAL_JINJA_ENV.from_string(html_content)
        rendered_html = template.render(context)
        pdf_file = HTML(string=rendered_html).write_pdf()
        filename = f"{db_doc.tipo_documento.codigo}_{db_doc.numero}.pdf"
        return pdf_file, filename
    except Exception as e:
        print(f"Error Renderizando: {e}") 
        raise HTTPException(status_code=500, detail=f"Error plantilla: {str(e)}")
    
    
def generate_account_ledger_report(
    db: Session,
    empresa_id: int,
    cuenta_id: int,
    fecha_inicio: date,
    fecha_fin: date
) -> Dict[str, Any]:
    cuenta_info = db.query(models_plan).filter(
        models_plan.id == cuenta_id,
        models_plan.empresa_id == empresa_id
    ).first()

    if not cuenta_info:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada para la empresa.")

    saldo_anterior_query = db.query(
        func.sum(models_mov.debito).label('total_debito'),
        func.sum(models_mov.credito).label('total_credito')
    ).join(models_doc, models_mov.documento_id == models_doc.id) \
    .filter(
        models_doc.empresa_id == empresa_id,
        models_mov.cuenta_id == cuenta_id,
        models_doc.fecha < fecha_inicio,
        models_doc.anulado.is_(False)
    )
    saldo_anterior_result = saldo_anterior_query.first()
    saldo_anterior = (saldo_anterior_result.total_debito or 0) - \
                     (saldo_anterior_result.total_credito or 0)

    movimientos_query = db.query(
        models_doc.fecha,
        models_tipo.nombre.label("tipo_documento"),
        models_doc.numero.label("numero_documento"),
        models_tercero.razon_social.label("beneficiario"),
        models_mov.concepto,
        models_mov.debito,
        models_mov.credito,
        models_centro_costo.codigo.label("centro_costo_codigo"),
        models_centro_costo.nombre.label("centro_costo_nombre")
    ).join(models_doc, models_mov.documento_id == models_doc.id) \
    .join(models_tipo, models_doc.tipo_documento_id == models_tipo.id) \
    .outerjoin(models_tercero, models_doc.beneficiario_id == models_tercero.id) \
    .outerjoin(models_centro_costo, models_doc.centro_costo_id == models_centro_costo.id) \
    .filter(
        models_doc.empresa_id == empresa_id,
        models_mov.cuenta_id == cuenta_id,
        models_doc.fecha.between(fecha_inicio, fecha_fin),
        models_doc.anulado.is_(False)
    )

    movimientos_data = movimientos_query.order_by(models_doc.fecha, models_doc.numero, models_doc.id, models_mov.id).all()

    current_running_balance = float(saldo_anterior)
    formatted_movimientos = []
    for mov in movimientos_data:
        current_running_balance += float(mov.debito) - float(mov.credito)
        formatted_movimientos.append({
            "fecha": mov.fecha, 
            "tipo_documento": mov.tipo_documento,
            "numero_documento": mov.numero_documento,
            "beneficiario": mov.beneficiario,
            "concepto": mov.concepto,
            "debito": float(mov.debito),
            "credito": float(mov.credito),
            "centro_costo_codigo": mov.centro_costo_codigo,
            "centro_costo_nombre": mov.centro_costo_nombre,
            "saldo_parcial": current_running_balance
        })

    return {
        "cuenta_info": {
            "id": cuenta_info.id,
            "codigo": cuenta_info.codigo,
            "nombre": cuenta_info.nombre
        },
        "saldoAnterior": float(saldo_anterior),
        "movimientos": formatted_movimientos
    }

def generate_account_ledger_report_pdf(
    db: Session,
    empresa_id: int,
    cuenta_id: int,
    fecha_inicio: date,
    fecha_fin: date
):
    report_data = generate_account_ledger_report(db, empresa_id, cuenta_id, fecha_inicio, fecha_fin)

    empresa_info = db.query(models_empresa).filter(models_empresa.id == empresa_id).first()
    empresa_nombre = empresa_info.razon_social if empresa_info else "Empresa Desconocida"
    empresa_nit = empresa_info.nit if empresa_info else "N/A"

    cuenta_info = report_data['cuenta_info']
    saldo_anterior = report_data['saldoAnterior']
    movimientos = report_data['movimientos']

    has_cost_centers = db.query(models_centro_costo).filter(models_centro_costo.empresa_id == empresa_id).count() > 0

    formatted_fecha_inicio = fecha_inicio.strftime('%d/%m/%Y')
    formatted_fecha_fin = fecha_fin.strftime('%d/%m/%Y')

    context = {
        "empresa_nombre": empresa_info.razon_social,
        "empresa_nit": empresa_info.nit,
        "cuenta_codigo": cuenta_info['codigo'],
        "cuenta_nombre": cuenta_info['nombre'],
        "fecha_inicio": formatted_fecha_inicio,
        "fecha_fin": formatted_fecha_fin,
        "saldo_anterior": saldo_anterior,
        "movimientos": movimientos,
        "has_cost_centers": has_cost_centers
    }

    try:
        template_string = TEMPLATES_EMPAQUETADOS['reports/account_ledger_report.html']
        template = GLOBAL_JINJA_ENV.from_string(template_string)
        rendered_html = template.render(context)
        return HTML(string=rendered_html).write_pdf()
    except KeyError:
        raise HTTPException(status_code=500, detail="La plantilla 'reports/account_ledger_report.html' no fue encontrada en el paquete.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al generar el PDF de Auxiliar por Cuenta: {e}")

def generate_tercero_account_ledger_report(
    db: Session,
    empresa_id: int,
    tercero_id: int,
    fecha_inicio: date,
    fecha_fin: date,
    cuenta_ids: Optional[List[int]] = None
) -> Dict[str, Any]:
    tercero_info = db.query(models_tercero).filter(
        models_tercero.id == tercero_id,
        models_tercero.empresa_id == empresa_id
    ).first()
    if not tercero_info:
        raise HTTPException(status_code=404, detail="Tercero no encontrado para la empresa.")

    saldo_anterior_global_query = db.query(
        func.sum(models_mov.debito).label('total_debito'),
        func.sum(models_mov.credito).label('total_credito')
    ).join(models_doc, models_mov.documento_id == models_doc.id) \
    .filter(
        models_doc.empresa_id == empresa_id,
        models_doc.beneficiario_id == tercero_id,
        models_doc.fecha < fecha_inicio,
        models_doc.anulado == False
    )
    if cuenta_ids:
        saldo_anterior_global_query = saldo_anterior_global_query.filter(models_mov.cuenta_id.in_(cuenta_ids))

    saldo_anterior_global_result = saldo_anterior_global_query.first()
    saldo_anterior_global = float((saldo_anterior_global_result.total_debito or 0) - \
                                (saldo_anterior_global_result.total_credito or 0))

    movimientos_query = db.query(
        models_doc.fecha,
        models_tipo.nombre.label("tipo_documento"),
        models_doc.numero.label("numero_documento"),
        models_plan.codigo.label("cuenta_codigo"),
        models_plan.nombre.label("cuenta_nombre"),
        models_mov.concepto,
        models_mov.debito,
        models_mov.credito,
        models_mov.cuenta_id,
        models_doc.id.label("documento_id"),
        models_mov.id.label("movimiento_id"),
        models_centro_costo.codigo.label("centro_costo_codigo"),
        models_centro_costo.nombre.label("centro_costo_nombre")
    ).join(models_mov, models_doc.id == models_mov.documento_id) \
    .join(models_tipo, models_doc.tipo_documento_id == models_tipo.id) \
    .join(models_plan, models_mov.cuenta_id == models_plan.id) \
    .outerjoin(models_centro_costo, models_doc.centro_costo_id == models_centro_costo.id) \
    .filter(
        models_doc.empresa_id == empresa_id,
        models_doc.beneficiario_id == tercero_id,
        models_doc.fecha.between(fecha_inicio, fecha_fin),
        models_doc.anulado == False
    )

    if cuenta_ids:
        movimientos_query = movimientos_query.filter(models_mov.cuenta_id.in_(cuenta_ids))

    movimientos_data = movimientos_query.order_by(
        models_mov.cuenta_id, 
        models_doc.fecha, 
        models_doc.numero, 
        models_mov.id
    ).all()

    movimientos_data_dicts = [row._asdict() for row in movimientos_data]
    all_affected_account_ids = set(mov['cuenta_id'] for mov in movimientos_data_dicts)
    saldos_iniciales_por_cuenta = {}

    if all_affected_account_ids:
        for c_id in all_affected_account_ids:
            saldo_query_cuenta = db.query(
                func.sum(models_mov.debito).label('total_debito'),
                func.sum(models_mov.credito).label('total_credito')
            ).join(models_doc, models_mov.documento_id == models_doc.id) \
            .filter(
                models_doc.empresa_id == empresa_id,
                models_doc.beneficiario_id == tercero_id,
                models_mov.cuenta_id == c_id,
                models_doc.fecha < fecha_inicio,
                models_doc.anulado == False
            ).first()
            saldos_iniciales_por_cuenta[c_id] = float((saldo_query_cuenta.total_debito or 0) - \
                                                (saldo_query_cuenta.total_credito or 0))

    current_running_balances_per_account = saldos_iniciales_por_cuenta.copy()
    final_formatted_movimientos = []
    for mov_dict in movimientos_data_dicts:
        debito_val = float(mov_dict.get('debito', 0))
        credito_val = float(mov_dict.get('credito', 0))
        cuenta_id_for_balance = mov_dict.get('cuenta_id')
        current_saldo_for_this_account = float(current_running_balances_per_account.get(cuenta_id_for_balance, 0))
        new_saldo_for_this_account = current_saldo_for_this_account + debito_val - credito_val
        current_running_balances_per_account[cuenta_id_for_balance] = new_saldo_for_this_account

        formatted_mov = {
            "fecha": mov_dict.get('fecha'),
            "tipo_documento": mov_dict.get('tipo_documento'),
            "numero_documento": mov_dict.get('numero_documento'),
            "cuenta_codigo": mov_dict.get('cuenta_codigo'),
            "cuenta_nombre": mov_dict.get('cuenta_nombre'),
            "concepto": mov_dict.get('concepto'),
            "debito": debito_val,
            "credito": credito_val,
            "centro_costo_codigo": mov_dict.get('centro_costo_codigo'),
            "centro_costo_nombre": mov_dict.get('centro_costo_nombre'),
            "saldo_parcial": new_saldo_for_this_account,
            "cuenta_id": cuenta_id_for_balance,
            "documento_id": mov_dict.get('documento_id'),
            "movimiento_id": mov_dict.get('movimiento_id')
        }
        final_formatted_movimientos.append(formatted_mov)

    return {
        "tercero_info": { "id": tercero_info.id, "nit": tercero_info.nit, "razon_social": tercero_info.razon_social },
        "saldoAnterior": saldo_anterior_global,
        "saldos_iniciales_por_cuenta": {str(k): float(v) for k, v in saldos_iniciales_por_cuenta.items()},
        "movimientos": final_formatted_movimientos
    }

def generate_tercero_account_ledger_report_pdf(
    db: Session,
    empresa_id: int,
    tercero_id: int,
    fecha_inicio: date,
    fecha_fin: date,
    cuenta_ids: Optional[List[int]] = None
):
    report_data = generate_tercero_account_ledger_report(db, empresa_id, tercero_id, fecha_inicio, fecha_fin, cuenta_ids)

    empresa_info = db.query(models_empresa).filter(models_empresa.id == empresa_id).first()
    empresa_nombre = empresa_info.razon_social if empresa_info else "Empresa Desconocida"
    empresa_nit = empresa_info.nit if empresa_info else "N/A"

    tercero_info = report_data['tercero_info']
    saldo_anterior_global = report_data['saldoAnterior']
    saldos_iniciales_por_cuenta = report_data['saldos_iniciales_por_cuenta']
    movimientos = report_data['movimientos']

    has_cost_centers = any(mov.get('centro_costo_codigo') for mov in movimientos)

    formatted_fecha_inicio = fecha_inicio.strftime('%d/%m/%Y')
    formatted_fecha_fin = fecha_fin.strftime('%d/%m/%Y')

    context = {
        "empresa_nombre": empresa_nombre,
        "empresa_nit": empresa_nit,
        "tercero_info": tercero_info,
        "fecha_inicio": formatted_fecha_inicio,
        "fecha_fin": formatted_fecha_fin,
        "saldo_anterior_global": saldo_anterior_global,
        "saldos_iniciales_por_cuenta": saldos_iniciales_por_cuenta, 
        "movimientos": movimientos,
        "has_cost_centers": has_cost_centers
    }

    try:
        template_string = TEMPLATES_EMPAQUETADOS['reports/tercero_account_ledger_report.html']
        template = GLOBAL_JINJA_ENV.from_string(template_string)
        rendered_html = template.render(context)
        return HTML(string=rendered_html).write_pdf()
    except KeyError:
        raise HTTPException(status_code=500, detail="La plantilla 'tercero_account_ledger_report.html' no fue encontrada en el paquete.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al generar el PDF de Auxiliar por Tercero: {e}")

def generate_income_statement_report(
    db: Session,
    empresa_id: int,
    fecha_inicio: date,
    fecha_fin: date
) -> Dict[str, Any]:
    def get_saldo_por_clase(db: Session, empresa_id: int, fecha_inicio: date, fecha_fin: date, codigo_prefixes: List[str]):
        query_saldo = db.query(
            models_plan.codigo.label("codigo"),
            models_plan.nombre.label("nombre"),
            func.sum(models_mov.debito).label("total_debito"),
            func.sum(models_mov.credito).label("total_credito")
        ).join(models_mov, models_plan.id == models_mov.cuenta_id) \
        .join(models_doc, models_mov.documento_id == models_doc.id) \
        .filter(
            models_doc.empresa_id == empresa_id,
            models_doc.fecha.between(fecha_inicio, fecha_fin),
            models_doc.anulado == False
        )

        if codigo_prefixes:
            codigo_like_conditions = [models_plan.codigo.like(f"{prefix}%") for prefix in codigo_prefixes]
            query_saldo = query_saldo.filter(or_(*codigo_like_conditions))
        else:
            return [] 

        query_saldo = query_saldo.group_by(
            models_plan.codigo,
            models_plan.nombre
        ).order_by(models_plan.codigo).all()

        formatted_data = []
        for row in query_saldo:
            saldo_contable = float(row.total_debito or 0) - float(row.total_credito or 0)
            formatted_data.append({
                "codigo": row.codigo,
                "nombre": row.nombre,
                "saldo_contable": saldo_contable,
                "debito": float(row.total_debito or 0),
                "credito": float(row.total_credito or 0)
            })
        return formatted_data

    ingresos_data_raw = get_saldo_por_clase(db, empresa_id, fecha_inicio, fecha_fin, ['4'])
    ingresos_data = [{"codigo": item['codigo'], "nombre": item['nombre'], "saldo": -item['saldo_contable']} for item in ingresos_data_raw]

    costos_data_raw = get_saldo_por_clase(db, empresa_id, fecha_inicio, fecha_fin, ['6', '7'])
    costos_data = [{"codigo": item['codigo'], "nombre": item['nombre'], "saldo": item['saldo_contable']} for item in costos_data_raw]

    gastos_data_raw = get_saldo_por_clase(db, empresa_id, fecha_inicio, fecha_fin, ['5'])
    gastos_data = [{"codigo": item['codigo'], "nombre": item['nombre'], "saldo": item['saldo_contable']} for item in gastos_data_raw]

    total_ingresos = sum(item['saldo'] for item in ingresos_data)
    total_costos = sum(item['saldo'] for item in costos_data)
    total_gastos = sum(item['saldo'] for item in gastos_data)

    utilidad_bruta = total_ingresos - total_costos
    utilidad_neta = utilidad_bruta - total_gastos

    utilidad_bruta = total_ingresos - total_costos
    utilidad_neta = utilidad_bruta - total_gastos

    return {
        "ingresos": ingresos_data,
        "costos": costos_data,
        "gastos": gastos_data,
        "totales": {
            "total_ingresos": total_ingresos,
            "total_costos": total_costos,
            "utilidad_bruta": utilidad_bruta,
            "total_gastos": total_gastos,
            "utilidad_neta": utilidad_neta
        }
    }


def generate_income_statement_report_pdf(
    db: Session,
    empresa_id: int,
    fecha_inicio: date,
    fecha_fin: date
):
    report_data = generate_income_statement_report(db, empresa_id, fecha_inicio, fecha_fin)

    empresa_info = db.query(models_empresa).filter(models_empresa.id == empresa_id).first()
    empresa_nombre = empresa_info.razon_social if empresa_info else "Empresa Desconocida"
    empresa_nit = empresa_info.nit if empresa_info else "N/A"

    context = {
        "empresa_nombre": empresa_nombre,
        "empresa_nit": empresa_nit,
        "fecha_inicio": fecha_inicio.strftime('%d/%m/%Y'),
        "fecha_fin": fecha_fin.strftime('%d/%m/%Y'),
        "ingresos": report_data['ingresos'],
        "costos": report_data['costos'],
        "gastos": report_data['gastos'],
        "totales": report_data['totales']
    }

    try:
        template_string = TEMPLATES_EMPAQUETADOS['reports/income_statement_report.html']
        template = GLOBAL_JINJA_ENV.from_string(template_string)
        rendered_html = template.render(context)
        return HTML(string=rendered_html).write_pdf()
    except KeyError:
        raise HTTPException(status_code=500, detail="La plantilla 'reports/income_statement_report.html' no fue encontrada en el paquete.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al generar el PDF de Estado de Resultados: {e}")

def generate_income_statement_cc_report(
    db: Session,
    empresa_id: int,
    fecha_inicio: date,
    fecha_fin: date,
    centro_costo_id: Optional[int] = None
) -> Dict[str, Any]:
    centro_costo_ids_a_filtrar = []
    if centro_costo_id:
        centro_costo_ids_a_filtrar = centro_costo_service.get_descendant_ids_inclusive(db, empresa_id, centro_costo_id)
        if not centro_costo_ids_a_filtrar:
            return { "ingresos": [], "costos": [], "gastos": [], "totales": {} }

    def get_saldo_por_clase_cc(db: Session, empresa_id: int, fecha_inicio: date, fecha_fin: date,
                                codigo_prefixes: List[str], centro_costo_ids: List[int]):
        query_saldo = db.query(
            models_plan.codigo.label("codigo"),
            models_plan.nombre.label("nombre"),
            func.sum(models_mov.debito).label("total_debito"),
            func.sum(models_mov.credito).label("total_credito")
        ).join(models_mov, models_plan.id == models_mov.cuenta_id) \
        .join(models_doc, models_mov.documento_id == models_doc.id) \
        .filter(
            models_doc.empresa_id == empresa_id,
            models_doc.fecha.between(fecha_inicio, fecha_fin),
            models_doc.anulado.is_(False)
        )

        if codigo_prefixes:
            codigo_like_conditions = [models_plan.codigo.like(f"{prefix}%") for prefix in codigo_prefixes]
            query_saldo = query_saldo.filter(or_(*codigo_like_conditions))

        if centro_costo_ids:
            query_saldo = query_saldo.filter(models_mov.centro_costo_id.in_(centro_costo_ids))

        query_saldo = query_saldo.group_by(models_plan.codigo, models_plan.nombre).order_by(models_plan.codigo).all()

        formatted_data = []
        for row in query_saldo:
            saldo_contable = float(row.total_debito or 0) - float(row.total_credito or 0)
            formatted_data.append({"codigo": row.codigo, "nombre": row.nombre, "saldo_contable": saldo_contable})
        return formatted_data

    ingresos_data_raw = get_saldo_por_clase_cc(db, empresa_id, fecha_inicio, fecha_fin, ['4'], centro_costo_ids_a_filtrar)
    ingresos_data = [{"codigo": item['codigo'], "nombre": item['nombre'], "saldo": -item['saldo_contable']} for item in ingresos_data_raw]

    costos_data_raw = get_saldo_por_clase_cc(db, empresa_id, fecha_inicio, fecha_fin, ['6', '7'], centro_costo_ids_a_filtrar)
    costos_data = [{"codigo": item['codigo'], "nombre": item['nombre'], "saldo": item['saldo_contable']} for item in costos_data_raw]

    gastos_data_raw = get_saldo_por_clase_cc(db, empresa_id, fecha_inicio, fecha_fin, ['5'], centro_costo_ids_a_filtrar)
    gastos_data = [{"codigo": item['codigo'], "nombre": item['nombre'], "saldo": item['saldo_contable']} for item in gastos_data_raw]

    total_ingresos = sum(item['saldo'] for item in ingresos_data)
    total_costos = sum(item['saldo'] for item in costos_data)
    total_gastos = sum(item['saldo'] for item in gastos_data)
    utilidad_bruta = total_ingresos - total_costos
    utilidad_neta = utilidad_bruta - total_gastos

    return {
        "ingresos": ingresos_data,
        "costos": costos_data,
        "gastos": gastos_data,
        "totales": {
            "total_ingresos": total_ingresos,
            "total_costos": total_costos,
            "utilidad_bruta": utilidad_bruta,
            "total_gastos": total_gastos,
            "utilidad_neta": utilidad_neta
        }
    }

def generate_income_statement_cc_report_pdf(
        
    db: Session,
    empresa_id: int,
    fecha_inicio: date,
    fecha_fin: date,
    centro_costo_id: Optional[int] = None
):
    report_data = generate_income_statement_cc_report(db, empresa_id, fecha_inicio, fecha_fin, centro_costo_id)

    empresa_info = db.query(models_empresa).filter(models_empresa.id == empresa_id).first()
    empresa_nombre = empresa_info.razon_social if empresa_info else "Empresa Desconocida"
    empresa_nit = empresa_info.nit if empresa_info else "N/A"

    centro_costo_info = None
    if centro_costo_id:
        centro_costo_info = db.query(models_centro_costo).filter(
            models_centro_costo.id == centro_costo_id,
            models_centro_costo.empresa_id == empresa_id
        ).first()

    centro_costo_nombre_display = "Todos los Centros de Costo"
    if centro_costo_info:
        centro_costo_nombre_display = f"{centro_costo_info.codigo} - {centro_costo_info.nombre}"

    context = {
        "empresa_nombre": empresa_nombre,
        "empresa_nit": empresa_nit,
        "fecha_inicio": fecha_inicio.strftime('%d/%m/%Y'),
        "fecha_fin": fecha_fin.strftime('%d/%m/%Y'),
        "centro_costo_nombre_display": centro_costo_nombre_display,
        "ingresos": report_data['ingresos'],
        "costos": report_data['costos'],
        "gastos": report_data['gastos'],
        "totales": report_data['totales']
    }

    try:
        template_string = TEMPLATES_EMPAQUETADOS['reports/income_statement_cc_report.html']
        template = GLOBAL_JINJA_ENV.from_string(template_string)
        rendered_html = template.render(context)
        return HTML(string=rendered_html).write_pdf()
    except KeyError:
        raise HTTPException(status_code=500, detail="La plantilla 'reports/income_statement_cc_report.html' no fue encontrada en el paquete.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al generar el PDF de Estado de Resultados por CC: {e}")

def generate_auxiliar_cc_cuenta_report(
    db: Session,
    empresa_id: int,
    centro_costo_id: int,
    fecha_inicio: date,
    fecha_fin: date,
    cuenta_id: Optional[int] = None
) -> Dict[str, Any]:
    centro_costo_ids_a_filtrar = centro_costo_service.get_descendant_ids_inclusive(db, empresa_id, centro_costo_id)
    if not centro_costo_ids_a_filtrar:
        raise HTTPException(status_code=404, detail="Centro de Costo no encontrado para la empresa.")

    centro_costo_info = db.query(models_centro_costo).filter(models_centro_costo.id == centro_costo_id).first()

    base_mov_query = db.query(
        models_doc.fecha, models_tipo.nombre.label("tipo_documento"), models_doc.numero.label("numero_documento"),
        models_tercero.razon_social.label("beneficiario"), models_plan.codigo.label("cuenta_codigo"),
        models_plan.nombre.label("cuenta_nombre"), models_mov.concepto, models_mov.debito, models_mov.credito,
        models_mov.cuenta_id, models_doc.id.label("documento_id"), models_mov.id.label("movimiento_id")
    ).join(models_mov, models_doc.id == models_mov.documento_id) \
    .join(models_tipo, models_doc.tipo_documento_id == models_tipo.id) \
    .join(models_plan, models_mov.cuenta_id == models_plan.id) \
    .outerjoin(models_tercero, models_doc.beneficiario_id == models_tercero.id) \
    .filter(
        models_doc.empresa_id == empresa_id,
        models_mov.centro_costo_id.in_(centro_costo_ids_a_filtrar),
        models_doc.anulado == False
    )

    saldo_anterior_global_query = base_mov_query.filter(models_doc.fecha < fecha_inicio)
    if cuenta_id:
        saldo_anterior_global_query = saldo_anterior_global_query.filter(models_mov.cuenta_id == cuenta_id)

    saldo_anterior_global_result = saldo_anterior_global_query.with_entities(
        func.sum(models_mov.debito).label('total_debito'),
        func.sum(models_mov.credito).label('total_credito')
    ).first()
    saldo_anterior_global = float((saldo_anterior_global_result.total_debito or 0) - (saldo_anterior_global_result.total_credito or 0))

    movimientos_rango_query = base_mov_query.filter(models_doc.fecha.between(fecha_inicio, fecha_fin))
    if cuenta_id:
        movimientos_rango_query = movimientos_rango_query.filter(models_mov.cuenta_id == cuenta_id)

    movimientos_data = movimientos_rango_query.order_by(models_mov.cuenta_id, models_doc.fecha, models_doc.numero, models_mov.id).all()
    movimientos_data_dicts = [row._asdict() for row in movimientos_data]
    all_affected_account_ids = set(mov['cuenta_id'] for mov in movimientos_data_dicts)
    saldos_iniciales_por_cuenta = {}

    for c_id in all_affected_account_ids:
        saldo_query_cuenta = base_mov_query.filter(
            models_mov.cuenta_id == c_id,
            models_doc.fecha < fecha_inicio
        ).with_entities(
            func.sum(models_mov.debito).label('total_debito'),
            func.sum(models_mov.credito).label('total_credito')
        ).first()
        saldos_iniciales_por_cuenta[c_id] = float((saldo_query_cuenta.total_debito or 0) - (saldo_query_cuenta.total_credito or 0))

    current_running_balances_per_account = saldos_iniciales_por_cuenta.copy() 
    final_formatted_movimientos = []
    for mov_dict in movimientos_data_dicts:
        debito_val = float(mov_dict.get('debito', 0))
        credito_val = float(mov_dict.get('credito', 0))
        cuenta_id_for_balance = mov_dict.get('cuenta_id')
        current_saldo_for_this_account = float(current_running_balances_per_account.get(cuenta_id_for_balance, 0))
        new_saldo_for_this_account = current_saldo_for_this_account + debito_val - credito_val
        current_running_balances_per_account[cuenta_id_for_balance] = new_saldo_for_this_account

        formatted_mov = {
            "fecha": mov_dict.get('fecha').isoformat() if mov_dict.get('fecha') else None,
            "tipo_documento": mov_dict.get('tipo_documento'),
            "numero_documento": mov_dict.get('numero_documento'),
            "beneficiario": mov_dict.get('beneficiario'),
            "cuenta_codigo": mov_dict.get('cuenta_codigo'),
            "cuenta_nombre": mov_dict.get('cuenta_nombre'),
            "concepto": mov_dict.get('concepto'),
            "debito": debito_val,
            "credito": credito_val,
            "saldo_parcial": new_saldo_for_this_account,
            "cuenta_id": cuenta_id_for_balance,
        }
        final_formatted_movimientos.append(formatted_mov)

    return {
        "centro_costo_info": {"id": centro_costo_info.id, "codigo": centro_costo_info.codigo, "nombre": centro_costo_info.nombre},
        "saldoAnteriorGlobal": saldo_anterior_global,
        "saldos_iniciales_por_cuenta": {str(k): float(v) for k, v in saldos_iniciales_por_cuenta.items()},
        "movimientos": final_formatted_movimientos
    }

def generate_auxiliar_cc_cuenta_report_pdf(
    db: Session,
    empresa_id: int,
    centro_costo_id: int,
    fecha_inicio: date,
    fecha_fin: date,
    cuenta_id: Optional[int] = None
):
    report_data_from_backend = generate_auxiliar_cc_cuenta_report(db, empresa_id, centro_costo_id, fecha_inicio, fecha_fin, cuenta_id)

    empresa_info = db.query(models_empresa).filter(models_empresa.id == empresa_id).first()
    empresa_nombre = empresa_info.razon_social if empresa_info else "Empresa Desconocida"
    empresa_nit = empresa_info.nit if empresa_info else "N/A"

    centro_costo_info = report_data_from_backend['centro_costo_info']
    saldo_anterior_global = report_data_from_backend['saldoAnteriorGlobal']
    saldos_iniciales_por_cuenta = report_data_from_backend['saldos_iniciales_por_cuenta']
    movimientos = report_data_from_backend['movimientos']

    centro_costo_nombre_display = f"{centro_costo_info['codigo']} - {centro_costo_info['nombre']}"

    cuenta_nombre_display = "Todas"
    if cuenta_id:
        cuenta_seleccionada = db.query(models_plan).filter(models_plan.id == cuenta_id).first()
        if cuenta_seleccionada:
            cuenta_nombre_display = f"{cuenta_seleccionada.codigo} - {cuenta_seleccionada.nombre}"

    has_cost_centers_general = db.query(models_centro_costo).filter(models_centro_costo.empresa_id == empresa_id).count() > 0

    report_rows_for_pdf = []

    report_rows_for_pdf.append({
        "type": "saldo_inicial_cc_global",
        "saldo": float(saldo_anterior_global or 0)
    })

    current_cuenta_id_in_loop = None
    for mov in movimientos:
        if mov['cuenta_id'] != current_cuenta_id_in_loop:
            report_rows_for_pdf.append({
                "type": "saldo_inicial_cuenta",
                "cuenta_id": mov['cuenta_id'],
                "cuenta_codigo": mov['cuenta_codigo'],
                "cuenta_nombre": mov['cuenta_nombre'],
                "saldo": float(saldos_iniciales_por_cuenta.get(str(mov['cuenta_id']), 0))
            })
            current_cuenta_id_in_loop = mov['cuenta_id']

        report_rows_for_pdf.append({
            "type": "movimiento",
            "fecha": mov.get('fecha'),
            "tipo_documento": mov.get('tipo_documento'),
            "numero_documento": mov.get('numero_documento'),
            "beneficiario": mov.get('beneficiario'),
            "cuenta_codigo": mov.get('cuenta_codigo'),
            "cuenta_nombre": mov.get('cuenta_nombre'),
            "concepto": mov.get('concepto'),
            "debito": float(mov.get('debito', 0)),
            "credito": float(mov.get('credito', 0)),
            "saldo_parcial": float(mov.get('saldo_parcial', 0)),
            "centro_costo_codigo": mov.get('centro_costo_codigo'),
            "centro_costo_nombre": mov.get('centro_costo_nombre')
        })

    saldo_final_cc_total = (movimientos[-1]['saldo_parcial'] if movimientos else saldo_anterior_global)

    report_rows_for_pdf.append({
        "type": "saldo_final_cc_global",
        "saldo": float(saldo_final_cc_total or 0)
    })

    formatted_fecha_inicio = fecha_inicio.strftime('%d/%m/%Y')
    formatted_fecha_fin = fecha_fin.strftime('%d/%m/%Y')

    context = {
        "empresa_nombre": empresa_nombre,
        "empresa_nit": empresa_nit,
        "centro_costo_nombre_display": centro_costo_nombre_display,
        "cuenta_nombre_display": cuenta_nombre_display,
        "fecha_inicio": formatted_fecha_inicio,
        "fecha_fin": formatted_fecha_fin,
        "report_rows_for_pdf": report_rows_for_pdf,
        "has_cost_centers": has_cost_centers_general
    }

    try:
        template_string = TEMPLATES_EMPAQUETADOS['reports/auxiliar_cc_cuenta_report.html']
        template = GLOBAL_JINJA_ENV.from_string(template_string)
        rendered_html = template.render(context)
        return HTML(string=rendered_html).write_pdf()
    except KeyError:
        raise HTTPException(status_code=500, detail="La plantilla 'reports/auxiliar_cc_cuenta_report.html' no fue encontrada en el paquete.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al generar el PDF de Auxiliar por CC y Cuenta: {e}")

def get_saldo_grupo_cuentas_cc(db: Session, empresa_id: int, fecha_corte: date, codigo_prefixes: List[str], centro_costo_ids: List[int]) -> List[Dict[str, Any]]:
    conditions = [func.substr(models_plan.codigo, 1, len(p)) == p for p in codigo_prefixes]

    query = (
        db.query(
            models_plan.codigo,
            models_plan.nombre,
            func.coalesce(func.sum(models_mov.debito - models_mov.credito), 0).label('saldo')
        )
        .outerjoin(models_mov, and_(
            models_mov.cuenta_id == models_plan.id,
            models_mov.documento.has(models_doc.fecha <= fecha_corte),
            models_mov.documento.has(models_doc.anulado == False)
        ))
        .filter(models_plan.empresa_id == empresa_id)
        .filter(or_(*conditions))
    )

    if centro_costo_ids:
        query = query.filter(models_mov.centro_costo_id.in_(centro_costo_ids))

    query = query.group_by(models_plan.codigo, models_plan.nombre).order_by(models_plan.codigo)

    saldos_consolidados = {}
    for row in query.all():
        if row.codigo not in saldos_consolidados:
            saldos_consolidados[row.codigo] = {'nombre': row.nombre, 'saldo': 0}
        saldos_consolidados[row.codigo]['saldo'] += row.saldo

    results = [{'codigo': k, 'nombre': v['nombre'], 'saldo': v['saldo']} for k, v in saldos_consolidados.items()]

    return [r for r in results if r['saldo'] != 0]

def generate_balance_sheet_cc_report(db: Session, empresa_id: int, fecha_corte: date, centro_costo_id: Optional[int] = None) -> Dict[str, Any]:
    centro_costo_ids_a_filtrar = []
    if centro_costo_id:
        centro_costo_ids_a_filtrar = centro_costo_service.get_descendant_ids_inclusive(db, empresa_id, centro_costo_id)
        if not centro_costo_ids_a_filtrar:
            return { "activos": [], "pasivos": [], "patrimonio": [], "utilidad_ejercicio": 0, "total_activos": 0, "total_pasivos": 0, "total_patrimonio": 0, "total_pasivo_patrimonio": 0 }

    activos_data = get_saldo_grupo_cuentas_cc(db, empresa_id, fecha_corte, ['1'], centro_costo_ids_a_filtrar)
    pasivos_data = get_saldo_grupo_cuentas_cc(db, empresa_id, fecha_corte, ['2'], centro_costo_ids_a_filtrar)
    patrimonio_data = get_saldo_grupo_cuentas_cc(db, empresa_id, fecha_corte, ['3'], centro_costo_ids_a_filtrar)

    fecha_inicio_ejercicio = date(fecha_corte.year, 1, 1)
    try:
        income_statement_data = generate_income_statement_cc_report(
            db, empresa_id, fecha_inicio_ejercicio, fecha_corte, centro_costo_id
        )
        utilidad_ejercicio = float(income_statement_data['totales'].get('utilidad_neta', 0))
    except Exception:
        utilidad_ejercicio = 0.0

    total_activos = float(sum(item['saldo'] for item in activos_data))
    for item in pasivos_data:
        item['saldo'] *= -1
    total_pasivos = float(sum(item['saldo'] for item in pasivos_data))
    for item in patrimonio_data:
        item['saldo'] *= -1
    total_patrimonio_base = float(sum(item['saldo'] for item in patrimonio_data))
    total_patrimonio = total_patrimonio_base + utilidad_ejercicio

    return {
        "activos": activos_data, "pasivos": pasivos_data, "patrimonio": patrimonio_data,
        "utilidad_ejercicio": utilidad_ejercicio, "total_activos": total_activos,
        "total_pasivos": total_pasivos, "total_patrimonio": total_patrimonio,
        "total_pasivo_patrimonio": total_pasivos + total_patrimonio
    }

def generate_balance_sheet_cc_report_pdf(db: Session, empresa_id: int, fecha_corte: date, centro_costo_id: Optional[int] = None):
    report_data = generate_balance_sheet_cc_report(db, empresa_id, fecha_corte, centro_costo_id)

    empresa = db.query(models_empresa).filter(models_empresa.id == empresa_id).first()

    centro_costo_nombre = "Todos (Consolidado)"
    if centro_costo_id:
        cc = db.query(models_centro_costo).filter(models_centro_costo.id == centro_costo_id).first()
        if cc:
            centro_costo_nombre = f"{cc.codigo} - {cc.nombre}"

    try:
        template_string = TEMPLATES_EMPAQUETADOS["reports/balance_general_cc_report.html"]
        template = GLOBAL_JINJA_ENV.from_string(template_string)
        html_string = template.render(
            reporte=report_data,
            empresa=empresa,
            fecha_corte=fecha_corte,
            centro_costo_nombre=centro_costo_nombre 
        )
        return HTML(string=html_string).write_pdf()
    except KeyError:
        raise HTTPException(status_code=500, detail="La plantilla 'reports/balance_general_cc_report.html' no fue encontrada en el paquete.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al generar el PDF de Balance General por CC: {e}")


def buscar_documentos_para_gestion(db: Session, filtros: schemas_doc.DocumentoGestionFiltros, empresa_id: int) -> List[schemas_doc.DocumentoGestionResult]:
    subquery_total = db.query(
        models_mov.documento_id,
        func.sum(models_mov.debito).label("total")
    ).group_by(models_mov.documento_id).subquery()

    query = db.query(
        models_doc.id,
        models_doc.fecha,
        models_tipo.nombre.label("tipo_documento"),
        models_doc.numero,
        models_tercero.razon_social.label("beneficiario"),
        subquery_total.c.total,
        models_doc.anulado,
        models_doc.estado
    ).join(subquery_total, models_doc.id == subquery_total.c.documento_id) \
     .join(models_tipo, models_doc.tipo_documento_id == models_tipo.id) \
     .outerjoin(models_tercero, models_doc.beneficiario_id == models_tercero.id) \
     .filter(models_doc.empresa_id == empresa_id)

    if not filtros.incluirAnulados:
        query = query.filter(models_doc.anulado == False)

    if filtros.fechaInicio and filtros.fechaFin:
        query = query.filter(models_doc.fecha.between(filtros.fechaInicio, filtros.fechaFin))

    if filtros.tipoDocIds:
        query = query.filter(models_doc.tipo_documento_id.in_(filtros.tipoDocIds))

    if filtros.terceroIds:
        query = query.filter(models_doc.beneficiario_id.in_(filtros.terceroIds))

    if filtros.centroCostoIds:
        query = query.filter(models_doc.centro_costo_id.in_(filtros.centroCostoIds))

    if filtros.numero:
        numeros = [n.strip() for n in filtros.numero.split(',') if n.strip()]
        if numeros:
            query = query.filter(models_doc.numero.in_(numeros))

    if filtros.valorMonto is not None and filtros.valorMonto > 0:
        if filtros.valorOperador == 'mayor':
            query = query.filter(subquery_total.c.total > filtros.valorMonto)
        elif filtros.valorOperador == 'menor':
            query = query.filter(subquery_total.c.total < filtros.valorMonto)
        elif filtros.valorOperador == 'igual':
            query = query.filter(subquery_total.c.total == filtros.valorMonto)

    # Filtros que requieren JOIN con Movimientos
    if filtros.cuentaIds or filtros.conceptoKeyword or filtros.productoIds:
        query = query.join(models_mov, models_doc.id == models_mov.documento_id)
        
        if filtros.cuentaIds:
            query = query.filter(models_mov.cuenta_id.in_(filtros.cuentaIds))
            
        if filtros.productoIds:
            query = query.filter(models_mov.producto_id.in_(filtros.productoIds))

        if filtros.conceptoKeyword:
            query = query.filter(models_mov.concepto.ilike(f"%{filtros.conceptoKeyword}%"))

    query = query.group_by(
        models_doc.id, models_doc.fecha, models_tipo.nombre,
        models_doc.numero, models_tercero.razon_social,
        subquery_total.c.total, models_doc.anulado, models_doc.estado
    ).order_by(models_doc.fecha.desc(), models_doc.numero.desc())

    resultados = query.limit(500).all()
    return resultados

def anular_documentos_masivamente(db: Session, payload: schemas_doc.DocumentoAccionMasivaPayload, empresa_id: int, user_id: int, user_email: str):
    documentos_anulados_count = 0
    ids_no_encontrados_o_fallidos = []

    try:
        for doc_id in payload.documentoIds:
            try:
                anular_documento(
                    db=db,
                    documento_id=doc_id,
                    empresa_id=empresa_id,
                    user_id=user_id,
                    user_email=user_email,
                    razon=payload.razon
                )
                documentos_anulados_count += 1
            except HTTPException as e:
                if e.status_code in [404, 400]:
                    ids_no_encontrados_o_fallidos.append(doc_id)
                else:
                    raise e

        db.commit()

        mensaje = f"{documentos_anulados_count} documento(s) anulado(s) exitosamente."
        if ids_no_encontrados_o_fallidos:
            mensaje += f" IDs no procesados (no encontrados, ya anulados, o con error): {ids_no_encontrados_o_fallidos}."

        return {"message": mensaje}

    except Exception as e:
        db.rollback()
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Error crítico durante la anulación masiva. Ningún documento fue anulado. Detalle: {str(e)}")

def eliminar_documentos_masivamente(db: Session, payload: schemas_doc.DocumentoAccionMasivaPayload, empresa_id: int, user_id: int):
    eliminados_count = 0
    fallidos_ids = []

    try:
        docs_a_eliminar = db.query(models_doc).filter(
            models_doc.id.in_(payload.documentoIds),
            models_doc.empresa_id == empresa_id
        ).all()

        ids_encontrados = {doc.id for doc in docs_a_eliminar}
        ids_no_encontrados = set(payload.documentoIds) - ids_encontrados
        fallidos_ids.extend(list(ids_no_encontrados))

        with db.begin_nested():
            for doc in docs_a_eliminar:
                beneficiario_id_afectado = doc.beneficiario_id

                eliminar_documento(db=db, documento_id=doc.id, empresa_id=empresa_id, user_id=user_id, razon=payload.razon)

                tipo_doc = db.query(models_tipo).filter(models_tipo.id == doc.tipo_documento_id).with_for_update().first()

                if tipo_doc and not tipo_doc.numeracion_manual:
                    if tipo_doc.consecutivo_actual == doc.numero:
                        tipo_doc.consecutivo_actual -= 1

                eliminados_count += 1

        db.commit()

        terceros_afectados_ids = {doc.beneficiario_id for doc in docs_a_eliminar if doc.beneficiario_id}

        for tercero_id in terceros_afectados_ids:
            cartera_service.recalcular_aplicaciones_tercero(db, tercero_id=tercero_id, empresa_id=empresa_id)

        mensaje = f"{eliminados_count} documento(s) eliminado(s) exitosamente."
        if fallidos_ids:
            mensaje += f" IDs no procesados (no encontrados o con error): {fallidos_ids}."

        return {"message": mensaje}

    except Exception as e:
        db.rollback()
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Error crítico durante la eliminación masiva. Ningún documento fue eliminado. Detalle: {str(e)}")

def update_documento(db: Session, documento_id: int, documento_update: schemas_doc.DocumentoUpdate, empresa_id: int, user_id: int):
    # 1. Buscamos el documento original (Lectura simple)
    db_documento_check = db.query(models_doc).filter(
        models_doc.id == documento_id, 
        models_doc.empresa_id == empresa_id
    ).first()

    if not db_documento_check:
        raise HTTPException(status_code=404, detail="Documento no encontrado.")

    # 2. BLINDAJE: Validamos el documento ORIGINAL
    periodo_service.validar_periodo_abierto(db, empresa_id, db_documento_check.fecha)

    # 3. BLINDAJE: Validamos la NUEVA FECHA (si cambia)
    if documento_update.fecha and documento_update.fecha != db_documento_check.fecha:
        periodo_service.validar_periodo_abierto(db, empresa_id, documento_update.fecha)

    try:
        with db.begin_nested():
            # Recargamos con bloqueo
            db_documento = db.query(models_doc).filter(models_doc.id == documento_id).with_for_update().first()

            if db_documento.anulado:
                raise HTTPException(status_code=400, detail="No se puede modificar un documento anulado.")

            beneficiario_original_id = db_documento.beneficiario_id

            total_debito = sum(mov.debito for mov in documento_update.movimientos)
            total_credito = sum(mov.credito for mov in documento_update.movimientos)
            if abs(total_debito - total_credito) > 0.001:
                raise HTTPException(status_code=400, detail="Error de partida doble.")

            update_data = documento_update.model_dump(exclude={"movimientos", "aplicaciones"}, exclude_unset=True)
            for key, value in update_data.items():
                setattr(db_documento, key, value)
            db_documento.updated_by = user_id

            db.query(models_mov).filter(models_mov.documento_id == documento_id).delete(synchronize_session=False)

            for mov_in in documento_update.movimientos:
                mov_data = mov_in.model_dump()
                if mov_data.get('centro_costo_id') is None and documento_update.centro_costo_id is not None:
                    mov_data['centro_costo_id'] = documento_update.centro_costo_id
                db_movimiento = models_mov(**mov_data, documento_id=documento_id)
                db.add(db_movimiento)

            db.query(models_aplica).filter(models_aplica.documento_pago_id == documento_id).delete(synchronize_session=False)
            if documento_update.aplicaciones:
                for aplicacion in documento_update.aplicaciones:
                    db.add(models_aplica(**aplicacion.model_dump(), documento_pago_id=documento_id, empresa_id=empresa_id))

            db.flush()

        # Recálculos post-update
        terceros_a_recalcular = set()
        if beneficiario_original_id:
            terceros_a_recalcular.add(beneficiario_original_id)
        if db_documento.beneficiario_id:
            terceros_a_recalcular.add(db_documento.beneficiario_id)

        if terceros_a_recalcular:
            tipo_doc = db.query(models_tipo).filter(models_tipo.id == db_documento.tipo_documento_id).first()
            funciones_relevantes = [
                FuncionEspecial.CARTERA_CLIENTE, 
                FuncionEspecial.RC_CLIENTE, 
                FuncionEspecial.CXP_PROVEEDOR, 
                FuncionEspecial.PAGO_PROVEEDOR
            ]
            if tipo_doc and tipo_doc.funcion_especial in funciones_relevantes:
                for tercero_id in terceros_a_recalcular:
                    cartera_service.recalcular_aplicaciones_tercero(db, tercero_id=tercero_id, empresa_id=empresa_id)
        
        log_entry_modificacion = models_log(
            empresa_id=db_documento.empresa_id,
            usuario_id=user_id,
            tipo_operacion='MODIFICACION',
            razon='Actualización de documento desde el editor.',
            fecha_operacion=datetime.utcnow(), 
            detalle_documento_json=[{"id": db_documento.id, "tipo_documento": db_documento.tipo_documento.codigo, "numero": db_documento.numero}]
        )

        db.add(log_entry_modificacion)
        db.commit()
        db.refresh(db_documento)

        return db_documento

    except Exception as e:
        db.rollback()
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")
    
    


def update_documento_concepto(db: Session, documento_id: int, nuevo_concepto: str, empresa_id: int):
    db_documento = db.query(models_doc).filter(
        models_doc.id == documento_id,
        models_doc.empresa_id == empresa_id
    ).first()

    if db_documento:
        for mov in db_documento.movimientos:
            mov.concepto = nuevo_concepto

def generate_auxiliar_por_facturas(
    db: Session,
    empresa_id: int,
    tercero_id: int,
    fecha_inicio: date,
    fecha_fin: date
) -> Dict[str, Any]:
    cuentas_cxc_ids = _get_cuentas_especiales_ids(db, empresa_id, 'cxc')
    if not cuentas_cxc_ids:
        return {"facturas": [], "totales": {}}

    factura_ids_query = db.query(models_doc.id).join(
        models_tipo, models_doc.tipo_documento_id == models_tipo.id
    ).join(
        models_mov, models_doc.id == models_mov.documento_id
    ).filter(
        models_doc.empresa_id == empresa_id,
        models_doc.beneficiario_id == tercero_id,
        models_doc.fecha.between(fecha_inicio, fecha_fin),
        models_doc.anulado == False,
        models_tipo.funcion_especial == FuncionEspecial.CARTERA_CLIENTE,
        models_mov.cuenta_id.in_(cuentas_cxc_ids)
    ).distinct()

    facturas_base = db.query(
        models_doc.id,
        models_doc.fecha,
        models_doc.numero
    ).filter(
        models_doc.id.in_(factura_ids_query)
    ).order_by(models_doc.fecha.asc(), models_doc.id.asc()).all()

    if not facturas_base:
        return {"facturas": [], "totales": {"total_facturas": 0, "total_abonos": 0, "saldo_final": 0}}

    factura_ids = [f.id for f in facturas_base]



    # REEMPLAZAR ESTE BLOQUE COMPLETO EN generate_auxiliar_por_facturas:
    valores_originales = db.query(
        models_mov.documento_id,
        func.sum(models_mov.debito).label("valor_original")
    ).filter(
        models_mov.documento_id.in_(factura_ids),
        models_mov.cuenta_id.in_(cuentas_cxc_ids) # <-- FIX CRÍTICO: SOLO SUMAR DÉBITOS A CUENTAS CXC
    ).group_by(models_mov.documento_id).all()
    
    
    original_map = {v.documento_id: v.valor_original for v in valores_originales}

    totales_abonos = db.query(
        models_aplica.documento_factura_id,
        func.sum(models_aplica.valor_aplicado).label("total_abonos")
    ).join(models_doc, models_aplica.documento_pago_id == models_doc.id)\
     .filter(models_aplica.documento_factura_id.in_(factura_ids), models_doc.anulado == False)\
     .group_by(models_aplica.documento_factura_id).all()
    abonos_map = {a.documento_factura_id: a.total_abonos for a in totales_abonos}

    abonos_detalle_query = db.query(
        models_aplica.documento_factura_id,
        models_aplica.valor_aplicado,
        models_tipo.nombre.label("pago_tipo"),
        models_doc.numero.label("pago_numero"),
        models_doc.fecha.label("pago_fecha")
    ).join(models_doc, models_aplica.documento_pago_id == models_doc.id)\
     .join(models_tipo, models_doc.tipo_documento_id == models_tipo.id)\
     .filter(models_aplica.documento_factura_id.in_(factura_ids), models_doc.anulado == False)\
     .order_by(models_doc.fecha.asc()).all()

    detalle_map = {fid: [] for fid in factura_ids}
    for abono in abonos_detalle_query:
        detalle_map[abono.documento_factura_id].append({
            "documento": f"{abono.pago_tipo}-{abono.pago_numero}",
            "valor": float(abono.valor_aplicado)
        })

    reporte_facturas = []
    for factura in facturas_base:
        valor_original = float(original_map.get(factura.id, 0))
        total_abonos = float(abonos_map.get(factura.id, 0))
        reporte_facturas.append({
            "id": factura.id,
            "fecha": factura.fecha,
            "documento": f"Factura de Venta-{factura.numero}",
            "valor_original": valor_original,
            "total_abonos": total_abonos,
            "saldo_factura": valor_original - total_abonos,
            "abonos_detalle": detalle_map.get(factura.id, [])
        })

    total_facturas_sum = sum(f['valor_original'] for f in reporte_facturas)
    total_abonos_sum = sum(f['total_abonos'] for f in reporte_facturas)

    totales = {
        "total_facturas": total_facturas_sum,
        "total_abonos": total_abonos_sum,
        "saldo_final": total_facturas_sum - total_abonos_sum
    }

    return {"facturas": reporte_facturas, "totales": totales}

def generate_auxiliar_por_recibos(
    db: Session,
    empresa_id: int,
    tercero_id: int,
    fecha_inicio: date,
    fecha_fin: date
) -> Dict[str, Any]:
    cuentas_cxc_ids = _get_cuentas_especiales_ids(db, empresa_id, 'cxc')
    if not cuentas_cxc_ids:
        return {"recibos": [], "totales": {"total_recibos": 0}}

    recibos_potenciales = db.query(
        models_doc.id,
        models_doc.fecha,
        models_doc.numero
    ).join(models_tipo, models_doc.tipo_documento_id == models_tipo.id)\
     .filter(
        models_doc.empresa_id == empresa_id,
        models_doc.beneficiario_id == tercero_id,
        models_doc.fecha.between(fecha_inicio, fecha_fin),
        models_doc.anulado == False,
        models_tipo.funcion_especial == FuncionEspecial.RC_CLIENTE
    ).order_by(models_doc.fecha.asc(), models_doc.id.asc()).all()

    if not recibos_potenciales:
        return {"recibos": [], "totales": {"total_recibos": 0}}

    recibos_base = []
    for rc in recibos_potenciales:
        if _documento_afecta_cuentas(db, rc.id, cuentas_cxc_ids):
            recibos_base.append(rc)

    if not recibos_base:
        return {"recibos": [], "totales": {"total_recibos": 0}}

    recibo_ids = [r.id for r in recibos_base]

    valores_recibos = db.query(
        models_mov.documento_id,
        func.sum(models_mov.credito).label("valor_total")
    ).filter(models_mov.documento_id.in_(recibo_ids), models_mov.cuenta_id.in_(cuentas_cxc_ids))\
     .group_by(models_mov.documento_id).all()
    valor_map = {v.documento_id: v.valor_total for v in valores_recibos}

    facturas_afectadas_query = db.query(
        models_aplica.documento_pago_id,
        models_aplica.valor_aplicado,
        models_doc.numero.label("factura_numero"),
        models_tipo.nombre.label("factura_tipo")
    ).join(models_doc, models_aplica.documento_factura_id == models_doc.id)\
     .join(models_tipo, models_doc.tipo_documento_id == models_tipo.id)\
     .filter(models_aplica.documento_pago_id.in_(recibo_ids)).all()

    facturas_map = {rid: [] for rid in recibo_ids}
    for f in facturas_afectadas_query:
        facturas_map[f.documento_pago_id].append({
            "documento": f"{f.factura_tipo}-{f.factura_numero}",
            "valor": float(f.valor_aplicado)
        })

    reporte_recibos = []
    for recibo in recibos_base:
        reporte_recibos.append({
            "id": recibo.id,
            "fecha": recibo.fecha,
            "documento": f"Recibo de Caja-{recibo.numero}",
            "valor_total": float(valor_map.get(recibo.id, 0)),
            "facturas_afectadas": facturas_map.get(recibo.id, [])
        })

    reporte_recibos = [r for r in reporte_recibos if r['valor_total'] > 0]

    total_recibos_sum = sum(r['valor_total'] for r in reporte_recibos)
    totales = {"total_recibos": total_recibos_sum}

    return {"recibos": reporte_recibos, "totales": totales}

def generate_auxiliar_por_facturas_pdf(
    db: Session,
    empresa_id: int,
    tercero_id: int,
    fecha_inicio: date,
    fecha_fin: date
):
    report_data = generate_auxiliar_por_facturas(db, empresa_id, tercero_id, fecha_inicio, fecha_fin)
    empresa = db.query(models_empresa).filter(models_empresa.id == empresa_id).first()
    tercero = db.query(models_tercero).filter(models_tercero.id == tercero_id).first()

    try:
        template_string = TEMPLATES_EMPAQUETADOS['reports/auxiliar_por_facturas_report.html']
        template = GLOBAL_JINJA_ENV.from_string(template_string)
        html_string = template.render(
            reporte=report_data,
            empresa=empresa,
            tercero=tercero,
            fecha_inicio=fecha_inicio.strftime('%d/%m/%Y'),
            fecha_fin=fecha_fin.strftime('%d/%m/%Y')
        )
        return HTML(string=html_string).write_pdf()
    except KeyError:
        raise HTTPException(status_code=500, detail="La plantilla 'reports/auxiliar_por_facturas_report.html' no fue encontrada en el paquete.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al generar el PDF de Auxiliar por Facturas: {e}")


def generate_auxiliar_por_recibos_pdf(
    db: Session,
    empresa_id: int,
    tercero_id: int,
    fecha_inicio: date,
    fecha_fin: date
):
    report_data = generate_auxiliar_por_recibos(db, empresa_id, tercero_id, fecha_inicio, fecha_fin)
    empresa = db.query(models_empresa).filter(models_empresa.id == empresa_id).first()
    tercero = db.query(models_tercero).filter(models_tercero.id == tercero_id).first()

    try:
        template_string = TEMPLATES_EMPAQUETADOS['reports/auxiliar_por_recibos_report.html']
        template = GLOBAL_JINJA_ENV.from_string(template_string)
        html_string = template.render(
            reporte=report_data,
            empresa=empresa,
            tercero=tercero,
            fecha_inicio=fecha_inicio.strftime('%d/%m/%Y'),
            fecha_fin=fecha_fin.strftime('%d/%m/%Y')
        )
        return HTML(string=html_string).write_pdf()
    except KeyError:
        raise HTTPException(status_code=500, detail="La plantilla 'reports/auxiliar_por_recibos_report.html' no fue encontrada en el paquete.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al generar el PDF de Auxiliar por Recibos: {e}")


def generate_auxiliar_proveedores_por_facturas(
    db: Session,
    empresa_id: int,
    tercero_id: int,
    fecha_inicio: date,
    fecha_fin: date
) -> Dict[str, Any]:
    cuentas_cxp_ids = _get_cuentas_especiales_ids(db, empresa_id, 'cxp')
    if not cuentas_cxp_ids:
        return {"facturas": [], "totales": {}}

    factura_ids_query = db.query(models_doc.id).join(
        models_tipo, models_doc.tipo_documento_id == models_tipo.id
    ).join(
        models_mov, models_doc.id == models_mov.documento_id
    ).filter(
        models_doc.empresa_id == empresa_id,
        models_doc.beneficiario_id == tercero_id,
        models_doc.fecha.between(fecha_inicio, fecha_fin),
        models_doc.anulado == False,
        models_tipo.funcion_especial == FuncionEspecial.CXP_PROVEEDOR,
        models_mov.cuenta_id.in_(cuentas_cxp_ids)
    ).distinct()

    facturas_base = db.query(
        models_doc.id, models_doc.fecha, models_doc.numero
    ).filter(
        models_doc.id.in_(factura_ids_query)
    ).order_by(models_doc.fecha.asc(), models_doc.id.asc()).all()

    if not facturas_base:
        return {"facturas": [], "totales": {"total_facturas": 0, "total_abonos": 0, "saldo_final": 0}}

    factura_ids = [f.id for f in facturas_base]



    valores_originales = db.query(
        models_mov.documento_id,
        func.sum(models_mov.credito).label("valor_original")
    ).filter(models_mov.documento_id.in_(factura_ids), models_mov.cuenta_id.in_(cuentas_cxp_ids))\
     .group_by(models_mov.documento_id).all()
    


    original_map = {v.documento_id: v.valor_original for v in valores_originales}

    totales_abonos = db.query(
        models_aplica.documento_factura_id,
        func.sum(models_aplica.valor_aplicado).label("total_abonos")
    ).join(models_doc, models_aplica.documento_pago_id == models_doc.id)\
     .filter(models_aplica.documento_factura_id.in_(factura_ids), models_doc.anulado == False)\
     .group_by(models_aplica.documento_factura_id).all()
    abonos_map = {a.documento_factura_id: a.total_abonos for a in totales_abonos}

    abonos_detalle_query = db.query(
        models_aplica.documento_factura_id,
        models_aplica.valor_aplicado,
        models_tipo.nombre.label("pago_tipo"),
        models_doc.numero.label("pago_numero"),
        models_doc.fecha.label("pago_fecha")
    ).join(models_doc, models_aplica.documento_pago_id == models_doc.id)\
     .join(models_tipo, models_doc.tipo_documento_id == models_tipo.id)\
     .filter(models_aplica.documento_factura_id.in_(factura_ids), models_doc.anulado == False)\
     .order_by(models_doc.fecha.asc()).all()

    detalle_map = {fid: [] for fid in factura_ids}
    for abono in abonos_detalle_query:
        detalle_map[abono.documento_factura_id].append({
            "documento": f"{abono.pago_tipo}-{abono.pago_numero}",
            "valor": float(abono.valor_aplicado)
        })

    reporte_facturas = []
    for factura in facturas_base:
        valor_original = float(original_map.get(factura.id, 0))
        total_abonos = float(abonos_map.get(factura.id, 0))
        reporte_facturas.append({
            "id": factura.id, "fecha": factura.fecha,
            "documento": f"Factura de Compra-{factura.numero}",
            "valor_original": valor_original, "total_abonos": total_abonos,
            "saldo_factura": valor_original - total_abonos,
            "abonos_detalle": detalle_map.get(factura.id, [])
        })

    totales = {
        "total_facturas": sum(f['valor_original'] for f in reporte_facturas),
        "total_abonos": sum(f['total_abonos'] for f in reporte_facturas),
        "saldo_final": sum(f['saldo_factura'] for f in reporte_facturas)
    }
    return {"facturas": reporte_facturas, "totales": totales}

def generate_auxiliar_proveedores_por_recibos(
    db: Session,
    empresa_id: int,
    tercero_id: int,
    fecha_inicio: date,
    fecha_fin: date
) -> Dict[str, Any]:
    cuentas_cxp_ids = _get_cuentas_especiales_ids(db, empresa_id, 'cxp')
    if not cuentas_cxp_ids:
        return {"recibos": [], "totales": {"total_recibos": 0}}

    recibos_potenciales = db.query(
        models_doc.id, models_doc.fecha, models_doc.numero
    ).join(models_tipo, models_doc.tipo_documento_id == models_tipo.id)\
     .filter(
        models_doc.empresa_id == empresa_id,
        models_doc.beneficiario_id == tercero_id,
        models_doc.fecha.between(fecha_inicio, fecha_fin),
        models_doc.anulado == False,
        models_tipo.funcion_especial == FuncionEspecial.PAGO_PROVEEDOR
    ).order_by(models_doc.fecha.asc(), models_doc.id.asc()).all()

    if not recibos_potenciales:
        return {"recibos": [], "totales": {"total_recibos": 0}}

    recibos_base = []
    for ce in recibos_potenciales:
        if _documento_afecta_cuentas(db, ce.id, cuentas_cxp_ids):
            recibos_base.append(ce)

    if not recibos_base:
        return {"recibos": [], "totales": {"total_recibos": 0}}

    recibo_ids = [r.id for r in recibos_base]

    valores_recibos = db.query(
        models_mov.documento_id,
        func.sum(models_mov.debito).label("valor_total")
    ).filter(models_mov.documento_id.in_(recibo_ids), models_mov.cuenta_id.in_(cuentas_cxp_ids))\
     .group_by(models_mov.documento_id).all()
    valor_map = {v.documento_id: v.valor_total for v in valores_recibos}

    facturas_afectadas_query = db.query(
        models_aplica.documento_pago_id,
        models_aplica.valor_aplicado,
        models_doc.numero.label("factura_numero"),
        models_tipo.nombre.label("factura_tipo")
    ).join(models_doc, models_aplica.documento_factura_id == models_doc.id)\
     .join(models_tipo, models_doc.tipo_documento_id == models_tipo.id)\
     .filter(models_aplica.documento_pago_id.in_(recibo_ids)).all()

    facturas_map = {rid: [] for rid in recibo_ids}
    for f in facturas_afectadas_query:
        facturas_map[f.documento_pago_id].append({
            "documento": f"{f.factura_tipo}-{f.factura_numero}",
            "valor": float(f.valor_aplicado)
        })

    reporte_recibos = []
    for recibo in recibos_base:
        reporte_recibos.append({
            "id": recibo.id,
            "fecha": recibo.fecha,
            "documento": f"Comprobante de Egreso-{recibo.numero}",
            "valor_total": float(valor_map.get(recibo.id, 0)),
            "facturas_afectadas": facturas_map.get(recibo.id, [])
        })

    reporte_recibos = [r for r in reporte_recibos if r['valor_total'] > 0]

    totales = {"total_recibos": sum(r['valor_total'] for r in reporte_recibos)}

    return {"recibos": reporte_recibos, "totales": totales}

def generate_auxiliar_proveedores_por_facturas_pdf(
    db: Session,
    empresa_id: int,
    tercero_id: int,
    fecha_inicio: date,
    fecha_fin: date
):
    report_data = generate_auxiliar_proveedores_por_facturas(db, empresa_id, tercero_id, fecha_inicio, fecha_fin)
    empresa = db.query(models_empresa).filter(models_empresa.id == empresa_id).first()
    tercero = db.query(models_tercero).filter(models_tercero.id == tercero_id).first()

    try:
        template_string = TEMPLATES_EMPAQUETADOS['reports/auxiliar_proveedores_por_facturas_report.html']
        template = GLOBAL_JINJA_ENV.from_string(template_string)
        html_string = template.render(
            reporte=report_data,
            empresa=empresa,
            tercero=tercero,
            fecha_inicio=fecha_inicio.strftime('%d/%m/%Y'),
            fecha_fin=fecha_fin.strftime('%d/%m/%Y')
        )
        return HTML(string=html_string).write_pdf()
    except KeyError:
        raise HTTPException(status_code=500, detail="La plantilla 'reports/auxiliar_proveedores_por_facturas_report.html' no fue encontrada en el paquete.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al generar el PDF de Auxiliar de Proveedores (Facturas): {e}")


def generate_auxiliar_proveedores_por_recibos_pdf(
    db: Session,
    empresa_id: int,
    tercero_id: int,
    fecha_inicio: date,
    fecha_fin: date
):
    report_data = generate_auxiliar_proveedores_por_recibos(db, empresa_id, tercero_id, fecha_inicio, fecha_fin)
    empresa = db.query(models_empresa).filter(models_empresa.id == empresa_id).first()
    tercero = db.query(models_tercero).filter(models_tercero.id == tercero_id).first()

    try:
        template_string = TEMPLATES_EMPAQUETADOS['reports/auxiliar_proveedores_por_recibos_report.html']
        template = GLOBAL_JINJA_ENV.from_string(template_string)
        html_string = template.render(
            reporte=report_data,
            empresa=empresa,
            tercero=tercero,
            fecha_inicio=fecha_inicio.strftime('%d/%m/%Y'),
            fecha_fin=fecha_fin.strftime('%d/%m/%Y')
        )
        return HTML(string=html_string).write_pdf()
    except KeyError:
        raise HTTPException(status_code=500, detail="La plantilla 'reports/auxiliar_proveedores_por_recibos_report.html' no fue encontrada en el paquete.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al generar el PDF de Auxiliar de Proveedores (Recibos): {e}")

def generate_estado_cuenta_cliente_report(
    db: Session,
    empresa_id: int,
    tercero_id: int,
    fecha_fin: date
) -> Dict[str, Any]:
    tercero_info = db.query(
        models_tercero.id,
        models_tercero.razon_social,
        models_tercero.nit
    ).filter(
        models_tercero.id == tercero_id,
        models_tercero.empresa_id == empresa_id
    ).first()

    if not tercero_info:
        raise HTTPException(status_code=404, detail="Cliente no encontrado.")

    cuentas_cxc_ids = _get_cuentas_especiales_ids(db, empresa_id, 'cxc')
    if not cuentas_cxc_ids:
        return { "clienteInfo": {}, "facturas": [], "saldoTotal": 0, "edades": {}, "fechaCorte": fecha_fin.isoformat() }

    sq_valor_original = db.query(
        models_doc.id.label("documento_id"),
        func.sum(models_mov.debito).label("valor_original")
    ).join(models_mov, models_doc.id == models_mov.documento_id)\
     .filter(
        models_doc.beneficiario_id == tercero_id, 
        models_doc.anulado == False,
        models_mov.cuenta_id.in_(cuentas_cxc_ids)
    ).group_by(models_doc.id).subquery()

    sq_abonos = db.query(
        models_aplica.documento_factura_id.label("documento_id"),
        func.sum(models_aplica.valor_aplicado).label("total_abonos")
    ).join(models_doc, models_aplica.documento_pago_id == models_doc.id)\
     .filter(models_doc.beneficiario_id == tercero_id, models_doc.anulado == False)\
     .group_by(models_aplica.documento_factura_id).subquery()

    facturas_con_saldo = db.query(
        models_doc.id,
        models_doc.fecha,
        models_doc.fecha_vencimiento,
        models_doc.numero,
        models_tipo.nombre.label("tipo_documento"),
        sq_valor_original.c.valor_original,
        func.coalesce(sq_abonos.c.total_abonos, 0).label("abonos")
    ).join(models_tipo, models_doc.tipo_documento_id == models_tipo.id)\
     .join(sq_valor_original, sq_valor_original.c.documento_id == models_doc.id)\
     .outerjoin(sq_abonos, sq_abonos.c.documento_id == models_doc.id)\
     .filter(
        models_doc.empresa_id == empresa_id,
        models_doc.beneficiario_id == tercero_id,
        models_doc.fecha <= fecha_fin,
        models_doc.anulado == False,
        models_tipo.funcion_especial == FuncionEspecial.CARTERA_CLIENTE,
        sq_valor_original.c.valor_original > func.coalesce(sq_abonos.c.total_abonos, 0)
    ).order_by(models_doc.fecha_vencimiento).all()

    reporte_facturas = []
    edades = {
        "por_vencer": 0, "vencida_1_30": 0, "vencida_31_60": 0,
        "vencida_61_90": 0, "vencida_mas_90": 0
    }
    saldo_total_cliente = 0

    for f in facturas_con_saldo:
        valor_original = float(f.valor_original or 0)
        abonos = float(f.abonos or 0)
        saldo_pendiente = valor_original - abonos
        saldo_total_cliente += saldo_pendiente

        dias_mora = 0
        dias_para_vencer = 0
        estado = "POR VENCER"

        if f.fecha_vencimiento and f.fecha_vencimiento < fecha_fin:
            dias_mora = (fecha_fin - f.fecha_vencimiento).days
            estado = "VENCIDA"
        elif f.fecha_vencimiento:
            dias_para_vencer = (f.fecha_vencimiento - fecha_fin).days

        if estado == "VENCIDA":
            if 1 <= dias_mora <= 30: edades["vencida_1_30"] += saldo_pendiente
            elif 31 <= dias_mora <= 60: edades["vencida_31_60"] += saldo_pendiente
            elif 61 <= dias_mora <= 90: edades["vencida_61_90"] += saldo_pendiente
            else: edades["vencida_mas_90"] += saldo_pendiente
        else:
            edades["por_vencer"] += saldo_pendiente

        reporte_facturas.append({
            "id": f.id,
            "tipo_documento": f.tipo_documento,
            "numero": f.numero,
            "fecha": f.fecha.isoformat(),
            "valor_original": valor_original,
            "abonos": abonos,
            "saldo_pendiente": saldo_pendiente,
            "dias_mora": dias_mora,
            "dias_para_vencer": dias_para_vencer,
            "estado": estado
        })

    return {
        "clienteInfo": {
            "id": tercero_info.id,
            "razon_social": tercero_info.razon_social,
            "nit": tercero_info.nit
        },
        "facturas": reporte_facturas,
        "saldoTotal": saldo_total_cliente,
        "edades": edades,
        "fechaCorte": fecha_fin.isoformat()
    }

def generate_estado_cuenta_cliente_report_pdf(
    db: Session,
    empresa_id: int,
    tercero_id: int,
    fecha_fin: date
):
    report_data = generate_estado_cuenta_cliente_report(db, empresa_id, tercero_id, fecha_fin)
    empresa_info = db.query(models_empresa).filter(models_empresa.id == empresa_id).first()

    try:
        template_string = TEMPLATES_EMPAQUETADOS['reports/estado_cuenta_cliente_report.html']
        template = GLOBAL_JINJA_ENV.from_string(template_string)
        html_string = template.render(
            reporte=report_data,
            empresa=empresa_info
        )
        return HTML(string=html_string).write_pdf()
    except KeyError:
        raise HTTPException(status_code=500, detail="La plantilla 'reports/estado_cuenta_cliente_report.html' no fue encontrada en el paquete.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al generar el PDF de Estado de Cuenta Cliente: {e}")

def generate_estado_cuenta_proveedor_report(
    db: Session,
    empresa_id: int,
    tercero_id: int,
    fecha_fin: date
) -> Dict[str, Any]:
    tercero_info = db.query(models_tercero).filter_by(id=tercero_id, empresa_id=empresa_id).first()
    if not tercero_info:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado.")

    cuentas_cxp_ids = _get_cuentas_especiales_ids(db, empresa_id, 'cxp')
    if not cuentas_cxp_ids:
        return { "proveedorInfo": {}, "facturas": [], "saldoTotal": 0, "edades": {}, "fechaCorte": fecha_fin.isoformat() }

    sq_valor_original = db.query(
        models_doc.id.label("documento_id"),
        func.sum(models_mov.credito).label("valor_original")
    ).join(models_mov, models_doc.id == models_mov.documento_id)\
     .filter(
        models_doc.beneficiario_id == tercero_id, 
        models_doc.anulado == False,
        models_mov.cuenta_id.in_(cuentas_cxp_ids)
    ).group_by(models_doc.id).subquery()

    sq_abonos = db.query(
        models_aplica.documento_factura_id.label("documento_id"),
        func.sum(models_aplica.valor_aplicado).label("total_abonos")
    ).join(models_doc, models_aplica.documento_pago_id == models_doc.id)\
     .filter(models_doc.beneficiario_id == tercero_id, models_doc.anulado == False)\
     .group_by(models_aplica.documento_factura_id).subquery()

    facturas_con_saldo = db.query(
        models_doc.id, models_doc.fecha, models_doc.fecha_vencimiento,
        models_doc.numero, models_tipo.nombre.label("tipo_documento"),
        sq_valor_original.c.valor_original,
        func.coalesce(sq_abonos.c.total_abonos, 0).label("abonos")
    ).join(models_tipo, models_doc.tipo_documento_id == models_tipo.id)\
     .join(sq_valor_original, sq_valor_original.c.documento_id == models_doc.id)\
     .outerjoin(sq_abonos, sq_abonos.c.documento_id == models_doc.id)\
     .filter(
        models_doc.empresa_id == empresa_id,
        models_doc.beneficiario_id == tercero_id,
        models_doc.fecha <= fecha_fin,
        models_doc.anulado == False,
        models_tipo.funcion_especial == FuncionEspecial.CXP_PROVEEDOR,
        sq_valor_original.c.valor_original > func.coalesce(sq_abonos.c.total_abonos, 0)
    ).order_by(models_doc.fecha_vencimiento).all()

    reporte_facturas = []
    edades = {
        "por_vencer": 0, "vencida_1_30": 0, "vencida_31_60": 0,
        "vencida_61_90": 0, "vencida_mas_90": 0
    }
    saldo_total_proveedor = 0

    for f in facturas_con_saldo:
        valor_original = float(f.valor_original or 0)
        abonos = float(f.abonos or 0)
        saldo_pendiente = valor_original - abonos
        saldo_total_proveedor += saldo_pendiente

        dias_mora = 0
        dias_para_vencer = 0
        estado = "POR VENCER"

        if f.fecha_vencimiento and f.fecha_vencimiento < fecha_fin:
            dias_mora = (fecha_fin - f.fecha_vencimiento).days
            estado = "VENCIDA"
        elif f.fecha_vencimiento:
            dias_para_vencer = (f.fecha_vencimiento - fecha_fin).days

        if estado == "VENCIDA":
            if 1 <= dias_mora <= 30: edades["vencida_1_30"] += saldo_pendiente
            elif 31 <= dias_mora <= 60: edades["vencida_31_60"] += saldo_pendiente
            elif 61 <= dias_mora <= 90: edades["vencida_61_90"] += saldo_pendiente
            else: edades["vencida_mas_90"] += saldo_pendiente
        else:
            edades["por_vencer"] += saldo_pendiente

        reporte_facturas.append({
            "id": f.id, "tipo_documento": f.tipo_documento,
            "numero": f.numero, "fecha": f.fecha.isoformat(),
            "valor_original": valor_original, "abonos": abonos,
            "saldo_pendiente": saldo_pendiente, "dias_mora": dias_mora,
            "dias_para_vencer": dias_para_vencer, "estado": estado
        })

    return {
        "proveedorInfo": { "id": tercero_info.id, "razon_social": tercero_info.razon_social, "nit": tercero_info.nit },
        "facturas": reporte_facturas,
        "saldoTotal": saldo_total_proveedor,
        "edades": edades,
        "fechaCorte": fecha_fin.isoformat()
    }

def generate_estado_cuenta_proveedor_report_pdf(
    db: Session,
    empresa_id: int,
    tercero_id: int,
    fecha_fin: date
):
    report_data = generate_estado_cuenta_proveedor_report(db, empresa_id, tercero_id, fecha_fin)
    empresa_info = db.query(models_empresa).filter(models_empresa.id == empresa_id).first()

    try:
        template_string = TEMPLATES_EMPAQUETADOS['reports/estado_cuenta_proveedor_report.html']
        template = GLOBAL_JINJA_ENV.from_string(template_string)
        html_string = template.render(
            reporte=report_data,
            empresa=empresa_info
        )
        return HTML(string=html_string).write_pdf()
    except KeyError:
        raise HTTPException(status_code=500, detail="La plantilla 'reports/estado_cuenta_proveedor_report.html' no fue encontrada en el paquete.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al generar el PDF de Estado de Cuenta Proveedor: {e}")


def get_documentos_anulados_para_gestion(db: Session, empresa_id: int) -> List[Dict[str, Any]]:
    subquery_total = db.query(
        models_mov.documento_id,
        func.sum(models_mov.debito).label("total")
    ).group_by(models_mov.documento_id).subquery()

    query = db.query(
        models_doc.id,
        models_doc.fecha,
        models_tipo.nombre.label("tipo_documento"),
        models_doc.numero,
        models_tercero.razon_social.label("beneficiario"),
        subquery_total.c.total
    ).join(subquery_total, models_doc.id == subquery_total.c.documento_id) \
     .join(models_tipo, models_doc.tipo_documento_id == models_tipo.id) \
     .outerjoin(models_tercero, models_doc.beneficiario_id == models_tercero.id) \
     .filter(
        models_doc.empresa_id == empresa_id,
        models_doc.anulado == True
    ).order_by(models_doc.fecha.desc(), models_doc.numero.desc())

    resultados = query.limit(500).all()

    return [
        {
            "id": r.id,
            "fecha": r.fecha,
            "tipo_documento": r.tipo_documento,
            "numero": r.numero,
            "beneficiario": r.beneficiario,
            "total": float(r.total or 0)
        }
        for r in resultados
    ]

def get_documentos_papelera(db: Session, empresa_id: int) -> List[Dict[str, Any]]:
    subquery_valor = db.query(
        models_mov_elim.documento_eliminado_id,
        func.sum(models_mov_elim.debito).label("valor_documento")
    ).group_by(models_mov_elim.documento_eliminado_id).subquery()

    query = db.query(
        models_doc_elim.id,
        models_doc_elim.id_original,
        models_doc_elim.numero,
        models_doc_elim.fecha,
        models_doc_elim.fecha_eliminacion,
        models_usuario.email.label("usuario_eliminacion"),
        models_tipo.nombre.label("tipo_documento_nombre"),
        func.coalesce(subquery_valor.c.valor_documento, 0).label("valor_documento")
    ).select_from(models_doc_elim) \
    .outerjoin(subquery_valor, models_doc_elim.id == subquery_valor.c.documento_eliminado_id) \
    .join(models_tipo, models_doc_elim.tipo_documento_id == models_tipo.id) \
    .outerjoin(models_usuario, models_doc_elim.usuario_eliminacion_id == models_usuario.id) \
    .filter(models_doc_elim.empresa_id == empresa_id) \
    .order_by(models_doc_elim.fecha_eliminacion.desc())

    resultados = query.all()
    return resultados

    from app.core.security import create_print_token
from app.core.config import settings

def generar_url_firmada_impresion(db: Session, documento_id: int, empresa_id: int) -> str:

    print("--- SONDA 2: Entrando a la función de servicio ---") # <--- AÑADIR ESTA LÍNEA
    """
    Verifica la existencia de un documento y genera una URL firmada y
    temporal para su impresión.
    """
    # Verificación de seguridad: Asegurarnos de que el documento existe y pertenece a la empresa.
    db_documento = db.query(models_doc.id).filter(
        models_doc.id == documento_id,
        models_doc.empresa_id == empresa_id
    ).first()

    if not db_documento:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Documento no encontrado o no pertenece a la empresa."
        )

    # Creamos el token de corta duración para este documento específico.
    token = create_print_token(documento_id=documento_id, empresa_id=empresa_id)

    # Construimos la URL completa que el frontend abrirá.
    # Usamos la nueva ruta pública que crearemos en el siguiente paso.
    signed_url = f"{settings.BASE_URL}/api/documentos/imprimir-firmado?token={token}"
    
    return signed_url

# --- INICIO: NUEVA FUNCIÓN ENRIQUECIDA CON RENTABILIDAD ---
def get_detalle_comercial_por_documento(db: Session, documento_id: int, empresa_id: int) -> List[schemas_doc.DetalleProductoVendido]:
    """
    Obtiene el detalle comercial (productos, cantidades, precios, costos y rentabilidad) 
    de un documento de venta.
    """
    
    query_items = (
        db.query(
            models_producto.id.label("producto_id"),
            models_producto.nombre.label("nombre_producto"),
            func.sum(models_mov_inv.cantidad).label("cantidad"), # Ojo: MovimientoInventario no esta importado como alias?
            func.sum(models_mov.credito).label("venta_total_linea"),
            # --- CAMBIO CLAVE: Añadimos el costo unitario a la consulta ---
            func.avg(models_mov_inv.costo_unitario).label("costo_unitario")
        )
        .join(models_doc, models_mov_inv.documento_id == models_doc.id)
        .join(models_producto, models_mov_inv.producto_id == models_producto.id)
        .join(models_grupo, models_producto.grupo_id == models_grupo.id)
        .join(models_mov, and_(
            models_mov.documento_id == models_doc.id,
            models_mov.cuenta_id == models_grupo.cuenta_ingreso_id,
            models_mov.producto_id == models_producto.id,
            models_mov.credito > 0
        ))
        .where(
            models_doc.empresa_id == empresa_id,
            models_doc.id == documento_id,
            models_mov_inv.tipo_movimiento == 'SALIDA_VENTA',
            models_doc.anulado == False
        )
        .group_by(
            models_producto.id,
            models_producto.nombre
        )
    )

    resultados_db = query_items.all()
    
    detalles_finales = []
    for r in resultados_db:
        # --- LÓGICA DE CÁLCULO AMPLIADA ---
        venta_total_float = float(r.venta_total_linea)
        cantidad_float = float(r.cantidad)
        costo_unitario_float = float(r.costo_unitario or 0) # Aseguramos que no sea None

        precio_unitario = (venta_total_float / cantidad_float) if cantidad_float != 0 else 0
        costo_total = cantidad_float * costo_unitario_float
        utilidad_bruta = venta_total_float - costo_total
        margen_rentabilidad = (utilidad_bruta / venta_total_float) if venta_total_float != 0 else 0

        detalles_finales.append(
            schemas_doc.DetalleProductoVendido(
                producto_id=r.producto_id,
                nombre_producto=r.nombre_producto,
                cantidad=cantidad_float,
                vrUnitario=precio_unitario,
                totalLinea=venta_total_float,
                # Pasamos los nuevos valores a nuestro schema enriquecido
                costoUnitario=costo_unitario_float,
                costoTotal=costo_total,
                utilidadBruta=utilidad_bruta,
                margenRentabilidad=margen_rentabilidad
            )
        )
        
    return detalles_finales
# --- FIN: NUEVA FUNCIÓN ENRIQUECIDA ---

# --- INICIO: NUEVA FUNCIÓN PARA GENERAR PDF DE RENTABILIDAD ---
def generar_pdf_rentabilidad_factura(db: Session, documento_id: int, empresa_id: int):
    """
    Genera el PDF del análisis de rentabilidad para una única factura.
    """
    # 1. Obtener el documento con todas sus relaciones cargadas.
    db_documento = get_documento_by_id(db, documento_id=documento_id, empresa_id=empresa_id)
    if not db_documento:
        raise HTTPException(status_code=404, detail="Documento no encontrado.")

    # 2. Reutilizamos nuestro servicio para obtener el detalle comercial enriquecido.
    detalle_productos = get_detalle_comercial_por_documento(db, documento_id, empresa_id)

    # 3. Calculamos los totales para el pie de página del reporte.
    total_venta = sum(item.total_linea for item in detalle_productos)
    total_costo = sum(item.costo_total for item in detalle_productos)
    total_utilidad = total_venta - total_costo
    margen_total = (total_utilidad / total_venta) if total_venta != 0 else 0

    totales = {
        "venta": total_venta,
        "costo": total_costo,
        "utilidad": total_utilidad,
        "margen": margen_total
    }

    # 4. Obtenemos la información de la empresa.
    empresa = db.query(models_empresa).filter(models_empresa.id == empresa_id).first()

    # 5. Preparamos el contexto completo para la plantilla Jinja2.
    context = {
        "empresa": empresa,
        "doc": db_documento,
        "detalle_productos": detalle_productos,
        "totales": totales
    }

    # 6. Renderizamos el HTML desde la plantilla empaquetada y generamos el PDF.
    try:
        template_string = TEMPLATES_EMPAQUETADOS['reports/rentabilidad_factura_report.html']
        template = GLOBAL_JINJA_ENV.from_string(template_string)
        rendered_html = template.render(context)
        return HTML(string=rendered_html).write_pdf()
    except KeyError:
        raise HTTPException(status_code=500, detail="La plantilla 'reports/rentabilidad_factura_report.html' no fue encontrada en el paquete.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al generar el PDF de rentabilidad: {e}")
# --- FIN: NUEVA FUNCIÓN PARA GENERAR PDF DE RENTABILIDAD ---

# --- INICIO: NUEVA FUNCIÓN PARA URL FIRMADA DE RENTABILIDAD ---
# --- INICIO: NUEVA FUNCIÓN PARA URL FIRMADA DE RENTABILIDAD (VERSIÓN CORREGIDA) ---
def generar_url_firmada_rentabilidad(db: Session, documento_id: int, empresa_id: int) -> str:
    """
    Verifica la existencia de un documento y genera una URL firmada y
    temporal para su reporte de rentabilidad.
    """
    # Verificación de seguridad
    db_documento = db.query(models_doc.id).filter(
        models_doc.id == documento_id,
        models_doc.empresa_id == empresa_id
    ).first()
    if not db_documento:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Documento no encontrado o no pertenece a la empresa."
        )

    # Creamos el token de corta duración
    token = create_print_token(documento_id=documento_id, empresa_id=empresa_id)
    
    # --- LA CORRECCIÓN CLAVE ---
    # Ahora construimos la URL absoluta, apuntando directamente al servidor del backend.
    signed_url = f"{settings.BASE_URL}/api/documentos/imprimir-rentabilidad-firmado?token={token}"
    
    return signed_url
# --- FIN: NUEVA FUNCIÓN PARA URL FIRMADA ---

# --- INICIO: NUEVAS FUNCIONES PARA BALANCE GENERAL ---

def generate_balance_sheet_report(
    db: Session, 
    empresa_id: int, 
    fecha_corte: date
) -> Dict[str, Any]:
    """
    Calcula los saldos de las cuentas de balance (Activo, Pasivo, Patrimonio)
    y la utilidad del ejercicio a una fecha de corte para el reporte en pantalla.
    Esta es la función que faltaba y que la ruta estaba intentando llamar.
    """
    saldos_query = db.query(
        models_plan.codigo,
        models_plan.nombre,
        func.sum(models_mov.debito - models_mov.credito).label('saldo')
    ).join(models_mov, models_plan.id == models_mov.cuenta_id)\
     .join(models_doc, models_mov.documento_id == models_doc.id)\
     .filter(
        models_doc.empresa_id == empresa_id,
        models_doc.fecha <= fecha_corte,
        models_doc.anulado == False,
        or_(
            models_plan.codigo.startswith('1'), # Activos
            models_plan.codigo.startswith('2'), # Pasivos
            models_plan.codigo.startswith('3'), # Patrimonio
            models_plan.codigo.startswith('4'), # Ingresos
            models_plan.codigo.startswith('5'), # Gastos
            models_plan.codigo.startswith('6'), # Costos de Venta
        )
     ).group_by(models_plan.codigo, models_plan.nombre).all()

    activos, pasivos, patrimonio = [], [], []
    total_ingresos, total_costos, total_gastos = 0.0, 0.0, 0.0

    for cuenta in saldos_query:
        saldo = float(cuenta.saldo or 0.0)
        if cuenta.codigo.startswith('1'):
            activos.append({'codigo': cuenta.codigo, 'nombre': cuenta.nombre, 'saldo': saldo})
        elif cuenta.codigo.startswith('2'):
            pasivos.append({'codigo': cuenta.codigo, 'nombre': cuenta.nombre, 'saldo': -saldo}) # Pasivo es naturaleza crédito
        elif cuenta.codigo.startswith('3'):
            patrimonio.append({'codigo': cuenta.codigo, 'nombre': cuenta.nombre, 'saldo': -saldo}) # Patrimonio es naturaleza crédito
        elif cuenta.codigo.startswith('4'):
            total_ingresos += -saldo # Ingreso es naturaleza crédito
        elif cuenta.codigo.startswith('5'):
            total_gastos += saldo
        elif cuenta.codigo.startswith('6'):
            total_costos += saldo
            
    utilidad_ejercicio = total_ingresos - total_costos - total_gastos

    total_activos = sum(c['saldo'] for c in activos)
    total_pasivos = sum(c['saldo'] for c in pasivos)
    total_patrimonio = sum(c['saldo'] for c in patrimonio) + utilidad_ejercicio
    
    return {
        "activos": sorted(activos, key=lambda x: x['codigo']),
        "pasivos": sorted(pasivos, key=lambda x: x['codigo']),
        "patrimonio": sorted(patrimonio, key=lambda x: x['codigo']),
        "total_activos": total_activos,
        "total_pasivos": total_pasivos,
        "total_patrimonio": total_patrimonio,
        "utilidad_ejercicio": utilidad_ejercicio,
        "total_pasivo_patrimonio": total_pasivos + total_patrimonio,
    }

def generate_balance_sheet_report_pdf(
    db: Session, 
    empresa_id: int, 
    fecha_corte: date
):
    """
    Genera el archivo PDF para el reporte de Balance General.
    """
    # 1. Reutilizamos la función que acabamos de crear para obtener los datos.
    report_data = generate_balance_sheet_report(db, empresa_id, fecha_corte)
    
    # 2. Obtenemos la información de la empresa.
    empresa_info = db.query(models_empresa).filter(models_empresa.id == empresa_id).first()
    if not empresa_info:
        raise HTTPException(status_code=404, detail=f"No se encontró la empresa con ID {empresa_id}")

    # 3. Preparamos el contexto para la plantilla, cumpliendo el contrato.
    context = {
        "empresa": empresa_info,
        "fecha_corte": fecha_corte,
        "reporte": report_data
    }
    
    # 4. Renderizamos el PDF.
    try:
        template_string = TEMPLATES_EMPAQUETADOS['reports/balance_general_report.html']
        template = GLOBAL_JINJA_ENV.from_string(template_string)
        rendered_html = template.render(context)
        return HTML(string=rendered_html).write_pdf()
    except KeyError:
        raise HTTPException(status_code=500, detail="La plantilla 'reports/balance_general_report.html' no fue encontrada.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al renderizar el PDF del Balance General: {e}")

# --- FIN: NUEVAS FUNCIONES PARA BALANCE GENERAL ---

