# app/services/inventario.py (Versión 100% Consolidada y Corregida)
# Nota: Este archivo contiene lógica de inventario, pero se respeta su contenido
# para la funcionalidad de utilidades, añadiendo la función faltante.

from sqlalchemy.orm import Session, selectinload, joinedload, contains_eager, aliased
from sqlalchemy import func, and_, case, or_, inspect, delete, select, cast, String as SAString, DECIMAL
from fastapi import HTTPException, status
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, date, time
from decimal import Decimal, ROUND_HALF_UP # Asegurar Decimal y ROUND_HALF_UP para costos
import traceback
import locale

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
    empresa as models_empresa,
    plan_cuenta as models_puc,
    tipo_documento as models_tipo_doc,
    aplicacion_pago as models_aplicacion,
    concepto_favorito as models_concepto,
    usuario as models_usuario,
    centro_costo as models_cc,
    log_operacion as models_log,
    # FIX CRÍTICO: Modelos de Plantilla añadidos para inspección
    plantilla_maestra as models_plantilla_maestra, # <--- AÑADIDO
    plantilla_detalle as models_plantilla_detalle, # <--- AÑADIDO
)

# --- Importaciones de Schemas y Servicios NECESARIAS ---
from ..schemas import inventario as schemas
from ..schemas import traslado_inventario as schemas_traslado
from ..schemas import documento as schemas_doc # FIX: Necesario para DocumentoCreate
from ..schemas import diagnostico as diagnostico_schemas # Importación de Schemas
from ..schemas import tipo_documento as schemas_tipo_doc # Se asume necesario para get_tipos_documento_por_empresa
from ..services import documento as service_documento # FIX: Necesario para create_documento
from ..services import tipo_documento as service_tipo_documento # Necesario para validación de tipo doc


# app/services/diagnostico.py (Añadir al final del archivo)
# Asegúrate de que los siguientes modelos estén importados al inicio del archivo:
from ..models import tercero as models_tercero
from ..models import plan_cuenta as models_puc
from ..models import centro_costo as models_cc
from ..models import tipo_documento as models_tipo_doc
from ..models import usuario as models_usuario
from ..models import documento as models_doc 
from ..models import movimiento_contable as models_mov 
from ..models import aplicacion_pago as models_aplicacion 
from ..models import concepto_favorito as models_concepto
from ..schemas import diagnostico as diagnostico_schemas # CRÍTICO


# ========== Funciones de Movimiento (CRÍTICAS) - Movidas al inicio ==========

from ..models import consumo_registros as models_consumo

def contar_registros_por_empresa(db: Session) -> List[diagnostico_schemas.ConteoResult]:
    """
    Cuenta el total de registros contables (movimientos) NO anulados para cada empresa 
    y lo compara con su límite. También obtiene saldos de bolsas y recargas.
    """
    try:
        # 1. Subconsulta para contar MOVIMIENTOS CONTABLES por empresa
        conteo_registros_por_empresa = (
            db.query(
                models_doc.Documento.empresa_id.label("empresa_id"),
                func.count(models_mov.MovimientoContable.id).label("total_registros")
            )
            .join(models_mov.MovimientoContable, models_mov.MovimientoContable.documento_id == models_doc.Documento.id)
            .filter(models_doc.Documento.anulado == False)
            .group_by(models_doc.Documento.empresa_id)
            .subquery()
        )

        # 2. Consulta principal que une empresas con el conteo
        resultados = db.query(
            models_empresa.Empresa.id,
            models_empresa.Empresa.razon_social,
            models_empresa.Empresa.nit, # <--- AÑADIDO
            models_empresa.Empresa.limite_registros,
            conteo_registros_por_empresa.c.total_registros
        ).outerjoin(
            conteo_registros_por_empresa,
            models_empresa.Empresa.id == conteo_registros_por_empresa.c.empresa_id
        ).order_by(models_empresa.Empresa.razon_social).all()

        # 3. Consultas Agregadas para Bolsas y Recargas (Eficiente)
        # Sumar Bolsas Vigentes
        bolsas_sub = (
            db.query(
                models_consumo.BolsaExcedente.empresa_id, 
                func.sum(models_consumo.BolsaExcedente.cantidad_disponible)
            )
            .filter(models_consumo.BolsaExcedente.estado == 'VIGENTE')
            .group_by(models_consumo.BolsaExcedente.empresa_id)
            .all()
        )
        bolsas_dict = {reg[0]: (reg[1] or 0) for reg in bolsas_sub}

        # Sumar Recargas Vigentes
        recargas_sub = (
            db.query(
                models_consumo.RecargaAdicional.empresa_id, 
                func.sum(models_consumo.RecargaAdicional.cantidad_disponible)
            )
            .filter(models_consumo.RecargaAdicional.estado == 'VIGENTE')
            .group_by(models_consumo.RecargaAdicional.empresa_id)
            .all()
        )
        recargas_dict = {reg[0]: (reg[1] or 0) for reg in recargas_sub}

        # 4. Formateo al Schema de respuesta
        lista_conteo = []
        for id, razon_social, nit, limite, total_registros in resultados: # <--- Unpack update
            total_bolsa = bolsas_dict.get(id, 0)
            total_recarga = recargas_dict.get(id, 0)
            
            lista_conteo.append(diagnostico_schemas.ConteoResult(
                empresa_id=id,
                nombre_empresa=razon_social,
                nit=nit, # <--- Pass NIT
                total_registros=total_registros or 0,
                limite_registros=limite, # Pydantic accepts None now
                bolsa_excedente_total=total_bolsa,
                recargas_disponibles=total_recarga
            ))

        return lista_conteo

    except Exception as e:
        db.rollback()
        print(f"Error CRÍTICO en contar_registros_por_empresa: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno al calcular el conteo de registros.")


