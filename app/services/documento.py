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
# --- SISTEMA DE CONSUMO ---
from app.services import consumo_service
from app.services.consumo_service import SaldoInsuficienteException
# ---------------------------



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
        
        # --- BLINDAJE AUDITORIA/CLON ---
        if empresa_info.modo_operacion == 'AUDITORIA_READONLY':
             raise HTTPException(
                status_code=403, 
                detail="🚫 Operación restringida: Esta empresa está en modo AUDITORÍA/CLON y no permite asentar nuevos documentos directamente. Use la importación masiva."
            )
        # -------------------------------
        

        # ==============================================================================
        # 3. SISTEMA DE CONSUMO DE REGISTROS (NUEVO MOTOR)
        # ==============================================================================
        
        cantidad_registros_consumo = len(documento.movimientos)
        
        # Validación de "Simulación" rápida antes de iniciar todo el proceso pesado
        # Esto mejora la UX al fallar rápido, aunque la validación real estricta será al final.
        if not consumo_service.verificar_disponibilidad(db, documento.empresa_id, cantidad_registros_consumo):
             raise HTTPException(status_code=409, detail="⛔ Saldo insuficiente (Validación preliminar). Verifique su Plan o Bolsa.")

        # ==============================================================================

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
            
        # --- REGISTRO DE CONSUMO (Post-Flush) ---
        # Ahora que tenemos el ID del documento, registramos el consumo.
        # Si esto falla (SaldoInsuficiente), la excepción subirá y hará rollback de todo
        # (si estamos en 'commit=True', el rollback lo captura el except general abajo).
        try:
            consumo_service.registrar_consumo(
                db=db,
                empresa_id=db_documento.empresa_id,
                cantidad=len(db_documento.movimientos),
                documento_id=db_documento.id,
                fecha_doc=db_documento.fecha
            )
            # Si ya habíamos hecho commit arriba (commit=True), necesitamos OTRO commit para el historial?
            # SÍ. registrar_consumo añade objetos a la sesión pero no hace commit por defecto.
            if commit:
                db.commit()
        except SaldoInsuficienteException as e:
            # Si falla consumo, debemos deshacer el documento creado
            # Si commit=True, ya se commiteó el documento. Tocaría borrarlo manualmente?
            # O mejor hacemos el flush primero, registramos consumo, y LUEGO el commit final.
            raise HTTPException(status_code=409, detail=f"⛔ {str(e)}")
        
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
        
        # --- REVERSIÓN DE CONSUMO ---
        # "Todo documento anulado devuelve sus registros al plan (o fuente)"
        consumo_service.revertir_consumo(db, db_documento.id)
        # ----------------------------

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

        # --- FIX: REVERSIÓN DE CONSUMO ANTICIPADA ---
        # 1. Revertimos el consumo para devolver el cupo al usuario.
        consumo_service.revertir_consumo(db, documento_id)
        db.flush() # <--- IMPORTANTE: Persistir el log de reversión para que el update lo vea

        # 2. Desvinculamos el historial (Original + Reversión) para romper la FK
        #    y permitir la eliminación física del documento sin violar integridad.
        from app.models.consumo_registros import HistorialConsumo
        db.query(HistorialConsumo).filter(
            HistorialConsumo.documento_id == documento_id
        ).update({HistorialConsumo.documento_id: None}, synchronize_session=False)
        db.flush()
        # --------------------------------------------

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

        # A. PREPARAR RECÁLCULO (Capturar IDs antes de borrar)
        # Esto es vital porque una vez borrados los movimientos, perdemos el rastro de qué productos cambiaron.
        productos_afectados_ids = [
            r.producto_id for r in db.query(models_mov_inv.producto_id)
            .filter(models_mov_inv.documento_id == documento_id)
            .distinct().all()
        ]

        # A. Eliminar Movimientos de Inventario (Si existen)
        db.query(models_mov_inv).filter(models_mov_inv.documento_id == documento_id).delete(synchronize_session=False)

        # C. Eliminar Movimientos Contables
        db.query(models_mov).filter(models_mov.documento_id == documento_id).delete(synchronize_session=False)
        
        # D. Finalmente, Eliminar el Documento
        db.delete(db_documento)

        # E. RECALCULAR SALDOS (Integridad de Inventario)
        # Importamos aquí para evitar Circular Import (documento <-> inventario)
        if productos_afectados_ids:
            from app.services.inventario import recalcular_saldos_producto
            print(f"[ELIMINACION MASIVA] Recalculando inventario para {len(productos_afectados_ids)} productos afectados...")
            for pid in productos_afectados_ids:
                recalcular_saldos_producto(db, pid)
        
        # F. REVERSIÓN DE CONSUMO (Movido al inicio - Deprecado aquí)
        # La reversión ya se ejecutó al principio para evitar FK constraints.
        # ----------------------------------
        
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
    print(f"--- DEBUG PDF: Buscando plantilla para Documento {documento_id} --")
    print(f"   -> Empresa ID: {empresa_id}")
    print(f"   -> Tipo Documento ID: {db_doc.tipo_documento_id}")

    plantilla = db.query(models_formato).filter(
        models_formato.empresa_id == empresa_id, 
        models_formato.tipo_documento_id == db_doc.tipo_documento_id
    ).first()
    
    if plantilla:
        print(f"   -> PLANTILLA ENCONTRADA: ID {plantilla.id} - {plantilla.nombre}")
        html_content = plantilla.contenido_html
    else:
        print("   -> PLANTILLA BD NO ENCONTRADA. Buscando en paquete local...")
        
        # Intentamos buscar por código de tipo de documento
        # Ej: "CE" -> "reports/ce_template.html" (convención)
        # O también "reports/comprobante_egreso_template.html" (nombre largo)
        
        tipo_codigo = db_doc.tipo_documento.codigo.lower() if db_doc.tipo_documento else "unknown"
        # Mapeo manual de códigos comunes a plantillas conocidas
        # Mapeo manual de códigos comunes a plantillas conocidas
        mapa_plantillas = {
            'ce': 'reports/comprobante_egreso_template.html',
            'rc': 'reports/auxiliar_por_recibos_report.html',
            # 'fv': 'reports/rentabilidad_factura_report.html' # <--- CAUSANTE DEL ERROR (Usaba 'doc' en vez de 'documento')
            'fv': 'reports/invoice_template.html',  # FIXED: Nueva plantilla moderna
        }
        
        plantilla_key = mapa_plantillas.get(tipo_codigo)
        
        # FIX: Prioridad de carga para la nueva plantilla de factura
        if tipo_codigo == 'fv' or (plantilla_key and 'invoice_template.html' in plantilla_key):
             try:
                 print(f"   -> USANDO PLANTILLA FACTURA MODERNA: app/templates/reports/invoice_template.html")
                 with open('app/templates/reports/invoice_template.html', 'r', encoding='utf-8') as f:
                     html_content = f.read()
             except Exception as e:
                 print(f"Error cargando plantilla factura: {e}")
                 html_content = "Error loading invoice template"

        elif plantilla_key and plantilla_key in TEMPLATES_EMPAQUETADOS:
             print(f"   -> PLANTILLA LOCAL ENCONTRADA: {plantilla_key}")
             html_content = TEMPLATES_EMPAQUETADOS[plantilla_key]
        else:
             print("   -> NO SE ENCONTRO NINGUNA PLANTILLA ESPECÍFICA. Usando plantila GENÉRICA de base.")
             # Usamos la plantilla genérica nueva
             try:
                 with open('app/templates/reports/generic_document_template.html', 'r', encoding='utf-8') as f:
                     html_content = f.read()
             except Exception as e:
                 print(f"Error cargando plantilla genérica: {e}")
                 html_content = "<html><body><h1>Error de Plantilla</h1><p>No se encontró la plantilla genérica base.</p></body></html>"
    
    # 3. Empresa
    empresa = db.query(models_empresa).filter(models_empresa.id == empresa_id).first()
    
    # 4. LÓGICA
    items_facturables = []
    subtotal_acumulado = 0
    impuestos_acumulados = 0
    
    # Acumuladores para bases gravables
    base_exenta = 0
    base_gravable_5 = 0
    base_gravable_19 = 0
    iva_5_total = 0
    iva_19_total = 0
    
    # Acumuladores Contables
    suma_debito_total = 0
    suma_credito_total = 0
    
    # --- DETECCIÓN DEL MODO ---
    modo_operacion = 'GENERAL' 
    func_especial = db_doc.tipo_documento.funcion_especial
    
    funcs_venta = ['FACTURA_VENTA', 'cartera_cliente']
    funcs_compra = ['FACTURA_COMPRA', 'cxp_proveedor', 'compras'] # Removed 'pago_proveedor' to allow CE to use GENERAL mode
    
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
    
    # Acumuladores para bases gravables
    base_exenta = 0
    base_gravable_5 = 0
    base_gravable_19 = 0
    iva_5_total = 0
    iva_19_total = 0
    
    if modo_operacion == 'VENTA':
        # RUTA A: VENTA - Incluir información de impuestos
        query_comercial = db.query(
            models_producto.codigo.label("codigo"),
            models_producto.nombre.label("nombre"),
            models_mov_inv.cantidad.label("cantidad_real"),
            models_mov.credito.label("valor_total"),
            models_producto.impuesto_iva_id.label("impuesto_iva_id")
        ).join(models_doc, models_mov_inv.documento_id == models_doc.id)\
         .join(models_producto, models_mov_inv.producto_id == models_producto.id)\
         .join(models_grupo, models_producto.grupo_id == models_grupo.id)\
         .join(models_mov, and_(
             models_mov.documento_id == models_doc.id,
             models_mov.cuenta_id == models_grupo.cuenta_ingreso_id, 
             models_mov.producto_id == models_producto.id
         ))\
         .filter(models_doc.id == documento_id, models_mov_inv.tipo_movimiento == 'SALIDA_VENTA').all()

        if query_comercial:
            # Obtener tasas de impuesto para calcular bases
            tasas_impuesto = {}
            impuesto_ids = [item.impuesto_iva_id for item in query_comercial if item.impuesto_iva_id]
            if impuesto_ids:
                from app.models.impuesto import TasaImpuesto
                tasas_db = db.query(TasaImpuesto).filter(TasaImpuesto.id.in_(impuesto_ids)).all()
                tasas_impuesto = {tasa.id: tasa.tasa for tasa in tasas_db}
            
            for item in query_comercial:
                cant = float(item.cantidad_real)
                val = float(item.valor_total)
                unit = val / cant if cant > 0 else 0
                
                # Obtener tasa de IVA del producto
                tasa_iva = 0
                if item.impuesto_iva_id and item.impuesto_iva_id in tasas_impuesto:
                    tasa_iva = tasas_impuesto[item.impuesto_iva_id]
                
                # Calcular base gravable (El valor en la cuenta de ingreso 4xxx ES la base)
                base_gravable = val 
                valor_iva = base_gravable * tasa_iva
                
                # Acumular por tipo de base
                if tasa_iva == 0:
                    base_exenta += base_gravable
                elif abs(tasa_iva - 0.05) < 0.001:  # 5%
                    base_gravable_5 += base_gravable
                    iva_5_total += valor_iva
                elif abs(tasa_iva - 0.19) < 0.001:  # 19%
                    base_gravable_19 += base_gravable
                    iva_19_total += valor_iva
                
                items_facturables.append({
                    "producto_codigo": item.codigo, 
                    "producto_nombre": item.nombre,
                    "cantidad": f"{cant:,.2f}", 
                    "precio_unitario": f"{unit:,.0f}", 
                    "subtotal": f"{val:,.0f}",
                    "debito_fmt": "0", 
                    "credito_fmt": f"{val:,.0f}",
                    "tasa_iva": tasa_iva,
                    "base_gravable": base_gravable,
                    "valor_iva": valor_iva
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
            models_producto.codigo.label("codigo"),
            models_producto.nombre.label("nombre"),
            models_mov_inv.cantidad.label("cantidad"),
            models_mov_inv.costo_unitario.label("costo_u"),
            models_mov_inv.costo_total.label("costo_t"),
            models_producto.impuesto_iva_id.label("impuesto_iva_id") # AGREGADO PARA IMPUESTOS
        ).join(models_producto, models_mov_inv.producto_id == models_producto.id)\
         .filter(
             models_mov_inv.documento_id == documento_id,
             # Aceptamos cualquier entrada (Compra, Ajuste, Inicial) para ser flexibles
             models_mov_inv.tipo_movimiento.like('ENTRADA%')
         ).all()

        if query_kardex:
            # Obtener tasas de impuesto para calcular bases (Igual que en VENTA)
            tasas_impuesto = {}
            impuesto_ids = [item.impuesto_iva_id for item in query_kardex if item.impuesto_iva_id]
            if impuesto_ids:
                from app.models.impuesto import TasaImpuesto
                tasas_db = db.query(TasaImpuesto).filter(TasaImpuesto.id.in_(impuesto_ids)).all()
                tasas_impuesto = {tasa.id: tasa.tasa for tasa in tasas_db}

            for item in query_kardex:
                cant = float(item.cantidad)
                unit = float(item.costo_u) # El costo unitario real de compra (BASE)
                val = float(item.costo_t)  # El total de la línea (BASE TOTAL)
                
                # Obtener tasa de IVA del producto
                tasa_iva = 0
                if item.impuesto_iva_id and item.impuesto_iva_id in tasas_impuesto:
                    tasa_iva = tasas_impuesto[item.impuesto_iva_id]

                # En compras, el costo registrado en el inventario suele ser la BASE (sin IVA)
                # El IVA descontable se registra aparte en la cuenta 24.
                # Aquí recalculamos el IVA teórico basado en el producto para mostrarlo.
                base_gravable = val 
                valor_iva = base_gravable * tasa_iva
                
                # Acumular por tipo de base
                if tasa_iva == 0:
                    base_exenta += base_gravable
                elif abs(tasa_iva - 0.05) < 0.001:  # 5%
                    base_gravable_5 += base_gravable
                    iva_5_total += valor_iva
                elif abs(tasa_iva - 0.19) < 0.001:  # 19%
                    base_gravable_19 += base_gravable
                    iva_19_total += valor_iva

                items_facturables.append({
                    "producto_codigo": item.codigo, 
                    "producto_nombre": item.nombre,
                    "cantidad": f"{cant:,.2f}", # Cantidad Real
                    "precio_unitario": f"$ {unit:,.0f}", # Costo Unitario Real
                    "subtotal": f"$ {val:,.0f}",
                    "debito_fmt": f"$ {val:,.0f}", 
                    "credito_fmt": "0",
                    "tasa_iva": tasa_iva,
                    "base_gravable": base_gravable,
                    "valor_iva": valor_iva
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

    # Calcular totales de IVA para el contexto
    total_iva_calculado = iva_5_total + iva_19_total
    
    # 5. Contexto
    beneficiario = db_doc.beneficiario
    context = {
        "empresa": {
            "razon_social": getattr(empresa, 'razon_social', 'Empresa') or "Empresa",
            "nit": getattr(empresa, 'nit', '') or "",
            "direccion": getattr(empresa, 'direccion', "") or "",
            "telefono": getattr(empresa, 'telefono', "") or "",
            "email": getattr(empresa, 'email', "") or "",
            "logo_url": getattr(empresa, 'logo_url', "") or ""
        },
        "documento": {
            "tipo_nombre": db_doc.tipo_documento.nombre.upper() if db_doc.tipo_documento else "DOCUMENTO",
            "consecutivo": db_doc.numero,
            "fecha_emision": db_doc.fecha.strftime('%d/%m/%Y'),
            "fecha_vencimiento": db_doc.fecha_vencimiento.strftime('%d/%m/%Y') if getattr(db_doc, 'fecha_vencimiento', None) else "",
            "observaciones": getattr(db_doc, 'observaciones', "") or ""
        },
        "tercero": {
            "razon_social": getattr(beneficiario, 'razon_social', "Varios") if beneficiario else "Varios",
            "nit": getattr(beneficiario, 'nit', "") if beneficiario else "",
            "direccion": getattr(beneficiario, 'direccion', "") if beneficiario else "",
            "telefono": getattr(beneficiario, 'telefono', "") if beneficiario else ""
        },
        "items": items_facturables,
        "totales": {
            "subtotal": f"{subtotal_acumulado:,.0f}",
            "base_exenta": f"{base_exenta:,.0f}" if base_exenta > 0 else "0.00",
            "base_gravable_5": f"{base_gravable_5:,.0f}" if base_gravable_5 > 0 else "0.00",
            "base_gravable_19": f"{base_gravable_19:,.0f}" if base_gravable_19 > 0 else "0.00",
            "iva_5": f"{iva_5_total:,.0f}" if iva_5_total > 0 else "0.00",
            "iva_19": f"{iva_19_total:,.0f}" if iva_19_total > 0 else "0.00",
            "impuestos": f"{total_iva_calculado:,.0f}" if modo_operacion == 'VENTA' else f"{impuestos_acumulados:,.0f}",
            "total": f"{total_redondeado:,.0f}",
            "total_debito": f"{suma_debito_total:,.0f}",
            "total_credito": f"{suma_credito_total:,.0f}",
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
    # --- MEJORA: LÓGICA DE NATURALEZA DE CUENTA ---
    # Determinamos si la cuenta es de naturaleza CRÉDITO para invertir el signo visualmente.
    # 1 (Activo), 5 (Gastos), 6 (Costos), 8 (Debe) -> Naturaleza DÉBITO (+).
    # 2 (Pasivo), 3 (Patrimonio), 4 (Ingresos), 7 (Costos Prod), 9 (Haber) -> Naturaleza CRÉDITO (-).
    first_digit = cuenta_info.codigo[0]
    is_credit_nature = first_digit in ['2', '3', '4', '7', '9']
    nature_factor = -1 if is_credit_nature else 1

    # Calculamos el saldo neto matemático (Débito - Crédito)
    saldo_anterior_neto = (saldo_anterior_result.total_debito or 0) - \
                     (saldo_anterior_result.total_credito or 0)
    
    # Aplicamos el factor para el saldo inicial visual
    saldo_anterior = saldo_anterior_neto * nature_factor

    movimientos_query = db.query(
        models_doc.fecha,
        models_tipo.nombre.label("tipo_documento"),
        models_doc.numero.label("numero_documento"),
        models_tercero.razon_social.label("beneficiario"),
        models_tercero.nit.label("beneficiario_nit"),
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

    current_running_balance_display = float(saldo_anterior)
    formatted_movimientos = []
    
    total_debito_periodo = 0.0
    total_credito_periodo = 0.0

    for mov in movimientos_data:
        debito = float(mov.debito)
        credito = float(mov.credito)
        
        total_debito_periodo += debito
        total_credito_periodo += credito

        # Movimiento Neto = Débito - Crédito
        # Si es naturaleza Crédito (-1):
        #   Un Crédito (aumento de deuda) es neto negativo. Al multiplicar por -1 se vuelve positivo (suma al saldo).
        #   Un Débito (pago de deuda) es neto positivo. Al multiplicar por -1 se vuelve negativo (resta al saldo).
        net_impact = (debito - credito) * nature_factor
        
        current_running_balance_display += net_impact
        
        formatted_movimientos.append({
            "fecha": mov.fecha, 
            "tipo_documento": mov.tipo_documento,
            "numero_documento": mov.numero_documento,
            "beneficiario": mov.beneficiario,
            "beneficiario_nit": mov.beneficiario_nit or "N/A",
            "concepto": mov.concepto,
            "debito": debito,
            "credito": credito,
            "centro_costo_codigo": mov.centro_costo_codigo,
            "centro_costo_nombre": mov.centro_costo_nombre,
            "saldo_parcial": current_running_balance_display
        })

    return {
        "cuenta_info": {
            "id": cuenta_info.id,
            "codigo": cuenta_info.codigo,
            "nombre": cuenta_info.nombre
        },
        "saldoAnterior": float(saldo_anterior),
        "totalDebitoPeriodo": total_debito_periodo, # Nuevo
        "totalCreditoPeriodo": total_credito_periodo, # Nuevo
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
    
    # Extraemos los totales
    total_debito_periodo = report_data.get('totalDebitoPeriodo', 0)
    total_credito_periodo = report_data.get('totalCreditoPeriodo', 0)

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
        "total_debito_periodo": total_debito_periodo, # Al contexto
        "total_credito_periodo": total_credito_periodo, # Al contexto
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
        models_centro_costo.nombre.label("centro_costo_nombre"),
        models_tercero.nit.label("tercero_nit"),
        models_tercero.razon_social.label("tercero_razon_social")
    ).join(models_mov, models_doc.id == models_mov.documento_id) \
    .join(models_tipo, models_doc.tipo_documento_id == models_tipo.id) \
    .join(models_plan, models_mov.cuenta_id == models_plan.id) \
    .join(models_tercero, models_doc.beneficiario_id == models_tercero.id) \
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
            "movimiento_id": mov_dict.get('movimiento_id'),
            "beneficiario_nit": mov_dict.get('tercero_nit') or "N/A"
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
    # 0. Validar Modo Auditoría (Restricción de Fechas)
    empresa_info = db.query(models_empresa).filter(models_empresa.id == empresa_id).first()
    if empresa_info and empresa_info.modo_operacion == 'AUDITORIA_READONLY':
        # Si intenta cambiar la fecha, bloqueamos.
        # Check: documento_update.fecha viene en el payload? Es diferente al actual?
        # Primero necesitamos la fecha actual del documento para comparar.
        current_doc_date = db.query(models_doc.fecha).filter(models_doc.id == documento_id).scalar()
        
        if documento_update.fecha and current_doc_date and documento_update.fecha != current_doc_date:
             raise HTTPException(
                status_code=403, 
                detail="🚫 Operación restringida: En modo AUDITORÍA/CLON no se permite modificar la fecha de los documentos históricos."
            )

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
        models_doc.numero,
        models_tipo.nombre.label("tipo_nombre"),
        models_tercero.nit.label("tercero_nit")
    ).join(models_tipo, models_doc.tipo_documento_id == models_tipo.id)\
     .join(models_tercero, models_doc.beneficiario_id == models_tercero.id)\
     .filter(
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
            "tipo_documento": factura.tipo_nombre,
            "numero_documento": factura.numero,
            "beneficiario_nit": factura.tercero_nit,
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
        models_doc.numero,
        models_tipo.nombre.label("tipo_nombre"),
        models_tercero.nit.label("tercero_nit")
    ).join(models_tipo, models_doc.tipo_documento_id == models_tipo.id)\
     .join(models_tercero, models_doc.beneficiario_id == models_tercero.id)\
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
            "tipo_documento": recibo.tipo_nombre,
            "numero_documento": recibo.numero,
            "beneficiario_nit": recibo.tercero_nit,
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
    fecha_corte: date,
    nivel: str = 'auxiliar'
) -> Dict[str, Any]:
    """
    Calcula los saldos de las cuentas de balance (Activo, Pasivo, Patrimonio)
    y la utilidad del ejercicio a una fecha de corte para el reporte en pantalla.
    Soporta niveles: 'auxiliar' (detalle), 'mayor' (4 dígitos), 'clasificado' (Corriente/No Corriente).
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

    # Estructuras base
    raw_activos = []
    raw_pasivos = []
    raw_patrimonio = []
    
    total_ingresos, total_costos, total_gastos = 0.0, 0.0, 0.0
    
    # --- FIX: Pre-fetch de Nombres de Cuentas Mayores (4 dígitos) ---
    # Para evitar que '2408' tome el nombre de '240810' (IVA 19%).
    # Recolectamos todos los códigos que vamos a procesar.
    codigos_procesados = [c.codigo for c in saldos_query]
    posibles_mayores = set()
    for cod in codigos_procesados:
        if len(cod) >= 4:
            posibles_mayores.add(cod[:4])
            
    mapa_nombres_mayores = {}
    if posibles_mayores:
        cuentas_mayor = db.query(models_plan.codigo, models_plan.nombre).filter(
            models_plan.empresa_id == empresa_id,
            models_plan.codigo.in_(list(posibles_mayores))
        ).all()
        mapa_nombres_mayores = {c.codigo: c.nombre for c in cuentas_mayor}
    # ----------------------------------------------------------------

    # 1. Clasificación inicial y cálculo de utilidad
    for cuenta in saldos_query:
        saldo = float(cuenta.saldo or 0.0)
        
        # Ingresos, Costos, Gastos (Solo para utilidad)
        if cuenta.codigo.startswith('4'):
            total_ingresos += -saldo
            continue
        elif cuenta.codigo.startswith('5'):
            total_gastos += saldo
            continue
        elif cuenta.codigo.startswith('6'):
            total_costos += saldo
            continue

        # Balance
        item = {'codigo': cuenta.codigo, 'nombre': cuenta.nombre, 'saldo': saldo}
        if cuenta.codigo.startswith('1'):
            raw_activos.append(item)
        elif cuenta.codigo.startswith('2'):
            item['saldo'] = -saldo # Pasivo naturaleza crédito
            raw_pasivos.append(item)
        elif cuenta.codigo.startswith('3'):
            item['saldo'] = -saldo # Patrimonio naturaleza crédito
            raw_patrimonio.append(item)

    utilidad_ejercicio = total_ingresos - total_costos - total_gastos

    # 2. Procesamiento según Nivel
    final_activos = []
    final_pasivos = []
    final_patrimonio = []
    
    # Estructura Especial para Clasificado
    clasificado_activo = None
    clasificado_pasivo = None

    if nivel == 'mayor':
        # Agrupar por 4 dígitos
        def agrupar_mayor(lista_items):
            agrupados = {}
            for it in lista_items:
                cod_mayor = it['codigo'][:4]
                if cod_mayor not in agrupados:
                    # FIX: Usar nombre oficial del mapa si existe, sino fallback al nombre del item actual
                    nombre_cuenta = mapa_nombres_mayores.get(cod_mayor, it['nombre'])
                    agrupados[cod_mayor] = {'codigo': cod_mayor, 'nombre': nombre_cuenta, 'saldo': 0.0}
                
                agrupados[cod_mayor]['saldo'] += it['saldo']
            
            # Ajuste de nombres (Intento de mejora visual)
            # Retornamos lista ordenada
            return sorted(list(agrupados.values()), key=lambda x: x['codigo'])

        final_activos = agrupar_mayor(raw_activos)
        final_pasivos = agrupar_mayor(raw_pasivos)
        final_patrimonio = agrupar_mayor(raw_patrimonio)

    elif nivel == 'clasificado':
        # Agrupar en Corriente / No Corriente
        # Reglas:
        # Activo Corriente: 11, 12, 13, 14
        # Activo No Corriente: 15, 16, 17, 18, 19
        # Pasivo Corriente: 21, 22, 23, 24, 25, 26, 27, 29
        # Pasivo No Corriente: 28 
        
        # Nota: Usaremos items base (auxiliar) agrupados visualmente, O items Nivel Mayor en las secciones.
        # Generalmente Clasificado implica resumen (Mayor). Usaremos Mayor dentro de las secciones.
        
        def agrupar_clasificado(lista_items, grupos_corriente):
            corriente = []
            no_corriente = []
            
            # Primero agrupamos a nivel Mayor (4 digitos) para limpiar detalle excesivo
            items_mayor = {}
            for it in lista_items:
                cod_mayor = it['codigo'][:4]
                if cod_mayor not in items_mayor:
                    # FIX: Usar nombre oficial del mapa
                    nombre_cuenta = mapa_nombres_mayores.get(cod_mayor, it['nombre'])
                    items_mayor[cod_mayor] = {'codigo': cod_mayor, 'nombre': nombre_cuenta, 'saldo': 0.0}
                items_mayor[cod_mayor]['saldo'] += it['saldo']
            
            items_procesados = sorted(list(items_mayor.values()), key=lambda x: x['codigo'])

            for it in items_procesados:
                grupo_2 = it['codigo'][:2]
                if grupo_2 in grupos_corriente:
                    corriente.append(it)
                else:
                    no_corriente.append(it)
            
            return {
                "corriente": corriente,
                "total_corriente": sum(x['saldo'] for x in corriente),
                "no_corriente": no_corriente,
                "total_no_corriente": sum(x['saldo'] for x in no_corriente)
            }

        clasificado_activo = agrupar_clasificado(raw_activos, ['11','12','13','14'])
        clasificado_pasivo = agrupar_clasificado(raw_pasivos, ['21','22','23','24','25','26','27','29']) # 28 estimada LP
        
        # Patrimonio no se suele dividir en Corriente/No Corriente, va directo
        # Usamos Mayor para consistencia
        items_mayor_pat = {}
        for it in raw_patrimonio:
            cod_mayor = it['codigo'][:4]
            if cod_mayor not in items_mayor_pat:
                # FIX: Usar nombre oficial del mapa
                nombre_cuenta = mapa_nombres_mayores.get(cod_mayor, it['nombre'])
                items_mayor_pat[cod_mayor] = {'codigo': cod_mayor, 'nombre': nombre_cuenta, 'saldo': 0.0}
            items_mayor_pat[cod_mayor]['saldo'] += it['saldo']
        final_patrimonio = sorted(list(items_mayor_pat.values()), key=lambda x: x['codigo'])
        
        # Para compatibilidad con frontend básico, poblamos final_activos flat concatenado
        final_activos = clasificado_activo['corriente'] + clasificado_activo['no_corriente']
        final_pasivos = clasificado_pasivo['corriente'] + clasificado_pasivo['no_corriente']

    else:
        # Nivel Auxiliar (Detalle completo)
        final_activos = sorted(raw_activos, key=lambda x: x['codigo'])
        final_pasivos = sorted(raw_pasivos, key=lambda x: x['codigo'])
        final_patrimonio = sorted(raw_patrimonio, key=lambda x: x['codigo'])

    total_activos = sum(c['saldo'] for c in final_activos)
    total_pasivos = sum(c['saldo'] for c in final_pasivos)
    total_patrimonio = sum(c['saldo'] for c in final_patrimonio) + utilidad_ejercicio
    
    return {
        "activos": final_activos,
        "pasivos": final_pasivos,
        "patrimonio": final_patrimonio,
        "clasificado_activo": clasificado_activo, # Solo presente si nivel='clasificado'
        "clasificado_pasivo": clasificado_pasivo, # Solo presente si nivel='clasificado'
        "total_activos": total_activos,
        "total_pasivos": total_pasivos,
        "total_patrimonio": total_patrimonio,
        "utilidad_ejercicio": utilidad_ejercicio,
        "total_pasivo_patrimonio": total_pasivos + total_patrimonio,
        "nivel": nivel
    }

def generate_balance_sheet_report_pdf(
    db: Session, 
    empresa_id: int, 
    fecha_corte: date,
    nivel: str = 'auxiliar'
):
    """
    Genera el archivo PDF para el reporte de Balance General.
    """
    # 1. Reutilizamos la función que acabamos de crear para obtener los datos.
    report_data = generate_balance_sheet_report(db, empresa_id, fecha_corte, nivel)
    
    # 2. Obtenemos la información de la empresa.
    empresa_info = db.query(models_empresa).filter(models_empresa.id == empresa_id).first()
    if not empresa_info:
        raise HTTPException(status_code=404, detail=f"No se encontró la empresa con ID {empresa_id}")

    # 3. Preparamos el contexto para la plantilla, cumpliendo el contrato.
    context = {
        "empresa": empresa_info,
        "fecha_corte": fecha_corte,
        "reporte": report_data,
        "nivel": nivel
    }
    
    # 4. Renderizamos el PDF.
    try:
        # Usamos una plantilla simple por defecto si falla el pack
        template_string = TEMPLATES_EMPAQUETADOS.get('reports/balance_general_report.html', """
            <html><body><h1>Error: Plantilla no encontrada</h1></body></html>
        """)
        
        # SI ES CLASIFICADO, INYECTAMOS UN CSS/HTML DIFERENTE O MANIPULAMOS EL CONTEXTO
        # Para simplificar y dado que no puedo editar el pack fácilmente,
        # si es clasificado, el reporte usa las listas planas (que ya poblé arriba)
        # por lo que saldrá con formato "Mayor". 
        # Si quisiera separadores "Corriente / No Corriente", necesitaría editar el HTML.
        # VOY A DEFINIR UNA PLANTILLA "SMART" AQUÍ MISMO PARA EL CASO CLASIFICADO SI SE REQUIERE,
        # PERO POR AHORA USAREMOS LA ESTANDÁR CON LOS DATOS PLANOS DE MAYOR.
        # (El usuario pidió que se adapte, asi que lo mejor es que si es clasificado salga con secciones).
        
        # -------------------------------------------------------------------------
        # PLANTILLA PROFESIONAL DE ALTO NIVEL (AUDIT STYLE)
        # -------------------------------------------------------------------------
        # Esta plantilla reemplaza la anterior para garantizar un look contable serio.
        # Soporta tanto la vista 'Clasificada' como 'Estándar' (Auxiliar/Mayor).
        
        template_string = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Balance General</title>
    <style>
        @page { size: letter; margin: 2cm 1.5cm; }
        body { 
            font-family: 'Times New Roman', Times, serif; 
            font-size: 10pt; 
            color: #000;
            line-height: 1.3;
        }
        
        /* HEADER */
        .header { text-align: center; margin-bottom: 40px; }
        .header h1 { 
            font-size: 16pt; 
            font-weight: bold; 
            margin: 0; 
            text-transform: uppercase; 
            letter-spacing: 1px;
        }
        .header p.nit { font-size: 10pt; margin: 2px 0 15px 0; }
        .header h2 { 
            font-size: 14pt; 
            font-weight: bold; 
            margin: 5px 0; 
            border-top: 1px solid #000; 
            border-bottom: 1px solid #000; 
            display: inline-block; 
            padding: 3px 20px;
            text-transform: uppercase;
        }
        .header p.meta { font-style: italic; font-size: 9pt; margin-top: 10px; }
        .currency-note { font-size: 8pt; text-align: center; margin-top: -5px; margin-bottom: 20px; }

        /* TABLAS Y CIFRAS */
        .section-title { 
            font-weight: bold; 
            font-size: 11pt; 
            text-transform: uppercase; 
            margin-top: 20px; 
            margin-bottom: 10px; 
            border-bottom: 2px solid #000;
            width: 100%;
            display: block;
        }
        
        .subsection-title {
            font-weight: bold;
            font-size: 10pt;
            text-transform: uppercase;
            margin-top: 10px;
            margin-bottom: 5px;
            padding-left: 10px;
            text-decoration: underline;
        }

        .row { 
            display: flex; 
            justify-content: space-between; 
            padding: 2px 0; 
            margin-bottom: 2px;
        }
        .row:hover { background-color: #f9f9f9; } /* Solo visible si se exporta html */
        
        .col-name { flex-grow: 1; padding-left: 15px; }
        .col-code { width: 60px; font-weight: bold; color: #333; }
        .col-val { width: 120px; text-align: right; font-family: 'Courier New', Courier, monospace; }

        .total-row { 
            display: flex; 
            justify-content: space-between; 
            font-weight: bold; 
            margin-top: 5px; 
            padding-top: 5px; 
            border-top: 1px solid #000;
        }
        .total-row.main {
            border-top: 2px solid #000;
            font-size: 11pt;
            margin-top: 15px;
            background-color: #f0f0f0;
            border-bottom: 1px solid #000;
            padding: 5px 0;
        }

        /* UTILIDADES */
        .text-right { text-align: right; }
        .bold { font-weight: bold; }
        .italic { font-style: italic; }
        .indent { padding-left: 30px; }
        
        /* FIRMAS */
        .signatures { 
            display: flex; 
            justify-content: space-around; 
            margin-top: 80px; 
            page-break-inside: avoid; 
        }
        .sig-block { 
            width: 40%; 
            border-top: 1px solid #000; 
            text-align: center; 
            padding-top: 10px; 
        }
        .sig-name { font-weight: bold; font-size: 10pt; }
        .sig-title { font-size: 9pt; color: #555; }

        /* ECUACIÓN */
        .equation-box {
            margin-top: 40px;
            border: 2px solid #000;
            padding: 10px;
            text-align: center;
            font-weight: bold;
            font-size: 11pt;
            background-color: #f9f9f9;
            width: 60%;
            margin-left: auto;
            margin-right: auto;
            page-break-inside: avoid;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>{{ empresa.razon_social }}</h1>
        <p class="nit">NIT: {{ empresa.nit }}</p>
        
        <h2>Estado de Situación Financiera</h2>
        
        <p class="meta">Corte al: {{ fecha_corte }}</p>
        <p class="currency-note">(Cifras expresadas en Pesos Colombianos)</p>
    </div>

    {% macro render_row(item) %}
    <div class="row">
        <div class="col-code">{{ item.codigo }}</div>
        <div class="col-name">{{ item.nombre }}</div>
        <div class="col-val">{{ "{:,.0f}".format(item.saldo) }}</div>
    </div>
    {% endmacro %}

    <!-- ========================================== -->
    <!--                 ACTIVOS                    -->
    <!-- ========================================== -->
    <div class="section-title">Activos</div>
    
    {% if nivel == 'clasificado' %}
        
        <div class="subsection-title">Activo Corriente</div>
        {% for item in reporte.clasificado_activo.corriente %}
            {{ render_row(item) }}
        {% endfor %}
        <div class="total-row indent">
            <span>Total Activo Corriente</span>
            <span>{{ "{:,.0f}".format(reporte.clasificado_activo.total_corriente) }}</span>
        </div>

        <div class="subsection-title">Activo No Corriente</div>
        {% for item in reporte.clasificado_activo.no_corriente %}
            {{ render_row(item) }}
        {% endfor %}
        <div class="total-row indent">
            <span>Total Activo No Corriente</span>
            <span>{{ "{:,.0f}".format(reporte.clasificado_activo.total_no_corriente) }}</span>
        </div>

    {% else %}
        <!-- STANDARD VIEW (Auxiliar/Mayor) -->
        {% for item in reporte.activos %}
            {{ render_row(item) }}
        {% endfor %}
    {% endif %}

    <div class="total-row main">
        <span style="padding-left: 10px;">TOTAL ACTIVOS</span>
        <span style="padding-right: 1px;">{{ "{:,.0f}".format(reporte.total_activos) }}</span>
    </div>


    <!-- ========================================== -->
    <!--                 PASIVOS                    -->
    <!-- ========================================== -->
    <div class="section-title">Pasivos</div>

    {% if nivel == 'clasificado' %}
        
        <div class="subsection-title">Pasivo Corriente</div>
        {% for item in reporte.clasificado_pasivo.corriente %}
            {{ render_row(item) }}
        {% endfor %}
        <div class="total-row indent">
            <span>Total Pasivo Corriente</span>
            <span>{{ "{:,.0f}".format(reporte.clasificado_pasivo.total_corriente) }}</span>
        </div>

        <div class="subsection-title">Pasivo No Corriente</div>
        {% for item in reporte.clasificado_pasivo.no_corriente %}
            {{ render_row(item) }}
        {% endfor %}
        <div class="total-row indent">
            <span>Total Pasivo No Corriente</span>
            <span>{{ "{:,.0f}".format(reporte.clasificado_pasivo.total_no_corriente) }}</span>
        </div>

    {% else %}
        {% for item in reporte.pasivos %}
            {{ render_row(item) }}
        {% endfor %}
    {% endif %}

    <div class="total-row main">
        <span style="padding-left: 10px;">TOTAL PASIVOS</span>
        <span style="padding-right: 1px;">{{ "{:,.0f}".format(reporte.total_pasivos) }}</span>
    </div>


    <!-- ========================================== -->
    <!--                 PATRIMONIO                 -->
    <!-- ========================================== -->
    <div class="section-title">Patrimonio</div>

    {% for item in reporte.patrimonio %}
        {{ render_row(item) }}
    {% endfor %}

    <!-- Utilidad (Insertada manual) -->
    <div class="row">
        <div class="col-code">3605</div>
        <div class="col-name bold">UTILIDAD DEL EJERCICIO</div>
        <div class="col-val bold">{{ "{:,.0f}".format(reporte.utilidad_ejercicio) }}</div>
    </div>

    <div class="total-row main">
        <span style="padding-left: 10px;">TOTAL PATRIMONIO</span>
        <span style="padding-right: 1px;">{{ "{:,.0f}".format(reporte.total_patrimonio) }}</span>
    </div>


    <!-- ========================================== -->
    <!--                 RESUMEN                    -->
    <!-- ========================================== -->
    <div class="equation-box">
        TOTAL PASIVO + PATRIMONIO: {{ "{:,.0f}".format(reporte.total_pasivo_patrimonio) }}
    </div>

    
    <!-- ========================================== -->
    <!--                  FIRMAS                    -->
    <!-- ========================================== -->
    <div class="signatures">
        <div class="sig-block">
            <div class="sig-name">REPRESENTANTE LEGAL</div>
            <div class="sig-title">C.C.</div>
        </div>
        <div class="sig-block">
            <div class="sig-name">CONTADOR PÚBLICO</div>
            <div class="sig-title">T.P.</div>
        </div>
    </div>

</body>
</html>
        """
        


        template = GLOBAL_JINJA_ENV.from_string(template_string)
        rendered_html = template.render(context)
        return HTML(string=rendered_html).write_pdf()
    except KeyError:
        raise HTTPException(status_code=500, detail="La plantilla 'reports/balance_general_report.html' no fue encontrada.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al renderizar el PDF del Balance General: {e}")

# --- FIN: NUEVAS FUNCIONES PARA BALANCE GENERAL ---

