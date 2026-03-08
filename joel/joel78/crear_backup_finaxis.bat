@echo off
setlocal enabledelayedexpansion

:: ==========================================
:: SCRIPT DE RESPALDO PARA INTEGRACION FINAXIS
:: ==========================================

echo Iniciando proceso de empaquetado para la Inteligencia Artificial del equipo de integracion...

:: 1. Obtener la fecha y hora sin caracteres especiales
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set datetime=%%I
set FECHA_HORA=%datetime:~0,4%-%datetime:~4,2%-%datetime:~6,2%_%datetime:~8,2%-%datetime:~10,2%

:: 2. Definir rutas (Origen es tu propia carpeta y destino ahi mismo)
set RUTA_PROYECTO=C:\SCFIN2
set RUTA_DESTINO=C:\SCFIN2\Backup_FINAXIS_%FECHA_HORA%.rar
set RUTA_WINRAR="C:\Program Files\WinRAR\WinRAR.exe"

:: Verificar si WinRAR está instalado
if not exist %RUTA_WINRAR% (
    echo [ERROR] No se encontro WinRAR en "C:\Program Files\WinRAR\WinRAR.exe"
    echo Por favor, asegurese de tener WinRAR instalado en esa ruta.
    pause
    exit /b
)

:: 3. Ejecutar comando WinRAR excluyendo librerias y frameworks pesados
:: -r : Recursivo (incluye subcarpetas)
:: -ep1: Excluye la ruta base en la estructura comprimida
:: -x : Excluye elementos pesados, instaladores fallidos o el propio backup generado antes.
echo Comprimiendo archivos en la carpeta raiz del proyecto...
%RUTA_WINRAR% a -r -ep1 ^
    -x*\node_modules\* ^
    -x*\.next\* ^
    -x*\.git\* ^
    -x*\__pycache__\* ^
    -x*\dist\* ^
    -x*\frontend-app\* ^
    -xBackup_FINAXIS_*.rar ^
    "%RUTA_DESTINO%" "%RUTA_PROYECTO%"

echo.
if %errorlevel% equ 0 (
    echo ========================================================
    echo [EXITO] Archivo creado correctamente en tu carpeta raiz SCFIN2:
    echo %RUTA_DESTINO%
    echo Se han excluido todas las rutinas innecesarias.
    echo Listo para ser enviado al otro equipo o IA del tio.
    echo ========================================================
) else (
    echo [ERROR] Hubo un problema al crear el archivo comprimido.
)

pause
