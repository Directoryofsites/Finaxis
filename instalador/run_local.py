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

# ── Base de datos: Prioridad config.json (Wizard) > SQLite (fallback) ────────
import json as _json
datos_dir = os.path.join(os.environ.get('APPDATA', APP_DIR), 'Finaxis')
os.makedirs(datos_dir, exist_ok=True)
config_path = os.path.join(datos_dir, 'config.json')

_db_url_from_config = None
if os.path.exists(config_path):
    try:
        with open(config_path, 'r', encoding='utf-8') as _f:
            _cfg = _json.load(_f)
            _db_url_from_config = _cfg.get('DATABASE_URL') or _cfg.get('database_url')
    except Exception as _e:
        print(f"[Finaxis] Advertencia: No se pudo leer config.json: {_e}")

if _db_url_from_config:
    os.environ['DATABASE_URL'] = _db_url_from_config
    print(f"[Finaxis] Modo MULTIUSUARIO (PostgreSQL): {_db_url_from_config[:50]}...")
else:
    db_path = os.path.join(datos_dir, 'finaxis_local.db')
    os.environ['DATABASE_URL'] = f'sqlite:///{db_path}'
    print(f"[Finaxis] Modo MONOUSUARIO (SQLite): {db_path}")

# Clave secreta fija para el instalador
os.environ.setdefault('SECRET_KEY', 'finaxis-local-secret-key-instalador-v1-2024')

# URL del backend (Se deja vacía para que el frontend la detecte dinámicamente según la IP del servidor)
os.environ['NEXT_PUBLIC_API_URL'] = ''

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
    env['HOSTNAME'] = '0.0.0.0'  # Escucha en toda la red (modo multiusuario)

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
    print(f"  Backend API:  http://0.0.0.0:{API_PORT}")
    print(f"  Frontend:     {FRONTEND_URL} (Accesible en red)")
    print(f"  Base de datos: {os.environ.get('DATABASE_URL', 'no configurada')[:60]}")
    print("=" * 55)

    # Registrar cleanup para Ctrl+C y cierre
    signal.signal(signal.SIGINT, _cleanup)
    signal.signal(signal.SIGTERM, _cleanup)

    # Lanzar frontend en hilo separado (no bloqueante)
    threading.Thread(target=_lanzar_frontend, daemon=True).start()

    # Abrir navegador en hilo separado
    threading.Thread(target=_abrir_navegador, daemon=True).start()

    # Lanzar FastAPI/Uvicorn (BLOQUEANTE - mantiene el proceso vivo)
    print(f"[Finaxis] Iniciando backend FastAPI en RED (0.0.0.0:{API_PORT}) ...")
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=API_PORT,
        log_level="warning",
        reload=False,
    )

if __name__ == "__main__":
    main()
