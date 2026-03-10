from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from typing import List, Optional
from datetime import datetime

from app.models import presupuesto_avanzado as models
from app.schemas import presupuesto_avanzado as schemas
from app.models import MovimientoContable, PlanCuenta, Documento
from app.models.periodo_contable_cerrado import PeriodoContableCerrado

# --- CRUD ESCENARIOS ---

def get_escenarios(db: Session, empresa_id: int, anio: Optional[int] = None):
    query = db.query(models.EscenarioPresupuestal).filter(models.EscenarioPresupuestal.empresa_id == empresa_id)
    if anio:
        query = query.filter(models.EscenarioPresupuestal.anio == anio)
    return query.all()

def get_escenario(db: Session, escenario_id: int):
    return db.query(models.EscenarioPresupuestal).filter(models.EscenarioPresupuestal.id == escenario_id).first()

def create_escenario(db: Session, empresa_id: int, escenario: schemas.EscenarioCreate, user_id: int):
    db_escenario = models.EscenarioPresupuestal(
        empresa_id=empresa_id,
        nombre=escenario.nombre,
        anio=escenario.anio,
        estado=escenario.estado,
        tipo_sector=escenario.tipo_sector,
        variables_globales=escenario.variables_globales,
        created_by=user_id
    )
    db.add(db_escenario)
    db.commit()
    db.refresh(db_escenario)
    
    # -----------------------------------------------------
    # INICIALIZACIÓN AUTOMÁTICA DE CUENTAS DE RESULTADO
    # -----------------------------------------------------
    # Al crear un presupuesto, se deben traer únicamente las
    # cuentas de resultado (4, 5, 6, 7) de nivel inferior 
    # (permite_movimiento = True) y que tengan algún movimiento.
    # -----------------------------------------------------
    from app.models import PlanCuenta, MovimientoContable
    
    # Buscar IDs de cuentas que cumplan las condiciones
    cuentas_elegibles = db.query(PlanCuenta.id).join(
        MovimientoContable, PlanCuenta.id == MovimientoContable.cuenta_id
    ).filter(
        PlanCuenta.empresa_id == empresa_id,
        PlanCuenta.permite_movimiento == True,
        or_(
            PlanCuenta.codigo.like('4%'),
            PlanCuenta.codigo.like('5%'),
            PlanCuenta.codigo.like('6%'),
            PlanCuenta.codigo.like('7%')
        )
    ).distinct().all()
    
    # Crear los items en ceros para cada cuenta
    if cuentas_elegibles:
        nuevos_items = []
        for (cuenta_id,) in cuentas_elegibles:
            nuevos_items.append(
                models.PresupuestoItem(
                    escenario_id=db_escenario.id,
                    cuenta_id=cuenta_id,
                    metodo_proyeccion=schemas.MetodoProyeccion.MANUAL,
                    valor_total=0
                )
            )
        db.bulk_save_objects(nuevos_items)
        db.commit()
        
    return db_escenario

def update_escenario(db: Session, escenario_id: int, updates: schemas.EscenarioUpdate):
    db_escenario = get_escenario(db, escenario_id)
    if not db_escenario:
        return None
        
    for key, value in updates.dict(exclude_unset=True).items():
        setattr(db_escenario, key, value)
        
    db.commit()
    db.refresh(db_escenario)
    return db_escenario

def delete_escenario(db: Session, escenario_id: int):
    db_escenario = get_escenario(db, escenario_id)
    if db_escenario:
        db.delete(db_escenario)
        db.commit()
        return True
    return False

# --- MOTOR DE PROYECCIÓN (MAGIC ENGINE) ---

