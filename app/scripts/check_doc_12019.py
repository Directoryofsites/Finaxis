from app.core.database import SessionLocal
from app.models.documento import Documento

db = SessionLocal()
doc = db.query(Documento).filter(Documento.id == 12019).first()

if doc:
    print(f"ID: {doc.id}")
    print(f"Numero: {doc.numero}")
    print(f"Estado DIAN: {doc.dian_estado}")
    print(f"XML URL: {doc.dian_xml_url}")
    print(f"CUFE: {doc.dian_cufe}")
else:
    print("Documento no encontrado")

db.close()
