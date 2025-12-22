from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.services.ai_agent import procesar_comando_natural
from app.core.security import get_current_user

router = APIRouter()

class VoiceCommandRequest(BaseModel):
    command: str

@router.post("/process-command")
async def process_voice_command(request: VoiceCommandRequest, current_user = Depends(get_current_user)):
    """
    Procesa un comando de voz/texto natural usando Gemini AI.
    """
    result = await procesar_comando_natural(request.command)
    return result

@router.post("/process-command-debug")
async def process_voice_command_debug(request: VoiceCommandRequest):
    """
    DEBUG ONLY: Endpoint sin autenticación para probar gemini
    """
    print(f"DEBUG: Setting up AI request for '{request.command}'")
    result = await procesar_comando_natural(request.command)
    return result
