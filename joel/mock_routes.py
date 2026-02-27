from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="FINAXIS Mock Backend (Sandbox)")

# Configurar CORS para que React pueda consumir la API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- MOCK DATA ---
# Usuarios estáticos (Quemados)
USERS = {
    "comercial@test.com": {
        "id": "U1",
        "nombre": "Juan Pérez",
        "perfil": "Cliente Comercial"
    },
    "apto500@test.com": {
        "id": "U2",
        "nombre": "Inquilino Condominio",
        "perfil": "Inquilino"
    }
}

# Facturas estáticas por usuario ID
INVOICES = {
    "U1": [
        {
            "id": "F1001",
            "concepto": "Crédito Rotativo - Cuota 1",
            "monto": 1250000,
            "fecha_vencimiento": "2026-03-05",
            "estado": "al_dia" # Verde
        },
        {
            "id": "F1002",
            "concepto": "Crédito Libre Inversión - Cuota 5",
            "monto": 840000,
            "fecha_vencimiento": "2026-02-28",
            "estado": "vence_pronto" # Amarillo
        }
    ],
    "U2": [
        {
            "id": "F2001",
            "concepto": "Cuota Administración Marzo",
            "monto": 350000,
            "fecha_vencimiento": "2026-03-10",
            "estado": "al_dia" # Verde
        },
        {
            "id": "F2002",
            "concepto": "Multa por Ruido",
            "monto": 150000,
            "fecha_vencimiento": "2026-02-15",
            "estado": "vencido" # Rojo
        }
    ]
}

# --- SCHEMAS ---
class LoginRequest(BaseModel):
    email: str
    password: str

class PQRRequest(BaseModel):
    asunto: str
    tipo: str
    mensaje: str

# --- ENDPOINTS MOCK ---
@app.post("/auth/login")
def login(request: LoginRequest):
    # En Sandbox, ignoramos la contraseña real
    user = USERS.get(request.email)
    if not user:
        raise HTTPException(status_code=401, detail="Credenciales inválidas. Usa comercial@test.com o apto500@test.com")
    
    return {
        "status": "success",
        "token": f"sandbox_token_{user['id']}",
        "usuario": user
    }

@app.get("/cuenta/estado/{user_id}")
def cuenta_estado(user_id: str):
    facturas = INVOICES.get(user_id, [])
    # Calculamos automáticamente el total adeudado
    total_adeudado = sum(f["monto"] for f in facturas)
    
    return {
        "status": "success",
        "total_adeudado": total_adeudado,
        "facturas": facturas
    }

@app.post("/solicitudes/nueva")
def nueva_solicitud(request: PQRRequest):
    # Simulacro de inserción exitosa
    if not request.asunto or not request.tipo or not request.mensaje:
        raise HTTPException(status_code=400, detail="Todos los campos son obligatorios")
        
    return {
        "status": 200,
        "mensaje": "Caso creado exitosamente. Hemos recibido su PQR."
    }

if __name__ == "__main__":
    import uvicorn
    # Para poder ejecutarlo directamente con > python mock_routes.py
    uvicorn.run(app, host="127.0.0.1", port=8000)
