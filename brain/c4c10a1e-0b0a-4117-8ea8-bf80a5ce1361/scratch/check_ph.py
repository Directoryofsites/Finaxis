import os
import sys

sys.path.append(os.path.abspath('c:/ContaPY2'))
from app.core.database import SessionLocal
from app.models.propiedad_horizontal import PHConfiguracion

db = SessionLocal()
emp_id = 134
config = db.query(PHConfiguracion).filter(PHConfiguracion.empresa_id == emp_id).first()
if config:
    print(f"Cuenta Cartera PH en Empresa 134: {config.cuenta_cartera_id}")
else:
    print("No hay configuración PH para Empresa 134.")
db.close()
