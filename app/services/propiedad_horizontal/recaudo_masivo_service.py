import pandas as pd
from decimal import Decimal
from datetime import datetime, date
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func
import io

from app.models.propiedad_horizontal.unidad import PHUnidad
from app.schemas.propiedad_horizontal import recaudo_masivo as schemas_rm
from app.services.propiedad_horizontal import pago_service

def parse_recaudo_file(file_content: bytes, file_name: str) -> List[schemas_rm.RecaudoFila]:
    """
    Parsea un archivo CSV o Excel buscando columnas clave.
    Columnas esperadas (flexibles, case insensitive):
    - Referencia, Ref, Codigo
    - Fecha
    - Monto, Valor, Pago
    - Descripcion, Detalle (Opcional)
    """
    try:
        if file_name.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(file_content))
        elif file_name.endswith('.xlsx') or file_name.endswith('.xls'):
            df = pd.read_excel(io.BytesIO(file_content))
        else:
            raise ValueError("Formato de archivo no soportado. Debe ser .csv, .xls o .xlsx")
        
        # Normalizar nombres de columnas a minúsculas
        df.columns = [str(c).strip().lower() for c in df.columns]
        
        # Mapear columnas reales a lógicas
        col_ref = next((c for c in df.columns if 'ref' in c or 'cod' in c or 'iden' in c), None)
        col_fecha = next((c for c in df.columns if 'fecha' in c or 'date' in c), None)
        col_monto = next((c for c in df.columns if 'monto' in c or 'valor' in c or 'pago' in c or 'total' in c), None)
        col_desc = next((c for c in df.columns if 'desc' in c or 'det' in c or 'obs' in c), None)
        
        if not col_ref or not col_fecha or not col_monto:
            raise ValueError(f"Faltan columnas requeridas. Encontradas: {list(df.columns)}")
            
        filas = []
        for index, row in df.iterrows():
            try:
                # Extraer y limpiar
                referencia = str(row[col_ref]).strip()
                if pd.isna(row[col_ref]) or not referencia:
                    continue
                    
                # Parsing fecha
                raw_fecha = row[col_fecha]
                if pd.isna(raw_fecha):
                    fecha = date.today()
                elif isinstance(raw_fecha, datetime):
                    fecha = raw_fecha.date()
                else:
                    # Intento genérico
                    fecha = pd.to_datetime(raw_fecha, dayfirst=True).date()
                
                # Parsing monto
                raw_monto = row[col_monto]
                if pd.isna(raw_monto):
                    continue
                # Limpiar signos $ y comas
                if isinstance(raw_monto, str):
                    raw_monto = raw_monto.replace('$', '').replace(',', '').strip()
                monto = Decimal(str(raw_monto))
                
                desc = str(row[col_desc]).strip() if col_desc and not pd.isna(row[col_desc]) else None
                
                filas.append(schemas_rm.RecaudoFila(
                    referencia=referencia,
                    fecha=fecha,
                    monto=monto,
                    descripcion=desc,
                    line_number=index + 1
                ))
            except Exception as e:
                # Skip invalid rows or log them
                pass
                
        return filas
    except Exception as e:
        raise ValueError(f"Error parseando el archivo: {str(e)}")

