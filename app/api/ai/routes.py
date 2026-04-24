from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional, Dict
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.services.ai_agent import procesar_comando_natural
from app.core.security import get_current_user
from app.core.database import get_db
from app.services.ai_quota_service import AIQuotaService, AIQuotaException

router = APIRouter()

class VoiceCommandRequest(BaseModel):
    command: str
    context: Optional[Dict] = None

class TutorRequest(BaseModel):
    query: str
    history: Optional[list] = []

@router.post("/process-command")
async def process_voice_command(
    request: VoiceCommandRequest, 
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Procesa un comando de voz/texto natural usando ChatGPT AI.
    Verifica los límites de cuota de IA antes de la solicitud.
    """
    try:
        if not current_user.empresa_id:
            raise HTTPException(status_code=403, detail="Usuario sin empresa asignada")
            
        # Verificar y descontar 1 uso de IA a la empresa
        AIQuotaService.verificar_y_descontar_cuota_ia(current_user.empresa_id, db)
        
    except AIQuotaException as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
        
    result = await procesar_comando_natural(request.command, request.context)
    return result

@router.post("/process-command-debug")
async def process_voice_command_debug(request: VoiceCommandRequest):
    """
    DEBUG ONLY: Endpoint sin autenticación para probar gemini
    """
    print(f"DEBUG: Setting up AI request for '{request.command}'")
    result = await procesar_comando_natural(request.command, request.context)
    return result

@router.post("/tutor")
async def process_tutor_query(
    request: TutorRequest,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Procesa una consulta para el Finaxis Tutor (RAG + Tools).
    """
    from app.services.tutor_service import tutor_service
    
    try:
        # Verificar cuota (el tutor consume saldo de IA)
        AIQuotaService.verificar_y_descontar_cuota_ia(current_user.empresa_id, db)
    except AIQuotaException as e:
        raise HTTPException(status_code=403, detail=str(e))
        
    result = await tutor_service.process_query(
        query=request.query,
        history=request.history,
        empresa_id=current_user.empresa_id,
        user_id=current_user.id
    )
    
    # Guardar en base de datos si no hay error
    if "error" not in result:
        try:
            # 1. Guardar mensaje del usuario
            db.execute(text("""
                INSERT INTO ai_tutor_messages (usuario_id, empresa_id, role, content)
                VALUES (:uid, :eid, 'user', :content)
            """), {"uid": current_user.id, "eid": current_user.empresa_id, "content": request.query})
            
            # 2. Guardar respuesta del asistente
            db.execute(text("""
                INSERT INTO ai_tutor_messages (usuario_id, empresa_id, role, content)
                VALUES (:uid, :eid, 'assistant', :content)
            """), {"uid": current_user.id, "eid": current_user.empresa_id, "content": result.get("text", "")})
            
            db.commit()
        except Exception as e:
            print(f"Error guardando historial: {e}")

    return result

@router.post("/tutor-debug")
async def process_tutor_debug(
    request: TutorRequest
):
    """
    DEBUG: Prueba el tutor sin auth para descartar errores de red/CORS.
    """
    from app.services.tutor_service import tutor_service
    result = await tutor_service.process_query(
        query=request.query,
        history=request.history,
        empresa_id=1,
        user_id=1
    )
    return result

@router.get("/tutor/history")
async def get_tutor_history(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Recupera los últimos 30 mensajes del historial del tutor para el usuario actual.
    """
    try:
        sql = text("""
            SELECT role, content 
            FROM ai_tutor_messages 
            WHERE usuario_id = :uid AND empresa_id = :eid 
            ORDER BY created_at ASC 
            LIMIT 50
        """)
        res = db.execute(sql, {"uid": current_user.id, "eid": current_user.empresa_id}).fetchall()
        return [{"role": row[0], "content": row[1]} for row in res]
    except Exception as e:
        print(f"Error cargando historial: {e}")
        return []

@router.delete("/tutor/history")
async def clear_tutor_history(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Borra el historial del chat para el usuario actual.
    """
    try:
        db.execute(text("""
            DELETE FROM ai_tutor_messages 
            WHERE usuario_id = :uid AND empresa_id = :eid
        """), {"uid": current_user.id, "eid": current_user.empresa_id})
        db.commit()
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
