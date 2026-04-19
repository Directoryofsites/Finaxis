import os
import sys

sys.path.append(os.path.abspath('c:/ContaPY2'))
from app.core.database import SessionLocal
from app.models.documento import Documento
from app.models.tipo_documento import TipoDocumento
from app.models.movimiento_contable import MovimientoContable
from app.models.plan_cuenta import PlanCuenta
from sqlalchemy.orm import joinedload
from sqlalchemy import func

db = SessionLocal()

# Buscamos los 20 documentos con ID más alto en todo el sistema
docs = db.query(Documento).order_by(Documento.id.desc()).limit(20).all()

print(f"--- 20 ÚLTIMOS DOCUMENTOS (ORDEN ID) ---")
for d in docs:
    tipo = db.query(TipoDocumento).get(d.tipo_documento_id)
    print(f"ID: {d.id} | Emp: {d.empresa_id} | Num: {d.numero} | Fecha: {d.fecha} | Tipo: {tipo.nombre if tipo else 'N/A'}")

db.close()
