#!/usr/bin/env python3
from app.core.database import SessionLocal
from app.models.plan_cuenta import PlanCuenta

db = SessionLocal()
try:
    print("🔍 Verificando cuentas que empiezan con 159...")
    cuentas_159 = db.query(PlanCuenta).filter(PlanCuenta.codigo.like('159%')).all()
    print(f"Total encontradas: {len(cuentas_159)}")
    
    for cuenta in cuentas_159:
        print(f"  {cuenta.codigo} - {cuenta.nombre}")
        
    if len(cuentas_159) == 0:
        print("❌ No hay cuentas 159. Verificando todas las cuentas de depreciación...")
        todas_dep = db.query(PlanCuenta).filter(PlanCuenta.nombre.ilike('%depreci%')).all()
        print(f"Cuentas con 'depreci' en el nombre: {len(todas_dep)}")
        for cuenta in todas_dep:
            print(f"  {cuenta.codigo} - {cuenta.nombre}")
            
finally:
    db.close()