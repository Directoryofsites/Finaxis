# instalador/README.md
# Estructura del Directorio del Instalador

## Archivos clave

| Archivo | Propósito |
|:---|:---|
| `run_local.py` | Punto de entrada del .exe (arranca FastAPI + abre navegador) |
| `finaxis_local.spec` | Receta de PyInstaller para crear el ejecutable |
| `finaxis_setup.iss` | Script de Inno Setup para crear el instalador con doble clic |
| `assets/finaxis.ico` | Ícono del programa (PENDIENTE: reemplazar con el real) |
| `assets/finaxis_banner.bmp` | Banner del instalador 497x314px (PENDIENTE) |
| `assets/finaxis_icon.bmp` | Ícono pequeño 55x58px (PENDIENTE) |
| `frontend_build/` | Build compilado de Next.js (se genera con build_instalador.bat) |

## Proceso de construcción

### Prerrequisitos
- Python 3.10+ con todas las dependencias instaladas
- Node.js 18+ con npm
- PyInstaller: `pip install pyinstaller`
- Inno Setup 6: https://jrsoftware.org/isinfo.php

### Construir el instalador (todo automático)
```batch
cd c:\ContaPY2
build_instalador.bat
```

### Paso a paso manual
```batch
# 1. Compilar frontend
cd frontend
npm run build
cd ..

# 2. Copiar build
xcopy /E /I /Y frontend\out instalador\frontend_build

# 3. Empaquetar con PyInstaller
python -m PyInstaller instalador\finaxis_local.spec --noconfirm --clean

# 4. Crear instalador
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" instalador\finaxis_setup.iss
```

## IMPORTANTE: Archivos que NO deben ir en el instalador
- `herramientas_privadas/` — Contiene la clave maestra de licencias
- `.env` — Variables de entorno de producción
- `alembic/versions/` — Las migraciones se incluyen pero son read-only

## Notas de seguridad
- La llave de licencia se valida con `itsdangerous` (no hay servidor externo)
- El código está ofuscado con PyArmor antes del empaquetado
- La base de datos SQLite se guarda en `%APPDATA%\Finaxis\finaxis_local.db`
