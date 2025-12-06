# app/services/dashboard.py (REEMPLAZO COMPLETO - FIX FINAL DE SUSTITUCIÓN DE MARGEN BRUTO)

from sqlalchemy.orm import Session
from sqlalchemy import func, case, and_
from typing import List, Dict
from datetime import date
from decimal import Decimal
from fastapi import HTTPException, status

from app.models.cupo_adicional import CupoAdicional


from ..models import movimiento_contable as models_mov_cont
from ..models import documento as models_doc
from ..models import plan_cuenta as models_pc
from ..models import empresa as models_empresa # <--- AGREGAR ESTA LÍNEA

from datetime import date, timedelta
import calendar
from typing import Optional # <--- Asegúrate de importar esto arriba

from ..schemas import dashboard as schemas_dashboard

# ==========================================================
# 1. DEFINICIÓN DE CONSTANTES Y PREFIJOS (PUC)
# ==========================================================
ACTIVO_PREFIJO = '1'
PASIVO_PREFIJO = '2'
PATRIMONIO_PREFIJO = '3'
INGRESOS_PREFIJO = '4' 
GASTOS_PREFIJOS = ('5', '8') 
COSTO_VENTAS_PREFIJO = '6'
COSTO_PRODUCCION_PREFIJO = '7' 

# Detalle de Corriente
CUENTAS_ACTIVO_CORRIENTE_PREFIJOS = ('11', '12', '13', '14') 
CUENTA_INVENTARIOS_INICIO = '14' 
CUENTAS_PASIVO_CORRIENTE_PREFIJOS = ('21', '22', '23', '24') 
MAX_TOLERANCE = Decimal('0.0000001') 


