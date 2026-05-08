# finaxis_local.spec
# ─────────────────────────────────────────────────────────────────────────────
# Archivo de configuracion para PyInstaller.
# Arquitectura: FastAPI (Python) + Next.js Standalone (Node.js)
#
# Este .spec empaqueta SOLO el backend Python.
# El frontend Next.js lo sirve node.exe (portable) en puerto 3000.
# build_instalador.bat coloca ambos juntos en dist\finaxis_local\
#
# Estructura final en dist\finaxis_local\
#   FinaxisLocal.exe   <- este .exe (lanza FastAPI + Node.js)
#   node.exe           <- Node.js portable
#   frontend\          <- Next.js standalone build
#     server.js
#     .next\
#     public\
# ─────────────────────────────────────────────────────────────────────────────

import os
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

# ── Rutas base ──────────────────────────────────────────────────────────────────────────────
# El archivo .spec está en C:\ContaPY2\instalador
# ROOT debe ser C:\ContaPY2
SPEC_DIR   = os.path.dirname(os.path.abspath(SPEC))
ROOT       = os.path.dirname(SPEC_DIR) 
INSTALADOR = SPEC_DIR

# Usar directorio protegido si existe (generado por proteger_codigo.bat)
APP_PROTEGIDA = os.path.join(INSTALADOR, 'app_protegida', 'app')
APP_ORIGINAL  = os.path.join(ROOT, 'app')
APP = APP_PROTEGIDA if os.path.isdir(APP_PROTEGIDA) else APP_ORIGINAL

print(f"[PyInstaller] ROOT dir: {ROOT}")
print(f"[PyInstaller] Usando directorio: {'PROTEGIDO' if APP == APP_PROTEGIDA else 'ORIGINAL (sin proteccion)'}")
print(f"[PyInstaller] APP dir: {APP}")

# ── Datos a incluir en el .exe ────────────────────────────────────────────────
# NOTA: El frontend NO va dentro del .exe.
# node.exe y frontend/ se copian junto al .exe por build_instalador.bat.
datas = [
    # 1. Codigo fuente (protegido o desarrollo segun disponibilidad)
    (APP, 'app'),

    # 2. Plantillas HTML para PDFs (WeasyPrint / Jinja2)
    (os.path.join(APP, 'templates'), 'app/templates'),

    # 3. Configuracion de Alembic (migraciones de base de datos)
    (os.path.join(ROOT, 'alembic'), 'alembic'),
    (os.path.join(ROOT, 'alembic.ini'), '.'),
]

# Runtime de PyArmor (necesario para archivos ofuscados)
PYARMOR_RUNTIME = os.path.join(INSTALADOR, 'app_protegida', 'app', 'pyarmor_runtime_000000')
if os.path.isdir(PYARMOR_RUNTIME):
    datas += [(PYARMOR_RUNTIME, 'app/pyarmor_runtime_000000')]
    print("[PyInstaller] Runtime de PyArmor incluido")
else:
    print("[PyInstaller] Sin PyArmor runtime — modo sin ofuscacion")

# Agregar datos de paquetes que los necesiten
datas += collect_data_files('weasyprint')
datas += collect_data_files('jinja2')
datas += collect_data_files('sqlalchemy')
datas += collect_data_files('alembic')
datas += collect_data_files('itsdangerous')

# ── Imports ocultos (módulos que PyInstaller no detecta automáticamente) ──────
hiddenimports = [
    # SQLAlchemy dialects
    'sqlalchemy.dialects.sqlite',
    'sqlalchemy.dialects.postgresql',

    # Alembic
    'alembic',
    'alembic.config',
    'alembic.command',
    'alembic.runtime.migration',
    'alembic.operations',

    # FastAPI / Starlette
    'uvicorn',
    'uvicorn.logging',
    'uvicorn.loops',
    'uvicorn.loops.auto',
    'uvicorn.protocols',
    'uvicorn.protocols.http',
    'uvicorn.protocols.http.auto',
    'uvicorn.protocols.websockets',
    'uvicorn.protocols.websockets.auto',
    'uvicorn.lifespan',
    'uvicorn.lifespan.on',
    'fastapi',
    'starlette',
    'starlette.staticfiles',

    # Base de datos SQLite
    'sqlite3',
    'aiosqlite',

    # Autenticación
    'jose',
    'jose.jwt',
    'passlib',
    'passlib.context',
    'passlib.handlers.bcrypt',
    'itsdangerous',
    'itsdangerous.url_safe',

    # PDF
    'weasyprint',
    'reportlab',
    'reportlab.pdfgen',

    # Módulos de la app
    'app.main',
    'app.core.licencia',
    'app.api.licencia.routes',
] + collect_submodules('app')

# ── Exclusiones (reducen el tamaño del .exe) ─────────────────────────────────
excludes = [
    # Servicios cloud (no se usan en modo local)
    'openai',
    'anthropic',
    'boto3',
    'botocore',
    'google.cloud',

    # WhatsApp (solo versión web)
    # 'app.api.whatsapp',  # Comentado: mejor excluir desde el código con FINAXIS_MODO

    # Testing
    'pytest',
    'unittest',

    # Desarrollo
    'IPython',
    'jupyter',
    'notebook',
]

# ── Análisis ──────────────────────────────────────────────────────────────────
a = Analysis(
    [os.path.join(INSTALADOR, 'run_local.py')],  # Punto de entrada
    pathex=[ROOT],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,         # PyArmor maneja la ofuscación
    noarchive=False,
)

# ── Empaquetar en un directorio (más rápido al arrancar que onefile) ──────────
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='FinaxisLocal',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,                        # Comprimir con UPX si está disponible
    console=True,                    # True = muestra ventana de consola (útil para ver errores)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon=os.path.join(INSTALADOR, 'assets', 'finaxis.ico'),  # Descomentar cuando exista el .ico
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='finaxis_local',            # Nombre de la carpeta en dist/
)
