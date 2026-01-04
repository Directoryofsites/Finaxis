import sys
import os
from datetime import date
from sqlalchemy import text

# Add project root to sys.path
sys.path.append(os.getcwd())

from app.core.database import SessionLocal
from app.models.movimiento_contable import MovimientoContable
from app.models.plan_cuenta import PlanCuenta
from app.models.documento import Documento

def debug_deep_scan():
    db = SessionLocal()
    empresa_id = 1
    # Ampliamos el rango para asegurar que capturamos algo si es problema de fechas
    fecha_inicio = date(2025, 1, 1) 
    fecha_fin = date(2025, 12, 31)

    print("="*60)
    print(f"DIAGNOSTICO PROFUNDO DE MOVIMIENTOS - EMPRESA {empresa_id}")
    print(f"Rango de analisis: {fecha_inicio} a {fecha_fin}")
    print("="*60)

    # 1. TOTAL MOVIMIENTOS EN EL RANGO (Sin filtros de cuenta)
    total_movs = db.query(MovimientoContable).join(Documento).filter(
        Documento.fecha >= fecha_inicio,
        Documento.fecha <= fecha_fin,
        Documento.empresa_id == empresa_id
    ).count()
    print(f"1. Total de movimientos contables en el rango: {total_movs}")

    if total_movs == 0:
        print("   (!) FATAL: No hay ningún movimiento contable en este rango de fechas.")
        return

    # 2. MOVIMIENTOS EN CUENTAS 11 (Efectivo)
    movs_caja = db.query(
        MovimientoContable, Documento
    ).join(PlanCuenta).join(Documento).filter(
        PlanCuenta.empresa_id == empresa_id,
        PlanCuenta.codigo.like("11%"),
        Documento.fecha >= fecha_inicio,
        Documento.fecha <= fecha_fin
    ).all()
    
    print(f"2. Movimientos en cuentas que empiezan por '11': {len(movs_caja)}")
    
    if not movs_caja:
        print("   (!) No hay movimientos en cuentas 11. Revisemos qué cuentas TIENEN movimiento...")
        # Query top 5 accounts with movements
        top_accounts = db.query(PlanCuenta.codigo, PlanCuenta.nombre).join(MovimientoContable).filter(PlanCuenta.empresa_id==empresa_id).distinct().limit(10).all()
        print("      Cuentas con actividad detectada:")
        for ac in top_accounts:
            print(f"      - {ac.codigo} {ac.nombre}")
        return

    # 3. ANALISIS DE ESTADOS DE LOS MOVIMIENTOS DE CAJA
    print(f"3. Analizando estados de los {len(movs_caja)} movimientos de caja encontrados:")
    
    count_aprobados = 0
    count_activos = 0
    count_anulados_db = 0 # anulado = True
    count_validos = 0 # anulado = False

    for mov, doc in movs_caja:
        is_anulado = doc.anulado if hasattr(doc, 'anulado') else "N/A"
        estado = doc.estado if hasattr(doc, 'estado') else "N/A"
        
        if is_anulado is False:
            count_validos += 1
        else:
            count_anulados_db += 1
            
        if estado == 'APROBADO': count_aprobados += 1
        if estado == 'ACTIVO': count_activos += 1

    print(f"   - Documentos con anulado=False (VÁLIDOS): {count_validos}")
    print(f"   - Documentos con anulado=True (ANULADOS): {count_anulados_db}")
    print(f"   - Estados detectados: APROBADO={count_aprobados}, ACTIVO={count_activos}")

    if count_validos == 0:
         print("   (!) TODOS LOS DOCUMENTOS ESTÁN ANULADOS O INVÁLIDOS.")
    else:
         print("   (OK) Existen documentos válidos. El reporte debería mostrar datos.")

    # 4. MUESTRA DE UN MOVIMIENTO VÁLIDO PARA REVISAR CONTRAPARTIDAS
    print("-" * 30)
    print("4. Simulando lógica del reporte para el primer movimiento válido found:")
    
    for mov, doc in movs_caja:
        if doc.anulado == False:
            print(f"   > Analizando Mov ID: {mov.id} | Doc: {doc.numero} | Valor: {mov.debito - mov.credito}")
            
            # Buscar contrapartidas
            contrapartidas = db.query(
                PlanCuenta.codigo,
                PlanCuenta.nombre,
                (MovimientoContable.debito - MovimientoContable.credito).label("neto")
            ).join(MovimientoContable).filter(
                MovimientoContable.documento_id == mov.documento_id,
                ~PlanCuenta.codigo.like("11%")
            ).all()
            
            if not contrapartidas:
                print("     (X) RECHAZADO: Sin contrapartidas (¿Transferencia interna?).")
            else:
                print(f"     (OK) {len(contrapartidas)} Contrapartidas encontradas.")
                for cp in contrapartidas:
                    print(f"         * {cp.codigo} {cp.nombre} | Neto: {cp.neto}")
            
            break # Solo analizó uno

if __name__ == "__main__":
    debug_deep_scan()
