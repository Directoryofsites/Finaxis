@echo off
echo ==========================================
echo      INICIANDO SISTEMA FINAXIS
echo ==========================================

echo 1. Iniciando Backend (Python/FastAPI) en puerto 8002...
:: Usamos -m uvicorn para asegurar que encuentre el modulo 'app' correctamente
start "Backend Finaxis (8002)" cmd /k "python -m uvicorn app.main:app --reload --port 8002 --host 127.0.0.1"

echo 2. Iniciando Frontend (Next.js) en puerto 3000...
cd frontend
start "Frontend Finaxis (3000)" cmd /k "npm run dev"

echo ==========================================
echo      SISTEMA INICIADO
echo ==========================================
echo Por favor, espera unos segundos a que carguen las ventanas.
echo Si alguna ventana se cierra inmediatamente, hay un error.
pause