def get_escenario_estrategico(ratios: Dict[str, Decimal], capital_trabajo_neto: Decimal, patrimonio_total: Decimal) -> Dict:
    """
    Motor del Sistema de Evaluación de Escenarios Estratégicos (SEEE).
    """
    rc = ratios['razon_corriente']
    pa = ratios['prueba_acida']
    end = ratios['nivel_endeudamiento'] / Decimal('100') 
    roe = ratios['rentabilidad_patrimonio'] / Decimal('100')
    mn = ratios['margen_neto_utilidad'] / Decimal('100')
    mbu = ratios['margen_bruto_utilidad'] / Decimal('100') 
    ctn = capital_trabajo_neto
    
    # 0. AUDITORÍA PREVIA Y FALLBACK CRÍTICO (El check de 100% se ha movido al cálculo final)
    if patrimonio_total.copy_abs() < MAX_TOLERANCE or mn > Decimal('0.70') or roe.copy_abs() > Decimal('5.0'): 
        return {
            'escenario_general': 3,
            'texto_interpretativo': f"Análisis en la frontera (Vigilancia). Detectamos una posible **anomalía en los datos de Rentabilidad o Patrimonio** (ej. Patrimonio Total ≈ $0). Los indicadores son atípicos y no encajan en ningún escenario puro. Se requiere una auditoría manual inmediata.",
            'recomendaciones_breves': ["Realizar una auditoría inmediata de las cuentas de Ingresos, Gastos y Patrimonio.", "Verificar la correcta contabilización de los asientos de cierre."]
        }

    # 5. CRÍTICO (💀)
    if (
        rc < Decimal('1.0') and ctn <= Decimal('0.0') and end > Decimal('0.8') and mn <= Decimal('0.0')
    ):
        return {
            'escenario_general': 5,
            'texto_interpretativo': "Situación crítica. La empresa presenta insolvencia estructural a corto plazo y una dependencia extrema del pasivo para financiarse, junto con pérdidas operativas. Existe un riesgo inminente de incumplimiento y pérdida de patrimonio.",
            'recomendaciones_breves': ["Inyección urgente de capital.", "Reestructuración profunda de pasivos a largo plazo.", "Análisis de viabilidad del negocio y posible liquidación."]
        }
    
    # 4. RIESGO (🚨)
    if (
        (rc < Decimal('1.0') or ctn < Decimal('0.0')) and end > Decimal('0.7') and roe <= Decimal('0.0')
    ):
        return {
            'escenario_general': 4,
            'texto_interpretativo': "Riesgo alto. La falta de liquidez (RC < 1 o CTN negativo) y el alto nivel de endeudamiento (más del 70% de activos financiados con deuda) sugieren un apalancamiento riesgoso que no está siendo compensado con rentabilidad.",
            'recomendaciones_breves': ["Venta de activos improductivos para reducir deuda.", "Revisar la estrategia de precios para mejorar margen.", "Negociar plazos de pago con proveedores."]
        }

    # 1.5. FORTALEZA (EXCESO DE CAPITAL OCIOSO)
    if (
        rc > Decimal('4.0') and pa > Decimal('3.0') and end < Decimal('0.30') and mbu > Decimal('0.35')
    ):
        return {
            'escenario_general': 2, 
            'texto_interpretativo': "Escenario de **FORTALEZA (Capital Ocioso)**. La empresa exhibe una liquidez extrema (RC > 4.0x) y un endeudamiento muy bajo, con un Margen Bruto sólido. Esto indica una robusta fortaleza financiera, pero la **Liquidez Excesiva** genera un riesgo de **capital inactivo** que está reduciendo la Rentabilidad del Activo potencial.",
            'recomendaciones_breves': ["Realizar un análisis de la estructura de activos para reducir capital ocioso.", "Evaluar oportunidades de inversión para generar mayor retorno.", "Optimizar el uso de los recursos."]}


    # 3. VIGILANCIA (⚠️)
    if ( 
        (rc < Decimal('1.5') and pa < Decimal('1.0')) or # Liquidez dependiente de inventarios
        (end >= Decimal('0.60') and end <= Decimal('0.70')) or # Endeudamiento alto pero no crítico
        (mn < Decimal('0.05') or roe < Decimal('0.10')) or # Margen/Rentabilidad bajos
        (mbu < Decimal('0.20')) # Margen Bruto bajo
    ):
        return {
            'escenario_general': 3,
            'texto_interpretativo': "Escenario de Vigilancia. Los indicadores muestran un equilibrio frágil. La liquidez es dependiente de inventarios, o la rentabilidad está comprometida por un bajo Margen Bruto. Es un momento clave para ajustes estratégicos.",
            'recomendaciones_breves': ["Optimizar la gestión de inventarios para reducir dependencia.", "Revisar la estructura de costos directos para mejorar el Margen Bruto.", "Estabilizar el nivel de endeudamiento."]
        }
        
    # 2. ESTABLE (📊) - Rango Estándar (FIX: MBU 100% ACEPTADO EN EL LÍMITE SUPERIOR Y SIN LÍMITES EN RENTABILIDAD)
    if ( 
        (rc >= Decimal('1.5') and rc <= Decimal('3.5')) and 
        (pa >= Decimal('1.0') and pa <= Decimal('2.5')) and 
        (end < Decimal('0.30') or (end >= Decimal('0.30') and end <= Decimal('0.60'))) and # Acepta bajo endeudamiento O moderado
        (mn >= Decimal('0.05')) and # Quitamos el límite superior de Margen Neto
        (roe >= Decimal('0.10')) and # Quitamos el límite superior de ROE
        (mbu >= Decimal('0.20') and mbu <= Decimal('1.00')) # MBU ACEPTADO hasta 100%
    ):
        return {
            'escenario_general': 2,
            'texto_interpretativo': "Escenario Estable. La empresa mantiene un sano equilibrio en sus indicadores. Muestra **excelente liquidez o liquidez funcional** y endeudamiento bajo a moderado. La **Rentabilidad (MN y ROE) es superior al rango estándar**, lo que indica una gestión eficiente y solidez financiera.",
            'recomendaciones_breves': ["Buscar eficiencias operativas adicionales para mejorar márgenes.", "Evaluar oportunidades de inversión para optimizar activos.", "Mantener una política de endeudamiento prudente."]
        }

    # 1. ÓPTIMO (📈) - Rango Superior (Prioriza la liquidez y la rentabilidad)
    if (
        rc > Decimal('2.0') and pa > Decimal('1.5') and end < Decimal('0.30') and mn > Decimal('0.20') and roe > Decimal('0.25') and mbu > Decimal('0.40')
    ):
        return {
            'escenario_general': 1,
            'texto_interpretativo': "Escenario Óptimo (Sólido y eficiente). La empresa exhibe una fuerte liquidez, bajo riesgo de apalancamiento y una rentabilidad superior en todos los niveles, incluyendo un Margen Bruto excelente.",
            'recomendaciones_breves': ["Evaluar reinversión productiva o distribución de utilidades.", "Buscar oportunidades de expansión y apalancamiento estratégico para maximizar valor.", "Continuar con el control estricto de costos y la innovación."]
        }
    
    # FALLBACK FINAL
    return {
        'escenario_general': 3, 
        'texto_interpretativo': "Análisis en la frontera (Vigilancia). Los indicadores se encuentran en los límites de múltiples escenarios o los datos son atípicos. Se asigna un estado de vigilancia hasta una auditoría manual para determinar el riesgo exacto.",
        'recomendaciones_breves': ["Realizar una auditoría manual de los indicadores y datos contables.", "Revisar la coherencia de los datos para periodos similares."]
    }


