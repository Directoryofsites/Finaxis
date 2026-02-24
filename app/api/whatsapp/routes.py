from fastapi import APIRouter, Request, Response, Depends, HTTPException, status
import logging
from typing import Dict, Any
import os
from sqlalchemy.orm import Session
import json
from app.core.database import get_db
from app.services.whatsapp_service import process_whatsapp_message

router = APIRouter(tags=["WhatsApp"])
logger = logging.getLogger(__name__)

WHATSAPP_VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "ContapySecreto2026")

@router.get("/webhook")
async def verify_webhook(request: Request):
    """
    Endpoint requerido por Meta para verificar el Webhook la primera vez que se configura.
    """
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode and token:
        if mode == "subscribe" and token == WHATSAPP_VERIFY_TOKEN:
            logger.info("WEBHOOK_VERIFIED")
            return Response(content=challenge, status_code=200)
        else:
            raise HTTPException(status_code=403, detail="Verification token mismatch")
    
    raise HTTPException(status_code=400, detail="Missing parameters")

@router.post("/webhook")
async def receive_message(request: Request, db: Session = Depends(get_db)):
    """
    Endpoint donde Meta enviará los mensajes de los usuarios.
    """
    try:
        body = await request.json()
        logger.info(f"WEBHOOK_INCOMING: {body}")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")
    
    # Validamos estructura del payload de WhatsApp
    if body.get("object") == "whatsapp_business_account":
        for entry in body.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {})
                messages = value.get("messages", [])
                
                if messages:
                    # Meta manda mensajes en una lista, por lo general procesamos el primero
                    message = messages[0]
                    
                    # Llamamos de forma asíncrona al procesador central de backend
                    # Se ejecuta background task o await dependiendo de si la app es intensiva
                    # Por ahora procesamos inline para facilidad de la IA
                    await process_whatsapp_message(message, value, db)

        # Meta requiere siempre un 200 OK rápido para saber que el webhook funciona
        return Response(content="EVENT_RECEIVED", status_code=200)
    else:
        return Response(content="Not a WhatsApp event", status_code=404)
