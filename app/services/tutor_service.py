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
            self.model_name = 'models/gemini-flash-latest' 
        else:
            self.model_name = None
            
        self.manuals_dir = os.path.join("c:\\ContaPY2", "frontend", "public", "manual")
        
    def _prepare_gemini_tools(self):
        """
        Convierte el esquema de OpenAI AI_TOOLS al formato que espera Google Gemini.
        Gemini espera tipos en MAYÚSCULAS (ej: 'OBJECT', 'STRING').
        """
        gemini_tools = []
        for tool in AI_TOOLS:
            if "function" in tool:
                f = tool["function"]
                
                # Función recursiva para convertir tipos a mayúsculas y limpiar campos
                def convert_types(obj):
                    if isinstance(obj, dict):
                        new_obj = {}
                        for k, v in obj.items():
                            if k in ["default", "additionalProperties"]: # Gemini no soporta estos campos en el Schema proto
                                continue
                            if k == "type" and isinstance(v, str):
                                new_obj[k] = v.upper()
                            else:
                                new_obj[k] = convert_types(v)
                        return new_obj
                    elif isinstance(obj, list):
                        return [convert_types(i) for i in obj]
                    else:
                        return obj

                gemini_tools.append({
                    "name": f["name"],
                    "description": f["description"],
                    "parameters": convert_types(f["parameters"])
                })
        return gemini_tools

    async def process_query(self, query: str, history: list, empresa_id: int, user_id: int):
        if not self.api_key:
            return {"error": "API Key de Gemini no configurada correctamente en el servidor."}
            
        # 1. Obtener contexto RELEVANTE de los manuales
        manuals_context = get_relevant_manuals_context(query, self.manuals_dir)
        
        # 2. Construir el System Prompt del Tutor
        today = datetime.now().strftime("%Y-%m-%d")
        system_instruction = f"""
ERES "FINAXIS TUTOR", UN ASISTENTE INTELIGENTE, ANALISTA FINANCIERO Y EXPERTO DE SOPORTE PARA EL SISTEMA FINAXIS.

MISIÓN:
1. Ayudar al usuario a usar la plataforma basándote en los manuales.
2. Responder dudas financieras sobre los datos de su empresa (ID: {empresa_id}).
3. Si el usuario pide datos reales (ej: "Dime mi saldo en bancos", "Genera el auxiliar de caja"), DEBES SUGERIR O LLAMAR a la herramienta adecuada.

REGLAS DE ORO:
- Usa el CONTEXTO DE MANUALES para guiar al usuario paso a paso.
- Si el usuario pregunta por cifras, explica cómo obtenerlas o usa las TOOLS proporcionadas.
- NUNCA inventes datos. Si no sabes algo, admite que no está en el manual.
- MANTÉN EL AISLAMIENTO: Solo tienes permiso para guiar sobre la empresa {empresa_id}.
- Usa formato Markdown para que las respuestas sean legibles (usa títulos, negritas y listas).

FECHA ACTUAL: {today}

--- CONTEXTO DE MANUALES DE FINAXIS ---
{manuals_context}
"""

        # 3. Preparar el historial para Gemini
        gemini_history = []
        for msg in history[-15:]:
            role = "user" if msg["role"] == "user" else "model"
            gemini_history.append({"role": role, "parts": [msg["content"]]})

        # 4. Configurar el modelo CON HERRAMIENTAS
        # Usamos las funciones de AI_TOOLS como declaraciones de funciones para Gemini
        model = genai.GenerativeModel(
            model_name=self.model_name,
            system_instruction=system_instruction,
            tools=self._prepare_gemini_tools()
        )

        max_retries = 3
        retry_delay = 2

        for attempt in range(max_retries):
            try:
                chat = model.start_chat(history=gemini_history)
                response = chat.send_message(query)
                
                # Verificar si Gemini quiere llamar a una función
                if response.candidates[0].content.parts[0].function_call:
                    fc = response.candidates[0].content.parts[0].function_call
                    args = dict(fc.args)
                    
                    # Generar comando natural sugerido
                    suggested_command = f"Ver {fc.name}" # Default
                    if fc.name == "buscar_recurso_o_reporte":
                        suggested_command = f"Ver reporte {args.get('termino_busqueda', '')}"
                    elif fc.name == "generar_auxiliar_cuenta":
                        suggested_command = f"Auxiliar de la cuenta {args.get('cuenta', '')}"
                    elif fc.name == "generar_relacion_saldos":
                        suggested_command = f"Saldos de {args.get('cuenta', '') or args.get('tercero', '')}"
                    elif fc.name == "generar_auditoria_avanzada":
                        prod = args.get('producto')
                        if prod: suggested_command = f"Movimientos de inventario de {prod}"
                        else: suggested_command = "Auditoría avanzada"

                    return {
                        "type": "tool",
                        "name": fc.name,
                        "parameters": args,
                        "suggested_command": suggested_command
                    }

                return {
                    "type": "text",
                    "text": response.text
                }

            except Exception as e:
                error_str = str(e).lower()
                if "429" in error_str or "resource exhausted" in error_str:
                    if attempt < max_retries - 1:
                        await asyncio.sleep(retry_delay * (attempt + 1))
                        continue
                
                logger.error(f"Error en Gemini Tutor (Intento {attempt+1}): {str(e)}")
                if attempt == max_retries - 1:
                    return {"error": f"Error en el motor de Gemini: {str(e)}"}

tutor_service = FinaxisTutorService()
