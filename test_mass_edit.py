from app.core.database import SessionLocal
from app.models.propiedad_horizontal.modulo_contribucion import PHModuloContribucion
from app.models.propiedad_horizontal.unidad import PHUnidad
from app.schemas.propiedad_horizontal import modulo_contribucion as modulo_schemas
from app.schemas.propiedad_horizontal import unidad as unidad_schemas
from app.services.propiedad_horizontal import unidad_service

db = SessionLocal()
empresa_id = 9 # Assuming from previous context or I will pick one
# Get an active empresa_id
first_unit = db.query(PHUnidad).first()
if not first_unit:
    print("No units found")
    exit()

empresa_id = first_unit.empresa_id
print(f"Testing with Empresa ID: {empresa_id}")

# 1. Test Fetch Modules
print("--- Fetching Modules ---")
modulos = db.query(PHModuloContribucion).filter(PHModuloContribucion.empresa_id == empresa_id).all()
print(f"Found {len(modulos)} modules")
for m in modulos:
    try:
        schema_obj = modulo_schemas.PHModuloContribucionResponse.from_orm(m)
        print(f"Valid Schema: {schema_obj.nombre} (ID: {schema_obj.id})")
    except Exception as e:
        print(f"INVALID Schema for {m.nombre}: {e}")

if not modulos:
    print("No modules to test update.")
    exit()

target_module_id = modulos[0].id

# 2. Test Mass Update
print(f"\n--- Testing Mass Update on Unit {first_unit.id} ---")
print(f"Initial Modules: {[m.id for m in first_unit.modulos_contribucion]}")

# ADD
payload = unidad_schemas.PHUnidadMassUpdateModules(
    unidades_ids=[first_unit.id],
    add_modules_ids=[target_module_id],
    remove_modules_ids=[]
)

count = unidad_service.masive_update_modules(db, payload, empresa_id)
print(f"Updated Count (ADD): {count}")
db.refresh(first_unit)
print(f"Modules after ADD: {[m.id for m in first_unit.modulos_contribucion]}")

if target_module_id not in [m.id for m in first_unit.modulos_contribucion]:
    print("FAILED: Module was not added")

# REMOVE
payload_remove = unidad_schemas.PHUnidadMassUpdateModules(
    unidades_ids=[first_unit.id],
    add_modules_ids=[],
    remove_modules_ids=[target_module_id]
)

count = unidad_service.masive_update_modules(db, payload_remove, empresa_id)
print(f"Updated Count (REMOVE): {count}")
db.refresh(first_unit)
print(f"Modules after REMOVE: {[m.id for m in first_unit.modulos_contribucion]}")

if target_module_id in [m.id for m in first_unit.modulos_contribucion]:
    print("FAILED: Module was not removed")

db.close()
