import os
import google.generativeai as genai
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

# --- CARGA DE REGLAS DE ENTRENAMIENTO ---
TRAINING_RULES_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "ai_training_rules.json")

def load_training_rules():
    try:
        if os.path.exists(TRAINING_RULES_PATH):
            with open(TRAINING_RULES_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error cargando reglas de IA: {e}")
    return {}

# Definición de herramientas (Tools) disponibles para la IA
TOOLS_SCHEMA = [
    {
        "name": "generar_reporte_movimientos",
        "description": "Genera una consulta de movimientos contables (auxiliar) filtrado por cuenta, tercero o fechas. Úsalo cuando pidan 'auxiliar', 'tercero', 'cuenta específica' o 'auditoría'.",
        "parameters": {
            "type": "object",
            "properties": {
                "tercero": { "type": "string" },
                "cuenta": { "type": "string" },
                "fecha_inicio": { "type": "string", "format": "date" },
                "fecha_fin": { "type": "string", "format": "date" },
                "formato": { "type": "string", "enum": ["PDF", "EXCEL", "PANTALLA"] },
                "whatsapp_destino": { "type": "string" },
                "email_destino": { "type": "string" },
                "producto": { "type": "string" },
                "tipo_documento": { "type": "string" },
                "numero_documento": { "type": "string" },
                "accion": { "type": "string" }
            },
            "required": ["fecha_inicio", "fecha_fin"]
        }
    },
    {
        "name": "generar_balance_prueba",
        "description": "Genera el reporte de Balance de Prueba (Saldos).",
        "parameters": {
            "type": "object",
            "properties": {
                "fecha_inicio": { "type": "string", "format": "date" },
                "fecha_fin": { "type": "string", "format": "date" },
                "nivel": { "type": "integer" },
                "formato": { "type": "string", "enum": ["PDF", "EXCEL", "PANTALLA"] },
                "whatsapp_destino": { "type": "string" }
            },
            "required": ["fecha_inicio", "fecha_fin"]
        }
    },
    {
        "name": "generar_estado_resultados",
        "description": "Genera el Estado de Resultados (P&L / Ganancias y Pérdidas). Ingresos, Costos y Gastos.",
        "parameters": {
            "type": "object",
            "properties": {
                "fecha_inicio": { "type": "string", "format": "date" },
                "fecha_fin": { "type": "string", "format": "date" },
                "formato": { "type": "string", "enum": ["PDF", "EXCEL", "PANTALLA"] },
                "whatsapp_destino": { "type": "string" }
            },
            "required": ["fecha_inicio", "fecha_fin"]
        }
    },
    {
        "name": "generar_balance_general",
        "description": "Genera el Balance General (Estado de Situación Financiera).",
        "parameters": {
            "type": "object",
            "properties": {
                "fecha_corte": { "type": "string", "format": "date" },
                "comparativo": { "type": "boolean" },
                "formato": { "type": "string", "enum": ["PDF", "EXCEL", "PANTALLA"] }
            },
            "required": ["fecha_corte"]
        }
    },
    {
        "name": "generar_relacion_saldos",
        "description": "Genera el reporte de 'Relación de Saldos' (Cuenta vs Tercero). Úsalo cuando pidan el 'saldo' de una cuenta filtrado por un tercero específico, o viceversa.",
        "parameters": {
            "type": "object",
            "properties": {
                "tercero": { "type": "string" },
                "cuenta": { "type": "string" },
                "fecha_inicio": { "type": "string", "format": "date" },
                "fecha_fin": { "type": "string", "format": "date" },
                "formato": { "type": "string", "enum": ["PDF", "EXCEL", "PANTALLA"] }
            }
        }
    },
    {
        "name": "crear_recurso",
        "description": "Abre el formulario para CREAR un nuevo registro.",
        "parameters": {
            "type": "object",
            "properties": {
                "tipo": { "type": "string", "enum": ["factura", "compra", "tercero", "item", "traslado", "cuenta"] }
            },
            "required": ["tipo"]
        }
    },
    {
        "name": "navegar_a_pagina",
        "description": "Redirige a un módulo específico.",
        "parameters": {
            "type": "object",
            "properties": {
                "modulo": { "type": "string" },
                "accion": { "type": "string" }
            },
            "required": ["modulo"]
        }
    },
    {
        "name": "extraer_datos_documento",
        "description": "Extrae datos para capturar un documento contable.",
        "parameters": {
            "type": "object",
            "properties": {
                "tipo_documento": { "type": "string" },
                "tercero": { "type": "string" },
                "valor": { "type": "number" },
                "accion": { "type": "string", "enum": ["DEFINIR_CABECERA", "FINALIZAR", "CANCELAR"] }
            }
        }
    }
]

def get_system_prompt():
    rules = load_training_rules()
    today = datetime.now().strftime('%Y-%m-%d')
    current_year = datetime.now().year
    
    prompt = f"""
Eres Finaxis AI, asistente contable inteligente. Interpreta la intención y mapea a una función.
Hoy es: {today}

Reglas:
1. Responde SIEMPRE con un JSON: {{ "name": "funcion", "parameters": {{ ... }} }}
2. INFORMES:
   - "Saldo" + "Cuenta" + "Tercero" -> 'generar_relacion_saldos'.
   - "Ingresos", "Gastos", "Costos" (SIN 'movimientos' o 'detalle') -> 'generar_estado_resultados'.
   - "Auxiliar", "Movimientos", "Detalle" -> 'generar_reporte_movimientos'.
   - "Balance General" -> 'generar_balance_general'.
   - "Balance de Prueba" -> 'generar_balance_prueba'.

3. FORMATO POR DEFECTO:
   - Si no especifican, usa "formato": "PDF".
   - SOLO usa "PANTALLA" si dicen explícitamente "pantalla".

4. FECHAS (CRÍTICO):
   - Si el usuario NO especifica periodo (ej: "Saldo de caja" o "Ingresos"), usa SIEMPRE desde el inicio de la historia hasta hoy: "fecha_inicio": "2024-01-01", "fecha_fin": "{today}".
   - "año en curso": 2024-01-01 a {today}
   - "periodo en curso": {datetime.now().strftime('%Y-%m')}-01 a {today}
   - "toda la historia" o "desde siempre": 2000-01-01 a {today}

5. ALIAS Y ENTRENAMIENTO:
   - Alias cargados: {json.dumps(rules.get('alias_cuentas', {}))}
   - Instrucciones específicas:
   {chr(10).join([f"* {i}" for i in rules.get('instrucciones_especificas', [])])}

EJEMPLOS:
- "Saldo de cafeteria por Angela" -> {{ "name": "generar_relacion_saldos", "parameters": {{ "cuenta": "Cafeteria", "tercero": "Angela", "fecha_inicio": "2024-01-01", "fecha_fin": "{today}", "formato": "PDF" }} }}
- "Muestrame los ingresos del año" -> {{ "name": "generar_estado_resultados", "parameters": {{ "fecha_inicio": "2024-01-01", "fecha_fin": "{today}", "formato": "PDF" }} }}
"""
    return prompt

async def procesar_comando_natural(texto_usuario: str, contexto: dict | None = None):
    if not api_key:
        return {"error": "API Key de Gemini no configurada."}

    models_to_try = [
        'gemini-2.0-flash',
        'gemini-2.0-flash-lite-001',
        'gemini-1.5-flash',
        'gemini-pro'
    ]

    last_error = None
    for model_name in models_to_try:
        try:
            prompt = get_system_prompt()
            model = genai.GenerativeModel(model_name, system_instruction=prompt)
            
            # Formatear el input para el modelo
            full_input = f"Contexto: {json.dumps(contexto or {})} \nUsuario: {texto_usuario}"
            
            completion = await model.generate_content_async(
                full_input,
                generation_config={"temperature": 0.1}
            )
            
            response_text = completion.text.strip()
            # Limpiar posibles bloques de código markdown
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
                
            return json.loads(response_text)
            
        except Exception as e:
            print(f"Error con modelo {model_name}: {e}")
            last_error = e
            continue

    return {"error": f"Error procesando comando: {str(last_error)}"}