# Asegúrate de importar esto en la parte superior si no existe: 
# from sqlalchemy import func, cast, String as SAString

# app/services/diagnostico.py (Función COMPLETA y FINAL)

# app/services/diagnostico.py (Función COMPLETA y FINAL)

def buscar_id_por_llave_natural(db: Session, request: diagnostico_schemas.BusquedaInversaRequest) -> diagnostico_schemas.BusquedaInversaResponse:
    """
    Busca el ID interno de un registro maestro.

    SOLUCIÓN FINAL: Saneamiento robusto con funciones de string de SQLAlchemy para 
    compatibilidad multi-DB, asegurando que se ignore el formato (puntos, guiones, DV).
    """
    # CRÍTICO: Estandarización de la entrada para eliminar el error 400
    busqueda_tipo = request.tipoBusqueda.lower().replace(" ", "_")
    valor1 = request.valor1
    empresa_id = request.empresaId

    db_item = None

    try:

        if busqueda_tipo == "tercero_por_nit":
            # 1. Saneamiento del valor de entrada (solo dígitos)
            #    Esto elimina todo, incluido el DV, si el usuario lo pone.
            valor1_saneado = ''.join(filter(str.isdigit, valor1))

            # 2. Saneamiento en la base de datos (Compatible con la mayoría de los SQL)
            #    Eliminamos los puntos y guiones de la columna 'nit' en la BD antes de comparar.
            #    Se usa CAST/TRIM para asegurar que la comparación sea de string contra string.
            nit_columna_saneada = func.trim(
                func.replace(func.replace(cast(models_tercero.Tercero.nit, SAString), '.', ''), '-', '')
            )
            
            # Si su base de datos NO tiene el DV separado (como lo hace el modelo) y el NIT
            # lo incluye (ej: 94280797-0), la consulta fallará. 
            # Si el valor es de longitud diferente, el saneamiento de REGEXP_REPLACE era mejor, 
            # pero asumiremos que el error es por el formato simple.

            db_item = db.query(models_tercero.Tercero)\
                        .filter(
                            # Búsqueda insensible a mayúsculas/minúsculas y formato de puntos/guiones
                            func.lower(nit_columna_saneada) == func.lower(valor1_saneado),
                            models_tercero.Tercero.empresa_id == empresa_id
                        )\
                        .first()

        elif busqueda_tipo == "cuenta_por_codigo":
            # FIX: Aplicar func.lower() a ambos lados para búsqueda insensible a mayúsculas/minúsculas
            db_item = db.query(models_puc.PlanCuenta)\
                        .filter(func.lower(models_puc.PlanCuenta.codigo) == func.lower(valor1),
                                models_puc.PlanCuenta.empresa_id == empresa_id)\
                        .first()

        elif busqueda_tipo == "cc_por_codigo":
            # FIX: Aplicar func.lower() a ambos lados
            from ..models import centro_costo as models_cc
            db_item = db.query(models_cc.CentroCosto)\
                        .filter(func.lower(models_cc.CentroCosto.codigo) == func.lower(valor1),
                                models_cc.CentroCosto.empresa_id == empresa_id)\
                        .first()

        elif busqueda_tipo == "producto_por_codigo":
            # FIX: Aplicar func.lower() a ambos lados
            db_item = db.query(models_producto.Producto)\
                        .filter(func.lower(models_producto.Producto.codigo) == func.lower(valor1),
                                models_producto.Producto.empresa_id == empresa_id)\
                        .first()

        elif busqueda_tipo == "tipodoc_por_codigo":
            # FIX: Aplicar func.lower() a ambos lados
            db_item = db.query(models_tipo_doc.TipoDocumento)\
                        .filter(func.lower(models_tipo_doc.TipoDocumento.codigo) == func.lower(valor1),
                                models_tipo_doc.TipoDocumento.empresa_id == empresa_id)\
                        .first()

        # --- Búsqueda de documento por Tipo Doc ID y Número (No necesita lower() si son INTs) ---
        elif busqueda_tipo == "documento_por_numero":
            if not request.valor2:
                raise HTTPException(status_code=400, detail="Se requiere el ID del Tipo de Documento (valor1) y el Número (valor2) para esta búsqueda.")

            try:
                tipo_doc_id = int(valor1)
                numero = int(request.valor2)
            except ValueError:
                raise HTTPException(status_code=400, detail="Los valores de búsqueda para Documento deben ser números enteros.")

            db_item = db.query(models_doc.Documento)\
                        .filter(models_doc.Documento.numero == numero,
                                models_doc.Documento.tipo_documento_id == tipo_doc_id,
                                models_doc.Documento.empresa_id == empresa_id)\
                        .first()

        else:
            raise HTTPException(status_code=400, detail=f"Tipo de búsqueda no soportado: {request.tipoBusqueda}")


        if not db_item:
            # Si no se encuentra, lanzar 404
            raise HTTPException(status_code=404, detail="ID interno no encontrado para los criterios dados.")

        return diagnostico_schemas.BusquedaInversaResponse(id=db_item.id)

    except HTTPException as e:
        raise e
    except Exception as e:
        db.rollback()
        print(f"Error CRÍTICO en buscar_id_por_llave_natural: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno del servidor al buscar el ID.")



