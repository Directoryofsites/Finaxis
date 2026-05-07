@echo off
REM ═══════════════════════════════════════════════════════════════════════════
REM  build_instalador.bat - Script maestro de construccion de Finaxis Local
REM
REM  Ejecutar desde la raiz del proyecto: c:\ContaPY2\
REM  ORDEN COMPLETO (Corregido):
REM    0. Protege el codigo (PyArmor + compileall)
REM    1. Compila el frontend Next.js (modo STANDALONE)
REM    2. Empaqueta backend con PyInstaller (Limpia la carpeta dist/finaxis_local)
REM    3. Copia el build standalone al directorio del instalador
REM    4. Verifica / descarga Node.js portable
REM    5. Genera el .exe final con Inno Setup
REM ═══════════════════════════════════════════════════════════════════════════

echo.
echo ====================================================
echo      FINAXIS - Construccion del Instalador
echo      Arquitectura: FastAPI + Next.js Standalone
echo ====================================================
echo.

SET ROOT=%~dp0
REM Quitar la barra final de ROOT para que las rutas no se dupliquen
IF "%ROOT:~-1%"=="\" SET ROOT=%ROOT:~0,-1%

SET FRONTEND_DIR=%ROOT%\frontend
SET INSTALLER_DIR=%ROOT%\instalador
SET DIST_DIR=%ROOT%\dist\finaxis_local
SET FRONTEND_BUILD=%DIST_DIR%\frontend
SET NODE_DEST=%DIST_DIR%\node.exe

REM ── PASO 0: Proteger el codigo fuente ────────────────────────────────────────
echo [0/5] Protegiendo codigo fuente...
echo       PyArmor + compileall (.pyc bytecode)
echo.

call "%INSTALLER_DIR%\proteger_codigo.bat"
IF %ERRORLEVEL% NEQ 0 (
    echo ERROR: Fallo la proteccion del codigo.
    pause
    exit /b 1
)

echo [OK] Codigo protegido.
echo.

REM ── PASO 1: Compilar el frontend Next.js (modo standalone) ───────────────────
echo [1/5] Compilando frontend Next.js en modo STANDALONE...
echo       Esto puede tomar 3-5 minutos...
echo.

cd /d "%FRONTEND_DIR%"
SET NEXT_PUBLIC_API_URL=http://localhost:8765

call npm run build
IF %ERRORLEVEL% NEQ 0 (
    echo ERROR: Fallo la compilacion del frontend.
    pause
    exit /b 1
)

echo [OK] Frontend compilado correctamente.
echo.
cd /d "%ROOT%"

REM ── PASO 2: Empaquetar backend con PyInstaller ────────────────────────────────
echo [2/5] Empaquetando backend con PyInstaller...
echo       Esto puede tomar 5-15 minutos...
echo.

REM NOTA: PyInstaller limpia y borra %DIST_DIR% por defecto, por lo que DEBE ejecutarse
REM antes de copiar el frontend y node.exe.
python -m PyInstaller "%INSTALLER_DIR%\finaxis_local.spec" --noconfirm --clean

IF %ERRORLEVEL% NEQ 0 (
    echo ERROR: Fallo PyInstaller.
    pause
    exit /b 1
)

echo [OK] PyInstaller completado.
echo.

REM ── PASO 3: Preparar el directorio dist y copiar standalone ──────────────────
echo [3/5] Preparando directorio de distribucion (Copiando Frontend)...

mkdir "%FRONTEND_BUILD%"

REM Verificar que el build standalone se genero
IF NOT EXIST "%FRONTEND_DIR%\.next\standalone" (
    echo ERROR: No se genero la carpeta .next\standalone
    echo Verifique que next.config.js tiene output: 'standalone'
    pause
    exit /b 1
)

REM Copiar el servidor Node.js minimalista
echo Copiando servidor Next.js standalone...
xcopy /E /I /Y /Q "%FRONTEND_DIR%\.next\standalone" "%FRONTEND_BUILD%"

REM Copiar los assets estaticos (CSS, JS, imagenes) — CRUCIAL
echo Copiando assets estaticos...
xcopy /E /I /Y /Q "%FRONTEND_DIR%\.next\static" "%FRONTEND_BUILD%\.next\static"

REM Copiar la carpeta public (logos, iconos, etc.)
IF EXIST "%FRONTEND_DIR%\public" (
    xcopy /E /I /Y /Q "%FRONTEND_DIR%\public" "%FRONTEND_BUILD%\public"
)

