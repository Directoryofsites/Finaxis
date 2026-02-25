import os
import json
from datetime import datetime
from dotenv import load_dotenv
from openai import AsyncOpenAI
from app.services.ai_tools_schema import AI_TOOLS

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY", "").strip()
client = None

if api_key:
    # Debug: Mostrar parte de la llave para verificar
    masked_key = f"{api_key[:10]}...{api_key[-4:]}" if len(api_key) > 15 else "INVALID"
    print(f"AI_DEBUG: Usando OpenAI API Key: {masked_key}")
    client = AsyncOpenAI(api_key=api_key)
else:
    print("AI_DEBUG: OPENAI_API_KEY no configurada.")

# --- CARGA DE REGLAS DE ENTRENAMIENTO ---
TRAINING_RULES_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "ai_training_rules.json")

def load_training_rules():
    try:
        if os.path.exists(TRAINING_RULES_PATH):
            with open(TRAINING_RULES_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error cargando reglas de entrenamiento: {e}")
    return {}

def get_system_prompt():
    rules = load_training_rules()
    today = datetime.now().strftime("%Y-%m-%d")
    alias_json = json.dumps(rules.get('alias_cuentas', {}))
    instructions_str = "\n".join([f"* {i}" for i in rules.get('instrucciones_especificas', [])])
    
    prompt = f"""
ERES UN ASISTENTE CONTABLE EXPERTO EN EL SISTEMA "FINAXIS".
TU OBJETIVO ES INTERPRETAR LAS INTENCIONES DEL USUARIO Y MAPEARLAS A LAS HERRAMIENTAS DIRECTAS, SIN INVENTAR DATOS.

FECHA ACTUAL: {today}

1. REGLAS GENERALES:
   - NO inventes información. Utiliza ÚNICAMENTE las funciones (tools) proporcionadas.
   - Si no se especifica explícitamente una fecha en la petición del cliente, DEJA EL CAMPO DE FECHA COMO NULO O VACÍO. No asumas fechas (ej: No uses 2020-01-01 si no lo pide el usuario).
   - El sistema de backend se encargará de rellenar las fechas vacías con "la fecha de creación de la empresa".
   - Extrae cuentas contables, terceros y valores tal cual los menciona el usuario.
   - ¡CRÍTICO SOBRE CUENTAS!: A veces el sistema tiene múltiples cuentas con nombres similares (ej: 41909001 - OFRENDAS DOMINGOS (Ingreso) y 511515 - AUXILIOS Y DONACIONES (Gasto)). SI el usuario pide "Movimiento de donaciones" debes extraer literalmente el nombre principal "Donaciones". Si el usuario dice "Pague donaciones" entonces es gasto.

2. ALIAS Y ENTRENAMIENTO:
   - Alias cargados: {alias_json}
   - Instrucciones específicas:
   {instructions_str}
"""
    return prompt

async def procesar_comando_natural(texto_usuario: str, contexto: dict | None = None):
    if not client:
        return {"error": "API Key de OpenAI no configurada."}

    model_name = "gpt-4o-mini"
    
    try:
        print(f"AI_DEBUG: Intentando usar modelo con tools: {model_name}")
        prompt = get_system_prompt()
        
        # Formatear el input para el modelo
        full_input = f"Contexto extra (ignoralo si no tienes contexto): {json.dumps(contexto or {})} \nUsuario solicitó: {texto_usuario}"
        
        completion = await client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": full_input}
            ],
            tools=AI_TOOLS,
            tool_choice="required", # Obligamos a elegir una función del sistema
            temperature=0.0         # Temperatura cero para máxima precisión en la extracción de parámetros
        )
        
        # Procesar el Tool Call
        choice = completion.choices[0].message
        if choice.tool_calls:
            tool_call = choice.tool_calls[0]
            function_name = tool_call.function.name
            
            try:
                # Los argumentos devueltos por function calling vienen como un string JSON
                arguments = json.loads(tool_call.function.arguments)
            except Exception as e:
                print(f"Error parseando argumentos JSON generados por GPT: {e}")
                arguments = {}

            print(f"AI_DEBUG: Éxito con function calling -> Tool: {function_name}")
            return {
                "name": function_name,
                "parameters": arguments
            }
        else:
            return {"error": "La inteligencia artificial no pudo vincular tu instrucción a ninguna función del sistema. Intenta escribirlo de otra forma."}
        
    except Exception as e:
        print(f"AI_DEBUG: Falló modelo {model_name}. Error: {e}")
        return {"error": f"Error procesando comando: {str(e)}"}
    
