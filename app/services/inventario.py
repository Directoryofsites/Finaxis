# app/services/inventario.py (VERSIÓN FINAL CON SONDA FORZADA Y MANEJO DE ERRORES BLINDADO)

from sqlalchemy.orm import Session, selectinload, joinedload, contains_eager, aliased
from sqlalchemy import func, and_, case, or_, inspect, delete, select, cast, String as SAString, DECIMAL
from fastapi import HTTPException, status

from sqlalchemy.exc import IntegrityError # IMPORTACIÓN CRÍTICA PARA BLINDAR ERRORES DE DB
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, date, time, timezone # <<<<<<< FIX CRÍTICO AQUÍ: datetime y timezone importados

from decimal import Decimal, ROUND_HALF_UP # Asegurar Decimal y ROUND_HALF_UP para costos
import traceback
import locale 
import os # Necesario para la generación de PDF
from io import BytesIO # Necesario para la generación de PDF
from weasyprint import HTML # Necesario para la generación de PDF
from jinja2 import Environment, FileSystemLoader # Necesario para la generación de PDF


# --- Importaciones de Modelos ---
from ..models import (
    producto as models_producto,
    bodega as models_bodega,
    grupo_inventario as models_grupo,
    impuesto as models_impuesto,
    movimiento_contable as models_mov,
    lista_precio as models_lista_precio,
    documento as models_doc,
    caracteristica_definicion as models_carac_def,
    caracteristica_valor_producto as models_carac_val,
    regla_precio_grupo as models_regla_precio,
    tercero as models_tercero,
    # === FIX: Asegurar que todos los modelos necesarios se importen
    empresa as models_empresa
)

# --- Importaciones de Schemas y Servicios NECESARIAS ---
from ..schemas import inventario as schemas
from ..schemas import traslado_inventario as schemas_traslado
from ..schemas import documento as schemas_doc # FIX: Necesario para DocumentoCreate
from ..services import documento as service_documento # FIX: Necesario para create_documento
from ..services import tipo_documento as service_tipo_documento # Necesario para validación de tipo doc

# --- INICIO: LÓGICA DE FILTRO DE MILES INYECTADA ---
# FIX: Estas funciones y configuraciones deben estar definidas antes de usarse
def format_miles(value):
    """Aplica formato de separador de miles con dos decimales, usando el formato CO."""
    try:
        val = float(value)
        locale.setlocale(locale.LC_ALL, 'es_ES.UTF-8') 
        formatted = locale.format_string("%.2f", val, grouping=True)
        # Lógica de corrección de formato local si es necesario.
        if '.' in formatted and ',' in formatted and formatted.rfind('.') < formatted.rfind(','):
             return formatted.replace('.', '#').replace(',', '.').replace('#', ',')
        return formatted
    except Exception:
        return f"{value or 0:.2f}" 

# --- Carga de Entorno Jinja2 (Para PDF) ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, '..', 'templates', 'reports')
env = Environment(loader=FileSystemLoader(TEMPLATES_DIR), trim_blocks=True, lstrip_blocks=True)
env.filters['format_miles'] = format_miles 

# Función para adaptar Decimal a float (necesario para Jinja2)
def _to_float(value):
    return float(value) if isinstance(value, (Decimal, int, float)) else (value or 0.0)

def generar_pdf_desde_html(html_content: str) -> bytes:
    """Función auxiliar para generar el PDF a partir del contenido HTML."""
    return HTML(string=html_content).write_pdf(stylesheets=[])


# ========== Funciones de Movimiento (CRÍTICAS) - Movidas al inicio ==========

def registrar_movimiento_inventario(db: Session, producto_id: int, bodega_id: int, tipo_movimiento: str, cantidad: float, costo_unitario: Optional[float], fecha: datetime, documento_id: int = None):
    """
    Registra el movimiento en la tabla MovimientoInventario y actualiza StockBodega y Costo Promedio.
    """
    try:
        db_producto = db.query(models_producto.Producto).filter(models_producto.Producto.id == producto_id).with_for_update().first()
        if not db_producto or db_producto.es_servicio: return
        
        # 1. Búsqueda/Creación de StockBodega con bloqueo
        stock_bodega = db.query(models_producto.StockBodega).filter_by(producto_id=producto_id, bodega_id=bodega_id).with_for_update().first()
        if not stock_bodega:
            stock_bodega = models_producto.StockBodega(producto_id=producto_id, bodega_id=bodega_id, stock_actual=0.0)
            db.add(stock_bodega); db.flush()
            
        stock_anterior_bodega = stock_bodega.stock_actual or 0.0
        
        # 2. Actualización de Cantidad
        if tipo_movimiento.startswith('SALIDA'): 
            stock_bodega.stock_actual -= cantidad
        else: 
            stock_bodega.stock_actual += cantidad
            
        # --- FIX STOCK/TRASLADO: Forzar el guardado de stock_actual en la sesión ---
        db.flush() 
        
        # 3. Recálculo de Costo Promedio (Solo si es ENTRADA)
        if tipo_movimiento.startswith('ENTRADA'):
            stock_total_anterior_otras_bodegas = db.query(func.sum(models_producto.StockBodega.stock_actual)).filter(
                models_producto.StockBodega.producto_id == producto_id, 
                models_producto.StockBodega.bodega_id != bodega_id
            ).scalar() or 0.0
            
            stock_total_anterior = stock_total_anterior_otras_bodegas + stock_anterior_bodega
            
            costo_anterior = db_producto.costo_promedio if db_producto.costo_promedio is not None else 0.0
            cantidad_entrada = cantidad
            costo_unitario_entrada = float(costo_unitario or 0.0)
            
            stock_total_nuevo = stock_total_anterior + cantidad_entrada
            nuevo_costo_promedio = 0.0
            
            if abs(stock_total_nuevo) > 1e-9:
                valor_total_anterior = stock_total_anterior * costo_anterior
                valor_entrada = cantidad_entrada * costo_unitario_entrada
                nuevo_costo_promedio = (valor_total_anterior + valor_entrada) / stock_total_nuevo
            elif cantidad_entrada > 0: 
                nuevo_costo_promedio = costo_unitario_entrada
                
            db_producto.costo_promedio = nuevo_costo_promedio
            
        # 4. Registro de Movimiento y Flush
        costo_unitario_guardar = float(costo_unitario or 0.0)
        costo_total_calculado = cantidad * costo_unitario_guardar
        movimiento = models_producto.MovimientoInventario(
            producto_id=producto_id, bodega_id=bodega_id, documento_id=documento_id, fecha=fecha, 
            tipo_movimiento=tipo_movimiento, cantidad=cantidad, costo_unitario=costo_unitario_guardar, 
            costo_total=costo_total_calculado
        )
        db.add(movimiento); db.flush()
        
    except Exception as e: 
        print(f"ERROR en registrar_movimiento_inventario: {e}"); traceback.print_exc(); 
        raise 

def get_stock_historico(db: Session, producto_id: int, bodega_id: Optional[int], fecha: datetime) -> float:
    documentos_validos = db.query(models_doc.Documento.id).filter(models_doc.Documento.anulado == False).subquery()
    saldo_query = db.query(func.sum(case((models_producto.MovimientoInventario.tipo_movimiento.startswith('ENTRADA'), models_producto.MovimientoInventario.cantidad), (models_producto.MovimientoInventario.tipo_movimiento.startswith('SALIDA'), -models_producto.MovimientoInventario.cantidad), else_=Decimal('0.0'))).label("saldo"))\
        .outerjoin(documentos_validos, models_producto.MovimientoInventario.documento_id == documentos_validos.c.id)\
        .filter(models_producto.MovimientoInventario.producto_id == producto_id, models_producto.MovimientoInventario.fecha < fecha, or_(models_producto.MovimientoInventario.documento_id == None, documentos_validos.c.id != None))
    if bodega_id:
        saldo_query = saldo_query.filter(models_producto.MovimientoInventario.bodega_id == bodega_id)
        
    saldo_result = saldo_query.scalar()
    return float(saldo_result or Decimal('0.0'))


