
import sys
import os
from datetime import date

# Add project root to path
sys.path.append(os.getcwd())

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.services import super_informe
from app.schemas import documento as schemas_doc
from app.models import Empresa

# Setup DB connection (using the string seen in logs or default local)
db_url = "postgresql://postgres:mysecretpassword@localhost:5432/contapy_db"
engine = create_engine(db_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

print("DB Connected.")

# Create valid filters
filtros = schemas_doc.DocumentoGestionFiltros(
    tipoEntidad='movimientos',
    estadoDocumento='activos',
    fechaInicio=date(2025, 1, 1),
    fechaFin=date(2025, 12, 31),
    pagina=1,
    limite=100,
    traerTodo=True
)

empresa_id = 146  # Using the ID found in previous run

try:
    print("Checking if empresa exists...")
    emp = db.query(Empresa).first()
    if emp:
        empresa_id = emp.id
        print(f"Using Empresa ID: {empresa_id}")
    else:
        print("No companies found, cannot test fully.")
        sys.exit(0)

    print("Calling generate_super_informe_pdf...")
    pdf_content = super_informe.generate_super_informe_pdf(db, filtros, empresa_id)
    print(f"Success! PDF generated, size: {len(pdf_content)} bytes")

except Exception as e:
    print(f"CRASH DETECTED: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()
