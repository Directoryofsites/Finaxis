@echo off
TITLE Arreglar Permisos de Conciliacion Bancaria

echo ======================================================================
echo   SOLUCION DE PERMISOS - MODULO DE CONCILIACION BANCARIA
echo ======================================================================
echo.
echo Este script creara los permisos faltantes en la base de datos
echo.

REM Cambia al directorio del proyecto
cd /d "%~dp0"

REM Ejecuta el script de Python con el entorno virtual
.\.venv\Scripts\python.exe check_and_fix_permissions.py

echo.
echo ======================================================================
echo   Presiona cualquier tecla para cerrar esta ventana
echo ======================================================================
pause
