@echo off
TITLE Verificar Estado de Permisos

echo ======================================================================
echo   VERIFICACION DE PERMISOS - MODULO DE CONCILIACION BANCARIA
echo ======================================================================
echo.
echo Este script verificara el estado actual de los permisos en la BD
echo.

REM Cambia al directorio del proyecto
cd /d "%~dp0"

REM Ejecuta el script de verificacion
.\.venv\Scripts\python.exe verificar_permisos_db.py

echo.
echo ======================================================================
echo   Presiona cualquier tecla para cerrar esta ventana
echo ======================================================================
pause