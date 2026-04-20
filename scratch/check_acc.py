
from app.core.database import SessionLocal
from app.models.contabilidad import AsientoContable
from decimal import Decimal

db = SessionLocal()
try:
    # Buscar asientos del documento 13859
    asientos = db.query(AsientoContable).filter(AsientoContable.documento_id == 13859).all()
    print(f"Asientos para Doc 13859:")
    for a in asientos:
        print(f"Cuenta: {a.cuenta_contable_id}, Debito: {a.debito}, Credito: {a.credito}")
finally:
    db.close()
