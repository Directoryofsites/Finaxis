from typing import List, Dict, Any, Optional
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from app.models.plan_cuenta import PlanCuenta
from app.models.movimiento_contable import MovimientoContable
from app.models.documento import Documento
from app.models.empresa import Empresa
from sqlalchemy import func, case
from app.models.plan_cuenta import PlanCuenta
from app.models.movimiento_contable import MovimientoContable
from app.models.documento import Documento
from app.models.empresa import Empresa
from app.services._templates_empaquetados import TEMPLATES_EMPAQUETADOS
from jinja2 import Environment, select_autoescape
from weasyprint import HTML

GLOBAL_JINJA_ENV = Environment(loader=None, autoescape=select_autoescape(['html', 'xml']))

def get_fuentes_usos_capital_trabajo(
    db: Session,
    empresa_id: int,
    fecha_inicio: date,
    fecha_fin: date
) -> Dict[str, Any]:
    """
    Calcula el Estado de Fuentes y Usos enfocado en el Capital de Trabajo.
    Valores aproximados a la unidad (sin decimales).
    """
    
    # 1. Definir cuentas de Capital de Trabajo
    # Se asume PUC colombiano estándar:
    # 1 = Activo, 11=Disponible, 12=Inversiones, 13=Deudores, 14=Inventarios
    prefix_activos_corrientes = ['11', '12', '13', '14']
    # 2 = Pasivo, 21=Obligaciones Fin, 22=Proveedores, 23=Ctas por Pagar, 24=Impuestos, 25=Laborales, 26=Pasivos Est., 27=Diferidos
    prefix_pasivos_corrientes = ['21', '22', '23', '24', '25', '26', '27']
    
    all_prefixes = prefix_activos_corrientes + prefix_pasivos_corrientes
    
    # 2. Obtener Cuentas relevantes (Nivel auxiliar o el que tenga movimientos, pero agruparemos por cuenta mayor o subcuenta para el reporte?)
    # El usuario quiere ver "Cambios", así que ver nivel Cuenta (4 dígitos) o Subcuenta (6 dígitos) es útil.
    # Usemos todas las cuentas que tengan movimiento o saldo.
    
    # Consulta masiva de saldos iniciales (antes de fecha_inicio)
    sq_saldo_ini = db.query(
        MovimientoContable.cuenta_id,
        func.sum(MovimientoContable.debito - MovimientoContable.credito).label("saldo")
    ).join(Documento).join(PlanCuenta).filter(
        Documento.empresa_id == empresa_id,
        Documento.fecha < fecha_inicio,
        Documento.anulado.is_(False),
        # Filtro de prefijos
        func.substr(PlanCuenta.codigo, 1, 2).in_(all_prefixes)
    ).group_by(MovimientoContable.cuenta_id).all()
    
    mapa_ini = {r.cuenta_id: float(r.saldo or 0) for r in sq_saldo_ini}
    
    # Consulta masiva de movimientos del periodo (variación)
    sq_movs = db.query(
        MovimientoContable.cuenta_id,
        func.sum(MovimientoContable.debito - MovimientoContable.credito).label("variacion_neta")
    ).join(Documento).join(PlanCuenta).filter(
        Documento.empresa_id == empresa_id,
        Documento.fecha.between(fecha_inicio, fecha_fin),
        Documento.anulado.is_(False),
        func.substr(PlanCuenta.codigo, 1, 2).in_(all_prefixes)
    ).group_by(MovimientoContable.cuenta_id).all()
    
    mapa_movs = {r.cuenta_id: float(r.variacion_neta or 0) for r in sq_movs}
    
    # 3. Unificar cuentas
    all_ids = set(mapa_ini.keys()) | set(mapa_movs.keys())
    if not all_ids:
        return {"filas": [], "totales": {}}
        
    cuentas = db.query(PlanCuenta).filter(PlanCuenta.id.in_(all_ids)).all()
    
    filas = []
    
    total_fuentes = 0.0
    total_usos = 0.0
    
    # Acumuladores para resumen de Capital de Trabajo (sin caja)
    sum_activo_corriente_ini = 0.0
    sum_activo_corriente_fin = 0.0
    sum_pasivo_corriente_ini = 0.0
    sum_pasivo_corriente_fin = 0.0

    # Acumulador específico para Caja (Grupo 11)
    variacion_caja = 0.0
    saldo_caja_ini = 0.0
    saldo_caja_fin = 0.0

    for c in cuentas:
        grupo = c.codigo[:2]
        
        # APROXIMACION A ENTEROS
        saldo_inicial = int(round(mapa_ini.get(c.id, 0.0)))
        variacion_neta = int(round(mapa_movs.get(c.id, 0.0))) # Debito - Credito
        # Recalcular Saldo Final
        saldo_final = saldo_inicial + variacion_neta

        # Si es CAJA (Grupo 11), lo tratamos aparte (Resultado)
        if codigo_starts_with(c.codigo, ['11']):
            saldo_caja_ini += saldo_inicial
            saldo_caja_fin += saldo_final
            variacion_caja += variacion_neta
            continue # NO lo agregamos a filas de fuentes/usos

        # Determinar tipo para el resto
        es_activo = codigo_starts_with(c.codigo, prefix_activos_corrientes) # Incluye 11 pero ya lo filtramos arriba
        es_pasivo = codigo_starts_with(c.codigo, prefix_pasivos_corrientes)
        
        fuente = 0.0
        uso = 0.0
        
        if es_activo:
            sum_activo_corriente_ini += saldo_inicial
            sum_activo_corriente_fin += saldo_final
            
            # Activo: Aumento (+) es USO. Disminución (-) es FUENTE.
            if variacion_neta > 0:
                uso = abs(variacion_neta)
            else:
                fuente = abs(variacion_neta)
                
        elif es_pasivo:
            # Pasivo: Saldo es negativo en lógica (Deb - Cred).
            # Para sumar el "Valor de Deuda", invertimos el signo.
            # Si es negativo (Crédito) -> se vuelve positivo (Deuda).
            # Si es positivo (Débito) -> se vuelve negativo (Menor Deuda / Saldo a favor).
            sum_pasivo_corriente_ini += -saldo_inicial
            sum_pasivo_corriente_fin += -saldo_final

            if variacion_neta < 0: 
                # Saldo se hizo más negativo (Aumentó deuda) -> FUENTE
                fuente = abs(variacion_neta)
            else:
                # Saldo se hizo más positivo (Disminuyó deuda, pagué) -> USO
                uso = abs(variacion_neta)
        
        # Filtro de valores insignificantes
        if abs(fuente) < 1 and abs(uso) < 1:
            continue
            
        filas.append({
            "cuenta_codigo": c.codigo,
            "cuenta_nombre": c.nombre,
            "saldo_inicial": saldo_inicial,
            "saldo_final": saldo_final,
            "variacion": saldo_final - saldo_inicial,
            "fuente": int(fuente),
            "uso": int(uso),
            "tipo": "Activo" if es_activo else "Pasivo"
        })
        
        total_fuentes += fuente
        total_usos += uso
        
    # Ordenar por código
    filas.sort(key=lambda x: x["cuenta_codigo"])
    
    # Calcular Capital de Trabajo Neto (Operativo, sin caja)
    kt_ini = sum_activo_corriente_ini - sum_pasivo_corriente_ini
    kt_fin = sum_activo_corriente_fin - sum_pasivo_corriente_fin
    
    # IMPORTANTE: Requerimiento del usuario
    # El usuario espera que "Variación K.T." coincida con "Fuentes - Usos".
    # Fuentes - Usos = Variación de Caja (Generada por Op).
    # Si Activo Aumenta -> KT Aumenta -> Uso -> Caja Baja.
    # Por tanto, para que coincida con el signo de Fuentes - Usos (Caja),
    # debemos calcular la variación como IMPACTO EN CAJA.
    # Impacto = KT_Inicial - KT_Final
    # (Si KT Final es mayor, el impacto es negativo/Uso).
    variacion_kt = kt_ini - kt_fin
    
    # El resultado conceptual es: Fuentes - Usos = Aumento de Caja
    # (En un mundo perfecto donde solo existe capital de trabajo)
    diferencia_fuentes_usos = total_fuentes - total_usos

    return {
        "filas": filas,
        "totales": {
            "total_fuentes": int(total_fuentes),
            "total_usos": int(total_usos),
            "diferencia": int(diferencia_fuentes_usos),
            "variacion_caja": int(variacion_caja), # TRAMO FINAL: EL RESULTADO
            "saldo_caja_ini": int(saldo_caja_ini),
            "saldo_caja_fin": int(saldo_caja_fin)
        },
        "resumen_kt": {
            "activo_cte_ini": int(sum_activo_corriente_ini),
            "pasivo_cte_ini": int(sum_pasivo_corriente_ini),
            "kt_ini": int(kt_ini),
            "activo_cte_fin": int(sum_activo_corriente_fin),
            "pasivo_cte_fin": int(sum_pasivo_corriente_fin),
            "kt_fin": int(kt_fin),
            "variacion_kt": int(variacion_kt) # Ahora alineado con Fuentes - Usos
        }
    }

def codigo_starts_with(codigo: str, prefixes: List[str]) -> bool:
    for p in prefixes:
        if codigo.startswith(p):
            return True
    return False

def generate_fuentes_usos_pdf(db: Session, empresa_id: int, fecha_inicio: date, fecha_fin: date):
    data = get_fuentes_usos_capital_trabajo(db, empresa_id, fecha_inicio, fecha_fin)
    empresa = db.query(Empresa).filter(Empresa.id == empresa_id).first()
    
    context = {
        "empresa": empresa,
        "fecha_inicio": fecha_inicio,
        "fecha_fin": fecha_fin,
        "filas": data["filas"],
        "totales": data["totales"],
        "resumen_kt": data["resumen_kt"]
    }
    
    # Importante: Asegurar que la plantilla exista
    if "reports/fuentes_usos_report.html" not in TEMPLATES_EMPAQUETADOS:
        # Fallback simple o error
         # Por ahora esperaremos que se cree la plantilla
         pass

    template_str = TEMPLATES_EMPAQUETADOS.get("reports/fuentes_usos_report.html", "<h1>Plantilla no encontrada</h1>")
    template = GLOBAL_JINJA_ENV.from_string(template_str)
    html_out = template.render(context)
    return HTML(string=html_out).write_pdf()