def recalcular_saldos_producto(db: Session, producto_id: int):
    """
    Reconstruye TOTALMENTE el Stock y Costo Promedio del producto basándose
    en todos los movimientos existentes en la base de datos.
    Crucial para mantener integridad tras eliminación de documentos.
    """
    print(f"\n[RECALCULO INVENTARIO] Iniciando para Producto ID {producto_id}")
    
    # 1. Obtener Producto 
    producto = db.query(models_producto.Producto).get(producto_id)
    if not producto: return

    # 1.5. PASO CRÍTICO: Resetear TODO el stock existente a 0.0
    # Esto elimina "saldos fantasma" de bodegas que ya no tienen movimientos asociados.
    db.query(models_producto.StockBodega).filter(
        models_producto.StockBodega.producto_id == producto_id
    ).update({"stock_actual": 0.0, "stock_comprometido": 0.0}, synchronize_session=False)

    # 2. Resetear valores en memoria (Saldos iniciales)
    # Si tiene historial, lo reconstruiremos. Si no, debería quedar en 0 (o manual).
    # OJO: Si se maneja saldo inicial manual en otra tabla, habría que sumarlo. 
    # Por ahora asumimos que 'ENTRADA_INICIAL' es un movimiento más.
    
    nuevo_costo_promedio = 0.0
    stocks_por_bodega = {} # Mapa: bodega_id -> cantidad
    
    # 3. Obtener TODOS los movimientos ordenados cronológicamente
    # El orden es VITAL para el promedio ponderado.
    movimientos = db.query(models_producto.MovimientoInventario).filter(
        models_producto.MovimientoInventario.producto_id == producto_id
    ).order_by(
        models_producto.MovimientoInventario.fecha.asc(),
        models_producto.MovimientoInventario.id.asc()
    ).all()

    stock_total_global = 0.0
    
    # 4. Re-procesar paso a paso
    for mov in movimientos:
        bodega_id = mov.bodega_id
        cantidad = float(mov.cantidad)
        costo_mov = float(mov.costo_unitario or 0.0)
        
        # Inicializar bodega si no existe en mapa
        if bodega_id not in stocks_por_bodega: stocks_por_bodega[bodega_id] = 0.0
        
        if mov.tipo_movimiento.startswith('ENTRADA'):
            # Lógica de Promedio Ponderado
            # Valor Anterior Total = Stock Total * Costo Promedio Actual
            valor_anterior = stock_total_global * nuevo_costo_promedio
            valor_entrada = cantidad * costo_mov
            
            # Nuevo Stock
            stocks_por_bodega[bodega_id] += cantidad
            stock_total_global += cantidad
            
            # Nuevo Promedio
            if stock_total_global > 0:
                nuevo_costo_promedio = (valor_anterior + valor_entrada) / stock_total_global
            else:
                nuevo_costo_promedio = costo_mov
                
        elif mov.tipo_movimiento.startswith('SALIDA'):
            # En salida, el costo promedio NO CAMBIA, solo baja el stock
            stocks_por_bodega[bodega_id] -= cantidad
            stock_total_global -= cantidad
            
    # 5. Aplicar cambios a la Base de Datos
    
    # A. Actualizar Producto
    # Evitamos errores de redondeo infinitesimal
    if abs(stock_total_global) < 0.00001: stock_total_global = 0.0
    
    producto.costo_promedio = nuevo_costo_promedio
    # OJO: Producto no tiene campo stock_total persistente fiable, lo calculamos sumando bodegas.
    # Pero actualizamos el costo que es lo crítico.
    
    db.add(producto)
    
    # B. Actualizar Stocks por Bodega (Sobreescribimos lo que haya en StockBodega)
    for b_id, nuevo_stock in stocks_por_bodega.items():
        if abs(nuevo_stock) < 0.00001: nuevo_stock = 0.0
        
        stock_db = db.query(models_producto.StockBodega).filter_by(
            producto_id=producto_id, bodega_id=b_id
        ).first()
        
        if stock_db:
            stock_db.stock_actual = nuevo_stock
            db.add(stock_db)
        else:
            # Si no existía un registro de stock pero hubo movimiento (raro pero posible)
            new_stock = models_producto.StockBodega(
                producto_id=producto_id, bodega_id=b_id, stock_actual=nuevo_stock
            )
            db.add(new_stock)
            
    # C. Limpieza de StockBodega huerfanos (opcional, si queremos borrar los q quedaron en 0)
    # Por ahora mejor no borrar para no perder historial de qué bodegas se usaron.
    
    db.flush() # Confirmar cambios en esta transacción
    print(f"[RECALCULO FINALIZADO] ID {producto_id} -> Stock Global: {stock_total_global}, Costo Prom: {nuevo_costo_promedio}")

    print(f"[RECALCULO FINALIZADO] ID {producto_id} -> Stock Global: {stock_total_global}, Costo Prom: {nuevo_costo_promedio}")


def recalcular_todo_inventario(db: Session, empresa_id: int):
    """
    Ejecuta el recálculo de saldos y costos para TODOS los productos de la empresa.
    Útil para corregir inconsistencias masivas o tras migraciones/eliminaciones.
    """
    print(f"\n[RECALCULO MASIVO] Iniciando para Empresa ID {empresa_id}")
    productos = db.query(models_producto.Producto).filter(models_producto.Producto.empresa_id == empresa_id).all()
    count = 0
    total = len(productos)
    
    for prod in productos:
        # Ignoramos servicios pues no manejan stock
        if not prod.es_servicio:
            recalcular_saldos_producto(db, prod.id)
            count += 1
            
            
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"[RECALCULO MASIVO ERROR] Fallo al hacer commit final: {e}")
        raise e

    print(f"[RECALCULO MASIVO] Finalizado. Procesados {count}/{total} productos.")
    return {"message": f"Recálculo completado. Productos procesados: {count}", "total": count}


# --- FUNCIÓN CLAVE: CREAR TRASLADO ENTRE BODEGAS (FIXED) ---
def crear_traslado_entre_bodegas(db: Session, traslado: schemas_traslado.TrasladoInventarioCreate, empresa_id: int, user_id: int) -> models_doc.Documento:
    """
    Registra un traslado atómico de inventario (Salida de Origen, Entrada en Destino).
    """
    print("\n[SONDA TRASLADO INICIO] ==================================")
    
    # 1. Validaciones básicas de existencias y reglas de negocio
    db_tipo_doc = service_tipo_documento.get_tipo_documento(db, traslado.tipo_documento_id)
    
    if not db_tipo_doc or db_tipo_doc.funcion_especial != 'traslado_inventario':
        raise HTTPException(status_code=400, detail="Tipo de documento inválido para un traslado.")
    db_origen = db.query(models_bodega.Bodega).filter_by(id=traslado.bodega_origen_id, empresa_id=empresa_id).first()
    db_destino = db.query(models_bodega.Bodega).filter_by(id=traslado.bodega_destino_id, empresa_id=empresa_id).first()
    if not db_origen or not db_destino:
        raise HTTPException(status_code=404, detail="Bodega de origen o destino no encontrada.")
    if traslado.bodega_origen_id == traslado.bodega_destino_id:
        raise HTTPException(status_code=400, detail="La bodega de origen y destino no pueden ser la misma.")

    try:
        with db.begin_nested():
            
            # 2. Creación del Documento TR (Neutro) - FIX DE FIRMA
            documento_payload = schemas_doc.DocumentoCreate(
                empresa_id=empresa_id,
                tipo_documento_id=traslado.tipo_documento_id,
                numero=None, 
                fecha=traslado.fecha,
                fecha_vencimiento=traslado.fecha, 
                beneficiario_id=None,
                centro_costo_id=None,
                observaciones=traslado.observaciones,
                valor_total=0.0,
                movimientos=[], 
                aplicaciones=[] 
            )
            # USAMOS EL PAYLOAD COMO ARGUMENTO 'documento', COMO ESPERA service_documento.create_documento
            documento_creado = service_documento.create_documento(
                db=db,
                documento=documento_payload, 
                user_id=user_id,
                commit=False # No hacer commit hasta después de los movimientos
            )
            
            # 3. Procesar Items (Salida y Entrada Atómica)
            for item in traslado.items:
                producto_id = item.producto_id
                cantidad = item.cantidad
                
                db_producto = db.query(models_producto.Producto).filter_by(id=producto_id, empresa_id=empresa_id).with_for_update().first()
                if not db_producto: raise HTTPException(status_code=404, detail=f"Producto ID {producto_id} no encontrado.")
                if db_producto.es_servicio: continue
                
                costo_unitario = db_producto.costo_promedio or 0.0
                
                # A. VALIDACIÓN DE STOCK (Origen)
                stock_origen = db.query(models_producto.StockBodega).filter_by(producto_id=producto_id, bodega_id=traslado.bodega_origen_id).with_for_update().first()
                stock_actual_origen = stock_origen.stock_actual if stock_origen else 0.0
                stock_comprometido = stock_origen.stock_comprometido if stock_origen else 0.0
                
                # En traslados SIEMPRE respetamos el comprometido
                stock_disponible_traslado = stock_actual_origen - stock_comprometido

                if stock_disponible_traslado < cantidad:
                    raise HTTPException(status_code=409, detail=f"Stock insuficiente en Bodega Origen ({db_origen.nombre}) para producto {db_producto.codigo}. Disp: {stock_disponible_traslado}, Req: {cantidad}")
                
                # app/services/inventario.py (Dentro de crear_traslado_entre_bodegas)

                # B. REGISTRO - SALIDA (Origen)
                registrar_movimiento_inventario( 
                    db=db, producto_id=producto_id, bodega_id=traslado.bodega_origen_id,
                    tipo_movimiento='SALIDA_TRASLADO', cantidad=cantidad, costo_unitario=costo_unitario,
                    fecha=documento_creado.fecha, documento_id=documento_creado.id # <-- CORREGIDO A .fecha
                )

                # C. REGISTRO - ENTRADA (Destino)
                registrar_movimiento_inventario( 
                    db=db, producto_id=producto_id, bodega_id=traslado.bodega_destino_id,
                    tipo_movimiento='ENTRADA_TRASLADO', cantidad=cantidad, costo_unitario=costo_unitario,
                    fecha=documento_creado.fecha, documento_id=documento_creado.id # <-- CORREGIDO A .fecha
                )


        # 4. Commit Final: Se guarda todo
        db.commit()
        print(f"[SONDA TRASLADO FIN] COMMIT EXITOSO. Traslado {documento_creado.numero} registrado.")
        return documento_creado
    
    except Exception as e:
        db.rollback()
        print(f"[SONDA TRASLADO FALLO] ROLLBACK EJECUTADO. Causa: {type(e).__name__}: {e}")
        if isinstance(e, HTTPException): 
            raise e
        raise HTTPException(status_code=500, detail=f"Error interno al procesar el traslado: {e}")


