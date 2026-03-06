from datetime import timedelta, date, datetime
from typing import Optional, Dict, Any, List, Union
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db
from app.core import security
from app.core.hashing import verify_password
from app.schemas import token as token_schema
from app.services import usuario as services_usuario
from app.models.plan_cuenta import PlanCuenta
from app.models.movimiento_contable import MovimientoContable
from app.models.documento import Documento
from app.models.empresa import Empresa

router = APIRouter()

@router.post("/auth", response_model=Dict[str, Any])
async def login_excel_addon(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Endpoint de autenticación universal para Finaxis.
    Soporta JSON (Google Sheets) y Form-Data (Excel/OAuth2).
    """
    username = None
    password = None
    
    content_type = request.headers.get("Content-Type", "")
    
    try:
        if "application/json" in content_type:
            data = await request.json()
            username = data.get("username")
            password = data.get("password")
        else:
            form_data = await request.form()
            username = form_data.get("username")
            password = form_data.get("password")
    except Exception:
        raise HTTPException(status_code=400, detail="Error al procesar los datos de entrada.")

    if not username or not password:
         raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Se requiere el usuario y la contraseña."
        )

    user = services_usuario.get_user_by_email(db, email=username)
    
    # --- DIAGNOSTICO DE AUTH ---
    print(f"DEBUG AUTH: Intentando login para: {username}")
    print(f"DEBUG AUTH: ¿Usuario encontrado?: {user is not None}")
    if user:
        print(f"DEBUG AUTH: Email en BD: {user.email}")
        is_correct = verify_password(password, user.password_hash)
        print(f"DEBUG AUTH: ¿Password verificado?: {is_correct}")
        if not is_correct:
             # Solo logueamos longitudes para evitar brechas de seguridad
             print(f"DEBUG AUTH: Longitud password enviado: {len(password)}")
             print(f"DEBUG AUTH: Hash en BD comienza por: {user.password_hash[:10]}")
    # --- FIN DIAGNOSTICO ---

    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrecta",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Token extendido (7 días) para evitar logins constantes en el panel de Excel
    access_token_expires = timedelta(days=7) 
    roles_list = [rol.nombre for rol in user.roles]
    
    access_token = security.create_access_token(
        data={"sub": user.email, "empresa_id": user.empresa_id, "roles": roles_list},
        expires_delta=access_token_expires
    )
    
    # Obtener lista de empresas para el UI del Taskpane de Excel
    empresas = []
    if user.empresa:
         empresas.append({"id": user.empresa.id, "razon_social": user.empresa.razon_social})
    for emp in user.empresas_asignadas:
         if not any(e["id"] == emp.id for e in empresas):
             empresas.append({"id": emp.id, "razon_social": emp.razon_social})
                 
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "usuario": user.nombre_completo,
        "email": user.email,
        "empresas": empresas
    }

@router.get("/saldo", response_model=Dict[str, float])
def get_saldo_excel(
    cuenta: str,
    periodo: Optional[str] = None, # Formato YYYY-MM
    db: Session = Depends(get_db),
    current_user: Any = Depends(security.get_current_user)
):
    """
    Endpoint principal para funciones personalizadas de Excel: `=FINAXIS.SALDO("1105", "2026-03")`.
    Calcula el saldo acumulado (suma recursiva si es cuenta mayor) hasta el final del parámetro especificado.
    """
    empresa_id = current_user.empresa_id
    if not empresa_id:
        raise HTTPException(status_code=400, detail="El usuario no tiene un contexto de empresa válido.")
        
    # Obtener todas las cuentas que comiencen con el código indicado (para sumar hijas si es cuenta padre)
    cuentas_obj = db.query(PlanCuenta.id).filter(
        PlanCuenta.empresa_id == empresa_id,
        PlanCuenta.codigo.like(f"{cuenta}%")
    ).all()
    
    if not cuentas_obj:
         return {"saldo": 0.0}
    
    cuenta_ids = [c[0] for c in cuentas_obj]
    
    query = db.query(
        func.coalesce(func.sum(MovimientoContable.debito), 0).label("total_debito"),
        func.coalesce(func.sum(MovimientoContable.credito), 0).label("total_credito")
    ).join(
        Documento, MovimientoContable.documento_id == Documento.id
    ).filter(
        MovimientoContable.cuenta_id.in_(cuenta_ids)
    )
    
    # Asegurarnos de que el documento no esté anulado (Acepta B y EMITIDO, etc)
    query = query.filter(Documento.estado != 'ANULADO')
    
    if periodo:
        try:
            # Soporta tanto "2026-03" como "2026-03-01"
            parts = periodo.split("-")
            
            if len(parts) == 3:
                # Caso: YYYY-MM-DD
                end_date_str = f"{periodo} 23:59:59"
            elif len(parts) == 2:
                # Caso: YYYY-MM (Fin de mes)
                year, month = int(parts[0]), int(parts[1])
                if month == 12:
                    next_month = date(year + 1, 1, 1)
                else:
                    next_month = date(year, month + 1, 1)
                end_date = next_month - timedelta(days=1)
                end_date_str = end_date.strftime("%Y-%m-%d 23:59:59")
            else:
                raise ValueError("Formato inválido")
                
            query = query.filter(Documento.fecha <= end_date_str)
        except Exception:
            raise HTTPException(status_code=400, detail="Formato de periodo inválido. Use YYYY-MM o YYYY-MM-DD.")
            
    resultado = query.first()
    
    if resultado:
        debito = float(resultado.total_debito)
        credito = float(resultado.total_credito)
        
        # Naturaleza Contable de Colombia
        # Activos (1), Gastos (5), Costos (6): Naturaleza Débito (Saldo = D - C)
        # Pasivos (2), Patrimonio (3), Ingresos (4): Naturaleza Crédito (Saldo = C - D)
        if cuenta.startswith(('2', '3', '4')):
            saldo_final = credito - debito
        else:
            saldo_final = debito - credito
            
        return {"saldo": saldo_final}
        
    return {"saldo": 0.0}
