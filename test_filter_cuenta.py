import sys
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import logging

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from app.core.database import SessionLocal
from app.models.documento import Documento
from app.models.movimiento_contable import MovimientoContable

def test_filter():
    db = SessionLocal()
    mov_con = db.query(MovimientoContable).first()
    if not mov_con:
        print("No hay movimientos contables")
        return
        
    f_cuenta = mov_con.cuenta_id
    doc_id = mov_con.documento_id
    doc = db.query(Documento).filter(Documento.id == doc_id).first()
    empresa_id = doc.empresa_id
    print(f"Usando Empresa ID: {empresa_id}")
    
    # 1. Total docs
    total = db.query(Documento).filter(Documento.empresa_id == empresa_id).count()
    print(f"Total documents initially: {total}")
    
    from app.models.plan_cuenta import PlanCuenta
    cuenta = db.query(PlanCuenta).filter(PlanCuenta.id == f_cuenta).first()
    
    if not cuenta:
        print(f"Cuenta id {f_cuenta} not found.")
        return
        
    print(f"Filtrando por cuenta_id = {f_cuenta} (Código: {cuenta.codigo})")
    
    # 3. Filter using any()
    q_any = db.query(Documento).filter(
        Documento.empresa_id == empresa_id,
        Documento.movimientos.any(MovimientoContable.cuenta_id == f_cuenta)
    )
    print(f"Docs found using .any(): {q_any.count()}")

    # 4. Filter using exists()
    q_exists = db.query(Documento).filter(
        Documento.empresa_id == empresa_id,
        db.query(MovimientoContable.id).filter(
            MovimientoContable.documento_id == Documento.id,
            MovimientoContable.cuenta_id == f_cuenta
        ).exists()
    )
    print(f"Docs found using .exists(): {q_exists.count()}")
    
    # 5. Filter using join()
    q_join = db.query(Documento).join(MovimientoContable).filter(
        Documento.empresa_id == empresa_id,
        MovimientoContable.cuenta_id == f_cuenta
    ).distinct()
    print(f"Docs found using .join(): {q_join.count()}")

if __name__ == "__main__":
    test_filter()