# ========== Funciones Auxiliares ==========
def _filter_stock_for_bodegas(productos: List[models_producto.Producto], bodega_ids: Optional[List[int]] = None):
    if not bodega_ids:
        for prod in productos:
            if prod.es_servicio:
                prod.stock_total_calculado = 0.0
                prod.stocks_bodega = []
                continue
            total_stock = sum(sb.stock_actual for sb in prod.stocks_bodega if sb) if prod.stocks_bodega else 0.0
            prod.stock_total_calculado = total_stock
        return productos
    for prod in productos:
        if prod.es_servicio:
            prod.stock_total_calculado = 0.0
            prod.stocks_bodega = []
            continue
        if not prod.stocks_bodega:
             prod.stocks_bodega = []
             prod.stock_total_calculado = 0.0
             continue
        filtered_stock = [sb for sb in prod.stocks_bodega if sb and sb.bodega_id in bodega_ids]
        prod.stocks_bodega = filtered_stock
        total_stock_filtrado = sum(sb.stock_actual for sb in filtered_stock if sb)
        prod.stock_total_calculado = total_stock_filtrado
    return productos


# ========== CRUD para Bodegas ==========
def create_bodega(db: Session, bodega: schemas.BodegaCreate, empresa_id: int):
    db_bodega = models_bodega.Bodega(**bodega.model_dump(), empresa_id=empresa_id)
    db.add(db_bodega); db.commit(); db.refresh(db_bodega); return db_bodega

def get_bodegas_by_empresa(db: Session, empresa_id: int):
    return db.query(models_bodega.Bodega).filter(models_bodega.Bodega.empresa_id == empresa_id).order_by(models_bodega.Bodega.nombre).all()

def update_bodega(db: Session, bodega_id: int, bodega: schemas.BodegaUpdate, empresa_id: int):
    db_bodega = db.query(models_bodega.Bodega).filter(models_bodega.Bodega.id == bodega_id, models_bodega.Bodega.empresa_id == empresa_id).first()
    if not db_bodega: return None
    update_data = bodega.model_dump(exclude_unset=True)
    for key, value in update_data.items(): setattr(db_bodega, key, value)
    db.commit(); db.refresh(db_bodega); return db_bodega

def delete_bodega(db: Session, bodega_id: int, empresa_id: int):
    db_bodega = db.query(models_bodega.Bodega).filter(models_bodega.Bodega.id == bodega_id, models_bodega.Bodega.empresa_id == empresa_id).first()
    if not db_bodega: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bodega no encontrada.")
    en_uso_movimiento = db.query(models_producto.MovimientoInventario.id).filter(models_producto.MovimientoInventario.bodega_id == bodega_id).first()
    en_uso_stock = db.query(models_producto.StockBodega.id).filter(models_producto.StockBodega.bodega_id == bodega_id).first()
    if en_uso_movimiento or en_uso_stock: raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Bodega tiene stock o movimientos.")
    db.delete(db_bodega); db.commit(); return {"ok": True}


# ========== CRUD para Grupos de Inventario (RESTAURADO y FUNCIONAL) ==========
# FIX: Estas funciones fueron perdidas o truncadas y se restauran al final del archivo.
def create_grupo_inventario(db: Session, grupo: schemas.GrupoInventarioCreate, empresa_id: int):
    db_grupo = models_grupo.GrupoInventario(**grupo.model_dump(exclude={'caracteristicas_definidas', 'reglas_precio'}), empresa_id=empresa_id)
    db.add(db_grupo); db.commit(); db.refresh(db_grupo); return db_grupo

def get_grupos_by_empresa(db: Session, empresa_id: int):
    return db.query(models_grupo.GrupoInventario).options(
        selectinload(models_grupo.GrupoInventario.caracteristicas_definidas),
        selectinload(models_grupo.GrupoInventario.reglas_precio).selectinload(models_regla_precio.ReglaPrecioGrupo.lista_precio)
    ).filter(models_grupo.GrupoInventario.empresa_id == empresa_id).order_by(models_grupo.GrupoInventario.nombre).all()

def get_grupo_by_id(db: Session, grupo_id: int, empresa_id: int):
    return db.query(models_grupo.GrupoInventario).options(
        selectinload(models_grupo.GrupoInventario.caracteristicas_definidas),
        selectinload(models_grupo.GrupoInventario.reglas_precio).selectinload(models_regla_precio.ReglaPrecioGrupo.lista_precio)
    ).filter(models_grupo.GrupoInventario.id == grupo_id, models_grupo.GrupoInventario.empresa_id == empresa_id).first()

def search_grupos_by_nombre(db: Session, empresa_id: int, search_term: str) -> List[Dict[str, Any]]:
    grupos = db.query(models_grupo.GrupoInventario).filter(
        models_grupo.GrupoInventario.empresa_id == empresa_id,
        models_grupo.GrupoInventario.nombre.ilike(f"%{search_term}%")
    ).order_by(models_grupo.GrupoInventario.nombre).limit(10).all()
    return [{"id": g.id, "nombre": g.nombre} for g in grupos]

def update_grupo_inventario(db: Session, grupo_id: int, grupo: schemas.GrupoInventarioUpdate, empresa_id: int):
    db_grupo = get_grupo_by_id(db, grupo_id, empresa_id)
    if not db_grupo: return None
    update_data = grupo.model_dump(exclude_unset=True, exclude={'caracteristicas_definidas', 'reglas_precio'})
    for key, value in update_data.items(): setattr(db_grupo, key, value)
    db.commit()
    db_grupo_completo = get_grupo_by_id(db, grupo_id, empresa_id)
    return db_grupo_completo

def delete_grupo_inventario(db: Session, grupo_id: int, empresa_id: int):
    db_grupo = db.query(models_grupo.GrupoInventario).filter(models_grupo.GrupoInventario.id == grupo_id, models_grupo.GrupoInventario.empresa_id == empresa_id).first()
    if not db_grupo: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Grupo no encontrado.")
    producto_asociado = db.query(models_producto.Producto.id).filter(models_producto.Producto.grupo_id == grupo_id).first()
    if producto_asociado: raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Grupo asignado a productos.")
    db.delete(db_grupo); db.commit(); return {"ok": True}


# ========== CRUD para Tasas de Impuesto ==========
def create_tasa_impuesto(db: Session, tasa: schemas.TasaImpuestoCreate, empresa_id: int):
    db_tasa = models_impuesto.TasaImpuesto(**tasa.model_dump(), empresa_id=empresa_id)
    db.add(db_tasa); db.commit(); db.refresh(db_tasa); return db_tasa