# ==========================================================
# 3. FUNCIONES AUXILIARES DE CONSULTA Y SALDOS
# ==========================================================

def get_saldos_balance_acumulado(db: Session, empresa_id: int, fecha_fin: date) -> List: 
    """Consulta consolidada de Balance (Clases 1, 2, 3) hasta la fecha de corte."""
    Mov = models_mov_cont.MovimientoContable
    Doc = models_doc.Documento
    PC = models_pc.PlanCuenta
    
    q_saldos_acumulados = db.query(
        PC.codigo.label('codigo'),
        func.sum(Mov.debito).label('total_debito'),
        func.sum(Mov.credito).label('total_credito'),
    ).join(Doc, Doc.id == Mov.documento_id).join(PC, PC.id == Mov.cuenta_id).filter(
        Doc.empresa_id == empresa_id, 
        Doc.anulado == False,
        Doc.fecha <= fecha_fin,
        # Solo cuentas de balance (Clases 1, 2, 3)
        PC.codigo.startswith(ACTIVO_PREFIJO) | 
        PC.codigo.startswith(PASIVO_PREFIJO) | 
        PC.codigo.startswith(PATRIMONIO_PREFIJO)
    ).group_by(PC.codigo).all()
    
    return q_saldos_acumulados

def get_saldos_pyg_periodo(db: Session, empresa_id: int, fecha_inicio: date, fecha_fin: date) -> List:
    """Consulta consolidada de PyG (Clases 4, 5, 6, 7) para un periodo específico."""
    Mov = models_mov_cont.MovimientoContable
    Doc = models_doc.Documento
    PC = models_pc.PlanCuenta
    
    q_saldos_periodo = db.query(
        PC.codigo.label('codigo'),
        func.sum(Mov.debito).label('total_debito'),
        func.sum(Mov.credito).label('total_credito'),
    ).join(Doc, Doc.id == Mov.documento_id).join(PC, PC.id == Mov.cuenta_id).filter(
        Doc.empresa_id == empresa_id, 
        Doc.anulado == False,
        Doc.fecha >= fecha_inicio,
        Doc.fecha <= fecha_fin,
        # Solo cuentas de PyG (Clases 4, 5, 6, 7)
        PC.codigo.startswith(INGRESOS_PREFIJO) | 
        PC.codigo.startswith(GASTOS_PREFIJOS[0]) | 
        PC.codigo.startswith(GASTOS_PREFIJOS[1]) | 
        PC.codigo.startswith(COSTO_VENTAS_PREFIJO) | 
        PC.codigo.startswith(COSTO_PRODUCCION_PREFIJO)
    ).group_by(PC.codigo).all()
    
    return q_saldos_periodo


# ==========================================================
# 4. FUNCIÓN PRINCIPAL DE ANÁLISIS (Endpoint) 
# ==========================================================

