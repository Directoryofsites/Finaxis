@echo off
TITLE Backend Server - ContaPY

:: Cambia al directorio del proyecto en el disco C
cd /d "C:\ContaPY2_Kiro"

echo Activando entorno virtual...
:: Activa el entorno virtual.
call .\.venv\Scripts\activate.bat
echo Entorno activado.

echo Iniciando servidor a través del lanzador personalizado...
:: --- INICIO DE LA MODIFICACIÓN FINAL ---
:: En lugar de llamar a 'uvicorn' directamente, se ejecuta el script 'run.py'.
:: Esto asegura que nuestra configuración de entorno se aplique primero.
:: Configuración de puerto para entorno KIRO
set PORT=8001
.\.venv\Scripts\python.exe run.py
:: --- FIN DE LA MODIFICACIÓN FINAL ---

:: Pausa al final para ver la salida si el servidor se detiene.
pause