def inspector_universal_id(db: Session, id_to_inspect: int) -> List[diagnostico_schemas.InspectorUniversalResult]:
    """
    Busca un ID en todas las tablas maestras y devuelve un diccionario de datos.
    Funciona como un inspector forense para un ID huérfano.
    """
    from ..models import (
        tercero as models_tercero,
        plan_cuenta as models_puc,
        centro_costo as models_cc,
        producto as models_producto,
        tipo_documento as models_tipo_doc,
        empresa as models_empresa,
        usuario as models_usuario,
    )
    
    # Mapeo de Tablas Maestras con el nombre que el Schema espera
    TABLAS_MAESTRAS = [
        ("empresas", models_empresa.Empresa),
        ("usuarios", models_usuario.Usuario),
        ("terceros", models_tercero.Tercero),
        ("plan_cuentas", models_puc.PlanCuenta),
        ("centros_costo", models_cc.CentroCosto),
        ("productos", models_producto.Producto),
        ("tipos_documento", models_tipo_doc.TipoDocumento),
        # Puedes añadir más aquí, como bodegas, grupos de inventario, etc.
    ]

    resultados = []
    
    for tabla_nombre, modelo in TABLAS_MAESTRAS:
        try:
            db_item = db.query(modelo).filter(modelo.id == id_to_inspect).first()
            
            if db_item:
                # Usa el inspector de SQLAlchemy para obtener todos los campos
                inspector = inspect(db_item)
                datos = {
                    col.key: getattr(db_item, col.key)
                    for col in inspector.mapper.column_attrs
                }
                
                # Saneamiento: Convertir objetos a serializables (especialmente datetime/Decimal)
                datos_saneados = {}
                for k, v in datos.items():
                    if isinstance(v, datetime) or isinstance(v, date):
                        datos_saneados[k] = v.isoformat()
                    elif isinstance(v, Decimal):
                        datos_saneados[k] = float(v)
                    else:
                        datos_saneados[k] = v
                
                resultados.append(diagnostico_schemas.InspectorUniversalResult(
                    tabla_origen=tabla_nombre,
                    datos=datos_saneados
                ))
                # Una vez encontrado en una tabla, se devuelve el resultado para evitar duplicidades
                # break # Puedes comentar esta línea si quieres que inspeccione TODAS las tablas

        except Exception as e:
            # Capturar errores si una tabla no tiene columna 'id' (aunque no debería pasar en maestras)
            print(f"Error al inspeccionar ID {id_to_inspect} en tabla {tabla_nombre}: {e}")
            continue

    if not resultados:
        # Devolver un resultado vacío si no se encuentra en ninguna tabla
        return []

    return resultados


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

                if stock_actual_origen < cantidad:
                    raise HTTPException(status_code=409, detail=f"Stock insuficiente en Bodega Origen ({db_origen.nombre}) para producto {db_producto.codigo}.")
                
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
    en_uso_movimiento = db.query(models_producto.MovimientoInventario).filter(models_producto.MovimientoInventario.bodega_id == bodega_id).first()
    en_uso_stock = db.query(models_producto.StockBodega).filter(models_producto.StockBodega.bodega_id == bodega_id).first()
    if en_uso_movimiento or en_uso_stock: raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Bodega tiene stock o movimientos.")
    db.delete(db_bodega); db.commit(); return {"ok": True}


# ========== CRUD para Grupos de Inventario ==========
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
    producto_asociado = db.query(models_producto.Producto).filter(models_producto.Producto.grupo_id == grupo_id).first()
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
    producto_asociado = db.query(models_producto.Producto).filter(models_producto.Producto.impuesto_iva_id == tasa_id).first()
    if producto_asociado: raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Tasa asignada a productos.")
    db.delete(db_tasa); db.commit(); return {"ok": True}


# ========== CRUD para Listas de Precios ==========
def create_lista_precio(db: Session, lista_precio: schemas.ListaPrecioCreate, empresa_id: int) -> models_lista_precio.ListaPrecio:
    lista_existente = db.query(models_lista_precio.ListaPrecio).filter(models_lista_precio.ListaPrecio.empresa_id == empresa_id, models_lista_precio.ListaPrecio.nombre == lista_precio.nombre).first()
    if lista_existente: raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Nombre '{lista_precio.nombre}' ya existe.")
    db_lista = models_lista_precio.ListaPrecio(**lista_precio.model_dump(), empresa_id=empresa_id)
    db.add(db_lista); db.commit(); db.refresh(db_lista); return db_lista

