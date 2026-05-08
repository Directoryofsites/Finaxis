@echo off
REM ═══════════════════════════════════════════════════════════════════════════
REM  proteger_codigo.bat
REM  Estrategia de protección multicapa para Finaxis Local (Opción B - Gratuita)
REM
REM  CAPAS DE PROTECCIÓN:
REM    Capa 1: PyArmor Trial → Ofusca archivos CRÍTICOS (licencia, seguridad)
REM    Capa 2: compileall    → Compila TODO a bytecode .pyc (ilegible directo)
REM    Capa 3: PyInstaller   → Empaqueta en .exe opaco
REM    Capa 4: UPX           → Comprime el ejecutable
REM
REM  EJECUTAR ANTES de build_instalador.bat
REM  Ubicación: c:\ContaPY2\instalador\proteger_codigo.bat
REM ═══════════════════════════════════════════════════════════════════════════

echo.
echo ╔══════════════════════════════════════════════════════╗
echo ║   FINAXIS — Protección de Código (Multicapa)        ║
echo ╚══════════════════════════════════════════════════════╝
echo.

SET ROOT=%~dp0..
SET APP_DIR=%ROOT%\app
SET BUILD_DIR=%ROOT%\instalador\app_protegida

REM Limpiar build anterior
IF EXIST "%BUILD_DIR%" rmdir /S /Q "%BUILD_DIR%"
mkdir "%BUILD_DIR%"

echo ════════════════════════════════════════
echo  CAPA 1: PyArmor — Archivos criticos
echo ════════════════════════════════════════
echo.

REM ── Archivos críticos a ofuscar con PyArmor ──────────────────────────────
REM (Solo archivos pequeños que entran en la licencia Trial)
SET CRITICOS=^
    "%APP_DIR%\core\licencia.py" ^
    "%APP_DIR%\core\security.py" ^
    "%APP_DIR%\core\database.py" ^
    "%APP_DIR%\core\hashing.py" ^
    "%APP_DIR%\core\config.py" ^
    "%APP_DIR%\core\security_encryption.py" ^
    "%APP_DIR%\core\constants.py"

echo Ofuscando archivos criticos con PyArmor...
for %%F in (%CRITICOS%) do (
    if exist %%F (
        echo   -> Ofuscando: %%~nxF
        pyarmor gen --output "%BUILD_DIR%\core_obf" %%F 2>nul
        if %ERRORLEVEL% NEQ 0 (
            echo      ADVERTENCIA: No se pudo ofuscar %%~nxF (demasiado grande para Trial)
            echo      Se usará compilacion .pyc como fallback.
        ) else (
            echo      OK: %%~nxF ofuscado correctamente
        )
    )
)

echo.
echo ════════════════════════════════════════
echo  CAPA 2: compileall — Compilar a .pyc
echo ════════════════════════════════════════
echo.
echo Compilando todo el codigo Python a bytecode...

python -m compileall "%APP_DIR%" -q -b
IF %ERRORLEVEL% EQU 0 (
    echo OK: Bytecode .pyc generado en todos los modulos
) ELSE (
    echo ADVERTENCIA: Algunos archivos no pudieron compilarse
)

echo.
echo ════════════════════════════════════════
echo  CAPA 3: Preparar directorio seguro
echo ════════════════════════════════════════
echo.

REM Copiar toda la app al directorio protegido
echo Copiando aplicacion al directorio protegido...
xcopy /E /I /Y /Q "%APP_DIR%" "%BUILD_DIR%\app"

REM Reemplazar archivos críticos con sus versiones ofuscadas de PyArmor
IF EXIST "%BUILD_DIR%\core_obf" (
    echo Reemplazando archivos criticos con versiones ofuscadas...
    
    REM Los archivos ofuscados por PyArmor van en una subcarpeta con el mismo nombre
    for %%F in ("%BUILD_DIR%\core_obf\*.py") do (
        SET FNAME=%%~nxF
        IF EXIST "%BUILD_DIR%\app\core\%%~nxF" (
            copy /Y "%%F" "%BUILD_DIR%\app\core\%%~nxF" >nul
            echo   -> Reemplazado: %%~nxF
        )
    )
    
    REM Copiar el runtime de PyArmor (necesario para que los archivos ofuscados funcionen)
    IF EXIST "%BUILD_DIR%\core_obf\pyarmor_runtime_000000" (
        xcopy /E /I /Y /Q "%BUILD_DIR%\core_obf\pyarmor_runtime_000000" "%BUILD_DIR%\app\pyarmor_runtime_000000"
        echo OK: Runtime de PyArmor copiado
    )
)

REM Eliminar archivos .py ORIGINALES (dejar solo .pyc) para los NO ofuscados
echo.
echo Eliminando fuentes .py (manteniendo solo .pyc compilado)...
for /R "%BUILD_DIR%\app" %%F in (*.py) do (
    REM Verificar si existe el .pyc correspondiente antes de borrar
    IF EXIST "%%~dpnF.pyc" (
        del /Q "%%F" >nul 2>&1
    )
)

REM NUNCA incluir herramientas privadas
IF EXIST "%BUILD_DIR%\app\herramientas_privadas" (
    rmdir /S /Q "%BUILD_DIR%\app\herramientas_privadas"
    echo OK: Herramientas privadas excluidas del build
)

REM Eliminar archivos de desarrollo que no deben ir en producción
del /Q "%BUILD_DIR%\app\*.log" >nul 2>&1
del /Q "%BUILD_DIR%\app\test_*.py" >nul 2>&1
del /Q "%BUILD_DIR%\app\debug_*.py" >nul 2>&1

echo.
echo ════════════════════════════════════════
echo  RESUMEN DE PROTECCION
echo ════════════════════════════════════════
echo.

REM Contar archivos
for /F %%A in ('dir /B /S "%BUILD_DIR%\app\*.pyc" 2^>nul ^| find /C /V ""') do SET PYC_COUNT=%%A
for /F %%A in ('dir /B /S "%BUILD_DIR%\app\*.py" 2^>nul ^| find /C /V ""') do SET PY_COUNT=%%A

echo   Archivos .pyc (bytecode protegido): %PYC_COUNT%
echo   Archivos .py (fuente visible):      %PY_COUNT%
echo   Directorio de salida: %BUILD_DIR%
echo.

IF %PY_COUNT% GTR 5 (
    echo NOTA: Quedan %PY_COUNT% archivos .py. Esto es normal para:
    echo   - Archivos de configuracion de Alembic
    echo   - __init__.py vacios
    echo   - Archivos que no tienen .pyc porque fallaron
)

echo.
echo ╔══════════════════════════════════════════════════════╗
echo ║  Proteccion completada                              ║
echo ║  Directorio listo para PyInstaller:                 ║
echo ║  instalador\app_protegida\                          ║
echo ╚══════════════════════════════════════════════════════╝
echo.
pause
