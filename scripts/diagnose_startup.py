import sys
import os

# Agregamos el directorio raíz al path
sys.path.append(os.getcwd())

print("--- INICIANDO DIAGNOSTICO DE ARRANQUE ---")

try:
    print("1. Intentando importar app.main...")
    from app.main import app
    print("✅ Importación de app.main EXITOSA.")
except Exception as e:
    print(f"❌ ERROR CRÍTICO AL IMPORTAR app.main: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

try:
    print("2. Verificando conexión a BD (simulada)...")
    from app.core.database import engine
    print(f"✅ Motor de BD configurado: {engine.url}")
except Exception as e:
    print(f"❌ ERROR AL CONFIGURAR BD: {e}")
    import traceback
    traceback.print_exc()

print("--- DIAGNOSTICO FINALIZADO: El código parece ejecutable ---")