def generar_preview(db: Session, empresa_id: int, filas: List[schemas_rm.RecaudoFila]) -> schemas_rm.RecaudoPreviewResult:
    """
    Cruza las filas extraídas contra la base de datos de unidades
    y simula financieramente el recaudo.
    """
    detalles = []
    total_recaudado = Decimal('0.0')
    filas_validas = 0
    filas_error = 0
    
    # Cargar unidades en memoria usando un diccionario para busqueda O(1)
    # Buscamos por referencia_recaudo primero, si no, por codigo.
    unidades_db = db.query(PHUnidad).filter(PHUnidad.empresa_id == empresa_id, PHUnidad.activo == True).all()
    
    map_por_ref = {u.referencia_recaudo.strip().lower(): u for u in unidades_db if u.referencia_recaudo}
    map_por_codigo = {u.codigo.strip().lower(): u for u in unidades_db if u.codigo}
    
    for fila in filas:
        match_info = schemas_rm.RecaudoMatch(
            line_number=fila.line_number,
            referencia=fila.referencia,
            fecha_pago=fila.fecha,
            monto_recibido=fila.monto,
            is_valid=False
        )
        
        ref_busqueda = fila.referencia.lower()
        unidad = map_por_ref.get(ref_busqueda)
        if not unidad:
            unidad = map_por_codigo.get(ref_busqueda)
            
        if not unidad:
            match_info.error_msg = f"Unidad no encontrada con referencia/código: {fila.referencia}"
            filas_error += 1
            detalles.append(match_info)
            continue
            
        # Unidad encontrada
        match_info.unidad_id = unidad.id
        match_info.unidad_codigo = unidad.codigo
        
        # Simular deuda de la unidad usando el servicio de pago
        try:
            # Creamos un pseudo doc vacio, get_pago_distribucion_detalle asume un pago,
            # pero necesitamos saber cuanto debe ANTES del pago.
            # En pago_service.py hay un calculo de "estado_cuenta_actual"
            # get_pago_distribucion_detalle requiere un documento de pago existente. 
            # Mejor usar obtener_datos_pago o get_estado_cuenta
            
            # Para masividad, simplificaremos trayendo la deuda por medio del estado de cuenta
            estado_cuenta = pago_service.get_estado_cuenta_unidad(db, unidad.id, empresa_id, True)
            
            # estado_cuenta['resumen']['total_adeudado'] tiene la deuda
            deuda = Decimal(str(estado_cuenta.get('resumen', {}).get('total_adeudado', 0)))
            match_info.deuda_total = deuda
            
            if fila.monto > deuda:
                match_info.monto_a_aplicar = deuda
                match_info.excedente_anticipo = fila.monto - deuda
            else:
                match_info.monto_a_aplicar = fila.monto
                match_info.excedente_anticipo = Decimal('0.0')
                
            match_info.is_valid = True
            filas_validas += 1
            total_recaudado += fila.monto
            
        except Exception as e:
            match_info.error_msg = f"Error calculando estado: {str(e)}"
            filas_error += 1
            
        detalles.append(match_info)
        
    return schemas_rm.RecaudoPreviewResult(
        total_filas=len(filas),
        filas_validas=filas_validas,
        filas_error=filas_error,
        total_recaudado=total_recaudado,
        detalles=detalles
    )

def procesar_lote_pagos(db: Session, empresa_id: int, request: schemas_rm.RecaudoProcessRequest, usuario_id: int) -> schemas_rm.RecaudoProcessResponse:
    exitosos = 0
    fallidos = 0
    errores = []
    
    # Solo procesamos los válidos
    filas_a_procesar = [f for f in request.filas if f.is_valid and f.unidad_id]
    
    for fila in filas_a_procesar:
        try:
            pago_service.registrar_pago_unidad(
                db,
                unidad_id=fila.unidad_id,
                empresa_id=empresa_id,
                usuario_id=usuario_id,
                monto=fila.monto_recibido,
                fecha_pago=fila.fecha_pago,
                forma_pago_id=request.cuenta_bancaria_id,
                skip_recalculo=True,
                commit=False # Procesar todo en una transacción
            )
            exitosos += 1
        except Exception as e:
            fallidos += 1
            errores.append(f"Linea {fila.line_number} (Unidad {fila.unidad_codigo}): {str(e)}")
            
    # Hacemos commit final
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    
    return schemas_rm.RecaudoProcessResponse(
        exitosos=exitosos,
        fallidos=fallidos,
        errores=errores,
        mensaje=f"Proceso masivo completado. {exitosos} pagos registrados correctamente."
    )