echo [OK] Frontend standalone listo en: dist\finaxis_local\frontend\
echo.

REM ── PASO 4: Verificar / obtener Node.js portable ─────────────────────────────
echo [4/5] Verificando Node.js portable...

REM Buscar node.exe en el PATH del sistema (el instalado normalmente)
SET NODE_SYS=""
FOR /F "delims=" %%i IN ('where node.exe 2^>nul') DO (
    IF "!NODE_SYS!"=="" SET NODE_SYS=%%i
)

REM Buscar en rutas tipicas de instalacion
IF EXIST "C:\Program Files\nodejs\node.exe" SET NODE_SYS="C:\Program Files\nodejs\node.exe"
IF EXIST "%APPDATA%\nvm\current\node.exe"   SET NODE_SYS="%APPDATA%\nvm\current\node.exe"
IF EXIST "%ProgramFiles%\nodejs\node.exe"   SET NODE_SYS="%ProgramFiles%\nodejs\node.exe"

IF NOT %NODE_SYS%=="" (
    echo Copiando node.exe desde: %NODE_SYS%
    copy /Y %NODE_SYS% "%NODE_DEST%" >nul
    echo [OK] node.exe copiado ^(~50MB^).
) ELSE (
    echo ADVERTENCIA: node.exe no encontrado en el sistema.
    echo Descargando Node.js LTS portable desde nodejs.org...
    echo Esto puede tardar 1-2 minutos segun la velocidad de Internet.
    
    SET NODE_URL=https://nodejs.org/dist/v20.11.1/node-v20.11.1-win-x64.zip
    SET NODE_ZIP=%TEMP%\node_portable.zip
    SET NODE_TMP=%TEMP%\node_portable
    
    powershell -Command "Invoke-WebRequest -Uri '%NODE_URL%' -OutFile '%NODE_ZIP%' -UseBasicParsing"
    IF %ERRORLEVEL% NEQ 0 (
        echo ERROR: No se pudo descargar Node.js. Verifique Internet o instale Node.js manualmente.
        pause
        exit /b 1
    )
    
    powershell -Command "Expand-Archive -Path '%NODE_ZIP%' -DestinationPath '%NODE_TMP%' -Force"
    copy /Y "%NODE_TMP%\node-v20.11.1-win-x64\node.exe" "%NODE_DEST%" >nul
    rmdir /S /Q "%NODE_TMP%" >nul 2>&1
    del /Q "%NODE_ZIP%" >nul 2>&1
    
    echo [OK] Node.js portable descargado y copiado.
)
echo.

REM ── PASO 5: Generar instalador con Inno Setup ─────────────────────────────────
echo [5/5] Generando instalador con Inno Setup...

SET INNO_PATH=""
IF EXIST "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"                    SET INNO_PATH="C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
IF EXIST "C:\Program Files\Inno Setup 6\ISCC.exe"                           SET INNO_PATH="C:\Program Files\Inno Setup 6\ISCC.exe"
IF EXIST "C:\Users\lenovo\AppData\Local\Programs\Inno Setup 6\ISCC.exe"     SET INNO_PATH="C:\Users\lenovo\AppData\Local\Programs\Inno Setup 6\ISCC.exe"

IF %INNO_PATH%=="" (
    echo ADVERTENCIA: Inno Setup no encontrado.
    echo El ejecutable de PyInstaller SI esta listo en: dist\finaxis_local\
    echo Para generar el instalador, instale Inno Setup 6 y ejecute:
    echo   iscc instalador\finaxis_setup.iss
) ELSE (
    %INNO_PATH% "%INSTALLER_DIR%\finaxis_setup.iss"
    IF %ERRORLEVEL% NEQ 0 (
        echo ERROR: Fallo Inno Setup.
        pause
        exit /b 1
    )
    echo [OK] Instalador generado en: dist\instalador\FinaxisSetup_v1.0.exe
)

echo.
echo ====================================================
echo  CONSTRUCCION COMPLETADA
echo ====================================================
echo.
echo Archivos generados:
echo   dist\finaxis_local\FinaxisLocal.exe      (ejecutable)
echo   dist\finaxis_local\node.exe              (Node.js portable)
echo   dist\finaxis_local\frontend\server.js    (Next.js)
echo   dist\instalador\FinaxisSetup_v1.0.exe    (instalador cliente)
echo.
pause
