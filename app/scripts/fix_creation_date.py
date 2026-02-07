from app.core.database import SessionLocal
from app.models.empresa import Empresa
from datetime import datetime

db = SessionLocal()

# Target Company: Gonzalez Asesores (176)
# Problem: Created at 2026-01-29, effectively blocking access to 2025 plans (detected as "Ghost Plans")
# Solution: Backdate creation to 2020-01-01 to allow legacy data usage.

empresa = db.query(Empresa).get(176)
if empresa:
    print(f"Empresa: {empresa.razon_social}")
    print(f"Fecha Creación Actual: {empresa.created_at}")
    
    # Backdating to 2024 to cover 2025 operations
    new_date = datetime(2024, 1, 1)
    empresa.created_at = new_date
    
    db.commit()
    print(f"--> Fecha Creación Actualizada a: {empresa.created_at}")
    print("El bloqueo 'Ghost Plan' ya no afectará a los planes de 2025.")
else:
    print("Empresa 176 no encontrada.")