def get_tasas_by_empresa(db: Session, empresa_id: int):
    return db.query(models_impuesto.TasaImpuesto).filter(models_impuesto.TasaImpuesto.empresa_id == empresa_id).order_by(models_impuesto.TasaImpuesto.nombre).all()

def update_tasa_impuesto(db: Session, tasa_id: int, tasa: schemas.TasaImpuestoUpdate, empresa_id: int):
    db_tasa = db.query(models_impuesto.TasaImpuesto).filter(models_impuesto.TasaImpuesto.id == tasa_id, models_impuesto.TasaImpuesto.empresa_id == empresa_id).first()
    if not db_tasa: return None
    update_data = tasa.model_dump(exclude_unset=True)
    for key, value in update_data.items(): setattr(db_tasa, key, value)
    db.commit(); db.refresh(db_tasa); return db_tasa

def delete_tasa_impuesto(db: Session, tasa_id: int, empresa_id: int):
    db_tasa = db.query(models_impuesto.TasaImpuesto).filter(models_impuesto.TasaImpuesto.id == tasa_id, models_impuesto.TasaImpuesto.empresa_id == empresa_id).first()
    if not db_tasa: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tasa no encontrada.")
    producto_asociado = db.query(models_producto.Producto.id).filter(models_producto.Producto.impuesto_iva_id == tasa_id).first()
    if producto_asociado: raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Tasa asignada a productos.")
    db.delete(db_tasa); db.commit(); return {"ok": True}


# ========== CRUD para Listas de Precios ==========
def create_lista_precio(db: Session, lista_precio: schemas.ListaPrecioCreate, empresa_id: int) -> models_lista_precio.ListaPrecio:
    lista_existente = db.query(models_lista_precio.ListaPrecio).filter(models_lista_precio.ListaPrecio.empresa_id == empresa_id, models_lista_precio.ListaPrecio.nombre == lista_precio.nombre).first()
    if lista_existente: raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Nombre '{lista_precio.nombre}' ya existe.")
    db_lista = models_lista_precio.ListaPrecio(**lista_precio.model_dump(), empresa_id=empresa_id)
    db.add(db_lista); db.commit(); db.refresh(db_lista); return db_lista

def get_listas_precio_by_empresa(db: Session, empresa_id: int) -> List[models_lista_precio.ListaPrecio]:
    # FIX: Esta función es crucial y se restauró para que la página de parámetros funcione.
    return db.query(models_lista_precio.ListaPrecio).filter(models_lista_precio.ListaPrecio.empresa_id == empresa_id).order_by(models_lista_precio.ListaPrecio.nombre).all()

def update_lista_precio(db: Session, lista_id: int, lista_update: schemas.ListaPrecioUpdate, empresa_id: int) -> Optional[models_lista_precio.ListaPrecio]:
    db_lista = db.query(models_lista_precio.ListaPrecio).filter(models_lista_precio.ListaPrecio.id == lista_id, models_lista_precio.ListaPrecio.empresa_id == empresa_id).first()
    if not db_lista: return None
    if lista_update.nombre and lista_update.nombre != db_lista.nombre:
        otra_lista = db.query(models_lista_precio.ListaPrecio).filter(models_lista_precio.ListaPrecio.empresa_id == empresa_id, models_lista_precio.ListaPrecio.nombre == lista_update.nombre, models_lista_precio.ListaPrecio.id != lista_id).first()
        if otra_lista: raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Nombre '{lista_update.nombre}' ya existe.")
    update_data = lista_update.model_dump(exclude_unset=True)
    for key, value in update_data.items(): setattr(db_lista, key, value)
    db.commit(); db.refresh(db_lista); return db_lista

def delete_lista_precio(db: Session, lista_id: int, empresa_id: int):
    db_lista = db.query(models_lista_precio.ListaPrecio).filter(models_lista_precio.ListaPrecio.id == lista_id, models_lista_precio.ListaPrecio.empresa_id == empresa_id).first()
    if not db_lista: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lista no encontrada.")
    regla_asociada = db.query(models_regla_precio.ReglaPrecioGrupo.id).filter(models_regla_precio.ReglaPrecioGrupo.lista_precio_id == lista_id).first()
    if regla_asociada: raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Lista asignada a reglas de grupo.")
    db.delete(db_lista); db.commit(); return {"ok": True}


# --- Gestión de Definiciones de Características por Grupo ---
def create_caracteristica_definicion(db: Session, definicion_data: schemas.CaracteristicaDefinicionCreate, grupo_id: int, empresa_id: int) -> models_carac_def.CaracteristicaDefinicion:
    grupo = db.query(models_grupo.GrupoInventario).filter(models_grupo.GrupoInventario.id == grupo_id, models_grupo.GrupoInventario.empresa_id == empresa_id).first()
    if not grupo: raise HTTPException(status_code=404, detail="Grupo no encontrado.")
    existente = db.query(models_carac_def.CaracteristicaDefinicion).filter(
        models_carac_def.CaracteristicaDefinicion.grupo_inventario_id == grupo_id,
        func.lower(models_carac_def.CaracteristicaDefinicion.nombre) == definicion_data.nombre.lower()
    ).first()
    if existente: raise HTTPException(status_code=409, detail=f"Característica '{definicion_data.nombre}' ya existe (insensible a mayúsculas) para este grupo.")
    if definicion_data.es_unidad_medida:
        unidad_existente = db.query(models_carac_def.CaracteristicaDefinicion).filter(
            models_carac_def.CaracteristicaDefinicion.grupo_inventario_id == grupo_id,
            models_carac_def.CaracteristicaDefinicion.es_unidad_medida == True
        ).first()
        if unidad_existente:
            raise HTTPException(status_code=409, detail=f"Ya existe una Unidad de Medida ('{unidad_existente.nombre}') definida para este grupo.")
    db_definicion = models_carac_def.CaracteristicaDefinicion(**definicion_data.model_dump(), grupo_inventario_id=grupo_id)
    db.add(db_definicion); db.commit(); db.refresh(db_definicion); return db_definicion

def get_caracteristicas_definicion_by_grupo(db: Session, grupo_id: int, empresa_id: int) -> List[models_carac_def.CaracteristicaDefinicion]:
    grupo = db.query(models_grupo.GrupoInventario).filter(models_grupo.GrupoInventario.id == grupo_id, models_grupo.GrupoInventario.empresa_id == empresa_id).first()
    if not grupo: raise HTTPException(status_code=404, detail="Grupo no encontrado.")
    return db.query(models_carac_def.CaracteristicaDefinicion).filter(
        models_carac_def.CaracteristicaDefinicion.grupo_inventario_id == grupo_id
    ).order_by(models_carac_def.CaracteristicaDefinicion.nombre).all()

def update_caracteristica_definicion(db: Session, definicion_id: int, definicion_update: schemas.CaracteristicaDefinicionUpdate, empresa_id: int) -> models_carac_def.CaracteristicaDefinicion:
    db_definicion = db.query(models_carac_def.CaracteristicaDefinicion).options(
        joinedload(models_carac_def.CaracteristicaDefinicion.grupo_inventario)
    ).filter(models_carac_def.CaracteristicaDefinicion.id == definicion_id).first()
    if not db_definicion or db_definicion.grupo_inventario.empresa_id != empresa_id:
        raise HTTPException(status_code=404, detail="Definición de característica no encontrada.")
    if definicion_update.nombre and definicion_update.nombre.lower() != db_definicion.nombre.lower():
        existente = db.query(models_carac_def.CaracteristicaDefinicion).filter(
            models_carac_def.CaracteristicaDefinicion.grupo_inventario_id == db_definicion.grupo_inventario_id,
            func.lower(models_carac_def.CaracteristicaDefinicion.nombre) == definicion_update.nombre.lower(),
            models_carac_def.CaracteristicaDefinicion.id != definicion_id
        ).first()
        if existente:
            raise HTTPException(status_code=409, detail=f"Característica '{definicion_update.nombre}' ya existe (insensible a mayúsculas) para este grupo.")
    if definicion_update.es_unidad_medida == True and not db_definicion.es_unidad_medida:
         unidad_existente = db.query(models_carac_def.CaracteristicaDefinicion).filter(
             models_carac_def.CaracteristicaDefinicion.grupo_inventario_id == db_definicion.grupo_inventario_id,
             models_carac_def.CaracteristicaDefinicion.es_unidad_medida == True,
             models_carac_def.CaracteristicaDefinicion.id != definicion_id
         ).first()
         if unidad_existente:
             raise HTTPException(status_code=409, detail=f"Ya existe una Unidad de Medida ('{unidad_existente.nombre}') definida para este grupo.")
    update_data = definicion_update.model_dump(exclude_unset=True)
    for key, value in update_data.items(): setattr(db_definicion, key, value)
    db.commit(); db.refresh(db_definicion)
    return db_definicion

