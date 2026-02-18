import sys
import os
sys.path.append(os.getcwd())
from app.core.database import SessionLocal
from app.models.configuracion_fe import ConfiguracionFE

db = SessionLocal()
config = db.query(ConfiguracionFE).first()
if config:
    config.nc_rango_id = 9
    config.nd_rango_id = 10
    config.ds_rango_id = 148 # Confirming
    config.rango_desde = 8   # Saving Factura ID here too just in case
    db.commit()
    print("Configuracion updated: NC=9, ND=10, DS=148, Factura=8")
else:
    print("Configuracion not found")
db.close()
