from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, extract
from fastapi import HTTPException
from app.models.propiedad_horizontal.presupuesto import PHPresupuesto
from app.models.plan_cuenta import PlanCuenta
from app.models.movimiento_contable import MovimientoContable
from app.models.documento import Documento
from app.schemas.propiedad_horizontal import presupuesto as schemas
from typing import List, Optional
from datetime import date
import calendar

def get_presupuestos(db: Session, empresa_id: int, anio: int):
    """
    Retorna los items de presupuesto para un año.
    Incluye filas vacias para cuentas de ingresos y gastos si no existen.
    """
    # 1. Traer existentes
    existentes = db.query(PHPresupuesto).options(joinedload(PHPresupuesto.cuenta))\
        .filter(PHPresupuesto.empresa_id == empresa_id, PHPresupuesto.anio == anio).all()
    
    # 2. Enriquecer respuesta
    response = []
    for p in existentes:
        item = schemas.PHPresupuestoResponse.model_validate(p)
        if p.cuenta:
            item.cuenta_codigo = p.cuenta.codigo
            item.cuenta_nombre = p.cuenta.nombre
        response.append(item)
        
    return response

def save_presupuestos_masivo(db: Session, empresa_id: int, payload: schemas.PHPresupuestoMasivo):
    """
    Guarda o actualiza multiples lineas de presupuesto (Upsert).
    """
    anio = payload.anio
    
    for item in payload.items:
        # Check if exists
        presupuesto = db.query(PHPresupuesto).filter(
            PHPresupuesto.empresa_id == empresa_id,
            PHPresupuesto.anio == anio,
            PHPresupuesto.cuenta_id == item.cuenta_id
        ).first()
        
        # Calcular total anual si no viene
        total_calculado = (
            (item.mes_01 or 0) + (item.mes_02 or 0) + (item.mes_03 or 0) +
            (item.mes_04 or 0) + (item.mes_05 or 0) + (item.mes_06 or 0) +
            (item.mes_07 or 0) + (item.mes_08 or 0) + (item.mes_09 or 0) +
            (item.mes_10 or 0) + (item.mes_11 or 0) + (item.mes_12 or 0)
        )
        
        if not presupuesto:
            presupuesto = PHPresupuesto(
                empresa_id=empresa_id,
                anio=anio,
                cuenta_id=item.cuenta_id
            )
            db.add(presupuesto)
        
        # Update fields
        presupuesto.mes_01 = item.mes_01 or 0
        presupuesto.mes_02 = item.mes_02 or 0
        presupuesto.mes_03 = item.mes_03 or 0
        presupuesto.mes_04 = item.mes_04 or 0
        presupuesto.mes_05 = item.mes_05 or 0
        presupuesto.mes_06 = item.mes_06 or 0
        presupuesto.mes_07 = item.mes_07 or 0
        presupuesto.mes_08 = item.mes_08 or 0
        presupuesto.mes_09 = item.mes_09 or 0
        presupuesto.mes_10 = item.mes_10 or 0
        presupuesto.mes_11 = item.mes_11 or 0
        presupuesto.mes_12 = item.mes_12 or 0
        presupuesto.valor_anual = total_calculado

    db.commit()
    return {"message": "Presupuesto actualizado correctamente"}