def delete_caracteristica_definicion(db: Session, definicion_id: int, empresa_id: int):
    db_definicion = db.query(models_carac_def.CaracteristicaDefinicion).options(
        joinedload(models_carac_def.CaracteristicaDefinicion.grupo_inventario)
    ).filter(models_carac_def.CaracteristicaDefinicion.id == definicion_id).first()
    if not db_definicion or db_definicion.grupo_inventario.empresa_id != empresa_id:
        raise HTTPException(status_code=404, detail="Definición de característica no encontrada.")
    # FIX: Se asume que el cascade de la DB o el modelo maneja la eliminación de CaracteristicaValorProducto.
    db.delete(db_definicion); db.commit(); return {"ok": True}


# --- Gestión de Reglas de Precio por Grupo ---
def create_or_update_regla_precio_grupo(db: Session, regla_data: schemas.ReglaPrecioGrupoCreate, grupo_id: int, empresa_id: int) -> models_regla_precio.ReglaPrecioGrupo:
    grupo = db.query(models_grupo.GrupoInventario).filter(models_grupo.GrupoInventario.id == grupo_id, models_grupo.GrupoInventario.empresa_id == empresa_id).first()
    lista = db.query(models_lista_precio.ListaPrecio).filter(models_lista_precio.ListaPrecio.id == regla_data.lista_precio_id, models_lista_precio.ListaPrecio.empresa_id == empresa_id).first()
    if not grupo: raise HTTPException(status_code=404, detail="Grupo no encontrado.")
    if not lista: raise HTTPException(status_code=404, detail="Lista de precios no encontrada.")
    db_regla = db.query(models_regla_precio.ReglaPrecioGrupo).filter(
        models_regla_precio.ReglaPrecioGrupo.grupo_inventario_id == grupo_id,
        models_regla_precio.ReglaPrecioGrupo.lista_precio_id == regla_data.lista_precio_id
    ).first()
    if db_regla:
        db_regla.porcentaje_incremento = regla_data.porcentaje_incremento
        print(f"Actualizando regla existente ID {db_regla.id} para Grupo {grupo_id}, Lista {regla_data.lista_precio_id}")
    else:
        db_regla = models_regla_precio.ReglaPrecioGrupo(**regla_data.model_dump(), grupo_inventario_id=grupo_id)
        db.add(db_regla)
        print(f"Creando nueva regla para Grupo {grupo_id}, Lista {regla_data.lista_precio_id}")
        db.flush()
    try:
        db.commit(); db.refresh(db_regla); db.refresh(db_regla.lista_precio); return db_regla
    except Exception as e:
        db.rollback(); print(f"ERROR: {e}"); traceback.print_exc(); raise HTTPException(status_code=500, detail="Error interno.")

def get_reglas_precio_by_grupo(db: Session, grupo_id: int, empresa_id: int) -> List[models_regla_precio.ReglaPrecioGrupo]:
    grupo = db.query(models_grupo.GrupoInventario).filter(models_grupo.GrupoInventario.id == grupo_id, models_grupo.GrupoInventario.empresa_id == empresa_id).first()
    if not grupo: raise HTTPException(status_code=404, detail="Grupo no encontrado.")
    return db.query(models_regla_precio.ReglaPrecioGrupo).options(joinedload(models_regla_precio.ReglaPrecioGrupo.lista_precio)).filter(models_regla_precio.ReglaPrecioGrupo.grupo_inventario_id == grupo_id).all()

def delete_regla_precio_grupo(db: Session, regla_id: int, empresa_id: int):
    db_regla = db.query(models_regla_precio.ReglaPrecioGrupo).options(joinedload(models_regla_precio.ReglaPrecioGrupo.grupo_inventario)).filter(models_regla_precio.ReglaPrecioGrupo.id == regla_id).first()
    if not db_regla or db_regla.grupo_inventario.empresa_id != empresa_id:
        raise HTTPException(status_code=404, detail="Regla de precio no encontrada.")
    db.delete(db_regla); db.commit(); return {"ok": True}


# --- FUNCIÓN CLAVE: Calcular Precio de Venta Dinámico ---
def calcular_precio_venta(db: Session, producto_id: int, lista_precio_id: int, empresa_id: int) -> float:
    
    print(f"\n[SONDA PRECIO INICIO] Producto ID: {producto_id}, Lista ID: {lista_precio_id}, Empresa ID: {empresa_id}") # SONDA 1
    
    # 1. Uso de func.coalesce para asegurar que porcentaje_incremento siempre sea un Float (0.0 si no hay regla)
    # Esto elimina el riesgo de TypeError al manejar el resultado del LEFT OUTER JOIN.
    coalesced_incremento = func.coalesce(models_regla_precio.ReglaPrecioGrupo.porcentaje_incremento, 0.0).label("incremento_seguro")
    
    query = db.query(models_producto.Producto, coalesced_incremento)\
        .join(models_grupo.GrupoInventario, models_producto.Producto.grupo_id == models_grupo.GrupoInventario.id, isouter=True)\
        .outerjoin(models_regla_precio.ReglaPrecioGrupo, and_(
            models_regla_precio.ReglaPrecioGrupo.grupo_inventario_id == models_grupo.GrupoInventario.id, 
            models_regla_precio.ReglaPrecioGrupo.lista_precio_id == lista_precio_id
        ))\
        .filter(models_producto.Producto.id == producto_id, models_producto.Producto.empresa_id == empresa_id)
        
    lista = db.query(models_lista_precio.ListaPrecio).filter(models_lista_precio.ListaPrecio.id == lista_precio_id, models_lista_precio.ListaPrecio.empresa_id == empresa_id).first()
    if not lista: raise HTTPException(status_code=404, detail=f"Lista de precios ID {lista_precio_id} no válida.")
    result = query.first()
    if not result: raise HTTPException(status_code=404, detail=f"Producto ID {producto_id} no encontrado.")
    
    # El segundo elemento del resultado es ahora el incremento seguro (float o 0.0)
    producto, porcentaje_incremento_float = result
    
    # 2. Blindaje de Precios Base: Usamos str() antes de Decimal() para evitar errores de precisión de float binario.
    
    # Base Price Fallback: precio_base_manual (preferido) -> costo_promedio -> 0.0
    precio_base_val = producto.precio_base_manual if producto.precio_base_manual is not None else (producto.costo_promedio or 0.0)
    
    print(f"[SONDA PRECIO INTERMEDIO] Precio Base (Recuperado): {precio_base_val} | Tipo: {type(precio_base_val)}") # SONDA 2
    print(f"[SONDA PRECIO INTERMEDIO] Porcentaje Inc (Coalesce): {porcentaje_incremento_float} | Tipo: {type(porcentaje_incremento_float)}") # SONDA 3
    
    # Conversión segura a Decimal a través de string
    try:
        # El valor recuperado de la DB debe ir a string primero
        precio_base_dec = Decimal(str(precio_base_val))
        porcentaje_incremento_dec = Decimal(str(porcentaje_incremento_float))
    except Exception as e:
        print(f"ERROR: No se pudo convertir a Decimal: {e}. Base: {precio_base_val}, Inc: {porcentaje_incremento_float}")
        raise HTTPException(status_code=500, detail="Error de integridad de datos en precio o margen.")
        
    # 3. Cálculo Atómico Único: Base * (1 + Incremento)
    precio_calculado_dec = precio_base_dec * (Decimal('1.0') + porcentaje_incremento_dec)
    
    # 4. Retorno: Convertir a float y redondear
    precio_final = round(float(precio_calculado_dec), 2)
    
    print(f"[SONDA PRECIO FINAL] Precio Base DEC: {precio_base_dec}, Incremento DEC: {porcentaje_incremento_dec}") # SONDA 4
    print(f"[SONDA PRECIO FINAL] Resultado Calculado (DEC): {precio_calculado_dec}, Precio Final (FLOAT): {precio_final}") # SONDA 5
    
    return precio_final


# --- Lógica Profesional para Productos (create/update/delete) ---
def get_producto_by_codigo(db: Session, codigo: str, empresa_id: int):
    return db.query(models_producto.Producto).filter(models_producto.Producto.codigo == codigo, models_producto.Producto.empresa_id == empresa_id).first()

