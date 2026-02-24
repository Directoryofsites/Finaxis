import os
import httpx
import logging
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.usuario import Usuario

logger = logging.getLogger(__name__)

WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN", "")
WHATSAPP_PHONE_ID = os.getenv("WHATSAPP_PHONE_ID", "")
WHATSAPP_API_URL = f"https://graph.facebook.com/v18.0/{WHATSAPP_PHONE_ID}/messages"

async def send_whatsapp_message(to_number: str, text: str):
    """
    Envía un mensaje de texto de vuelta al usuario usando la Graph API de Meta.
    """
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "text",
        "text": {"body": text}
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(WHATSAPP_API_URL, json=payload, headers=headers)
        if response.status_code != 200:
            logger.error(f"Error enviando WhatsApp: {response.text}")
        return response

async def process_whatsapp_message(message_data: dict, meta_value: dict, db: Session):
    """
    Parsea el mensaje entrante, lo vincula a un usuario y gestiona la respuesta IA.
    """
    sender_phone = message_data.get("from")
    
    # Extraer el texto si es de tipo texto
    if message_data.get("type") == "text":
        text_body = message_data["text"]["body"]
        
        try:
            # Prevención de UnicodeEncodeError en consola Windows si el usuario manda emojis
            safe_text = text_body.encode('ascii', 'replace').decode()
            logger.info(f"Mensaje recibido de {sender_phone}: {safe_text}")
        except:
            pass
            
        # --- PRUEBA DE ECO (PING-PONG) ---
        if text_body.strip().lower() == "hola":
            await send_whatsapp_message(sender_phone, "Hola, bienvenido. ¿En qué puedo ayudarte?")
            return
            
        
        # 1. Autenticar: Buscar en la BD qué usuario tiene este whatsapp
        user = db.query(Usuario).filter(Usuario.whatsapp_number == sender_phone).first()
        
        if not user:
            # Flujo de Onboarding / Usuario No Registrado
            msg = (
                "¡Hola! Soy Finaxis AI. 🤖\n\n"
                "Parece que no tengo este número registrado. Para usarme, "
                "por favor inicia sesión en la plataforma web y registra tu número de WhatsApp "
                "en tu perfil o contacta con el administrador de tu empresa."
            )
            await send_whatsapp_message(sender_phone, msg)
            return

        # 2. Verificar y descontar cuota IA
        from app.services.ai_quota_service import AIQuotaService, AIQuotaException
        from app.services.ai_agent import procesar_comando_natural
        
        try:
            if not user.empresa_id:
                await send_whatsapp_message(sender_phone, "⛔ No estás asignado a ninguna empresa en el sistema.")
                return

            AIQuotaService.verificar_y_descontar_cuota_ia(user.empresa_id, db)
        except AIQuotaException as e:
            # Enviar mensaje de límite de cuota
            await send_whatsapp_message(sender_phone, f"⚠️ *Alerta Finaxis AI*\n\n{str(e)}")
            return
            
        # 3. Llamar al Motor Cognitivo
        try:
            # Usaremos el módulo principal que se armó para la voz
            ai_response = await procesar_comando_natural(text_body, contexto={"via": "whatsapp", "empresa_id": user.empresa_id, "user_id": user.id})
            
            # Pasar la respuesta del motor cognitivo al Dispatcher para buscar datos en DB y resumirlos
            from app.services.whatsapp_dispatcher import dispatch_whatsapp_command
            respuesta_texto = await dispatch_whatsapp_command(ai_response, text_body, user.empresa_id, user.id, db)
                
            await send_whatsapp_message(sender_phone, respuesta_texto)
            
        except Exception as e:
            logger.error(f"Error procesando IA en WhatsApp: {e}")
            await send_whatsapp_message(sender_phone, "❌ Ocurrió un error en mis circuitos procesando tu mensaje. Intenta de nuevo más tarde.")
            
        return