def get_ejecucion_presupuestal(
    db: Session, 
    empresa_id: int, 
    anio: Optional[int] = None, 
    mes_corte: Optional[int] = 12,
    fecha_inicio: Optional[date] = None, 
    fecha_fin: Optional[date] = None
):
    """
    Compara Presupuesto vs Movimientos Contables Reales con acumulacion jerarquica.
    Soporta filtrado por anio/mes (legacy) o por rango de fechas arbitrario.
    """

    # 1. Determinar Rango de Fechas
    start_date = fecha_inicio
    end_date = fecha_fin

    # Fallback legacy: si no mandan fechas completas, usar anio/mes
    if not start_date or not end_date:
        if not anio:
             anio = date.today().year
        
        start_date = date(anio, 1, 1)
        if not mes_corte: mes_corte = 12
        last_day = calendar.monthrange(anio, mes_corte)[1]
        end_date = date(anio, mes_corte, last_day)

    # 2. Calcular Ejecucion Real (Movimientos Exactos en Rango)
    # Traemos movimientos DESGLOSADOS por cuenta con su codigo
    movimientos = db.query(
        MovimientoContable.cuenta_id,
        PlanCuenta.codigo.label('cuenta_codigo'),
        func.sum(MovimientoContable.debito).label('total_debito'),
        func.sum(MovimientoContable.credito).label('total_credito')
    ).join(Documento, MovimientoContable.documento_id == Documento.id)\
     .join(PlanCuenta, MovimientoContable.cuenta_id == PlanCuenta.id)\
    .filter(
        Documento.empresa_id == empresa_id,
        Documento.estado.in_(['ACTIVO', 'PROCESADO']),
        Documento.fecha >= start_date,
        Documento.fecha <= end_date
    ).group_by(MovimientoContable.cuenta_id, PlanCuenta.codigo).all()
    
    lista_movimientos = []
    for m in movimientos:
        lista_movimientos.append({
            "codigo": m.cuenta_codigo,
            "debito": float(m.total_debito or 0),
            "credito": float(m.total_credito or 0)
        })

    # 3. Calcular Presupuesto Esperado (Suma Mensual en Rango)
    # Identificar meses involucrados.
    
    presupuesto_map = {}
    
    # Iterador de meses
    curr_y = start_date.year
    curr_m = start_date.month
    
    end_y = end_date.year
    end_m = end_date.month
    
    # Pre-fetch de todos los presupuestos involucrados (puede ser mas de 1 anio)
    years_involved = []
    y_iter = curr_y
    while y_iter <= end_y:
        years_involved.append(y_iter)
        y_iter += 1
        
    db_presupuestos = db.query(PHPresupuesto).options(joinedload(PHPresupuesto.cuenta))\
        .filter(PHPresupuesto.empresa_id == empresa_id, PHPresupuesto.anio.in_(years_involved)).all()
        
    # Indexar para buscar rapido
    presupuesto_db_map = {}
    cuentas_info = {} # {id: {codigo, nombre}}
    
    for p in db_presupuestos:
        presupuesto_db_map[(p.anio, p.cuenta_id)] = p
        if p.cuenta:
            cuentas_info[p.cuenta_id] = {"codigo": p.cuenta.codigo, "nombre": p.cuenta.nombre}

    # Sumar mes a mes lo que corresponda al rango
    # Loop 'temporal'
    temp_y = curr_y
    temp_m = curr_m
    
    while (temp_y < end_y) or (temp_y == end_y and temp_m <= end_m):
        # Para el mes (temp_y, temp_m), sumar budget de todas las cuentas
        for (p_anio, p_cuenta_id), p_obj in presupuesto_db_map.items():
            if p_anio == temp_y:
                val_mes = getattr(p_obj, f"mes_{temp_m:02d}", 0) or 0
                if p_cuenta_id not in presupuesto_map:
                    presupuesto_map[p_cuenta_id] = 0
                presupuesto_map[p_cuenta_id] += val_mes
        
        # Next month
        temp_m += 1
        if temp_m > 12:
            temp_m = 1
            temp_y += 1

    # 4. Consolidar Resultados
    # Iteramos sobre PRESUPUESTOS encontrados
    # (Podriamos tambien iterar sobre movimientos que no tengan presupuesto, pero mantenemos logica original de 'listar presupuestos')
    
    reporte_items = []
    total_pres = 0
    total_ejec = 0
    total_var = 0

    processed_accounts = set()

    # Agregar items con presupuesto
    for c_id, val_pres in presupuesto_map.items():
        processed_accounts.add(c_id)
        c_info = cuentas_info.get(c_id)
        if not c_info: continue 
        
        budget_code = c_info['codigo']
        
        # Ejecucion Hijos
        suma_debito = 0
        suma_credito = 0
        for mov in lista_movimientos:
            if mov['codigo'].startswith(budget_code):
                suma_debito += mov['debito']
                suma_credito += mov['credito']
        
        # Naturaleza
        saldo_real = 0
        if budget_code.startswith('4'): # Ingresos (Credito)
            saldo_real = suma_credito - suma_debito
        elif budget_code.startswith('5') or budget_code.startswith('6'): # Gastos (Debito)
            saldo_real = suma_debito - suma_credito
        else:
             saldo_real = suma_debito - suma_credito
             
        variacion_abs = saldo_real - val_pres
        
        cumplimiento = 0
        if val_pres != 0:
            cumplimiento = (saldo_real / val_pres) * 100
        elif saldo_real > 0:
            cumplimiento = 100
            
        reporte_items.append({
            "cuenta_id": c_id,
            "cuenta_codigo": budget_code,
            "cuenta_nombre": c_info['nombre'],
            "presupuestado": val_pres,
            "ejecutado": saldo_real,
            "variacion_absoluta": variacion_abs,
            "cumplimiento_porcentaje": cumplimiento
        })

        total_pres += val_pres
        total_ejec += saldo_real
        total_var += variacion_abs

    # Ordenar
    reporte_items.sort(key=lambda x: x['cuenta_codigo'])

    return {
        "anio": start_date.year,
        "mes_corte": end_date.month,
        "fecha_inicio": start_date,
        "fecha_fin": end_date,
        "items": reporte_items,
        "total_presupuestado": total_pres,
        "total_ejecutado": total_ejec,
        "total_variacion": total_var
    }
