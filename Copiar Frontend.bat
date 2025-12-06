@echo off
setlocal

:: ============================================================================
:: SCRIPT DE BACKUP PARA EL FRONTEND DE CONTAPY (v5 - A PRUEBA DE FALLOS)
:: ============================================================================
:: Propósito: Crea un archivo .rar del frontend, excluyendo carpetas pesadas
::            y usando un nombre de archivo legible y seguro.
:: ============================================================================

:: 1. Obtener fecha y hora del sistema
echo Obteniendo fecha y hora del sistema...
:: Reemplaza las barras (/) de la fecha por guiones (-).
set "FECHA_HOY=%date:/=-%"
:: Reemplaza los dos puntos (:) de la hora por guiones (-).
set "HORA_AHORA=%time::=-%"
:: Elimina los milisegundos y cualquier carácter restante que pueda dar problemas.
for /f "tokens=1 delims=," %%i in ("%HORA_AHORA%") do set "HORA_LIMPIA=%%i"


:: 2. Definir rutas
echo Configurando rutas...
:: Ruta específica a la carpeta del frontend.
set "RUTA_PROYECTO_FRONTEND=C:\ContaPY2\frontend\"
:: Carpeta donde se guardarán las copias de seguridad.
set "RUTA_BACKUP=C:\Backups\"
:: Nombre del archivo final con el formato legible.
set "ARCHIVO_BACKUP=Frontend_ContaPY2_Backup fecha_%FECHA_HOY% hora_%HORA_LIMPIA%.rar"
:: Ruta al programa WinRAR.
set "RUTA_WINRAR=C:\Program Files\WinRAR\WinRAR.exe"


:: 3. Crear la carpeta de backups si no existe
if not exist "%RUTA_BACKUP%" (
    echo La carpeta de backups no existe. Creando: %RUTA_BACKUP%
    mkdir "%RUTA_BACKUP%"
)


:: 4. Ejecutar el backup
echo.
echo ============================================================================
echo Creando backup: %RUTA_BACKUP%%ARCHIVO_BACKUP%
echo ============================================================================
echo.

:: Se excluyen las carpetas .next (archivos de compilación) y node_modules (librerías)
"%RUTA_WINRAR%" a -r -x*\.next\* -x*\node_modules\* "%RUTA_BACKUP%%ARCHIVO_BACKUP%" "%RUTA_PROYECTO_FRONTEND%"


:: 5. Finalización
echo.
echo ✅ Backup completado con éxito.
echo El archivo se ha guardado en: %RUTA_BACKUP%
echo.
pause