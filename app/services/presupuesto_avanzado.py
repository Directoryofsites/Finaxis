from sqlalchemy.orm import Session
from sqlalchemy import func
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
    ).join(Documento, MovimientoContable.documento_id == Documento.id).filter(
        Documento.empresa_id == escenario.empresa_id,
        func.extract('year', Documento.fecha) == base_year
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
    return db.query(models.PresupuestoItem).filter(models.PresupuestoItem.escenario_id == escenario_id).all()

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

def calcular_ejecucion_comparativa(db: Session, escenario_id: int):
    escenario = get_escenario(db, escenario_id)
    if not escenario: return None
    
    # 1. Obtener Presupuesto (Plan)
    items_presupuesto = get_items_escenario(db, escenario_id)
    plan_map = {item.cuenta_id: item for item in items_presupuesto}
    
    # 2. Obtener Ejecución Real (Realidad)
    # Similar a la proyección, pero del año ACTUAL del escenario
    movimientos_reales = db.query(
        MovimientoContable.cuenta_id,
        func.sum(MovimientoContable.debito).label("total_debito"),
        func.sum(MovimientoContable.credito).label("total_credito"),
        func.extract('month', Documento.fecha).label("mes")
    ).join(Documento, MovimientoContable.documento_id == Documento.id).filter(
        Documento.empresa_id == escenario.empresa_id,
        func.extract('year', Documento.fecha) == escenario.anio
    ).group_by(
        MovimientoContable.cuenta_id,
        func.extract('month', Documento.fecha)
    ).all()
    
    real_map = {} # {cuenta_id: {mes: valor}}
    
    for row in movimientos_reales:
        cid = row.cuenta_id
        mes = int(row.mes)
        neto = row.total_debito - row.total_credito # Asumimos neto por ahora
        
        if cid not in real_map:
            real_map[cid] = {m: 0.0 for m in range(1, 13)}
        real_map[cid][mes] += float(neto)
        
    # 3. Unificar Cuentas
    all_cuentas_ids = set(plan_map.keys()).union(set(real_map.keys()))
    
    reporte_items = []
    
    for cid in all_cuentas_ids:
        # Obtener datos de cuenta (Plan o Real)
        # Necesitamos el objeto cuenta para nombre/codigo. 
        # Si está en plan, lo tenemos fácil. Si solo está en real, consulta extra o cache.
        cuenta_obj = None
        codigo = "N/A"
        nombre = "Cuenta Desconocida"
        
        if cid in plan_map:
             if plan_map[cid].cuenta:
                 codigo = plan_map[cid].cuenta.codigo
                 nombre = plan_map[cid].cuenta.nombre
        else:
             # Fetch ad-hoc si solo tuvo movimiento real sin presupuesto
             c = db.query(PlanCuenta).filter(PlanCuenta.id == cid).first()
             if c:
                 codigo = c.codigo
                 nombre = c.nombre
        
        # Construir Item
        item_data = {
            "cuenta_id": cid,
            "codigo": codigo,
            "nombre": nombre,
            "total_anual": {"presupuestado": 0, "ejecutado": 0, "variacion": 0, "porcentaje_ejecucion": 0}
        }
        
        for m in range(1, 13):
            mes_key = f"mes_{m:02d}"
            # Plan
            val_plan = 0
            if cid in plan_map:
                val_plan = getattr(plan_map[cid], mes_key, 0) or 0
                
            # Real
            val_real = 0
            if cid in real_map:
                val_real = real_map[cid].get(m, 0)
                
            variacion = val_plan - val_real # Positivo = Ahorro (en gastos), Negativo = Sobrecosto
            porc = 0
            if val_plan != 0:
                porc = (val_real / val_plan) * 100
            elif val_real > 0:
                porc = 100 # No presupuestado pero ejecutado
                
            # Mapear nombre mes español
            nombres_meses = ["enero", "febrero", "marzo", "abril", "mayo", "junio", 
                             "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
            
            nome_mes = nombres_meses[m-1]
            
            item_data[nome_mes] = {
                "presupuestado": val_plan,
                "ejecutado": val_real,
                "variacion": variacion,
                "porcentaje_ejecucion": porc
            }
            
            # Acumular Anual
            item_data["total_anual"]["presupuestado"] += val_plan
            item_data["total_anual"]["ejecutado"] += val_real
            
        # Calcular variacion total final
        t_plan = item_data["total_anual"]["presupuestado"]
        t_real = item_data["total_anual"]["ejecutado"]
        item_data["total_anual"]["variacion"] = t_plan - t_real
        if t_plan != 0:
            item_data["total_anual"]["porcentaje_ejecucion"] = (t_real / t_plan) * 100
        elif t_real > 0:
             item_data["total_anual"]["porcentaje_ejecucion"] = 100
             
        reporte_items.append(item_data)
        
    return {"escenario": escenario, "items": reporte_items}