def get_financial_ratios_analysis(db: Session, empresa_id: int, fecha_inicio: date, fecha_fin: date):
    # 1. OBTENER SALDOS
    balance_saldos = get_saldos_balance_acumulado(db, empresa_id, fecha_fin)
    pyg_saldos = get_saldos_pyg_periodo(db, empresa_id, fecha_inicio, fecha_fin)

    # 2. PROCESAMIENTO DE SALDOS Y CLASIFICACIÓN
    saldos_agrupados = {
        'ACTIVO': Decimal(0), 'PASIVO': Decimal(0), 'PATRIMONIO': Decimal(0),
        'ACTIVO_CORRIENTE': Decimal(0), 'PASIVO_CORRIENTE': Decimal(0), 'INVENTARIOS': Decimal(0),
        'INGRESOS': Decimal(0), 'GASTOS': Decimal(0), 'COSTO_VENTAS': Decimal(0),
        'COSTO_PRODUCCION': Decimal(0), 
        'UTILIDAD_NETA_EJERCICIO': Decimal(0) 
    }

    # Procesar Saldos de Balance (Clases 1, 2, 3)
    for row in balance_saldos:
        
        if row.codigo.startswith(ACTIVO_PREFIJO):
            saldo = row.total_debito - row.total_credito # Naturaleza Débito (Activo)
            saldos_agrupados['ACTIVO'] += saldo
            if row.codigo.startswith(CUENTAS_ACTIVO_CORRIENTE_PREFIJOS):
                saldos_agrupados['ACTIVO_CORRIENTE'] += saldo
            if row.codigo.startswith(CUENTA_INVENTARIOS_INICIO):
                 saldos_agrupados['INVENTARIOS'] += saldo
        
        elif row.codigo.startswith(PASIVO_PREFIJO): 
            # FIX CRÍTICO: Pasivo es naturaleza crédito, su saldo es Credito - Debito
            saldo = row.total_credito - row.total_debito
            saldos_agrupados['PASIVO'] += saldo
            if row.codigo.startswith(CUENTAS_PASIVO_CORRIENTE_PREFIJOS):
                 saldos_agrupados['PASIVO_CORRIENTE'] += saldo
            
        elif row.codigo.startswith(PATRIMONIO_PREFIJO):
            # FIX CRÍTICO: Patrimonio es naturaleza crédito, su saldo es Credito - Debito
            saldo = row.total_credito - row.total_debito
            saldos_agrupados['PATRIMONIO'] += saldo
            # Si existe la cuenta 3705, tomamos su saldo
            if row.codigo.startswith('3705'):
                saldos_agrupados['UTILIDAD_NETA_EJERCICIO'] = saldo 

    # Procesar Saldos de PyG (Clases 4, 5, 6, 7 - del periodo)
    for row in pyg_saldos:
        
        if row.codigo.startswith(INGRESOS_PREFIJO):
            # Ingresos son naturaleza crédito
            saldo = row.total_credito - row.total_debito
            saldos_agrupados['INGRESOS'] += saldo
        elif row.codigo.startswith(COSTO_VENTAS_PREFIJO): 
            # Costo de Ventas (Clase 6) es naturaleza débito
            saldo = row.total_debito - row.total_credito
            saldos_agrupados['COSTO_VENTAS'] += saldo
        elif row.codigo.startswith(COSTO_PRODUCCION_PREFIJO): # NUEVO: Clase 7
            # Costo de Producción (Clase 7) es naturaleza débito
            saldo = row.total_debito - row.total_credito
            saldos_agrupados['COSTO_PRODUCCION'] += saldo
        elif row.codigo.startswith(GASTOS_PREFIJOS): # Clases 5 y 8
            # Gastos (Clase 5 y 8) son naturaleza débito
            saldo = row.total_debito - row.total_credito
            saldos_agrupados['GASTOS'] += saldo
            
    # Asignación final de variables
    act_tot = saldos_agrupados['ACTIVO']
    pas_tot = saldos_agrupados['PASIVO']
    pat_tot = saldos_agrupados['PATRIMONIO']
    ingresos = saldos_agrupados['INGRESOS']
    costo_ventas_total = saldos_agrupados['COSTO_VENTAS']
    costo_produccion_total = saldos_agrupados['COSTO_PRODUCCION'] # NUEVA VARIABLE
    gastos_totales = saldos_agrupados['GASTOS']
    
    act_cor = saldos_agrupados['ACTIVO_CORRIENTE']
    pas_cor = saldos_agrupados['PASIVO_CORRIENTE']
    inventarios = saldos_agrupados['INVENTARIOS']
    
    # CÁLCULOS DE COSTO TOTAL Y UTILIDAD
    costo_total_ventas_ampliado = costo_ventas_total + costo_produccion_total # CLASE 6 + CLASE 7
    utilidad_bruta = ingresos - costo_total_ventas_ampliado
    utilidad_neta_final_para_ratios = utilidad_bruta - gastos_totales # Utilidad Bruta - Gastos (Clase 5, 8)
    
    # 4. CÁLCULO DE RAZONES
    
    # 1. Razón Corriente (Liquidez)
    cor_rate = (act_cor / pas_cor) if pas_cor > MAX_TOLERANCE else Decimal(0)
    
    # 2. Prueba Ácida (Liquidez Inmediata)
    acid_test = ((act_cor - inventarios) / pas_cor) if pas_cor > MAX_TOLERANCE else Decimal(0)
    
    # 3. Capital de Trabajo Neto (Se calcula aquí para el SEEE)
    capital_trabajo_neto = act_cor - pas_cor
    
    # 4. Nivel de Endeudamiento (Ratio)
    endeudamiento = (pas_tot / act_tot) if act_tot > MAX_TOLERANCE else Decimal(0)
    
    # 5. Apalancamiento Financiero (Pasivo Total / Patrimonio)
    apalancamiento = (pas_tot / pat_tot) if pat_tot.copy_abs() > MAX_TOLERANCE else Decimal(0)
    
    # 6. Margen Neto de Utilidad (Porcentaje)
    margen_neto = (utilidad_neta_final_para_ratios / ingresos * 100) if ingresos != 0 else Decimal(0)
    
    # NUEVO CÁLCULO: Margen Bruto de Utilidad (Porcentaje)
    margen_bruto_utilidad = (utilidad_bruta / ingresos * 100) if ingresos != 0 else Decimal(0)

    # 7. Rentabilidad del Patrimonio (ROE) (Porcentaje)
    roe = (utilidad_neta_final_para_ratios / pat_tot * 100) if pat_tot.copy_abs() > MAX_TOLERANCE else Decimal(0)
    
    # 8. Rentabilidad del Activo (ROA) (Porcentaje)
    roa = (utilidad_neta_final_para_ratios / act_tot * 100) if act_tot != 0 else Decimal(0)
    
    # 9. Rotación de Activos (Ignorado)
    rotacion_act = Decimal(0.0)

    # Diccionario de Ratios para el SEEE (usando los valores Decimal)
    ratios_dict = {
        'razon_corriente': cor_rate,
        'prueba_acida': acid_test,
        'apalancamiento_financiero': apalancamiento,
        'nivel_endeudamiento': endeudamiento,
        'margen_neto_utilidad': margen_neto,
        'margen_bruto_utilidad': margen_bruto_utilidad, # NUEVO
        'rentabilidad_patrimonio': roe,
        'rentabilidad_activo': roa,
        'rotacion_activos': rotacion_act, # Ignorado en SEEE
    }
    
    # 5. DIAGNÓSTICO ESTRATÉGICO SEEE (NUEVO PASO)
    diagnostico_seee = get_escenario_estrategico(ratios_dict, capital_trabajo_neto, pat_tot)
    
    # 6. CONSTRUIR RESPUESTA
    
    def to_float(d):
        """Convierte Decimal a float para el schema, asegurando 0.0 si es None."""
        return float(d) if d is not None else 0.0

    return schemas_dashboard.FinancialRatiosResponse(
        fecha_corte=fecha_fin,
        ingresos_anuales=to_float(ingresos),
        costo_ventas_total=to_float(costo_ventas_total),
        utilidad_neta=to_float(utilidad_neta_final_para_ratios), # Usamos la utilidad calculada
        activos_total=to_float(act_tot),
        pasivos_total=to_float(pas_tot),
        patrimonio_total=to_float(pat_tot),
        activo_corriente=to_float(act_cor),
        pasivo_corriente=to_float(pas_cor),
        inventarios_total=to_float(inventarios),
        
        # --- 9 RAZONES FINANCIERAS ---
        razon_corriente=to_float(cor_rate),
        prueba_acida=to_float(acid_test),
        apalancamiento_financiero=to_float(apalancamiento),
        nivel_endeudamiento=to_float(endeudamiento * 100), # Multiplicar por 100 para porcentaje
        margen_neto_utilidad=to_float(margen_neto),
        margen_bruto_utilidad=to_float(margen_bruto_utilidad), # NUEVO CAMPO
        rentabilidad_patrimonio=to_float(roe),
        rentabilidad_activo=to_float(roa),
        rotacion_activos=to_float(rotacion_act), # Se envía 0.0 para cumplir el Schema, aunque el valor es irrelevante
        
        # --- DIAGNÓSTICO ESTRATÉGICO SEEE (Nuevos campos) ---
        escenario_general=diagnostico_seee['escenario_general'],
        texto_interpretativo=diagnostico_seee['texto_interpretativo'],
        recomendaciones_breves=diagnostico_seee['recomendaciones_breves'],
    )

