from app.schemas.empresa import EmpresaConUsuariosCreate
from pydantic import ValidationError
from datetime import date

print("--- TESTING COMPANY CREATION SCHEMA ---")

try:
    # Attempt to create valid payload but with empty users list
    data = {
        "razon_social": "Company No Users",
        "nit": "888888888",
        "fecha_inicio_operaciones": date.today(),
        "usuarios": []  # This should fail currently
    }
    
    obj = EmpresaConUsuariosCreate(**data)
    print("SUCCESS: Validation Passed (Unexpected)")
    
except ValidationError as e:
    print("\nEXPECTED VALIDATION ERROR CAUGHT:")
    print(e)
except Exception as e:
    print(f"\nOTHER ERROR: {e}")
