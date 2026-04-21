import os
import json
import logging
import asyncio
from datetime import datetime
import google.generativeai as genai
from app.services.manual_parser import get_relevant_manuals_context
from app.services.ai_tools_schema import AI_TOOLS

logger = logging.getLogger(__name__)

class FinaxisTutorService:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY", "").strip()
        if self.api_key:
            genai.configure(api_key=self.api_key)
            # Usaremos gemini-flash-latest para asegurar compatibilidad y estabilidad
            self.model_name = 'models/gemini-flash-latest' 
        else:
            self.model_name = None
            
        self.manuals_dir = os.path.join("c:\\ContaPY2", "frontend", "public", "manual", "ph")
        
    async def process_query(self, query: str, history: list, empresa_id: int, user_id: int):
        if not self.api_key:
            return {"error": "API Key de Gemini no configurada correctamente en el servidor."}
            
        # 1. Obtener contexto RELEVANTE de los manuales
        manuals_context = get_relevant_manuals_context(query, self.manuals_dir)
        
        # 2. Construir el System Prompt del Tutor
        today = datetime.now().strftime("%Y-%m-%d")
        system_instruction = f"""
ERES "FINAXIS TUTOR", UN ANALISTA FINANCIERO Y EXPERTO DE SOPORTE PARA EL SISTEMA CONTABLE FINAXIS.

OBJETIVO:
1. Ayudar al usuario a usar la plataforma basándote en los manuales proporcionados abajo.
2. Responder dudas financieras sobre los datos de su empresa (ID: {empresa_id}).
3. Ser profesional, pedagógico y empoderador.

REGLAS DE ORO:
- Usa el CONTEXTO DE MANUALES para guiar al usuario paso a paso.
- Si el usuario pregunta por cifras, explica cómo obtenerlas o sugiere el reporte adecuado.
- NUNCA inventes datos. Si no sabes algo, admite que no está en el manual y sugiere contactar a soporte técnico.
- MANTÉN EL AISLAMIENTO: Solo tienes permiso para guiar sobre la empresa {empresa_id}.
- Usa formato Markdown para que las respuestas sean legibles.

FECHA ACTUAL: {today}

--- CONTEXTO DE MANUALES DE FINAXIS ---
{manuals_context}
"""

        # 3. Preparar el historial para Gemini
        gemini_history = []
        for msg in history[-15:]:
            role = "user" if msg["role"] == "user" else "model"
            gemini_history.append({"role": role, "parts": [msg["content"]]})

        # 4. Configurar el modelo
        model = genai.GenerativeModel(
            model_name=self.model_name,
            system_instruction=system_instruction
        )

        max_retries = 3
        retry_delay = 2 # segundos iniciales

        # 5. Bucle de ejecución con reintentos (Resiliencia ante 429)
        for attempt in range(max_retries):
            try:
                chat = model.start_chat(history=gemini_history)
                response = chat.send_message(query)
                
                return {
                    "type": "text",
                    "text": response.text
                }

            except Exception as e:
                error_str = str(e).lower()
                # Si es un error de cuota (429), esperamos y reintentamos
                if "429" in error_str or "resource exhausted" in error_str:
                    if attempt < max_retries - 1:
                        wait_time = retry_delay * (attempt + 1)
                        logger.warning(f"Gemini 429 detectado. Reintento {attempt+1}/{max_retries} en {wait_time}s...")
                        await asyncio.sleep(wait_time)
                        continue
                
                logger.error(f"Error en Gemini Tutor (Intento {attempt+1}): {str(e)}")
                # Si fallan todos los reintentos o es otro tipo de error
                if attempt == max_retries - 1:
                    return {"error": f"El servicio de IA está saturado. Por favor, intenta de nuevo en un momento. (Error: {str(e)})"}

tutor_service = FinaxisTutorService()
