
import sys
import os

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models.documento import Documento
from app.models.tipo_documento import TipoDocumento
from app.models.propiedad_horizontal import PHConfiguracion
from sqlalchemy.orm import joinedload

db = SessionLocal()

print("--- PH Configuration ---")
config = db.query(PHConfiguracion).first()
if config:
    print(f"Config ID: {config.id}")
    print(f"Recibo Doc ID: {config.tipo_documento_recibo_id}")
    
    tipo_recibo = db.query(TipoDocumento).filter(TipoDocumento.id == config.tipo_documento_recibo_id).first()
    if tipo_recibo:
        print(f"Tipo Recibo: {tipo_recibo.nombre} (ID: {tipo_recibo.id})")
        print(f"Funcion Especial: '{tipo_recibo.funcion_especial}'")
    else:
        print("TIPO DOCUMENTO RECIBO NO ENCONTRADO")
else:
    print("NO PH CONFIG FOUND")

print("\n--- Recent Documents (Last 5) ---")
docs = db.query(Documento).options(joinedload(Documento.tipo_documento)).order_by(Documento.id.desc()).limit(5).all()

for d in docs:
    print(f"Doc ID: {d.id} | No: {d.numero} | Fecha: {d.fecha} | Tipo: {d.tipo_documento.nombre} | Func: '{d.tipo_documento.funcion_especial}'")
    
db.close()
