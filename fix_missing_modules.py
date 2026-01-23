from app.core.database import SessionLocal
from app.models.propiedad_horizontal.modulo_contribucion import PHModuloContribucion
from app.models.propiedad_horizontal.unidad import PHUnidad

db = SessionLocal()

# Get target empresa
first_unit = db.query(PHUnidad).first()
if not first_unit:
    print("No units found to determine company.")
    exit()

target_empresa_id = first_unit.empresa_id
print(f"Target Empresa: {target_empresa_id}")

# Check existing
count = db.query(PHModuloContribucion).filter_by(empresa_id=target_empresa_id).count()
if count > 0:
    print(f"Empresa {target_empresa_id} already has {count} modules. No action needed.")
    exit()

# Templates to create
to_create = [
    {"nombre": "Residencial", "tipo_distribucion": "IGUALITARIO", "descripcion": "Coeficiente Igualitario Residencial"},
    {"nombre": "Local", "tipo_distribucion": "COEFICIENTE", "descripcion": "Coeficiente Variable Locales"}
]

print("Creating default modules...")
for data in to_create:
    mod = PHModuloContribucion(
        empresa_id=target_empresa_id,
        nombre=data["nombre"],
        tipo_distribucion=data["tipo_distribucion"],
        descripcion=data["descripcion"]
    )
    db.add(mod)

db.commit()
print("Modules created successfully.")
db.close()
