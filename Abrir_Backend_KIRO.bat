@echo off
TITLE Backend Server KIRO - Base de Datos Exclusiva
COLOR 0A

echo.
echo ========================================
echo    🤖 BACKEND KIRO - ENTORNO AISLADO
echo ========================================
echo.
echo 🗄️  Base de datos: kiro_clean_db
echo 🌐 Puerto backend: 8002
echo 🔒 Entorno completamente aislado
echo.

:: Cambia al directorio del proyecto Kiro
cd /d "C:\ContaPY2_Kiro"

echo 🔄 Activando entorno virtual...
:: Activa el entorno virtual
call .\.venv\Scripts\activate.bat

echo ✅ Entorno activado.
echo.
echo 🚀 Iniciando servidor KIRO en puerto 8002...
echo    - Base de datos: kiro_clean_db
echo    - Puerto: 8002 (aislado de Antigravity)
echo    - Seeder automático: HABILITADO
echo.

:: Ejecuta el script run.py que tomará automáticamente PORT=8002 del .env
.\.venv\Scripts\python.exe run.py

echo.
echo ⚠️  El servidor KIRO se ha detenido.
echo.
:: Pausa al final para ver la salida si el servidor se detiene
pause