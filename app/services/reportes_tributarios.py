from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict, Any
from datetime import date
from fastapi import HTTPException

from app.models.configuracion_reporte import ConfiguracionReporte
from app.models.movimiento_contable import MovimientoContable
from app.models.plan_cuenta import PlanCuenta
from app.models.documento import Documento

def get_configuracion(db: Session, empresa_id: int, tipo_reporte: str) -> List[ConfiguracionReporte]:
    """ Obtiene la configuración de renglones para un reporte específico. """
    return db.query(ConfiguracionReporte).filter(
        ConfiguracionReporte.empresa_id == empresa_id,
        ConfiguracionReporte.tipo_reporte == tipo_reporte
    ).order_by(ConfiguracionReporte.id).all()

def save_configuracion(db: Session, empresa_id: int, tipo_reporte: str, configs: List[Dict[str, Any]]):
    """ Guarda o actualiza la configuración de renglones. """
    # 1. Limpiar config anterior (Estrategia simple: Borrar y re-crear, o Upsert si r.id existe)
    # Por simplicidad y dado que son pocos renglones, borramos los de este tipo y recreamos.
    db.query(ConfiguracionReporte).filter(
        ConfiguracionReporte.empresa_id == empresa_id,
        ConfiguracionReporte.tipo_reporte == tipo_reporte
    ).delete()
    
    for c in configs:
        # Si es Header, marcamos renglon especial
        renglon_val = str(c.get('renglon'))
        concepto_val = c.get('concepto')
        cuentas_val = c.get('cuentas_ids', [])
        
        if c.get('is_header'):
            renglon_val = "HEADER"
            cuentas_val = ["SECTION"]

        nueva_conf = ConfiguracionReporte(
            empresa_id=empresa_id,
            tipo_reporte=tipo_reporte,
            renglon=renglon_val,
            concepto=concepto_val,
            cuentas_ids=cuentas_val
        )
        db.add(nueva_conf)
    
    db.commit()
    return get_configuracion(db, empresa_id, tipo_reporte)

