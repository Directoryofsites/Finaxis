from app.core.database import engine
from app.models.propiedad_horizontal.concepto import PHConcepto
import sqlalchemy

print("Forzando creación de tabla ph_conceptos...")
try:
    PHConcepto.__table__.create(engine)
    print("EXITO: Tabla creada correctamente.")
except sqlalchemy.exc.ProgrammingError as e:
    if "already exists" in str(e):
        print("AVISO: La tabla ya existe. Todo correcto.")
    else:
        print(f"ERROR: {e}")
except Exception as e:
    print(f"ERROR FATAL: {e}")