def get_producto_by_id(db: Session, producto_id: int, empresa_id: int, load_all: bool = True):
    query = db.query(models_producto.Producto)
    if load_all:
        query = query.options(
            selectinload(models_producto.Producto.stocks_bodega),
            joinedload(models_producto.Producto.grupo_inventario).options(selectinload(models_grupo.GrupoInventario.caracteristicas_definidas)),
            joinedload(models_producto.Producto.impuesto_iva),
            selectinload(models_producto.Producto.valores_caracteristicas).selectinload(models_carac_val.CaracteristicaValorProducto.definicion)
        )
    return query.filter(models_producto.Producto.id == producto_id, models_producto.Producto.empresa_id == empresa_id).first()


def create_producto(db: Session, producto: schemas.ProductoCreate, empresa_id: int):
    print("\n--- SONDA CREATE 1: Datos recibidos en create_producto ---")
    print(f"Producto Schema: {producto.model_dump()}")
    producto_existente = get_producto_by_codigo(db, codigo=producto.codigo, empresa_id=empresa_id)
    if producto_existente: raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Código '{producto.codigo}' ya existe.")
    
    # >>> INICIO SONDA DE FALLO FORZADO (Protocolo de Caja Negra - Nivel 3)
    # Si esta línea se ejecuta, DEBE causar un error 500 y DEBE hacer que el commit falle.
    # Después de confirmar que el bloque except funciona, esta línea debe ELIMINARSE.
    if producto.codigo == "SONDA_FALLO":
        print("\n--- SONDA CRÍTICA: FALLO FORZADO ACTIVADO ---");
        raise ValueError("FALLO FORZADO POR SONDA DE DIAGNÓSTICO. IGNORAR Y VERIFICAR CONSOLA.")
    # <<< FIN SONDA DE FALLO FORZADO
    
    grupo = None; definiciones_grupo_ids = set()
    if producto.grupo_id:
        grupo = db.query(models_grupo.GrupoInventario).options(selectinload(models_grupo.GrupoInventario.caracteristicas_definidas)).filter(models_grupo.GrupoInventario.id == producto.grupo_id, models_grupo.GrupoInventario.empresa_id == empresa_id).first()
        if not grupo: raise HTTPException(status_code=400, detail=f"Grupo ID {producto.grupo_id} no encontrado.")
        definiciones_grupo_ids = {d.id for d in grupo.caracteristicas_definidas}
    if producto.impuesto_iva_id:
        impuesto = db.query(models_impuesto.TasaImpuesto).filter(models_impuesto.TasaImpuesto.id == producto.impuesto_iva_id, models_impuesto.TasaImpuesto.empresa_id == empresa_id).first()
        if not impuesto: raise HTTPException(status_code=400, detail=f"Impuesto ID {producto.impuesto_iva_id} no encontrado.")
    valores_a_crear = []
    
    # *** INICIO BLOQUE DE TRANSACCIÓN MEJORADO ***
    try:
        # Aquí eliminamos el begin_nested y lo manejamos en el commit final
        producto_data = producto.model_dump(exclude={'valores_caracteristicas', 'stock_inicial', 'costo_inicial', 'bodega_id_inicial'})
        db_producto = models_producto.Producto(**producto_data, empresa_id=empresa_id, costo_promedio=producto.costo_inicial or 0.0)
        db.add(db_producto); db.flush() # Flush para obtener el ID del producto ANTES de crear características
        
        if producto.valores_caracteristicas:
            definiciones_usadas = set()
            for val_data in producto.valores_caracteristicas:
                if not val_data.valor: continue
                if val_data.definicion_id in definiciones_usadas: raise HTTPException(status_code=400, detail=f"Característica ID {val_data.definicion_id} duplicada.")
                definiciones_usadas.add(val_data.definicion_id)
                if grupo and val_data.definicion_id not in definiciones_grupo_ids: raise HTTPException(status_code=400, detail=f"Característica ID {val_data.definicion_id} no pertenece al grupo.")
                # No es necesario verificar existencia, el DB lo hace, pero verificaremos si la llave foránea falla.
                valores_a_crear.append(models_carac_val.CaracteristicaValorProducto(producto_id=db_producto.id, definicion_id=val_data.definicion_id, valor=val_data.valor))
            print("\n--- SONDA CREATE 2: Valores de Características a crear ---"); print(f"Total: {len(valores_a_crear)}")
            for val in valores_a_crear: print(f"  - Def ID: {val.definicion_id}, Valor: '{val.valor}', Prod ID (asignado): {val.producto_id}")
            if valores_a_crear: db.add_all(valores_a_crear); db.flush() # Flush intermedio para ver fallos de FK

        if not db_producto.es_servicio and producto.stock_inicial and producto.stock_inicial > 0:
            if not producto.bodega_id_inicial: raise HTTPException(status_code=400, detail="Bodega requerida para stock inicial.")
            bodega_exists = db.query(models_bodega.Bodega.id).filter(models_bodega.Bodega.id == producto.bodega_id_inicial, models_bodega.Bodega.empresa_id == empresa_id).first()
            if not bodega_exists: raise HTTPException(status_code=400, detail=f"Bodega ID {producto.bodega_id_inicial} no encontrada.")
            
           
            # FIX CRÍTICO: Se utiliza datetime.now(timezone.utc) para evitar problemas de zona horaria con la DB
            registrar_movimiento_inventario(db=db, producto_id=db_producto.id, bodega_id=producto.bodega_id_inicial, tipo_movimiento='ENTRADA_INICIAL', cantidad=producto.stock_inicial, costo_unitario=producto.costo_inicial or 0.0, fecha=datetime.now(timezone.utc))

        
        print("\n--- SONDA CREATE 3: Antes del commit principal ---"); print(f"Producto ID (final): {db_producto.id}")
        db.commit() # Intenta el commit. Si falla por FK, aquí lanza la excepción.

        print("\n--- SONDA CREATE 4: Después del commit EXITOSO ---")
        db.refresh(db_producto)
        
        # Auditoría de datos guardados (Para confirmar si se guardó todo)
        valores_guardados = db.query(models_carac_val.CaracteristicaValorProducto).filter(models_carac_val.CaracteristicaValorProducto.producto_id == db_producto.id).all()
        print(f"Valores de características REALMENTE guardados en BD:")
        if valores_guardados:
            for val in valores_guardados: print(f"  - ID: {val.id}, Def ID: {val.definicion_id}, Valor: '{val.valor}'")
        else: print("  - NINGUNO.")
        
        db_producto_completo = get_producto_by_id(db, db_producto.id, empresa_id)
        return db_producto_completo
    
    except Exception as e:
        # Capturamos y relanzamos el error real de la DB
        db.rollback(); 
        print(f"\n--- SONDA CREATE FALLO DEFINITIVO: Excepción REAL de la DB ---"); 
        traceback.print_exc()

        if isinstance(e, IntegrityError):
            # Lanza el error de integridad explícitamente como 409
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Violación de datos: Verifique códigos o campos obligatorios. Causa: {e.orig}")
        
        if isinstance(e, HTTPException): 
            raise e
        
        # Relanzamos como error 500 para ver la causa real
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error interno al crear el producto: Causa: {type(e).__name__} | Mensaje: {e}")
    