# ==========================================================
# 5. CONSUMO DE REGISTROS (NUEVO)
# ==========================================================

# -----------------------------------------------------------------------------
# NUEVA FUNCIÓN AUXILIAR (Pegar antes de get_consumo_actual)
# -----------------------------------------------------------------------------
def get_limite_real_mes(db: Session, empresa_id: int, anio: int, mes: int) -> int:
    """
    Calcula el límite TOTAL para un mes específico:
    Plan Base + Cupos Adicionales comprados para ese mes.
    """
    # 1. Obtener Plan Base
    empresa = db.query(models_empresa.Empresa).filter(models_empresa.Empresa.id == empresa_id).first()
    limite_base = empresa.limite_registros if empresa and empresa.limite_registros else 0
    
    # 2. Buscar si hay adicionales para ese mes específico
    adicional = db.query(CupoAdicional).filter(
        CupoAdicional.empresa_id == empresa_id,
        CupoAdicional.anio == anio,
        CupoAdicional.mes == mes
    ).first()
    
    cantidad_extra = adicional.cantidad_adicional if adicional else 0
    
    return limite_base + cantidad_extra


# -----------------------------------------------------------------------------
# FUNCIÓN PRINCIPAL ACTUALIZADA
# -----------------------------------------------------------------------------
def get_consumo_actual(db: Session, empresa_id: int, mes: Optional[int] = None, anio: Optional[int] = None):
    """
    Calcula el consumo de registros para un mes específico.
    Si no se especifica mes/anio, usa la fecha actual.
    """
    # 1. Determinar la fecha base
    hoy = date.today()
    
    target_year = anio if anio else hoy.year
    target_month = mes if mes else hoy.month
    
    # Crear fecha base (Día 1 del mes solicitado)
    try:
        fecha_base = date(target_year, target_month, 1)
    except ValueError:
        # Fallback por si envían un mes 13 o algo raro
        fecha_base = hoy.replace(day=1)

    # 2. Definir rango del mes
    inicio_mes = fecha_base
    ultimo_dia = calendar.monthrange(fecha_base.year, fecha_base.month)[1]
    fin_mes = fecha_base.replace(day=ultimo_dia)

    # 3. Contar movimientos en ese rango histórico
    total_registros_mes = db.query(func.count(models_mov_cont.MovimientoContable.id))\
        .join(models_doc.Documento, models_mov_cont.MovimientoContable.documento_id == models_doc.Documento.id)\
        .filter(
            models_doc.Documento.empresa_id == empresa_id,
            models_doc.Documento.anulado == False,
            models_doc.Documento.fecha >= inicio_mes,
            models_doc.Documento.fecha <= fin_mes
        ).scalar() or 0

    # 4. Obtener el límite REAL del mes (Base + Adicionales)
    # Usamos la nueva función auxiliar que creamos arriba
    limite = get_limite_real_mes(db, empresa_id, fecha_base.year, fecha_base.month)

    # 5. Calcular porcentaje
    porcentaje = 0
    if limite > 0:
        porcentaje = (total_registros_mes / limite) * 100

    # Nombre del mes para el frontend
    nombres_meses = ["", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    nombre_mes = nombres_meses[fecha_base.month]

    return {
        "total_registros": total_registros_mes,
        "limite_registros": limite,
        "porcentaje": round(porcentaje, 2),
        "estado": "OK" if porcentaje < 90 else "CRITICO",
        "periodo_texto": f"{nombre_mes} {fecha_base.year}"
    }


# EN app/services/dashboard.py

# EN app/services/dashboard.py -> Función get_limite_real_mes

def get_limite_real_mes(db: Session, empresa_id: int, anio: int, mes: int) -> int:
    # 1. Obtener Plan Base
    empresa = db.query(models_empresa.Empresa).filter(models_empresa.Empresa.id == empresa_id).first()
    limite_base = empresa.limite_registros if empresa and empresa.limite_registros else 0
    
    # 2. Buscar excepción
    adicional = db.query(CupoAdicional).filter(
        CupoAdicional.empresa_id == empresa_id,
        CupoAdicional.anio == anio,
        CupoAdicional.mes == mes
    ).first()
    
    # CORRECCIÓN AQUÍ TAMBIÉN:
    if adicional and adicional.cantidad_adicional > 0:
        return adicional.cantidad_adicional
    
    # Si no hay adicional o es 0, retornamos la base
    return limite_base