def get_listas_precio_by_empresa(db: Session, empresa_id: int) -> List[models_lista_precio.ListaPrecio]:
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
    regla_asociada = db.query(models_regla_precio.ReglaPrecioGrupo).filter(models_regla_precio.ReglaPrecioGrupo.lista_precio_id == lista_id).first()
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
    query = db.query(models_producto.Producto, models_regla_precio.ReglaPrecioGrupo.porcentaje_incremento)\
        .join(models_grupo.GrupoInventario, models_producto.Producto.grupo_id == models_grupo.GrupoInventario.id, isouter=True)\
        .outerjoin(models_regla_precio.ReglaPrecioGrupo, and_(models_regla_precio.ReglaPrecioGrupo.grupo_inventario_id == models_grupo.GrupoInventario.id, models_regla_precio.ReglaPrecioGrupo.lista_precio_id == lista_precio_id))\
        .filter(models_producto.Producto.id == producto_id, models_producto.Producto.empresa_id == empresa_id)
    lista = db.query(models_lista_precio.ListaPrecio).filter(models_lista_precio.ListaPrecio.id == lista_precio_id, models_lista_precio.ListaPrecio.empresa_id == empresa_id).first()
    if not lista: raise HTTPException(status_code=404, detail=f"Lista de precios ID {lista_precio_id} no válida.")
    result = query.first()
    if not result: raise HTTPException(status_code=404, detail=f"Producto ID {producto_id} no encontrado.")
    producto, porcentaje_incremento = result
    precio_base = producto.precio_base_manual if producto.precio_base_manual is not None else (producto.costo_promedio or 0.0)
    if porcentaje_incremento is not None:
        precio_calculado = precio_base * (1 + porcentaje_incremento)
        return round(precio_calculado, 2)
    else:
        return round(precio_base, 2)

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
    grupo = None; definiciones_grupo_ids = set()
    if producto.grupo_id:
        grupo = db.query(models_grupo.GrupoInventario).options(selectinload(models_grupo.GrupoInventario.caracteristicas_definidas)).filter(models_grupo.GrupoInventario.id == producto.grupo_id, models_grupo.GrupoInventario.empresa_id == empresa_id).first()
        if not grupo: raise HTTPException(status_code=400, detail=f"Grupo ID {producto.grupo_id} no encontrado.")
        definiciones_grupo_ids = {d.id for d in grupo.caracteristicas_definidas}
    if producto.impuesto_iva_id:
        impuesto = db.query(models_impuesto.TasaImpuesto).filter(models_impuesto.TasaImpuesto.id == producto.impuesto_iva_id, models_impuesto.TasaImpuesto.empresa_id == empresa_id).first()
        if not impuesto: raise HTTPException(status_code=400, detail=f"Impuesto ID {producto.impuesto_iva_id} no encontrado.")
    valores_a_crear = []
    try:
        with db.begin_nested():
            producto_data = producto.model_dump(exclude={'valores_caracteristicas', 'stock_inicial', 'costo_inicial', 'bodega_id_inicial'})
            db_producto = models_producto.Producto(**producto_data, empresa_id=empresa_id, costo_promedio=producto.costo_inicial or 0.0)
            db.add(db_producto); db.flush()
            if producto.valores_caracteristicas:
                definiciones_usadas = set()
                for val_data in producto.valores_caracteristicas:
                    if not val_data.valor: continue
                    if val_data.definicion_id in definiciones_usadas: raise HTTPException(status_code=400, detail=f"Característica ID {val_data.definicion_id} duplicada.")
                    definiciones_usadas.add(val_data.definicion_id)
                    if grupo and val_data.definicion_id not in definiciones_grupo_ids: raise HTTPException(status_code=400, detail=f"Característica ID {val_data.definicion_id} no pertenece al grupo.")
                    definicion_exists = db.query(models_carac_def.CaracteristicaDefinicion.id).filter(models_carac_def.CaracteristicaDefinicion.id == val_data.definicion_id).first()
                    if not definicion_exists: raise HTTPException(status_code=400, detail=f"Característica ID {val_data.definicion_id} no existe.")
                    valores_a_crear.append(models_carac_val.CaracteristicaValorProducto(producto_id=db_producto.id, definicion_id=val_data.definicion_id, valor=val_data.valor))
                print("\n--- SONDA CREATE 2: Valores de Características a crear ---"); print(f"Total: {len(valores_a_crear)}")
                for val in valores_a_crear: print(f"  - Def ID: {val.definicion_id}, Valor: '{val.valor}', Prod ID (asignado): {val.producto_id}")
                if valores_a_crear: db.add_all(valores_a_crear)
            if not db_producto.es_servicio and producto.stock_inicial and producto.stock_inicial > 0:
                if not producto.bodega_id_inicial: raise HTTPException(status_code=400, detail="Bodega requerida para stock inicial.")
                bodega_exists = db.query(models_bodega.Bodega.id).filter(models_bodega.Bodega.id == producto.bodega_id_inicial, models_bodega.Bodega.empresa_id == empresa_id).first()
                if not bodega_exists: raise HTTPException(status_code=400, detail=f"Bodega ID {producto.bodega_id_inicial} no encontrada.")
                registrar_movimiento_inventario(db=db, producto_id=db_producto.id, bodega_id=producto.bodega_id_inicial, tipo_movimiento='ENTRADA_INICIAL', cantidad=producto.stock_inicial, costo_unitario=producto.costo_inicial or 0.0, fecha=datetime.now())
        print("\n--- SONDA CREATE 3: Antes del commit principal ---"); print(f"Producto ID (potencial): {db_producto.id}"); print(f"Valores en sesión (estado pendiente):"); print(f"  - Producto: {producto_data}"); print(f"  - Valores Caracteristicas: {[v.__dict__ for v in valores_a_crear]}")
        db.commit()
        print("\n--- SONDA CREATE 4: Después del commit ---"); db.refresh(db_producto)
        valores_guardados = db.query(models_carac_val.CaracteristicaValorProducto).filter(models_carac_val.CaracteristicaValorProducto.producto_id == db_producto.id).all()
        print(f"Valores de características REALMENTE guardados en BD:")
        if valores_guardados:
            for val in valores_guardados: print(f"  - ID: {val.id}, Def ID: {val.definicion_id}, Valor: '{val.valor}'")
        else: print("  - NINGUNO.")
        db_producto_completo = get_producto_by_id(db, db_producto.id, empresa_id)
        return db_producto_completo
    except Exception as e:
        db.rollback(); print(f"ERROR create_producto: {e}"); traceback.print_exc()
        if isinstance(e, HTTPException): raise e
        else: raise HTTPException(status_code=500, detail=f"Error interno al crear.")

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
    
    # 1. SANEAMIENTO ATÓMICO: Eliminar registros StockBodega donde stock_actual es CERO.
    #    Esto resuelve el problema de la llave foránea causada por saldos fantasma (stock=0, registro existe).
    stock_cero_stmt = delete(models_producto.StockBodega).where(
        models_producto.StockBodega.producto_id == producto_id,
        models_producto.StockBodega.stock_actual == 0.0
    )
    db.execute(stock_cero_stmt)
    db.flush() # Forzar la eliminación antes de la verificación de uso.
    
    # 2. VERIFICACIÓN DE USO (El stock restante es la ÚNICA dependencia que debe quedar)
    en_uso_kardex = db.query(models_producto.MovimientoInventario.id).filter(models_producto.MovimientoInventario.producto_id == producto_id).first()
    en_uso_contable = db.query(models_mov.MovimientoContable.id).filter(models_mov.MovimientoContable.producto_id == producto_id).first()
    
    # FIX CRÍTICO: Consulta correcta que verifica si queda ALGÚN registro de stock (donde stock_actual != 0).
    # Se corrige la consulta ineficiente (producto cartesiano) a un filtro directo por producto_id.
    en_uso_stock = db.query(models_producto.StockBodega.id).filter(
        models_producto.StockBodega.producto_id == producto_id
    ).first() 

    if en_uso_kardex or en_uso_contable or en_uso_stock:
        usos = []
        if en_uso_kardex: usos.append("kardex")
        if en_uso_contable: usos.append("contabilidad")
        if en_uso_stock: usos.append("stock asociados (saldos > 0)")
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"No se puede eliminar: tiene {', '.join(usos)}.")
    
    # 3. ELIMINACIÓN FINAL
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

    if grupo_ids:
        query_base = query_base.filter(models_producto.Producto.grupo_id.in_(grupo_ids))

    if search_term:
         search_like = f"%{search_term}%"
         query_base = query_base.filter(
             or_(
                 models_producto.Producto.codigo.ilike(search_like),
                 models_producto.Producto.nombre.ilike(search_like)
             )
         )

    stock_select_stmt = select(func.sum(models_producto.StockBodega.stock_actual)).where(
        models_producto.StockBodega.producto_id == models_producto.Producto.id
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
         raise HTTPException(status_code=500, detail="Error al buscar productos.")

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
    if filtros.grupo_id: query = query.filter(models_producto.Producto.grupo_id == filtros.grupo_id)
    if filtros.search_term: query = query.filter(or_(models_producto.Producto.codigo.ilike(f"%{filtros.search_term}%"), models_producto.Producto.nombre.ilike(f"%{filtros.search_term}%")))
    productos = query.order_by(models_producto.Producto.nombre).all()
    productos_con_stock = _filter_stock_for_bodegas(productos, filtros.bodega_ids)
    return productos_con_stock

def get_producto_para_kardex(db: Session, producto_id: int) -> Optional[models_producto.Producto]:
    return db.query(models_producto.Producto).filter(models_producto.Producto.id == producto_id).first()

# app/services/inventario.py (ADICIÓN DE FUNCIÓN PDF)

# Importaciones para PDF
from jinja2 import Environment, FileSystemLoader
from io import BytesIO
from weasyprint import HTML
import os


# app/services/inventario.py (REEMPLAZO DEL BLOQUE DE GENERACIÓN DE PDF)

# Importaciones para PDF
from jinja2 import Environment, FileSystemLoader
from io import BytesIO
from weasyprint import HTML
import os

# --- INICIO: LÓGICA DE FILTRO DE MILES INYECTADA ---
import locale
def format_miles(value):
    """Aplica formato de separador de miles con dos decimales, usando el formato CO."""
    try:
        val = float(value)
        # Configurar la localización a español (si el sistema lo soporta)
        locale.setlocale(locale.LC_ALL, 'es_ES.UTF-8') 
        # Usamos formato localizado, y luego manipulamos para forzar el formato CO
        # que usa punto como separador de miles y coma como decimal.
        # Primero, formateamos como string con separador de miles (que usa punto o coma según locale)
        formatted = locale.format_string("%.2f", val, grouping=True)
        # Luego, reemplazamos el separador de miles (generalmente , o .) por el estándar CO (punto para miles, coma para decimales)
        # Esta lógica es compleja debido a la inconsistencia de locale en diferentes SO/entornos.
        # Simplificamos forzando a dos decimales y usando toLocaleString si fuera JS, 
        # pero en Python, la forma más segura es esta:
        # Revertir el punto/coma a lo que queremos (ej. 1.234,56 -> 1,234.56)
        if '.' in formatted and ',' in formatted and formatted.rfind('.') < formatted.rfind(','): # Estilo Europeo
             return formatted.replace('.', '#').replace(',', '.').replace('#', ',')
        return formatted
    except Exception:
        # En caso de fallo (ej: None, NaN), devolver cadena formateada
        return f"{value or 0:.2f}" 

# --- Carga de Entorno Jinja2 (Para PDF) ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, '..', 'templates', 'reports')
env = Environment(loader=FileSystemLoader(TEMPLATES_DIR), trim_blocks=True, lstrip_blocks=True)

# --- REGISTRO DEL FILTRO CRÍTICO ---
env.filters['format_miles'] = format_miles # <--- REGISTRO AHORA EN INVENTARIO.PY

# Función para adaptar Decimal a float (necesario para Jinja2)
def _to_float(value):
    return float(value) if isinstance(value, (Decimal, int, float)) else (value or 0.0)

def generar_pdf_lista_productos(db: Session, empresa_id: int, filtros: schemas.ProductoFiltros):
    """
    Genera el PDF de la lista de productos de la página de administración de inventario.
    """
    try:
        # 1. Obtener la lista completa de productos filtrados (traerTodo = True)
        productos = get_productos_filtrados(db, empresa_id, filtros)

        # 2. Obtener datos de la empresa (asumiendo que models_empresa está importado)
        from ..models import empresa as models_empresa
        empresa_db = db.query(models_empresa.Empresa).filter(models_empresa.Empresa.id == empresa_id).first()
        empresa_nombre = empresa_db.razon_social if empresa_db else f"Empresa ID {empresa_id}"

        # 3. Preparar los datos para la plantilla
        items_serializables = []
        for p in productos:
            stock_display = p.stock_total_calculado if hasattr(p, 'stock_total_calculado') else 0.0
            items_serializables.append({
                "codigo": p.codigo,
                "nombre": p.nombre,
                "grupo_nombre": p.grupo_inventario.nombre if p.grupo_inventario else "N/A",
                "es_servicio": p.es_servicio,
                "costo_promedio": _to_float(p.costo_promedio),
                "precio_base_manual": _to_float(p.precio_base_manual),
                "stock_actual": _to_float(stock_display),
            })

        context = {
            "titulo_reporte": "CARTILLA DE INVENTARIO",
            "empresa_nombre": empresa_nombre,
            "filtros": filtros.model_dump(),
            "productos": items_serializables,
            "fecha_reporte": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        # 4. Renderizar la plantilla
        template_name = 'cartilla_inventario_admin_report.html'
        template = env.get_template(template_name)
        html_out = template.render(context)

        # 5. Generar PDF con WeasyPrint
        pdf_file = HTML(string=html_out).write_pdf(stylesheets=[])
        return pdf_file

    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Error CRÍTICO al generar PDF de Lista de Productos: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error al generar PDF: {str(e)}")
    


# app/services/diagnostico.py (Función COMPLETA y CORREGIDA)

# --- FUNCIÓN AUXILIAR REQUERIDA (NO CAMBIA) ---
def _get_dependencias(db: Session, modelo_hijo, campo_filtro_id: str, id_maestro: int, descripcion_hijo: str) -> List[diagnostico_schemas.Dependencia]:
    """Función auxiliar para buscar dependencias en una tabla."""
    dependencias = []
    # Construir el filtro dinámicamente
    filtro = {campo_filtro_id: id_maestro}
    
    # Contar la cantidad de registros en la tabla hija
    count = db.query(modelo_hijo).filter_by(**filtro).count()

    if count > 0:
        dependencias.append(diagnostico_schemas.Dependencia(
            tipo=descripcion_hijo,
            descripcion=f"Usado en {count} registros.",
        ))
    return dependencias


def inspeccionar_entidades(db: Session, request: diagnostico_schemas.InspeccionRequest) -> List[diagnostico_schemas.EntidadInspeccionada]:
    """
    Inspecciona registros maestros (terceros, PUC, etc.) para detectar dependencias.
    (CORREGIDO PARA USAR LOS NOMBRES DE COLUMNA REALES DE LOS MODELOS)
    """
    entidad_tipo = request.tipo_entidad
    empresa_id = request.empresa_id
    resultados = []
    
    # --- Terceros ---
    if entidad_tipo == 'terceros':
        maestros = db.query(models_tercero.Tercero)\
                     .filter(models_tercero.Tercero.empresa_id == empresa_id)\
                     .order_by(models_tercero.Tercero.razon_social)\
                     .all()
        
        for maestro in maestros:
            dependencias = []
            
            # 1. Documentos que usan al Tercero como beneficiario
            dependencias.extend(_get_dependencias(db, models_doc.Documento, 'beneficiario_id', maestro.id, 'Documentos (Facturas/Recibos)'))
            
            resultados.append(diagnostico_schemas.EntidadInspeccionada(
                id=maestro.id,
                descripcion_principal=maestro.razon_social,
                descripcion_secundaria=maestro.nit,
                email=maestro.email,
                dependencias=dependencias
            ))
            
    # --- Plan de Cuentas (PUC) ---
    elif entidad_tipo == 'plan_cuentas':
        maestros = db.query(models_puc.PlanCuenta)\
                     .filter(models_puc.PlanCuenta.empresa_id == empresa_id)\
                     .order_by(models_puc.PlanCuenta.codigo)\
                     .all()
        
        for maestro in maestros:
            dependencias = []
            
            # 1. Movimientos Contables (registros en el diario)
            dependencias.extend(_get_dependencias(db, models_mov.MovimientoContable, 'cuenta_id', maestro.id, 'Movimientos Contables'))
            
            # 2. Documentos que referencian la cuenta (usando campos reales del modelo TipoDocumento)
            dependencias.extend(_get_dependencias(db, models_tipo_doc.TipoDocumento, 'cuenta_debito_cxc_id', maestro.id, 'Tipos Doc. (Cta. Débito CxC)'))
            dependencias.extend(_get_dependencias(db, models_tipo_doc.TipoDocumento, 'cuenta_credito_cxp_id', maestro.id, 'Tipos Doc. (Cta. Crédito CxP)'))
            dependencias.extend(_get_dependencias(db, models_tipo_doc.TipoDocumento, 'cuenta_caja_id', maestro.id, 'Tipos Doc. (Cta. Caja/Banco)'))

            # 3. Cuentas Padre (relación jerárquica)
            # FIX CRÍTICO: Se usa el campo REAL 'cuenta_padre_id'
            dependencias.extend(_get_dependencias(db, models_puc.PlanCuenta, 'cuenta_padre_id', maestro.id, 'Subcuentas asociadas'))
            
            resultados.append(diagnostico_schemas.EntidadInspeccionada(
                id=maestro.id,
                descripcion_principal=maestro.codigo,
                descripcion_secundaria=maestro.nombre,
                dependencias=dependencias
            ))
            
    # --- Tipos de Documento ---
    elif entidad_tipo == 'tipos_documento':
        maestros = db.query(models_tipo_doc.TipoDocumento)\
                     .filter(models_tipo_doc.TipoDocumento.empresa_id == empresa_id)\
                     .order_by(models_tipo_doc.TipoDocumento.codigo)\
                     .all()
                     
        for maestro in maestros:
            dependencias = []
            # 1. Documentos creados
            dependencias.extend(_get_dependencias(db, models_doc.Documento, 'tipo_documento_id', maestro.id, 'Documentos creados'))
            
            resultados.append(diagnostico_schemas.EntidadInspeccionada(
                id=maestro.id,
                descripcion_principal=maestro.codigo,
                descripcion_secundaria=maestro.nombre,
                dependencias=dependencias
            ))
    
    # --- Centros de Costo ---
    elif entidad_tipo == 'centros_costo':
        maestros = db.query(models_cc.CentroCosto)\
                     .filter(models_cc.CentroCosto.empresa_id == empresa_id)\
                     .order_by(models_cc.CentroCosto.nombre)\
                     .all()
                     
        for maestro in maestros:
            dependencias = []
            # 1. Movimientos Contables
            dependencias.extend(_get_dependencias(db, models_mov.MovimientoContable, 'centro_costo_id', maestro.id, 'Movimientos Contables'))
            # 2. Documentos
            dependencias.extend(_get_dependencias(db, models_doc.Documento, 'centro_costo_id', maestro.id, 'Documentos Cabecera'))
            
            resultados.append(diagnostico_schemas.EntidadInspeccionada(
                id=maestro.id,
                descripcion_principal=maestro.codigo,
                descripcion_secundaria=maestro.nombre,
                dependencias=dependencias
            ))

    # --- Usuarios ---
    elif entidad_tipo == 'usuarios':
        maestros = db.query(models_usuario.Usuario)\
                     .filter(models_usuario.Usuario.empresa_id == empresa_id)\
                     .order_by(models_usuario.Usuario.email)\
                     .all()
                     
        for maestro in maestros:
            dependencias = []
            # 1. Documentos creados por el usuario
            dependencias.extend(_get_dependencias(db, models_doc.Documento, 'usuario_creador_id', maestro.id, 'Documentos creados'))
            # 2. Logs de operaciones
            dependencias.extend(_get_dependencias(db, models_log.LogOperacion, 'usuario_id', maestro.id, 'Logs de Operación')) 
            
            # FIX CRÍTICO: Se usa maestro.email para la descripción secundaria, ya que 'nombre' no existe.
            resultados.append(diagnostico_schemas.EntidadInspeccionada(
                id=maestro.id,
                descripcion_principal=maestro.email,
                descripcion_secundaria=maestro.email, # <-- CORRECCIÓN AQUÍ
                dependencias=dependencias
            ))


    # --- Conceptos Favoritos ---
    elif entidad_tipo == 'conceptos_favoritos':
        maestros = db.query(models_concepto.ConceptoFavorito)\
                     .filter(models_concepto.ConceptoFavorito.empresa_id == empresa_id)\
                     .order_by(models_concepto.ConceptoFavorito.descripcion)\
                     .all()
        
        for maestro in maestros:
            dependencias = []
            
            resultados.append(diagnostico_schemas.EntidadInspeccionada(
                id=maestro.id,
                descripcion_principal=maestro.descripcion,
                descripcion_secundaria=maestro.descripcion,
                dependencias=dependencias
            ))



# --- Conceptos Favoritos ---
    elif entidad_tipo == 'conceptos_favoritos':
        maestros = db.query(models_concepto.ConceptoFavorito)\
                     .filter(models_concepto.ConceptoFavorito.empresa_id == empresa_id)\
                     .order_by(models_concepto.ConceptoFavorito.descripcion)\
                     .all()
        
        for maestro in maestros:
            dependencias = []
            
            resultados.append(diagnostico_schemas.EntidadInspeccionada(
                id=maestro.id,
                descripcion_principal=maestro.descripcion,
                descripcion_secundaria=maestro.descripcion,
                dependencias=dependencias
            ))
            
    # --- Plantillas Maestras ---
    elif entidad_tipo == 'plantillas_maestras': # <--- NUEVA LÓGICA DE INSPECCIÓN
        maestros = db.query(models_plantilla_maestra.PlantillaMaestra)\
                     .filter(models_plantilla_maestra.PlantillaMaestra.empresa_id == empresa_id)\
                     .order_by(models_plantilla_maestra.PlantillaMaestra.nombre_plantilla)\
                     .all()
        
        for maestro in maestros:
            dependencias = []
            
            # 1. Detalles asociados a la plantilla (campo: plantilla_maestra_id)
            dependencias.extend(_get_dependencias(db, models_plantilla_detalle.PlantillaDetalle, 'plantilla_maestra_id', maestro.id, 'Líneas de Detalle (Movimientos)'))
            
            resultados.append(diagnostico_schemas.EntidadInspeccionada(
                id=maestro.id,
                descripcion_principal=maestro.nombre_plantilla,
                descripcion_secundaria=f"Tipo Doc. Sugerido ID: {maestro.tipo_documento_id_sugerido or 'N/A'}",
                dependencias=dependencias
            ))
    # --- FIN: NUEVA LÓGICA DE INSPECCIÓN ---
        
    else:
        raise HTTPException(status_code=400, detail=f"Entidad '{entidad_tipo}' no soportada para inspección.")

    return resultados


# app/services/diagnostico.py (Añadir al final del archivo)

def erradicar_entidades_maestras(db: Session, request: diagnostico_schemas.ErradicacionMaestrosRequest):
    """
    Elimina registros maestros (Centros de Costo, Tipos de Documento, etc.) si y solo si 
    no tienen dependencias (Movimientos, Documentos).
    """
    entidad_tipo = request.tipo_entidad
    empresa_id = request.empresa_id
    ids_a_erradicar = request.ids_a_erradicar
    
    # 1. Mapeo de Entidad a Modelo de SQLAlchemy y dependencias críticas
    if entidad_tipo == 'terceros':
        Modelo = models_tercero.Tercero
        # Las dependencias críticas son los Documentos (usando beneficiario_id)
        Dependencias = [
            (models_doc.Documento, 'beneficiario_id', 'Documentos (Cabecera)'),
        ]
    elif entidad_tipo == 'plan_cuentas':
        Modelo = models_puc.PlanCuenta
        # Las dependencias críticas son los Movimientos Contables (usando cuenta_id)
        Dependencias = [
            (models_mov.MovimientoContable, 'cuenta_id', 'Movimientos Contables'),
        ]
    elif entidad_tipo == 'centros_costo':
        Modelo = models_cc.CentroCosto
        # Las dependencias críticas son Movimientos y Documentos
        Dependencias = [
            (models_mov.MovimientoContable, 'centro_costo_id', 'Movimientos Contables'),
            (models_doc.Documento, 'centro_costo_id', 'Documentos (Cabecera)'),
        ]
    elif entidad_tipo == 'tipos_documento':
        Modelo = models_tipo_doc.TipoDocumento
        # Las dependencias críticas son Documentos creados
        Dependencias = [
            (models_doc.Documento, 'tipo_documento_id', 'Documentos Creados'),
        ]
    elif entidad_tipo == 'conceptos_favoritos':
        Modelo = models_concepto.ConceptoFavorito
        # No tiene dependencias fuertes en el código transaccional
        Dependencias = [] 
    elif entidad_tipo == 'plantillas_maestras':
        Modelo = models_plantilla_maestra.PlantillaMaestra
        # Las dependencias se manejan con ON DELETE CASCADE en los detalles
        Dependencias = []
    elif entidad_tipo == 'usuarios':
        Modelo = models_usuario.Usuario
        # Dependencias: Documentos (usuario_creador_id) y Logs (usuario_id)
        Dependencias = [
            (models_doc.Documento, 'usuario_creador_id', 'Documentos Creados'),
            (models_log.LogOperacion, 'usuario_id', 'Logs de Operación'),
        ]
    else:
        raise HTTPException(status_code=400, detail=f"Entidad '{entidad_tipo}' no soportada para erradicación.")
        
    registros_erradicados = 0
    errores = []

    try:
        with db.begin_nested():
            for id_maestro in ids_a_erradicar:
                db_item = db.query(Modelo).filter(Modelo.id == id_maestro, Modelo.empresa_id == empresa_id).first()
                
                if not db_item:
                    errores.append(f"ID {id_maestro}: No encontrado o ya fue eliminado.")
                    continue

                # 2. Verificar dependencias
                dependencias_encontradas = []
                for ModeloHijo, campo_filtro, descripcion in Dependencias:
                    # Usamos la misma lógica de filtro que en inspeccionar_entidades
                    filtro = {campo_filtro: id_maestro}
                    count = db.query(ModeloHijo).filter_by(**filtro).count()
                    
                    if count > 0:
                        dependencias_encontradas.append(f"{descripcion} ({count} usos)")

                if dependencias_encontradas:
                    # Si tiene dependencias, lanzar un conflicto
                    errores.append(f"ID {id_maestro} ({getattr(db_item, 'codigo', getattr(db_item, 'razon_social', ''))}): No se puede eliminar. Aún tiene dependencias: {', '.join(dependencias_encontradas)}.")
                else:
                    # 3. Erradicación
                    db.delete(db_item)
                    registros_erradicados += 1

        db.commit() # Commit final después del bucle
        
        if errores:
            raise HTTPException(status_code=409, detail={"msg": f"{registros_erradicados} entidades erradicadas, pero {len(errores)} fallaron la verificación.", "errores": errores})

        return {"msg": f"¡Éxito! {registros_erradicados} entidades de tipo '{entidad_tipo}' erradicadas completamente.", "erradicados": registros_erradicados}

    except HTTPException as e:
        raise e
    except Exception as e:
        db.rollback()
        print(f"Error CRÍTICO en erradicar_entidades_maestras: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno al procesar la erradicación masiva.")
    
# app/services/diagnostico.py (Añadir al final del archivo)

def get_tipos_documento_por_empresa(db: Session, empresa_id: int) -> List[schemas_tipo_doc.TipoDocumento]:
    """
    Obtiene la lista de Tipos de Documento (incluyendo su consecutivo actual) para una empresa específica.
    Usado por el panel de soporte para auditoría de consecutivos.
    """
    # models_tipo_doc y schemas_tipo_doc ya están importados.
    
    tipos_documento = db.query(models_tipo_doc.TipoDocumento)\
                        .filter(models_tipo_doc.TipoDocumento.empresa_id == empresa_id)\
                        .order_by(models_tipo_doc.TipoDocumento.codigo)\
                        .all()
    
    # Se devuelve la lista de modelos, que FastAPI mapeará automáticamente al schema TipoDocumento.
    return tipos_documento