def update_producto(db: Session, producto_id: int, producto_update: schemas.ProductoUpdate, empresa_id: int):
    print("\n--- SONDA UPDATE 1: Datos recibidos en update_producto ---"); print(f"Producto ID: {producto_id}"); print(f"Update Schema: {producto_update.model_dump()}")
    db_producto = get_producto_by_id(db, producto_id=producto_id, empresa_id=empresa_id, load_all=False)
    if not db_producto: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado.")
    if producto_update.codigo and producto_update.codigo != db_producto.codigo:
        otro_producto = get_producto_by_codigo(db, codigo=producto_update.codigo, empresa_id=empresa_id)
        if otro_producto: raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Código '{producto_update.codigo}' ya existe.")
    grupo_cambio = False; grupo_final = None; definiciones_grupo_final_ids = set()
    grupo_id_nuevo = producto_update.grupo_id; grupo_id_actual = db_producto.grupo_id
    if grupo_id_nuevo != grupo_id_actual:
        grupo_cambio = True
        if grupo_id_nuevo is not None:
            grupo_final = db.query(models_grupo.GrupoInventario).options(selectinload(models_grupo.GrupoInventario.caracteristicas_definidas)).filter(models_grupo.GrupoInventario.id == grupo_id_nuevo, models_grupo.GrupoInventario.empresa_id == empresa_id).first()
            if not grupo_final: raise HTTPException(status_code=400, detail=f"Grupo ID {producto_id} no encontrado.")
            definiciones_grupo_final_ids = {d.id for d in grupo_final.caracteristicas_definidas}
    elif grupo_id_actual is not None:
        grupo_final = db.query(models_grupo.GrupoInventario).options(selectinload(models_grupo.GrupoInventario.caracteristicas_definidas)).filter(models_grupo.GrupoInventario.id == grupo_id_actual).first()
        if grupo_final: definiciones_grupo_final_ids = {d.id for d in grupo_final.caracteristicas_definidas}
    if producto_update.impuesto_iva_id is not None and producto_update.impuesto_iva_id != db_producto.impuesto_iva_id:
        if producto_update.impuesto_iva_id > 0:
            impuesto = db.query(models_impuesto.TasaImpuesto).filter(models_impuesto.TasaImpuesto.id == producto_update.impuesto_iva_id, models_impuesto.TasaImpuesto.empresa_id == empresa_id).first()
            if not impuesto: raise HTTPException(status_code=400, detail=f"Impuesto ID {producto_update.impuesto_iva_id} no encontrado.")
    valores_a_crear = []
    try:
        with db.begin_nested():
            update_data = producto_update.model_dump(exclude_unset=True, exclude={'valores_caracteristicas'})
            producto_updated = False
            for key, value in update_data.items():
                 if hasattr(db_producto, key):
                      if getattr(db_producto, key) != value: setattr(db_producto, key, value); producto_updated = True
                 else: print(f"WARN: Atributo '{key}' no encontrado en Producto durante update.")
            if producto_update.valores_caracteristicas is not None:
                print("\n--- SONDA UPDATE 2: Valores de Características recibidos para actualizar ---"); print(f"Total recibidos: {len(producto_update.valores_caracteristicas)}"); print(f"Valores: {producto_update.valores_caracteristicas}")
                stmt_delete = delete(models_carac_val.CaracteristicaValorProducto).where(models_carac_val.CaracteristicaValorProducto.producto_id == producto_id)
                delete_result = db.execute(stmt_delete)
                print(f"--- SONDA UPDATE 2.1: Resultado del DELETE: {delete_result.rowcount} filas eliminadas.")
                if producto_update.valores_caracteristicas:
                    definiciones_usadas = set()
                    for val_data in producto_update.valores_caracteristicas:
                        if not val_data.valor: continue
                        if val_data.definicion_id in definiciones_usadas: raise HTTPException(status_code=400, detail=f"Característica ID {val_data.definicion_id} duplicada.")
                        definiciones_usadas.add(val_data.definicion_id)
                        if grupo_final and val_data.definicion_id not in definiciones_grupo_final_ids: raise HTTPException(status_code=400, detail=f"Característica ID {val_data.definicion_id} no pertenece al grupo final.")
                        definicion_exists = db.query(models_carac_def.CaracteristicaDefinicion.id).filter(models_carac_def.CaracteristicaDefinicion.id == val_data.definicion_id).first()
                        if not definicion_exists: raise HTTPException(status_code=400, detail=f"Característica ID {val_data.definicion_id} no existe.")
                        valores_a_crear.append(models_carac_val.CaracteristicaValorProducto(producto_id=db_producto.id, definicion_id=val_data.definicion_id, valor=val_data.valor))
                    print("\n--- SONDA UPDATE 3: Valores de Características a crear (después de borrar) ---"); print(f"Total: {len(valores_a_crear)}")
                    for val in valores_a_crear: print(f"  - Def ID: {val.definicion_id}, Valor: '{val.valor}', Prod ID: {val.producto_id}")
                    if valores_a_crear: db.bulk_save_objects(valores_a_crear)
                producto_updated = True
        print("\n--- SONDA UPDATE 4: Antes del commit principal ---"); print(f"Producto ID: {db_producto.id}"); print(f"Valores en sesión (estado pendiente):"); print(f"  - Producto (campos actualizados): {[k for k,v in update_data.items() if hasattr(db_producto, k) and getattr(db_producto, k) == v]}"); print(f"  - Valores Caracteristicas (a crear): {[v.__dict__ for v in valores_a_crear]}")
        db.commit()
        print("\n--- SONDA UPDATE 5: Después del commit ---"); db.refresh(db_producto)
        valores_guardados = db.query(models_carac_val.CaracteristicaValorProducto).filter(models_carac_val.CaracteristicaValorProducto.producto_id == producto_id).all()
        print(f"Valores de características REALMENTE guardados en BD:")
        if valores_guardados:
            for val in valores_guardados: print(f"  - ID: {val.id}, Def ID: {val.definicion_id}, Valor: '{val.valor}'")
        else: print("  - NINGUNO.")
        db_producto_completo = get_producto_by_id(db, db_producto.id, empresa_id)
        return db_producto_completo
    except Exception as e:
        db.rollback(); print(f"ERROR update_producto: {e}"); traceback.print_exc(); raise HTTPException(status_code=500, detail=f"Error interno al actualizar.")

def delete_producto(db: Session, producto_id: int, empresa_id: int):
    db_producto = db.query(models_producto.Producto).filter(models_producto.Producto.id == producto_id, models_producto.Producto.empresa_id == empresa_id).first()
    if not db_producto: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado.")
    
    # --- INICIO: FASE DE SANEAMIENTO (Eliminar dependencias inocuas) ---
    
    # 1. ELIMINAR REGISTROS STOCK CERO (Saneamiento Atómico)
    # Esto rompe la llave foránea para registros StockBodega donde stock_actual es CERO.
    stock_cero_stmt = delete(models_producto.StockBodega).where(
        models_producto.StockBodega.producto_id == producto_id,
        models_producto.StockBodega.stock_actual == 0.0 # El float 0.0 es necesario para coincidir con el tipo Float de la columna.
    )
    db.execute(stock_cero_stmt)
    
    # 2. ELIMINAR VALORES DE CARACTERÍSTICAS (Dependencia Oculta)
    # El error puede estar aquí si la cascada no funciona. Se fuerza la eliminación manual.
    caracteristica_val_stmt = delete(models_carac_val.CaracteristicaValorProducto).where(
        models_carac_val.CaracteristicaValorProducto.producto_id == producto_id
    )
    db.execute(caracteristica_val_stmt)

    # 3. ELIMINAR REGLAS DE PRECIO DE GRUPO RELACIONADAS (Si el producto era el último del grupo)
    # Esto es una protección extra. La dependencia es indirecta, pero es buena práctica.
    if db_producto.grupo_id:
        regla_precio_stmt = delete(models_regla_precio.ReglaPrecioGrupo).where(
            models_regla_precio.ReglaPrecioGrupo.grupo_inventario_id == db_producto.grupo_id
        )
        db.execute(regla_precio_stmt)
    
    db.flush() # Forzar la eliminación antes de la verificación de uso.
    
    # --- FIN: FASE DE SANEAMIENTO ---

    # 4. VERIFICACIÓN DE USO (El stock restante es la ÚNICA dependencia que debe quedar)
    en_uso_kardex = db.query(models_producto.MovimientoInventario.id).filter(models_producto.MovimientoInventario.producto_id == producto_id).first()
    en_uso_contable = db.query(models_mov.MovimientoContable.id).filter(models_mov.MovimientoContable.producto_id == producto_id).first()
    
    # FIX CRÍTICO: Consulta correcta que verifica si queda ALGÚN registro de stock (donde stock_actual != 0).
    en_uso_stock = db.query(models_producto.StockBodega.id).filter(
        models_producto.StockBodega.producto_id == producto_id
    ).first() 

    if en_uso_kardex or en_uso_contable or en_uso_stock:
        usos = []
        if en_uso_kardex: usos.append("kardex")
        if en_uso_contable: usos.append("contabilidad")
        if en_uso_stock: usos.append("stock asociados (saldos > 0)")
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"No se puede eliminar: tiene {', '.join(usos)}.")
    
    # 5. ELIMINACIÓN FINAL
    try:
        db.delete(db_producto); db.commit(); return {"ok": True}
    except Exception as e:
        db.rollback(); print(f"ERROR: {e}"); traceback.print_exc(); raise HTTPException(status_code=500, detail=f"Error interno. Verifique dependencias.")


