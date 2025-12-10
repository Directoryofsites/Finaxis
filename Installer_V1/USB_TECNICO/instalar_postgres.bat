@echo off
TITLE Instalador Silencioso de Motor de Base de Datos (SOLO USO TECNICO)
echo.
echo =============================================================
echo    INSTALADOR AUTOMATICO DE POSTGRESQL - FINAXIS
echo =============================================================
echo.
echo    ESTE SCRIPT INSTALARA EL MOTOR DE BASE DE DATOS.
echo    LA CLAVE MAESTRA SE INYECTARA AUTOMATICAMENTE.
echo    NO TOQUE EL TECLADO DURANTE EL PROCESO.
echo.
echo    Asegurese de que el archivo instalador de PostgreSQL
echo    se llame "postgresql-installer.exe" y este en esta misma carpeta.
echo.
pause

echo.
echo [1/2] Iniciando instalacion desatendida...
echo       Esto puede tardar unos minutos. Por favor espere...

:: COMANDO DE INSTALACION SILENCIOSA
:: --mode unattended: No muestra ventanas
:: --superpassword: Define la clave maestra
:: --servicepassword: Clave para el servicio de Windows (usamos la misma por simplicidad o una segura)

postgresql-installer.exe --mode unattended --superpassword "Jh_811880_:Panica_33195_/*" --servicepassword "Jh_811880_:Panica_33195_/*"

echo.
echo [2/2] Instalacion finalizada.
echo       El motor ya esta listo para recibir la conexion de Finaxis.
echo.
pause
