import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

print("=== INICIANDO CHECK DE INTEGRIDAD DEL BACKEND ===")

try:
    print("1. Intentando importar app.core.database...")
    from app.core import database
    print("   [OK] app.core.database importado.")

    print("2. Intentando importar app.services.dashboard...")
    from app.services import dashboard
    print("   [OK] app.services.dashboard importado.")

    print("3. Intentando importar app.api.empresas.routes...")
    from app.api.empresas import routes
    print("   [OK] app.api.empresas.routes importado.")

    print("4. Intentando importar app.main (Aplicación Completa)...")
    from app import main
    print("   [OK] app.main importado exitosamente.")
    
    print("=== BACKEND INTEGRITY CHECK PASSED ===")

except ImportError as e:
    print(f"\n[CRITICAL ERROR] Fallo de Importación: {e}")
except Exception as e:
    print(f"\n[CRITICAL ERROR] Fallo General: {e}")
