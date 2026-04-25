import sys
import os
from sqlalchemy import func, extract
from datetime import date

# Añadir el path del proyecto para importar los módulos
sys.path.append('c:\\ContaPY2')

from app.core.database import SessionLocal
from app.models.movimiento_contable import MovimientoContable
from app.models.documento import Documento
from app.models.plan_cuenta import PlanCuenta

def analysis_high_expenses(empresa_id, year):
    db = SessionLocal()
    try:
        # --- 1. A NIVEL DE CUENTA MAYOR (4 DÍGITOS) ---
        mayor_expenses = db.query(
            func.substr(PlanCuenta.codigo, 1, 4).label('codigo_mayor'),
            func.sum(MovimientoContable.debito - MovimientoContable.credito).label('saldo')
        ).join(
            Documento, MovimientoContable.documento_id == Documento.id
        ).join(
            PlanCuenta, MovimientoContable.cuenta_id == PlanCuenta.id
        ).filter(
            Documento.empresa_id == empresa_id,
            Documento.fecha >= date(year, 1, 1),
            Documento.fecha <= date(year, 12, 31),
            Documento.anulado == False,
            PlanCuenta.codigo.like('5%')
        ).group_by(
            func.substr(PlanCuenta.codigo, 1, 4)
        ).order_by(
            func.sum(MovimientoContable.debito - MovimientoContable.credito).desc()
        ).all()

        # --- 2. A NIVEL DE CUENTA AUXILIAR (DETALLE) ---
        aux_expenses = db.query(
            PlanCuenta.codigo,
            PlanCuenta.nombre,
            func.sum(MovimientoContable.debito - MovimientoContable.credito).label('saldo')
        ).join(
            Documento, MovimientoContable.documento_id == Documento.id
        ).join(
            PlanCuenta, MovimientoContable.cuenta_id == PlanCuenta.id
        ).filter(
            Documento.empresa_id == empresa_id,
            Documento.fecha >= date(year, 1, 1),
            Documento.fecha <= date(year, 12, 31),
            Documento.anulado == False,
            PlanCuenta.codigo.like('5%')
        ).group_by(
            PlanCuenta.codigo,
            PlanCuenta.nombre
        ).order_by(
            func.sum(MovimientoContable.debito - MovimientoContable.credito).desc()
        ).all()

        print(f"ANALISIS DE GASTOS MAYORES - EMPRESA {empresa_id} - AÑO {year}")
        print("-" * 70)
        
        if mayor_expenses:
            top_mayor = mayor_expenses[0]
            # Buscamos el nombre de la cuenta mayor
            mayor_name_query = db.query(PlanCuenta.nombre).filter(
                PlanCuenta.empresa_id == empresa_id,
                PlanCuenta.codigo == top_mayor.codigo_mayor
            ).first()
            m_name = mayor_name_query.nombre if mayor_name_query else "Cuenta del Grupo"
            
            print(f"EL GASTO MÁS ALTO A NIVEL DE CUENTA MAYOR (4 DIGITOS):")
            print(f"CÓDIGO: {top_mayor.codigo_mayor} | {m_name}")
            print(f"VALOR TOTAL: ${top_mayor.saldo:,.2f}")
        
        print("-" * 70)
        
        if aux_expenses:
            top_aux = aux_expenses[0]
            print(f"EL GASTO MÁS ALTO A NIVEL DE CUENTA AUXILIAR:")
            print(f"CÓDIGO: {top_aux.codigo} | {top_aux.nombre}")
            print(f"VALOR TOTAL: ${top_aux.saldo:,.2f}")
            
            print("\nOtras cuentas con alto impacto:")
            for item in aux_expenses[1:5]:
                print(f"- {item.codigo} {item.nombre[:35]:<35}: ${item.saldo:,.2f}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    analysis_high_expenses(222, 2026)
