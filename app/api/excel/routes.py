from datetime import timedelta, date, datetime
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status
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
def login_excel_addon(db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Endpoint de autenticación optimizado para el Add-in de Excel.
    Retorna el token y la lista de empresas a las que el usuario tiene acceso.
    """
    user = services_usuario.get_user_by_email(db, email=form_data.username)
    if not user or not verify_password(form_data.password, user.password_hash):
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
            # Parsear "2026-03" -> Fecha límite "2026-03-31" (último día del mes)
            parts = periodo.split("-")
            year, month = int(parts[0]), int(parts[1])
            if month == 12:
                next_month = date(year + 1, 1, 1)
            else:
                next_month = date(year, month + 1, 1)
            
            end_date = next_month - timedelta(days=1)
            # Acotamos hasta el final del día de la fecha límite
            end_date_str = end_date.strftime("%Y-%m-%d 23:59:59")
            query = query.filter(Documento.fecha <= end_date_str)
        except Exception:
            raise HTTPException(status_code=400, detail="Formato de periodo inválido. Use YYYY-MM.")
            
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
