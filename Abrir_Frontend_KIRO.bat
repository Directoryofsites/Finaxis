@echo off
TITLE Frontend Server KIRO - Puerto 3002
COLOR 0B

echo.
echo ========================================
echo    🌐 FRONTEND KIRO - ENTORNO AISLADO
echo ========================================
echo.
echo 🖥️  Puerto frontend: 3002
echo 🔗 Backend conectado: localhost:8002
echo 🔒 Entorno completamente aislado
echo.

:: Cambia al directorio del frontend Kiro
cd /d "C:\ContaPY2_Kiro\frontend"

echo 🔄 Verificando configuración...
echo    - API URL: http://localhost:8002
echo    - Puerto: 3002 (aislado de Antigravity)
echo.

echo 🚀 Iniciando servidor frontend KIRO...
echo.
echo 📱 Una vez iniciado, accede a:
echo    👉 http://localhost:3002
echo.
echo 🔑 Credenciales disponibles:
echo    - SOPORTE: soporte@soporte.com / Jh811880
echo      URL: http://localhost:3002/admin/utilidades/soporte-util
echo    - ADMIN: admin@empresa.com / admin123
echo      URL: http://localhost:3002/login
echo.

:: Ejecuta el servidor en puerto 3002
npm run dev -- -p 3002

echo.
echo ⚠️  El servidor frontend KIRO se ha detenido.
echo.
:: Pausa al final para ver la salida si el servidor se detiene
pause