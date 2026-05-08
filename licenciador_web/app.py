from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from itsdangerous import URLSafeSerializer
import datetime

app = FastAPI()

# Mismas claves que en tu script original para que los seriales funcionen
_CLAVE_MAESTRA = "FINAXIS_LOCAL_MASTER_KEY_2026_VERY_SECRET_DO_NOT_SHARE_THIS_123456789"
_SALT = "finaxis-local-activation-salt"

def generar_serial(version="FULL", cliente="Cliente Prueba", max_registros=-1, machine_id=None):
    s = URLSafeSerializer(_CLAVE_MAESTRA, salt=_SALT)
    payload = {
        "version": version,
        "cliente": cliente,
        "emitida": datetime.datetime.now().date().isoformat(),
        "max_registros": max_registros,
        "machine_id": machine_id
    }
    return s.dumps(payload)

@app.get("/", response_class=HTMLResponse)
async def home():
    return """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Finaxis - Licenciador</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap" rel="stylesheet">
        <style>
            body { font-family: 'Inter', sans-serif; background-color: #0f172a; color: #f8fafc; }
            .glass { background: rgba(30, 41, 59, 0.7); backdrop-filter: blur(10px); border: 1px solid rgba(255,255,255,0.1); }
            input { background: #1e293b !important; color: white !important; border: 1px solid #334155 !important; }
        </style>
    </head>
    <body class="flex items-center justify-center min-h-screen p-4">
        <div class="glass p-8 rounded-3xl w-full max-w-md shadow-2xl">
            <div class="text-center mb-8">
                <div class="bg-emerald-500 w-16 h-16 rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-lg shadow-emerald-500/20">
                    <svg class="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z"></path></svg>
                </div>
                <h1 class="text-2xl font-bold">Finaxis Master</h1>
                <p class="text-slate-400 text-sm">Generador de Activación</p>
            </div>

            <form action="/generar" method="post" class="space-y-6">
                <div>
                    <label class="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Nombre del Cliente</label>
                    <input type="text" name="cliente" placeholder="Ej: Ferretería Central" class="w-full p-4 rounded-xl focus:ring-2 focus:ring-emerald-500 outline-none transition-all" required>
                </div>
                <div>
                    <label class="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">ID de la Máquina (Hardware ID)</label>
                    <input type="text" name="mid" placeholder="Pega el ID aquí..." class="w-full p-4 rounded-xl focus:ring-2 focus:ring-emerald-500 outline-none transition-all" required>
                </div>
                <button type="submit" class="w-full bg-emerald-600 hover:bg-emerald-500 text-white font-bold py-4 rounded-xl shadow-lg shadow-emerald-900/20 transition-all active:scale-95">
                    Generar Serial
                </button>
            </form>
        </div>
    </body>
    </html>
    """

@app.post("/generar", response_class=HTMLResponse)
async def result(cliente: str = Form(...), mid: str = Form(...)):
    serial = generar_serial(cliente=cliente, machine_id=mid)
    return f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Serial Generado</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <style>
            body {{ font-family: 'Inter', sans-serif; background-color: #0f172a; color: #f8fafc; }}
            .glass {{ background: rgba(30, 41, 59, 0.7); backdrop-filter: blur(10px); border: 1px solid rgba(255,255,255,0.1); }}
        </style>
    </head>
    <body class="flex items-center justify-center min-h-screen p-4">
        <div class="glass p-8 rounded-3xl w-full max-w-md text-center shadow-2xl">
            <div class="mb-6">
                <span class="bg-emerald-500/20 text-emerald-400 px-4 py-2 rounded-full text-xs font-bold uppercase tracking-widest">¡Éxito!</span>
            </div>
            <h2 class="text-xl font-bold mb-2">{cliente}</h2>
            <p class="text-slate-400 text-xs mb-6">Serial vinculado al ID: {mid}</p>
            
            <div class="bg-slate-900/50 p-4 rounded-xl border border-slate-700 break-all text-emerald-400 font-mono text-sm mb-6 select-all" id="serialText">
                {serial}
            </div>

            <div class="grid grid-cols-1 gap-4">
                <button onclick="copySerial()" class="w-full bg-slate-700 hover:bg-slate-600 text-white font-bold py-3 rounded-xl transition-all">
                    Copiar Código
                </button>
                <a href="https://wa.me/?text=Hola {cliente}, aquí tienes tu serial de activación para Finaxis: {serial}" 
                   class="w-full bg-green-600 hover:bg-green-500 text-white font-bold py-3 rounded-xl flex items-center justify-center gap-2 transition-all">
                    <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path d="M.057 24l1.687-6.163c-1.041-1.804-1.588-3.849-1.588-5.946 0-6.556 5.332-11.888 11.888-11.888 3.176 0 6.161 1.237 8.404 3.48 2.245 2.245 3.481 5.23 3.481 8.408 0 6.556-5.332 11.888-11.888 11.888-2.003 0-3.963-.505-5.696-1.464l-6.29 1.651zm6.29-4.103c1.73.993 3.42 1.488 5.541 1.488 5.485 0 9.951-4.467 9.951-9.953 0-2.652-1.034-5.147-2.907-7.022-1.873-1.874-4.368-2.907-7.044-2.907-5.484 0-9.95 4.467-9.95 9.953 0 2.228.616 3.966 1.706 5.86l-.888 3.243 3.541-.942zm9.244-12.316c.304-.067.669-.067.896-.067.148 0 .252.013.336.033.084.02.213.047.333.153.12.106.467.46.467 1.127 0 .667-.48 1.314-.587 1.46-.107.147-1.12 1.714-2.713 2.4-.38.163-.674.26-.913.333-.387.12-.74.107-1.013.067-.307-.046-.94-.386-1.073-.746-.134-.36-.134-.667-.094-.746.04-.08.147-.127.307-.207.16-.08.94-.467 1.087-.52.147-.053.253-.08.36-.08.107 0 .213.04.307.16.094.12.36.467.44.573.08.107.16.12.307.04.147-.08.627-.233.827-.413.2-.18.333-.393.333-.66s-.133-.513-.267-.64c-.133-.127-.253-.127-.36-.213-.107-.08-.094-.133-.047-.213.047-.08.187-.333.253-.413.067-.08.134-.147.2-.213.067-.067.14-.147.213-.213z"/></svg>
                    WhatsApp Cliente
                </a>
                <a href="/" class="text-slate-500 text-sm mt-4 hover:text-slate-400">Volver al inicio</a>
            </div>
        </div>
        <script>
            function copySerial() {{
                const text = document.getElementById('serialText').innerText;
                navigator.clipboard.writeText(text);
                alert('¡Serial copiado!');
            }}
        </script>
    </body>
    </html>
    """

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
