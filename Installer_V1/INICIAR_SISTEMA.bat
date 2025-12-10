@echo off
TITLE Finaxis - Sistema Contable y Propiedad Horizontal

echo ======================================================
echo    BIENVENIDO A FINAXIS (MODO PORTABLE)
echo ======================================================
echo.
echo [1/3] Iniciando Servidor Backend (API)...
echo       Por favor espere a que se inicie el motor interno.
cd backend
start "Finaxis API" /MIN FinaxisServer.exe
cd ..

echo.
echo       Esperando 5 segundos para arranque del nucleo...
timeout /t 5 >nul

echo.
echo [2/3] Iniciando Interfaz de Usuario...
echo       El sistema estara disponible en: http://localhost:3000
echo.
echo       CIERRE ESTA VENTANA PARA DETENER EL SISTEMA.
echo.

cd frontend
..\runtime\node.exe server.js