def proyectar_escenario_automatico(db: Session, escenario_id: int, base_year: int, metodo: schemas.MetodoProyeccion, factor: float = 0):
    """
    Genera o actualiza los items del presupuesto basándose en la contabilidad histórica (MovimientoContable).
    """
    escenario = get_escenario(db, escenario_id)
    if not escenario: return None
    
    # 1. Obtener ejecución real del año base por cuenta
    # Agrupamos por cuenta y sumamos (crédito - débito para ingresos, débito - crédito para gastos? 
    # Simplifiquemos: sumamos saldo neto).
    
    # Asumimos que las cuentas de resultados (Gastos/Ingresos) son las que se presupuestan normalmente.
    # Filtramos movimientos del año base.
    
    # IMPORTANTE: MovimientoContable se enlaza con Documento para la fecha
    movimientos = db.query(
        MovimientoContable.cuenta_id,
        func.sum(MovimientoContable.debito).label("total_debito"),
        func.sum(MovimientoContable.credito).label("total_credito"),
        func.extract('month', Documento.fecha).label("mes")
    ).join(Documento, MovimientoContable.documento_id == Documento.id).join(
        PlanCuenta, MovimientoContable.cuenta_id == PlanCuenta.id
    ).filter(
        Documento.empresa_id == escenario.empresa_id,
        func.extract('year', Documento.fecha) == base_year,
        or_(
            PlanCuenta.codigo.like('4%'),
            PlanCuenta.codigo.like('5%'),
            PlanCuenta.codigo.like('6%'),
            PlanCuenta.codigo.like('7%')
        )
    ).group_by(
        MovimientoContable.cuenta_id,
        func.extract('month', Documento.fecha)
    ).all()
    
    # Estructura temporal para agrupar
    proyeccion_data = {} # {cuenta_id: {1: val, 2: val...}}
    
    for row in movimientos:
        cid = row.cuenta_id
        mes = int(row.mes)
        # Nota: La naturaleza de la cuenta define si es Debito - Credito o al revés.
        # Por ahora usaremos Debito - Credito como 'neto' pardo.
        # TODO: Refinar según naturaleza (Ingresos vs Gastos).
        neto = row.total_debito - row.total_credito
        
        if cid not in proyeccion_data:
            proyeccion_data[cid] = {m: 0.0 for m in range(1, 13)}
            
        proyeccion_data[cid][mes] += float(neto)
        
    # 2. Iterar y Crear/Actualizar Items
    items_created = 0
    
    # Obtener cuentas involucradas para saber naturaleza si fuese necesario
    # cuentas_ids = list(proyeccion_data.keys())
    # ...
    
    for cuenta_id, valores_mes in proyeccion_data.items():
        # Aplicar factor de ajuste
        # Factor 5.0 -> 5% -> Multiplicador 1.05
        # Si factor es 0, no cambia.
        multiplicador = 1 + (factor / 100.0)
        
        nuevo_total = 0
        attrs = {}
        for m in range(1, 13):
            val_base = valores_mes[m]
            val_proyectado = val_base * multiplicador
            attrs[f"mes_{m:02d}"] = val_proyectado
            nuevo_total += val_proyectado
            
        # Upsert Item
        item = db.query(models.PresupuestoItem).filter_by(escenario_id=escenario_id, cuenta_id=cuenta_id).first()
        
        if not item:
            item = models.PresupuestoItem(
                escenario_id=escenario_id,
                cuenta_id=cuenta_id,
                metodo_proyeccion=metodo,
                base_calculo=str(base_year),
                factor_ajuste=factor,
                **attrs,
                valor_total=nuevo_total
            )
            db.add(item)
            items_created += 1
        else:
            # Update existing
            item.metodo_proyeccion = metodo
            item.base_calculo = str(base_year)
            item.factor_ajuste = factor
            item.valor_total = nuevo_total
            for k, v in attrs.items():
                setattr(item, k, v)
    
    db.commit()
    return {"message": "Proyección completada", "items_procesados": len(proyeccion_data), "items_nuevos": items_created}

def get_items_escenario(db: Session, escenario_id: int):
    from app.models import PlanCuenta
    return db.query(models.PresupuestoItem).join(
        PlanCuenta, models.PresupuestoItem.cuenta_id == PlanCuenta.id
    ).filter(
        models.PresupuestoItem.escenario_id == escenario_id,
        or_(
            PlanCuenta.codigo.like('4%'),
            PlanCuenta.codigo.like('5%'),
            PlanCuenta.codigo.like('6%'),
            PlanCuenta.codigo.like('7%')
        )
    ).all()

def update_item_manual(db: Session, item_id: int, data: schemas.PresupuestoItemUpdate):
    item = db.query(models.PresupuestoItem).filter(models.PresupuestoItem.id == item_id).first()
    if not item: return None
    
    # Recalcular total si cambian los meses
    total = 0
    # Actualizar campos
    for key, value in data.dict(exclude_unset=True).items():
        if key.startswith("mes_"):
             setattr(item, key, value)
        elif key == "observacion":
             item.observacion = value
             
    # Recalcular total sumando propiedad actual
    item.valor_total = (
        item.mes_01 + item.mes_02 + item.mes_03 + item.mes_04 + 
        item.mes_05 + item.mes_06 + item.mes_07 + item.mes_08 + 
        item.mes_09 + item.mes_10 + item.mes_11 + item.mes_12
    )
    
    db.commit()
    db.refresh(item)
    return item

# --- REPORTE DE EJECUCIÓN ---

