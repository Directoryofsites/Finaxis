import asyncio
import os
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.usuario import Usuario

async def test_full_pipeline():
    from app.services.ai_agent import procesar_comando_natural
    from app.services.whatsapp_dispatcher import dispatch_whatsapp_command
    
    db = SessionLocal()
    # Cambia el numero de tu admin
    user = db.query(Usuario).filter(Usuario.whatsapp_number == "573234259925").first()
    
    if not user:
        print("No user found")
        return
        
    print(f"User: {user.email} (Empresa: {user.empresa_id})")
    text = "Dame los ingresos y gastos de enero"
    
    print("\n1. Running procesar_comando_natural...")
    ai_response = await procesar_comando_natural(text, contexto={"via": "whatsapp", "empresa_id": user.empresa_id, "user_id": user.id})
    print(f"AI Response: {ai_response}")
    
    print("\n2. Running dispatch_whatsapp_command...")
    try:
        final_text = await dispatch_whatsapp_command(ai_response, text, user.empresa_id, user.id, db)
        print(f"Final Text Sent to WhatsApp:\n{final_text}")
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        
    db.close()

if __name__ == "__main__":
    asyncio.run(test_full_pipeline())
