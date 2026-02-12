import os
import google.generativeai as genai
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY", "").strip()
if api_key:
    # Debug: Mostrar parte de la llave para verificar que es la NUEVA (Finaxis 2)
    masked_key = f"{api_key[:10]}...{api_key[-4:]}" if len(api_key) > 15 else "INVALID"
    print(f"AI_DEBUG: Usando API Key: {masked_key}")
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
def get_system_prompt():
    rules = load_training_rules()
    today = datetime.now().strftime("%Y-%m-%d")
    
    prompt = f"""
ERES UN ASISTENTE CONTABLE EXPERTO EN EL SISTEMA "FINAXIS".
TU OBJETIVO ES INTERPRETAR LAS INTENCIONES DEL USUARIO Y MAPEARLAS A FUNCIONES DEL SISTEMA.

FECHA ACTUAL: {today}

1. REGLAS GENERALES:
   - NO inventes información.
   - Si falta información crítica, pide confirmación (pero intenta inferir lo obvio).
   - Responde SIEMPRE en formato JSON estricto.

2. FORMATO DE RESPUESTA (JSON):
   {{
     "name": "nombre_de_la_funcion",
     "parameters": {{
       "param1": "valor1",
       "param2": "valor2"
     }}
   }}

3. FUNCIONES DISPONIBLES:
   - generar_auxiliar_cuenta(cuenta: str, fecha_inicio: str, fecha_fin: str, formato: str)
     * "Quiero un auxiliar de la 1105"
     * "Dame el auxiliar de caja de enero"
   
   - generar_balance_prueba(nivel: int, fecha_inicio: str, fecha_fin: str, formato: str)
     * "Genera un balance de prueba"
   
   - generar_estado_situacion_financiera(fecha_inicio: str, fecha_fin: str, formato: str)
     * "Necesito un balance general"
     * "Estado de situación financiera"
     
   - generar_estado_resultados(fecha_inicio: str, fecha_fin: str, formato: str)
     * "PyG de este mes"
     * "Estado de resultados"
     
   - generar_certificado_retencion(tercero: str, fecha_inicio: str, fecha_fin: str, formato: str)
     * "Certificado de retención para Pedro Pérez"
     
   - generar_relacion_saldos(cuenta: str, tercero: str, fecha_inicio: str, fecha_fin: str, formato: str)
     * "Relación de saldos de proveedores"
     * "Saldo de la 1305"
     
   - generar_estado_cuenta_proveedor(tercero: str, fecha_corte: str, formato: str)
     * "Estado de cuenta de Juanito"

4. EXTTRACCIÓN DE ENTIDADES:
   - Fechas: Si no se especifica, asume el mes actual o el año actual según contexto.
   - Formatos: Por defecto "PDF" si no dice "Excel".
   - Cuentas: Intenta identificar el código o nombre (e.g., "Caja" -> "1105").

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
    if not client:
        return {"error": "API Key de OpenAI no configurada."}

    model_name = "gpt-4o-mini"
    
    try:
        print(f"AI_DEBUG: Intentando usar modelo: {model_name}")
        prompt = get_system_prompt()
        
        # Formatear el input para el modelo
        full_input = f"Contexto: {json.dumps(contexto or {})} \nUsuario: {texto_usuario}"
        
        completion = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": full_input}
            ],
            temperature=0.1
        )
        
        response_text = completion.choices[0].message.content.strip()
        
        # Limpiar posibles bloques de código markdown
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        print(f"AI_DEBUG: Éxito con modelo {model_name}")
        return json.loads(response_text)
        
    except Exception as e:
        print(f"AI_DEBUG: Falló modelo {model_name}. Error: {e}")
        return {"error": f"Error procesando comando: {str(e)}"}
