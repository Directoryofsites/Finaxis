from app.core.database import SessionLocal
from app.models.propiedad_horizontal.unidad import PHUnidad
from app.models.propiedad_horizontal.modulo_contribucion import PHModuloContribucion
from app.services.propiedad_horizontal import unidad_service
from app.schemas.propiedad_horizontal import unidad as schemas

db = SessionLocal()

# 1. Setup Data
empresa_id = 128
mod = db.query(PHModuloContribucion).filter_by(empresa_id=empresa_id, nombre="Local").first()
unit = db.query(PHUnidad).filter_by(empresa_id=empresa_id).first()

if not mod or not unit:
    print("Missing data for test")
    exit()

print(f"Testing on Unit {unit.codigo} and Module {mod.nombre}")

# Ensure clean slate
unit.modulos_contribucion = []
db.commit()
db.refresh(unit)
print(f"Initial Modules: {len(unit.modulos_contribucion)}")

# 2. Execute Service Action
payload = schemas.PHUnidadMassUpdateModules(
    unidades_ids=[unit.id],
    add_modules_ids=[mod.id],
    remove_modules_ids=[]
)

print("Calling Service...")
count = unidad_service.masive_update_modules(db, payload, empresa_id)
print(f"Service returned count: {count}")

# 3. Verify Persistence (SAME SESSION)
print(f"Same Session Modules: {[m.nombre for m in unit.modulos_contribucion]}")

# 4. Verify Persistence (NEW SESSION)
db.close()
db2 = SessionLocal()
unit_refreshed = db2.query(PHUnidad).get(unit.id)
print(f"New Session Modules: {[m.nombre for m in unit_refreshed.modulos_contribucion]}")

if len(unit_refreshed.modulos_contribucion) == 0:
    print("FATAL: PERSISTENCE FAILED")
else:
    print("SUCCESS: Data Persisted")
    
db2.close()