def calcular_declaracion_iva(db: Session, empresa_id: int, anio: int, periodo: str) -> Dict[str, Any]:
    """
    Calcula los valores para el Formulario 300 basado en Movimientos Contables.
    periodo: '01' (Ene-Feb), '02' (Mar-Abr), etc.
    """
    
    # 1. Definir Fechas del Periodo
    # Simplificación Bimestral
    periodos_map = {
        '01': ((date(anio, 1, 1), date(anio, 2, 28) if anio % 4 != 0 else date(anio, 2, 29))), # Ajustar bisiesto si es critico
        '02': ((date(anio, 3, 1), date(anio, 4, 30))),
        '03': ((date(anio, 5, 1), date(anio, 6, 30))),
        '04': ((date(anio, 7, 1), date(anio, 8, 31))),
        '05': ((date(anio, 9, 1), date(anio, 10, 31))),
        '06': ((date(anio, 11, 1), date(anio, 12, 31))),
    }
    
    # Manejo básico de fecha fin mes 2 (mejor usar calendar.monthrange, pero standard lib ok)
    import calendar
    rango = periodos_map.get(periodo)
    if not rango:
        # Default o error
        rango = (date(anio, 1, 1), date(anio, 1, 31))
    
    f_inicio, f_fin_base = rango
    # Ajuste fino de fin de mes
    last_day = calendar.monthrange(f_fin_base.year, f_fin_base.month)[1]
    f_fin = date(f_fin_base.year, f_fin_base.month, last_day)

    # 2. Obtener Configuración
    configs = get_configuracion(db, empresa_id, 'IVA')
    if not configs:
        # --- AUTO-SEEDING DEFAULT IVA ---
        default_iva = [
            # INGRESOS
            {"is_header": True, "concepto": "Ingresos"},
            {"renglon": "27", "concepto": "Ingresos Operaciones 5%", "cuentas_ids": []},
            {"renglon": "28", "concepto": "Ingresos Operaciones General (19%)", "cuentas_ids": []},
            {"renglon": "35", "concepto": "Ingresos Exentos", "cuentas_ids": []},
            {"renglon": "39", "concepto": "Operaciones excluidas", "cuentas_ids": []},
            {"renglon": "40", "concepto": "Ingresos No Gravados", "cuentas_ids": []},
            {"renglon": "41", "concepto": "Total Ingresos Brutos", "cuentas_ids": ["[27]+[28]+[35]+[39]+[40]"]}, 
            {"renglon": "42", "concepto": "Devoluciones en ventas anuladas", "cuentas_ids": []},
            {"renglon": "43", "concepto": "Total Ingresos Netos", "cuentas_ids": ["[41]-[42]"]},

            # COMPRAS
            {"is_header": True, "concepto": "Compras"},
            {"renglon": "50", "concepto": "Bienes gravados 5%", "cuentas_ids": []},
            {"renglon": "51", "concepto": "Bienes gravados 19%", "cuentas_ids": []},
            {"renglon": "52", "concepto": "Servicios gravados 5%", "cuentas_ids": []},
            {"renglon": "53", "concepto": "Servicios gravados 19%", "cuentas_ids": []},
            {"renglon": "54", "concepto": "Bienes/Servicios excluidos/exentos", "cuentas_ids": []},
            {"renglon": "55", "concepto": "Total compras brutas", "cuentas_ids": ["[50]+[51]+[52]+[53]+[54]"]},
            {"renglon": "56", "concepto": "Devoluciones en compras", "cuentas_ids": []},
            {"renglon": "57", "concepto": "Total compras netas", "cuentas_ids": ["[55]-[56]"]},

            # IMPUESTO GENERADO
            {"is_header": True, "concepto": "Impuesto Generado"},
            {"renglon": "58", "concepto": "IVA Generado 5%", "cuentas_ids": []},
            {"renglon": "59", "concepto": "IVA Generado 19%", "cuentas_ids": []},
            {"renglon": "66", "concepto": "IVA recuperado en devoluciones", "cuentas_ids": []},
            {"renglon": "67", "concepto": "Total impuesto generado", "cuentas_ids": ["[58]+[59]+[66]"]},

            # IMPUESTO DESCONTABLE
            {"is_header": True, "concepto": "Impuesto Descontable"},
            {"renglon": "71", "concepto": "IVA Descontable Compras 5%", "cuentas_ids": []},
            {"renglon": "72", "concepto": "IVA Descontable Compras 19%", "cuentas_ids": []},
            {"renglon": "74", "concepto": "Servicios gravados 5%", "cuentas_ids": []},
            {"renglon": "75", "concepto": "Servicios gravados 19%", "cuentas_ids": []},
            {"renglon": "77", "concepto": "Total impuesto pagado", "cuentas_ids": ["[71]+[72]+[74]+[75]"]},
            {"renglon": "78", "concepto": "IVA Retenido servicios no domic.", "cuentas_ids": []},
            {"renglon": "79", "concepto": "IVA por devoluciones ventas", "cuentas_ids": []},
            {"renglon": "80", "concepto": "Ajuste impuestos descontables", "cuentas_ids": []},
            {"renglon": "81", "concepto": "Total impuestos descontables", "cuentas_ids": ["[77]+[78]+[79]-[80]"]},

            # SALDOS
            {"is_header": True, "concepto": "Control de Saldos"},
            {"renglon": "82", "concepto": "Saldo a pagar", "cuentas_ids": ["max(0, [67]-[81])"]}, 
            {"renglon": "83", "concepto": "Saldo a favor", "cuentas_ids": ["max(0, [81]-[67])"]},
            {"renglon": "85", "concepto": "Retenciones IVA practicadas", "cuentas_ids": []},
            {"renglon": "86", "concepto": "Saldo a pagar final", "cuentas_ids": ["[82]-[85]"]},
        ]
        
        configs = save_configuracion(db, empresa_id, 'IVA', default_iva)

    resultados = []
    
    for conf in configs:
        renglon_val = 0
        codigos_cuentas = conf.cuentas_ids # ej: ["413501", "413502"]
        
        if codigos_cuentas:
            # Buscar movimientos
            # Join con PlanCuenta para filtrar por codigo
            # Filter por fecha de Documento
            query = db.query(
                func.sum(MovimientoContable.debito).label("total_debito"),
                func.sum(MovimientoContable.credito).label("total_credito")
            ).join(MovimientoContable.cuenta).join(MovimientoContable.documento).filter(
                Documento.empresa_id == empresa_id,
                Documento.fecha >= f_inicio,
                Documento.fecha <= f_fin,
                Documento.estado == 'ACTIVO', # Solo documentos activos
                PlanCuenta.codigo.in_(codigos_cuentas)
            )
            
            saldo = query.first()
            debito = saldo.total_debito or 0
            credito = saldo.total_credito or 0
            
            # Determinar Naturaleza basada en el primer dígito de la primera cuenta configurada
            # (Asumimos homogeneidad en el renglón)
            primer_digito = codigos_cuentas[0][0] if len(codigos_cuentas[0]) > 0 else '1'
            
            if primer_digito in ['1', '5', '6']:
                # Naturaleza Débito
                renglon_val = debito - credito
            else:
                # Naturaleza Crédito (2, 3, 4)
                renglon_val = credito - debito
        
        resultados.append({
            "r": conf.renglon,
            "c": conf.concepto,
            "v": 0.0, # Placeholder
            "cuentas": codigos_cuentas,
            "is_header": (conf.renglon == "HEADER")
        })

    # --- FASE 2: CÁLCULO DE VALORES ---
    # Diccionario temporal para formulas: { "27": 1000.0, ... }
    valores_renglon = {}

    # Paso 2.1: Calcular Cuentas Contables (Base)
    for res in resultados:
        if res["is_header"]: continue
        
        codigos = res["cuentas"]
        # Si NO es formula (no tiene brackets ni operadores basicos) y tiene numeros
        es_formula = False
        if codigos and isinstance(codigos, list):
             # Si el primer elemento parece una formula (e.g. "[27]+[28]")
             # codigos es lista de strings. En ParametrosView mandamos 'cuentas' como string unida.
             # Pero en 'save_configuracion', 'cuentas_ids' se guarda como lista.
             # Si era formula, ParametrosView mando: cuentas_ids=["[27]+[28]"] (un elemento)
             if len(codigos) == 1 and ('[' in codigos[0] or '+' in codigos[0]):
                 es_formula = True
        
        if not es_formula and codigos:
            # Lógica Existente de Query
            query = db.query(
                func.sum(MovimientoContable.debito).label("total_debito"),
                func.sum(MovimientoContable.credito).label("total_credito")
            ).join(MovimientoContable.cuenta).join(MovimientoContable.documento).filter(
                Documento.empresa_id == empresa_id,
                Documento.fecha >= f_inicio,
                Documento.fecha <= f_fin,
                Documento.estado == 'ACTIVO',
                PlanCuenta.codigo.in_(codigos)
            )
            
            saldo = query.first()
            debito = saldo.total_debito or 0
            credito = saldo.total_credito or 0
            
            val = 0.0
            primer_digito = codigos[0][0] if len(codigos[0]) > 0 else '1'
            if primer_digito in ['1', '5', '6', '7']: # Gastos/Costos/Activos -> Debito
                val = debito - credito
            else: # Ingresos/Pasivos -> Credito
                val = credito - debito
            
            res["v"] = val
            valores_renglon[res["r"]] = val

    # Paso 2.2: Calcular Fórmulas
    # Se hace en una segunda pasada. Si hay dependencias anidadas, se necesitaria un bucle o orden topologico.
    # Asumimos formulas simples que dependen de valores base ya calculados.
    # OJO: Si [81] depende de [77] que es formula, necesitamos orden.
    # Solucion simple: Repetir pasada 2 o 3 veces para resolver dependencias. (3 pasadas es seguro para niveles normales)
    
    import re
    
    def evaluar_formula(formula, valores):
        # 1. Reemplazar [XX] por valores
        # Regex para encontrar [DIGITOS]
        pattern = re.compile(r'\[(\w+)\]')
        
        def replacement(match):
            key = match.group(1)
            return str(valores.get(key, 0.0))
        
        expr = pattern.sub(replacement, formula)
        
        # 2. Evaluar
        try:
            # Permitir max, min
            safe_env = {"max": max, "min": min, "__builtins__": None}
            return float(eval(expr, safe_env))
        except Exception as e:
            print(f"Error evaluando formula {formula} -> {expr}: {e}")
            return 0.0

    for _ in range(3): # 3 pasadas para resolver dependencias
        for res in resultados:
            if res["is_header"]: continue
            codigos = res["cuentas"]
            
            # Chequear si es formula
            if codigos and len(codigos) == 1 and ('[' in codigos[0] or '+' in codigos[0]):
                formula_str = codigos[0]
                val_calc = evaluar_formula(formula_str, valores_renglon)
                res["v"] = val_calc
                valores_renglon[res["r"]] = val_calc


    return {
        "periodo": f"{anio}-{periodo}",
        "fecha_inicio": f_inicio,
        "fecha_fin": f_fin,
        "renglones": resultados
    }