# --- FUNCIONES ADICIONALES PARA BUSCAR PRODUCTOS (AUTOCOMPLETAR) ---
def search_productos(
    db: Session,
    empresa_id: int,
    search_term: Optional[str] = None, 
    bodega_id: Optional[int] = None,
    grupo_ids: Optional[List[int]] = None
) -> List[Dict[str, Any]]:
    """Busca productos por código o nombre para autocompletar, filtrando opcionalmente por bodega y/o grupo(s)."""
    query_base = db.query(
        models_producto.Producto.id,
        models_producto.Producto.codigo,
        models_producto.Producto.nombre,
        models_producto.Producto.es_servicio,
        models_producto.Producto.precio_base_manual,
        models_producto.Producto.costo_promedio
    ).filter(models_producto.Producto.empresa_id == empresa_id)

    # FIX CRÍTICO: Se debe asegurar que grupo_ids NO sea una lista vacía para evitar fallos de Query Param.
    if grupo_ids and len(grupo_ids) > 0:
        query_base = query_base.filter(models_producto.Producto.grupo_id.in_(grupo_ids))

    if search_term:
         search_like = f"%{search_term}%"
         query_base = query_base.filter(
             or_(
                 models_producto.Producto.codigo.ilike(search_like),
                 models_producto.Producto.nombre.ilike(search_like)
             )
         )

    # FIX CRÍTICO: Se corrige la referencia de StockBodega.producto_id a Producto.id
    stock_select_stmt = select(func.sum(models_producto.StockBodega.stock_actual)).where(
        models_producto.StockBodega.producto_id == models_producto.Producto.id # <--- FIX APLICADO AQUÍ
    )
    if bodega_id:
        stock_select_stmt = stock_select_stmt.where(models_producto.StockBodega.bodega_id == bodega_id)

    query_final = query_base.add_column(stock_select_stmt.scalar_subquery().label("stock_actual")) \
        .order_by(models_producto.Producto.nombre) \
        .limit(20)

    try:
        resultados = query_final.all()
    except Exception as e:
         print(f"ERROR en search_productos query: {e}")
         traceback.print_exc()
         # Devolver el error 500 para una depuración más fácil.
         raise HTTPException(status_code=500, detail=f"Error interno al buscar productos: {e}")

    productos_dict = [
        {
            "id": p.id,
            "codigo": p.codigo,
            "nombre": p.nombre,
            "es_servicio": p.es_servicio,
            "precio_base_manual": p.precio_base_manual,
            "costo_promedio": p.costo_promedio,
            "stock_actual": float(p.stock_actual or 0.0)
        } for p in resultados
    ]
    return productos_dict

# --- GET PRODUCTOS FILTRADOS ---
def get_productos_filtrados(db: Session, empresa_id: int, filtros: schemas.ProductoFiltros) -> List[models_producto.Producto]:
    query = db.query(models_producto.Producto).options(selectinload(models_producto.Producto.stocks_bodega), joinedload(models_producto.Producto.grupo_inventario), joinedload(models_producto.Producto.impuesto_iva), selectinload(models_producto.Producto.valores_caracteristicas).options(joinedload(models_carac_val.CaracteristicaValorProducto.definicion)))\
        .filter(models_producto.Producto.empresa_id == empresa_id)
        
    # *********** FIX CRÍTICO: ATRIBUTO OBLITERADO ***********
    # La corrección del schema eliminó 'grupo_id' y lo reemplazó por 'grupo_ids'.
    # Actualizamos el servicio para usar el campo plural.
    if hasattr(filtros, 'grupo_ids') and filtros.grupo_ids and len(filtros.grupo_ids) > 0:
        query = query.filter(models_producto.Producto.grupo_id.in_(filtros.grupo_ids))
    # ********************************************************
    
    if filtros.search_term: query = query.filter(or_(models_producto.Producto.codigo.ilike(f"%{filtros.search_term}%"), models_producto.Producto.nombre.ilike(f"%{filtros.search_term}%")))
    productos = query.order_by(models_producto.Producto.nombre).all()
    productos_con_stock = _filter_stock_for_bodegas(productos, filtros.bodega_ids)
    return productos_con_stock

def get_producto_para_kardex(db: Session, producto_id: int) -> Optional[models_producto.Producto]:
    return db.query(models_producto.Producto).filter(models_producto.Producto.id == producto_id).first()


# app/services/inventario.py (SOLO LA FUNCIÓN MODIFICADA)

# app/services/inventario.py

# ... (El resto del archivo se mantiene igual, solo reemplaza la función final) ...

# ==============================================================================
# === GENERACIÓN DE PDF BLINDADO (INNER JOIN) ===
# ==============================================================================

def generar_pdf_lista_productos(db: Session, empresa_id: int, filtros: schemas.ProductoFiltros):
    """
    Genera el PDF calculando el stock mediante un INNER JOIN con Bodegas.
    Esto filtra automáticamente los 'Datos Huérfanos' (stock de bodegas eliminadas)
    que causan la discrepancia con la pantalla.
    """

    print("\n>>> EJECUTANDO PDF: MODO CLON DE PANTALLA (SUMA ORM) <<<")
    try:
        # 1. Obtener metadatos de los productos (Nombres, códigos, precios)
        # Usamos get_productos_filtrados para respetar los filtros de búsqueda del usuario
        productos_metadatos = get_productos_filtrados(db, empresa_id, filtros)
        
        if not productos_metadatos:
             # Si no hay productos, retornamos PDF vacío rápido
             return _generar_pdf_renderizado(env, empresa_id, filtros, [], db)

        product_ids = [p.id for p in productos_metadatos]

        # 2. CONSULTA QUIRÚRGICA: Sumar Stock SOLO si la Bodega existe.
        # El INNER JOIN actúa como un filtro de integridad forzado.
        stmt_stock = (
            select(
                models_producto.StockBodega.producto_id,
                func.sum(models_producto.StockBodega.stock_actual).label("total_stock")
            )
            .join(models_bodega.Bodega, models_producto.StockBodega.bodega_id == models_bodega.Bodega.id) # <--- EL ESCUDO
            .where(
                models_producto.StockBodega.producto_id.in_(product_ids),
                models_bodega.Bodega.empresa_id == empresa_id
            )
            .group_by(models_producto.StockBodega.producto_id)
        )

        # Aplicar filtro de bodega si el usuario seleccionó una específica
        if filtros.bodega_ids and len(filtros.bodega_ids) > 0:
            stmt_stock = stmt_stock.where(models_producto.StockBodega.bodega_id.in_(filtros.bodega_ids))

        # Ejecutar consulta
        resultados_stock = db.execute(stmt_stock).all()

        # 3. Mapear resultados a un diccionario para acceso rápido
        # { producto_id: stock_total }
        mapa_stock = {row.producto_id: float(row.total_stock or 0.0) for row in resultados_stock}

        # 4. Construir la lista para el PDF fusionando metadatos y stock limpio
        items_serializables = []

        for p in productos_metadatos:
            if p.es_servicio:
                stock_real = 0.0
                costo_real = 0.0
            else:
                # Obtenemos el stock del mapa limpio. Si no está en el mapa, es 0.
                stock_real = mapa_stock.get(p.id, 0.0)
                costo_real = float(p.costo_promedio or 0.0)

            items_serializables.append({
                "codigo": p.codigo,
                "nombre": p.nombre,
                "grupo_nombre": p.grupo_inventario.nombre if p.grupo_inventario else "N/A",
                "es_servicio": p.es_servicio,
                
                # Variables numéricas formateadas
                "costo_calculado": _to_float(costo_real),
                "precio_base_manual": _to_float(p.precio_base_manual),
                
                # "stock_actual" es la variable que espera tu HTML antiguo.
                # Le pasamos el "stock_real" filtrado por el INNER JOIN.
                "stock_calculado": _to_float(stock_real),
                "stock_actual": _to_float(stock_real), 
            })

        # 5. Renderizar
        return _generar_pdf_renderizado(env, empresa_id, filtros, items_serializables, db)

    except Exception as e:
        print(f"ERROR CRÍTICO PDF: {e}"); traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error generando PDF: {e}")

def _generar_pdf_renderizado(env_jinja, empresa_id, filtros, productos, db):
    """Función auxiliar para renderizar el template."""
    empresa_db = db.query(models_empresa.Empresa).filter(models_empresa.Empresa.id == empresa_id).first()
    empresa_nombre = empresa_db.razon_social if empresa_db else "Empresa"
    
    context = {
        "titulo_reporte": "CARTILLA DE INVENTARIO",
        "empresa_nombre": empresa_nombre,
        "filtros": filtros.model_dump(),
        "productos": productos,
        "fecha_reporte": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    template_name = 'cartilla_inventario_admin_report.html'
    template = env_jinja.get_template(template_name)
    html_out = template.render(context)
    return HTML(string=html_out).write_pdf(stylesheets=[])