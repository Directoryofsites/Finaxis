@echo off
TITLE Consola del Backend (venv ACTIVO)

REM Cambia al directorio del proyecto
cd /d "E:\ContaPY2"

REM Abre una nueva terminal, ejecuta el script de activación y la deja abierta y lista.
start cmd /K .\.venv\Scripts\activate.bat