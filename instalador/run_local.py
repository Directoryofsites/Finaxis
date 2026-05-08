"""
run_local.py — Punto de entrada del instalador local de Finaxis.

Este archivo es el que PyInstaller empaqueta como .exe.
Responsabilidades:
  1. Configurar el entorno para modo LOCAL (SQLite, sin IA, sin internet)
  2. Lanzar el servidor FastAPI/Uvicorn en background (puerto 8765)
  3. Lanzar el servidor Next.js con Node.js portable (puerto 3000)
  4. Abrir el navegador apuntando a localhost:3000 (el frontend)
  5. Mantener el proceso vivo mientras el usuario trabaja
"""
import os
import sys
import time
import threading
import webbrowser
import subprocess
import signal

# ── 1. Resolver la ruta base (funciona tanto en .py como en .exe de PyInstaller) ──
if getattr(sys, 'frozen', False):
    # Estamos dentro del .exe de PyInstaller
    BASE_DIR = sys._MEIPASS
    APP_DIR  = os.path.dirname(sys.executable)
else:
    # Modo desarrollo normal
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    APP_DIR  = os.path.dirname(BASE_DIR)

# ── 2. Variables de entorno para modo LOCAL ──────────────────────────────────
os.environ['FINAXIS_MODO'] = 'LOCAL'
os.environ['RUN_SEEDS']    = 'true'

# Base de datos SQLite local (en AppData del usuario para persistencia)
datos_dir = os.path.join(os.environ.get('APPDATA', APP_DIR), 'Finaxis')
os.makedirs(datos_dir, exist_ok=True)
db_path = os.path.join(datos_dir, 'finaxis_local.db')
os.environ['DATABASE_URL'] = f'sqlite:///{db_path}'

# Clave secreta fija para el instalador
os.environ.setdefault('SECRET_KEY', 'finaxis-local-secret-key-instalador-v1-2024')

# URL del backend para que Next.js sepa dónde está la API
os.environ['NEXT_PUBLIC_API_URL'] = 'http://localhost:8765'

# Directorio de trabajo
os.chdir(APP_DIR)

# Agregar BASE_DIR al path de Python
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# ── Puertos ──────────────────────────────────────────────────────────────────
API_PORT      = 8765   # FastAPI backend
FRONTEND_PORT = 3000   # Next.js frontend
FRONTEND_URL  = f"http://localhost:{FRONTEND_PORT}"

# Proceso de Node.js (para poder cerrarlo al salir)
_node_process = None

# ── 3. Lanzar el servidor Next.js con Node.js portable ───────────────────────
def _lanzar_frontend():
    global _node_process

    # Buscar node.exe en el directorio del ejecutable
    node_exe = os.path.join(APP_DIR, 'node.exe')
    server_js = os.path.join(APP_DIR, 'frontend', 'server.js')

    if not os.path.exists(node_exe):
        print(f"[Finaxis] ADVERTENCIA: node.exe no encontrado en {node_exe}")
        print("[Finaxis] El frontend no estara disponible.")
        return

    if not os.path.exists(server_js):
        print(f"[Finaxis] ADVERTENCIA: server.js no encontrado en {server_js}")
        return

    # Variables de entorno para Next.js
    env = os.environ.copy()
    env['PORT']     = str(FRONTEND_PORT)
    env['HOSTNAME'] = '127.0.0.1'

    print(f"[Finaxis] Iniciando frontend Next.js en {FRONTEND_URL} ...")

    _node_process = subprocess.Popen(
        [node_exe, server_js],
        env=env,
        cwd=os.path.join(APP_DIR, 'frontend'),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    print(f"[Finaxis] Frontend PID: {_node_process.pid}")

# ── 4. Abrir el navegador (con retraso para que ambos servidores arranquen) ──
def _abrir_navegador():
    time.sleep(5)   # Esperar que FastAPI y Node.js estén listos
    webbrowser.open(FRONTEND_URL)
    print(f"[Finaxis] Navegador abierto en {FRONTEND_URL}")

# ── 5. Cleanup al cerrar ─────────────────────────────────────────────────────
def _cleanup(*args):
    global _node_process
    if _node_process and _node_process.poll() is None:
        print("[Finaxis] Cerrando servidor Node.js...")
        _node_process.terminate()
    sys.exit(0)

# ── 6. Main ──────────────────────────────────────────────────────────────────
def main():
    print("=" * 55)
    print("  FINAXIS - Sistema Contable Local")
    print(f"  Version: 1.0")
    print(f"  Backend API:  http://localhost:{API_PORT}")
    print(f"  Frontend:     {FRONTEND_URL}")
    print(f"  Base de datos: {db_path}")
    print("=" * 55)

    # Registrar cleanup para Ctrl+C y cierre
    signal.signal(signal.SIGINT, _cleanup)
    signal.signal(signal.SIGTERM, _cleanup)

    # Lanzar frontend en hilo separado (no bloqueante)
    threading.Thread(target=_lanzar_frontend, daemon=True).start()

    # Abrir navegador en hilo separado
    threading.Thread(target=_abrir_navegador, daemon=True).start()

    # Lanzar FastAPI/Uvicorn (BLOQUEANTE - mantiene el proceso vivo)
    print(f"[Finaxis] Iniciando backend FastAPI en http://localhost:{API_PORT} ...")
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=API_PORT,
        log_level="warning",
        reload=False,
    )

if __name__ == "__main__":
    main()
