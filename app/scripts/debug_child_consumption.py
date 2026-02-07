import sys
import os
from sqlalchemy import func, extract
from datetime import date
import calendar

# Add the project root to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from app.core.database import SessionLocal
from app.models.empresa import Empresa
from app.models.documento import Documento
from app.models.movimiento_contable import MovimientoContable
from app.models.consumo_registros import HistorialConsumo, ControlPlanMensual
import app.models.nomina # fix import error

def debug_consumption():
    db = SessionLocal()
    try:
        # 1. Find Pajarera
        empresa = db.query(Empresa).filter(Empresa.razon_social.ilike("%Pajarera%")).first()
        if not empresa:
            print("Company 'Pajarera' not found.")
            return

        print(f"Target Company: {empresa.razon_social} (ID: {empresa.id})")
        print(f"Parent ID: {empresa.padre_id}")

        # 2. Define Date Range (Jan 2026)
        year = 2026
        month = 1
        inicio_mes = date(year, month, 1)
        last_day = calendar.monthrange(year, month)[1]
        fin_mes = date(year, month, last_day)
        
        print(f"Analysing Period: {inicio_mes} to {fin_mes}")

        # 3. Physical Count
        physical_count = db.query(func.count(MovimientoContable.id))\
            .join(Documento, MovimientoContable.documento_id == Documento.id)\
            .filter(
                Documento.empresa_id == empresa.id,
                Documento.anulado == False,
                Documento.fecha >= inicio_mes,
                Documento.fecha <= fin_mes
            ).scalar()
        
        print(f"Physical Count (Movimientos): {physical_count}")
        
        # 4. Financial Count (HistorialConsumo)
        financial_count = db.query(func.sum(HistorialConsumo.cantidad)).filter(
            HistorialConsumo.empresa_id == empresa.id,
            extract('year', HistorialConsumo.fecha) == year,
            extract('month', HistorialConsumo.fecha) == month,
        ).scalar() or 0
        
        print(f"Financial Count (Historial): {financial_count}")
        
        if empresa.padre_id:
            parent = db.query(Empresa).get(empresa.padre_id)
            print(f"Parent Name: {parent.razon_social} (ID: {parent.id})")
            
            # Check ControlPlanMensual for Parent
            plan = db.query(ControlPlanMensual).filter_by(
                empresa_id=parent.id, anio=year, mes=month
            ).first()
            if plan:
                print(f"Parent Plan {year}-{month}: Used={plan.limite_asignado - plan.cantidad_disponible}, Available={plan.cantidad_disponible}, Limit={plan.limite_asignado}")

            # List Historial Consolidated
            history = db.query(HistorialConsumo).filter_by(empresa_id=parent.id).all()
            print(f"Total History Records for Parent: {len(history)}")
            for h in history:
                print(f" - ID: {h.id}, Date: {h.fecha}, Qty: {h.cantidad}, Type: {h.tipo_operacion}, Source: {h.fuente_tipo}")


    except Exception as e:
        print(f"Error: {e}")

def list_all_companies():
    db = SessionLocal()
    print("\n--- ALL COMPANIES ---")
    try:
        empresas = db.query(Empresa).all()
        for emp in empresas:
            print(f"ID: {emp.id} | Name: {emp.razon_social} | Parent: {emp.padre_id}")
            
            # Count movements
            movs = db.query(func.count(MovimientoContable.id)).join(Documento).filter(Documento.empresa_id == emp.id).scalar()
            
            # Count History
            hist = db.query(func.sum(HistorialConsumo.cantidad)).filter(HistorialConsumo.empresa_id == emp.id).scalar() or 0
            
            # Detailed analysis for Pajarera
            if emp.id == 183:
                docs = db.query(Documento).filter(Documento.empresa_id == emp.id).all()
                print(f"   [PAJARERA DETAIL] Found {len(docs)} docs:")
                for d in docs:
                    print(f"    - ID: {d.id} | Date: {d.fecha} | Void: {d.anulado} | Type: {d.tipo_documento_id}")

            
    finally:
        db.close()

if __name__ == "__main__":
    debug_consumption()
    list_all_companies()

