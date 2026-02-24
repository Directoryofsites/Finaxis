from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional, Dict
from sqlalchemy.orm import Session
from app.services.ai_agent import procesar_comando_natural
from app.core.security import get_current_user
from app.core.database import get_db
from app.services.ai_quota_service import AIQuotaService, AIQuotaException

router = APIRouter()

class VoiceCommandRequest(BaseModel):
    command: str
    context: Optional[Dict] = None

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
