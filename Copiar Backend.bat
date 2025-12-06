@echo off
setlocal

:: ============================================================================
:: SCRIPT DE BACKUP PARA EL BACKEND DE CONTAPY (v5 - A PRUEBA DE FALLOS)
:: ============================================================================

:: --- INICIO DE LA CORRECCIÓN DEFINITIVA ---
:: Se usa el método más robusto y universal para obtener fecha y hora.
:: No se cortan cadenas, solo se reemplazan caracteres inválidos.

echo Obteniendo fecha y hora del sistema...
:: Reemplaza las barras (/) de la fecha por guiones (-).
set "FECHA_HOY=%date:/=-%"
:: Reemplaza los dos puntos (:) de la hora por guiones (-).
set "HORA_AHORA=%time::=-%"
:: Elimina los milisegundos y cualquier carácter restante que pueda dar problemas.
for /f "tokens=1 delims=," %%i in ("%HORA_AHORA%") do set "HORA_LIMPIA=%%i"

:: --- FIN DE LA CORRECCIÓN DEFINITIVA ---


:: 2. Definir rutas
echo Configurando rutas...
set "RUTA_PROYECTO=C:\ContaPY2\"
set "RUTA_BACKUP=C:\Backups\"
set "ARCHIVO_BACKUP=Backend_ContaPY2_Backup fecha_%FECHA_HOY% hora_%HORA_LIMPIA%.rar"
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

"%RUTA_WINRAR%" a -r -x*__pycache__\* -x*.venv\* -x*.git\* -x*frontend\* -x*alembic\versions_old\* -x*test_bug.py* "%RUTA_BACKUP%%ARCHIVO_BACKUP%" "%RUTA_PROYECTO%"


:: 5. Finalización
echo.
echo ✅ Backup completado con éxito.
echo El archivo se ha guardado en: %RUTA_BACKUP%
echo.
pause