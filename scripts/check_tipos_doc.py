
from app.core.database import SessionLocal
from app.models.tipo_documento import TipoDocumento

db = SessionLocal()
try:
    tipos = db.query(TipoDocumento).all()
    print(f"{'ID':<5} | {'Codigo':<10} | {'Nombre':<30} | {'Funcion Especial':<20} | {'Es Venta':<10}")
    print("-" * 80)
    for t in tipos:
        print(f"{t.id:<5} | {t.codigo:<10} | {t.nombre:<30} | {str(t.funcion_especial):<20} | {t.es_venta:<10}")
finally:
    db.close()