def calcular_declaracion_retefuente(db: Session, empresa_id: int, anio: int, periodo: str) -> Dict[str, Any]:
    """
    Calcula Formulario 350 (Mensual).
    periodo: '01' (Enero), '02' (Febrero)...
    """
    import calendar
    
    # 1. Definir Fechas (Mensual)
    mes = int(periodo)
    f_inicio = date(anio, mes, 1)
    last_day = calendar.monthrange(anio, mes)[1]
    f_fin = date(anio, mes, last_day)

    # 2. Configuración
    configs = get_configuracion(db, empresa_id, 'RETEFUENTE')
    
    # --- AUTO-SEEDING CONFIG SI NO EXISTE (MVP Helper) ---
    if not configs:
        default_rete = [
            {"renglon": "27", "concepto": "Rentas de trabajo (Salarios)", "cuentas_ids": ["236505"]},
            {"renglon": "29", "concepto": "Compras", "cuentas_ids": ["236540"]},
            {"renglon": "30", "concepto": "Honorarios", "cuentas_ids": ["236515"]},
            {"renglon": "31", "concepto": "Servicios", "cuentas_ids": ["236525"]},
            {"renglon": "32", "concepto": "Arrendamientos", "cuentas_ids": ["236530"]},
            {"renglon": "40", "concepto": "Total Retenciones", "cuentas_ids": []} # Calculado o sumado? Mejor sumar todo
        ]
        # Guardamos y recargamos
        configs = save_configuracion(db, empresa_id, 'RETEFUENTE', default_rete)
    # -----------------------------------------------------

    resultados = []
    
    for conf in configs:
        renglon_val = 0.0
        codigos_cuentas = conf.cuentas_ids
        
        if codigos_cuentas:
            query = db.query(
                func.sum(MovimientoContable.debito).label("total_debito"),
                func.sum(MovimientoContable.credito).label("total_credito")
            ).join(MovimientoContable.cuenta).join(MovimientoContable.documento).filter(
                MovimientoContable.empresa_id == empresa_id,
                Documento.fecha >= f_inicio,
                Documento.fecha <= f_fin,
                Documento.estado == 'ACTIVO',
                PlanCuenta.codigo.in_(codigos_cuentas)
            )
            
            saldo = query.first()
            debito = saldo.total_debito or 0
            credito = saldo.total_credito or 0
            
            # Retefuente es Pasivo (2365) => Naturaleza Crédito
            # Saldo = Crédito - Débito (Lo que retuve menos lo que ajusté/pagué si aplica, 
            # aunque declaración suele ser lo causado en el periodo, es decir Créditos netos).
            renglon_val = credito - debito
        
        resultados.append({
            "r": conf.renglon,
            "c": conf.concepto,
            "v": float(renglon_val) if renglon_val > 0 else 0.0, # Retefuente no suele ser negativa
            "cuentas": codigos_cuentas
        })

    return {
        "periodo": f"{anio}-{periodo}",
        "fecha_inicio": f_inicio,
        "fecha_fin": f_fin,
        "renglones": resultados
    }