def calcular_ejecucion_comparativa(db: Session, escenario_id: int, mes_desde: int = 1, mes_hasta: int = 12):
    escenario = get_escenario(db, escenario_id)
    if not escenario: return None
    
    # 1. Obtener Presupuesto (Plan)
    items_presupuesto = get_items_escenario(db, escenario_id)
    
    # 2. Obtener Ejecución Real (Realidad) para el rango de meses seleccionado
    movimientos_reales = db.query(
        MovimientoContable.cuenta_id,
        func.sum(MovimientoContable.debito).label("total_debito"),
        func.sum(MovimientoContable.credito).label("total_credito")
    ).join(Documento, MovimientoContable.documento_id == Documento.id).filter(
        Documento.empresa_id == escenario.empresa_id,
        func.extract('year', Documento.fecha) == escenario.anio,
        func.extract('month', Documento.fecha) >= mes_desde,
        func.extract('month', Documento.fecha) <= mes_hasta
    ).group_by(
        MovimientoContable.cuenta_id
    ).all()
    
    real_map = {} # {cuenta_id: valor_neto}
    for row in movimientos_reales:
        cid = row.cuenta_id
        # Asumimos neto, aunque para ingresos (4) es crédito - débito. Lo simplificamos o evaluamos.
        # En contabilidad, cuentas 4 son naturaleza crédito. 5,6,7 son naturaleza débito.
        # Si queremos mostrar en positivo siempre para el reporte:
        c = db.query(PlanCuenta.codigo).filter(PlanCuenta.id == cid).first()
        if c and str(c[0]).startswith('4'):
            neto = row.total_credito - row.total_debito
        else:
            neto = row.total_debito - row.total_credito
        real_map[cid] = float(neto)
        
    # 3. Traer TODAS las cuentas de RESULTADO de la empresa para habilitar la mayorización
    todas_cuentas = db.query(PlanCuenta).filter(
        PlanCuenta.empresa_id == escenario.empresa_id,
        or_(
            PlanCuenta.codigo.like('4%'),
            PlanCuenta.codigo.like('5%'),
            PlanCuenta.codigo.like('6%'),
            PlanCuenta.codigo.like('7%')
        )
    ).all()
    map_cuentas = {c.id: c for c in todas_cuentas}
    
    # Preparar el diccionario de resultados acumulados
    resultados_agrupados = {
        c.id: {
            "cuenta_id": c.id,
            "codigo": c.codigo,
            "nombre": c.nombre,
            "nivel": c.nivel,
            "cuenta_padre_id": c.cuenta_padre_id,
            "presupuestado": 0.0,
            "ejecutado": 0.0
        } for c in todas_cuentas
    }
    
    # 4. Asignar Valores Base (Hojas)
    # 4a. Asignar Presupuesto
    for item in items_presupuesto:
        if item.cuenta_id in resultados_agrupados:
            val_plan_rango = 0.0
            # Sumar solo los meses del rango seleccionado
            for m in range(mes_desde, mes_hasta + 1):
                mes_key = f"mes_{m:02d}"
                val_plan_rango += getattr(item, mes_key, 0.0) or 0.0
            resultados_agrupados[item.cuenta_id]["presupuestado"] += val_plan_rango

    # 4b. Asignar Ejecución Real
    for cuenta_id, val_real in real_map.items():
        if cuenta_id in resultados_agrupados:
            resultados_agrupados[cuenta_id]["ejecutado"] += val_real
            
    # 5. Mayorización (Roll-Up Bubbling)
    # Ordenamos de mayor nivel a menor nivel, iterando para propagar valores al padre
    niveles_descendentes = sorted(list(set([c.nivel for c in todas_cuentas])), reverse=True)
    
    for nivel in niveles_descendentes:
        # Buscar todas las cuentas en este nivel
        cuentas_nivel = [c for c in resultados_agrupados.values() if c["nivel"] == nivel]
        for cuenta in cuentas_nivel:
            padre_id = cuenta["cuenta_padre_id"]
            if padre_id and padre_id in resultados_agrupados:
                # Sumarle los montos del hijo al padre
                resultados_agrupados[padre_id]["presupuestado"] += cuenta["presupuestado"]
                resultados_agrupados[padre_id]["ejecutado"] += cuenta["ejecutado"]
                
    # 6. Filtrar y Formatear Resultado Final
    # Solo devolver las cuentas que tengan algún monto (presupuestado o ejecutado) para no llenar de ceros
    reporte_items = []
    
    # Ordenar por codigo contable
    cuentas_ordenadas = sorted(resultados_agrupados.values(), key=lambda x: str(x["codigo"]))
    
    for cuenta in cuentas_ordenadas:
        if cuenta["presupuestado"] != 0 or cuenta["ejecutado"] != 0:
            val_plan = cuenta["presupuestado"]
            val_real = cuenta["ejecutado"]
            
            # Para cuentas 4 (Ingresos), la meta de presupuesto significa "Ganar más". 
            # Variacion Positiva = Superaste la meta. 
            variacion = val_real - val_plan if cuenta["codigo"].startswith('4') else val_plan - val_real
            
            porc = 0.0
            if val_plan != 0:
                porc = (val_real / val_plan) * 100
            elif val_real > 0:
                porc = 100.0
                
            reporte_items.append({
                "cuenta_id": cuenta["cuenta_id"],
                "codigo": cuenta["codigo"],
                "nombre": cuenta["nombre"],
                "nivel": cuenta["nivel"],
                "cuenta_padre_id": cuenta["cuenta_padre_id"],
                "rango": {
                    "presupuestado": val_plan,
                    "ejecutado": val_real,
                    "variacion": variacion,
                    "porcentaje_ejecucion": porc
                }
            })
            
    return {"escenario": escenario, "items": reporte_items}