def calcular_declaracion_renta(db: Session, empresa_id: int, anio: int) -> Dict[str, Any]:
    """
    Calcula Formulario 110 (Anual) Declaración de Renta.
    """
    # 1. Definir Fechas (Anual)
    f_inicio = date(anio, 1, 1)
    f_fin = date(anio, 12, 31)

    # 2. Configuración
    configs = get_configuracion(db, empresa_id, 'RENTA')
    
    # --- AUTO-SEEDING CONFIG SI NO EXISTE ---
    if not configs:
        default_renta = [
            # Patrimonio (Saldos a 31 de Dic) - En teoria DEBERIAN ser fiscales, no contables.
            {"renglon": "36", "concepto": "Efectivo y equivalentes", "cuentas_ids": ["11"]},
            {"renglon": "37", "concepto": "Inversiones", "cuentas_ids": ["12"]},
            {"renglon": "38", "concepto": "Cuentas por cobrar", "cuentas_ids": ["13"]},
            {"renglon": "39", "concepto": "Inventarios", "cuentas_ids": ["14"]},
            {"renglon": "40", "concepto": "Activos Intangibles", "cuentas_ids": ["16"]},
            {"renglon": "42", "concepto": "Propiedades, planta y equipo", "cuentas_ids": ["15"]},
            {"renglon": "43", "concepto": "Otros activos", "cuentas_ids": ["17", "18", "19"]},
            {"renglon": "45", "concepto": "Pasivos", "cuentas_ids": ["2"]},
            
            # Ingresos (Movimiento del año)
            {"renglon": "47", "concepto": "Ingresos Brutos Act. Ordinarias", "cuentas_ids": ["41"]},
            {"renglon": "48", "concepto": "Ingresos Financieros", "cuentas_ids": ["4210"]},
            {"renglon": "51", "concepto": "Otros Ingresos", "cuentas_ids": ["42"]},

            # Costos y Gastos (Movimiento del año)
            {"renglon": "62", "concepto": "Costo de Ventas", "cuentas_ids": ["61", "71"]},
            {"renglon": "63", "concepto": "Gastos de Administración", "cuentas_ids": ["51"]},
            {"renglon": "64", "concepto": "Gastos de Distribución y Ventas", "cuentas_ids": ["52"]},
            {"renglon": "65", "concepto": "Gastos Financieros", "cuentas_ids": ["53"]},
        ]
        # Guardamos y recargamos
        configs = save_configuracion(db, empresa_id, 'RENTA', default_renta)
    # -----------------------------------------------------

    resultados = []
    
    for conf in configs:
        renglon_val = 0.0
        codigos_cuentas = conf.cuentas_ids
        
        if codigos_cuentas:
            # Estrategia de búsqueda depende del tipo de cuenta:
            # SIEMPRE consultamos movimientos del año.
            # Para CUENTAS DE BALANCE (1, 2, 3), el saldo fiscal suele ser el saldo final a 31/Dic.
            #     Saldo = SaldoInicial + Debitos - Creditos (o viceversa segun naturaleza).
            #     PERO aqui 'MovimientoContable' son transacciones. Si queremos Saldo Final,
            #     tecnicamente deberiamos sumar TODOS los movimientos HISTORICOS hasta f_fin.
            #     **SIMPLIFICACION**: Asumimos que el usuario migró saldos iniciales con fecha Enero 1 del año.
            #     Entonces sumamos movimientos desde f_inicio hasta f_fin.
            
            query = db.query(
                func.sum(MovimientoContable.debito).label("total_debito"),
                func.sum(MovimientoContable.credito).label("total_credito")
            ).join(MovimientoContable.cuenta).join(MovimientoContable.documento).filter(
                MovimientoContable.empresa_id == empresa_id,
                Documento.fecha >= f_inicio,
                Documento.fecha <= f_fin,
                Documento.estado == 'ACTIVO',
                # Busqueda flexible por prefijo ("EMPIEZA CON")
                # PlanCuenta.codigo.like(f"{codigo}%") ... esto requiere un OR grande si son varios
            )
            
            # Construcción dinámica del filtro OR para los prefijos de cuenta
            from sqlalchemy import or_
            filtros_cuenta = [PlanCuenta.codigo.like(f"{code}%") for code in codigos_cuentas]
            query = query.filter(or_(*filtros_cuenta))
            
            saldo = query.first()
            debito = saldo.total_debito or 0
            credito = saldo.total_credito or 0
            
            # Determinamos Naturaleza (Simplificado: 1,5,6,7 = Debito; 2,3,4 = Credito)
            primer_digito = codigos_cuentas[0][0] if len(codigos_cuentas[0]) > 0 else '1'
            
            if primer_digito in ['1', '5', '6', '7']:
                renglon_val = debito - credito
            else:
                renglon_val = credito - debito

        resultados.append({
            "r": conf.renglon,
            "c": conf.concepto,
            "v": float(renglon_val),
            "cuentas": codigos_cuentas
        })

    return {
        "periodo": f"{anio}-ANUAL",
        "fecha_inicio": f_inicio,
        "fecha_fin": f_fin,
        "renglones": resultados
    }
