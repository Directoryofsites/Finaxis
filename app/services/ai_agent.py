import os
import google.generativeai as genai
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

# Definición de herramientas (Tools) disponibles para la IA
TOOLS_SCHEMA = [
    {
        "name": "generar_reporte_movimientos",
        "description": "Genera una consulta de movimientos contables (auxiliar) filtrado por cuenta, tercero o fechas. Úsalo cuando pidan 'auxiliar', 'tercero', 'cuenta específica' o 'auditoría'.",
        "parameters": {
            "type": "object",
            "properties": {
                "tercero": {
                    "type": "string",
                    "description": "Nombre aproximado del tercero (cliente, proveedor) si se menciona."
                },
                "cuenta": {
                    "type": "string",
                    "description": "Nombre o descripción de la cuenta contable (ej: Caja, Bancos, Ingresos)."
                },
                "fecha_inicio": {
                    "type": "string",
                    "format": "date",
                    "description": "Fecha de inicio en formato YYYY-MM-DD. Interpreta 'mes pasado', 'esta semana', 'noviembre 2024', etc."
                },
                "fecha_fin": {
                    "type": "string",
                    "format": "date",
                    "description": "Fecha fin en formato YYYY-MM-DD."
                },
                "formato": {
                    "type": "string",
                    "enum": ["PDF", "EXCEL", "PANTALLA"],
                    "description": "Formato de salida solicitado (opcional)."
                }
            },
            "required": ["fecha_inicio", "fecha_fin"]
        }
    },
    {
        "name": "generar_balance_prueba",
        "description": "Genera el reporte de Balance de Prueba. Muestra saldos iniciales, movimientos y saldos finales.",
        "parameters": {
            "type": "object",
            "properties": {
                "fecha_inicio": { "type": "string", "format": "date" },
                "fecha_fin": { "type": "string", "format": "date" },
                "nivel": { "type": "integer", "description": "Nivel de detalle (1-5). Por defecto 4." }
            },
            "required": ["fecha_inicio", "fecha_fin"]
        }
    },
    {
        "name": "generar_balance_general",
        "description": "Genera el Balance General (Estado de Situación Financiera). Activos, Pasivos y Patrimonio.",
        "parameters": {
            "type": "object",
            "properties": {
                "fecha_corte": { "type": "string", "format": "date", "description": "Fecha de corte del balance (usualmente fin de mes/año). Si piden rango, usa fecha_fin." },
                "comparativo": { "type": "boolean", "description": "Si se solicita comparar con año anterior." }
            },
            "required": ["fecha_corte"]
        }
    },
    {
        "name": "generar_estado_resultados",
        "description": "Genera el Estado de Resultados (P&L / Ganancias y Pérdidas). Ingresos, Costos y Gastos.",
        "parameters": {
            "type": "object",
            "properties": {
                "fecha_inicio": { "type": "string", "format": "date" },
                "fecha_fin": { "type": "string", "format": "date" }
            },
            "required": ["fecha_inicio", "fecha_fin"]
        }
    },
    {
        "name": "crear_recurso",
        "description": "Abre el formulario o modal para CREAR un nuevo registro (Factura, Tercero, Item, etc.).",
        "parameters": {
            "type": "object",
            "properties": {
                "tipo": {
                    "type": "string",
                    "description": "Tipo EXACTO del recurso: factura, compra, tercero, item, traslado, centro_costo, unidad_ph, bodega, receta, nomina, plantilla, empresa.",
                    "enum": [
                        "factura", "compra", "tercero", "item", 
                        "traslado", "centro_costo", "unidad_ph", 
                        "bodega", "receta", "nomina",
                        "plantilla", "empresa", "cuenta", "tipo_documento"
                    ]
                }
            },
            "required": ["tipo"]
        }
    },
    {
        "name": "consultar_documento",
        "description": "Busca documentos o movimientos contables específicos por número, tipo, tercero o fecha (Super Búsqueda Especializada).",
        "parameters": {
            "type": "object",
            "properties": {
                "tipo_documento": { "type": "string", "description": "Tipo de documento (ej: FV, CE, RC, o nombre completo 'Factura de Venta')." },
                "numero_documento": { "type": "string", "description": "Número consecutivo del documento (ej: 1020, 500)." },
                "tercero": { "type": "string", "description": "Nombre o documento del tercero/cliente/proveedor a buscar." },
                "fecha_inicio": { "type": "string", "description": "Fecha inicial (YYYY-MM-DD)." },
                "fecha_fin": { "type": "string", "description": "Fecha final (YYYY-MM-DD)." },
                "concepto": { "type": "string", "description": "Palabra clave en el concepto o descripción." },
                "cuenta": { "type": "string", "description": "Nombre o código de la cuenta contable (ej: Caja, Bancos)." }
            }
        }
    },
    {
        "name": "navegar_a_pagina",
        "description": "Navega o redirige al usuario a una página o módulo específico del sistema.",
        "parameters": {
            "type": "object",
            "properties": {
                "modulo": {
                    "type": "string",
                    "description": "Nombre del módulo (ej: Facturación, Inventario, Nómina)."
                },
                "accion": {
                    "type": "string",
                    "description": "Acción específica (ej: Crear, Listar, Reporte)."
                }
            },
            "required": ["modulo"]
        }
    },
    {
        "name": "generar_backup",
        "description": "Genera inmediatamente una copia de seguridad completa (backup, respaldo) de la base de datos en formato JSON.",
        "parameters": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "extraer_datos_documento",
        "description": "Extrae datos estructurados de lo que dice el usuario para llenar un documento contable (factura, recibo, etc).",
        "parameters": {
            "type": "object",
            "properties": {
                "tipo_documento": { "type": "string", "description": "Tipo de documento detectado (ej: Recibo de Caja, Factura de Venta)." },
                "tercero": { "type": "string", "description": "Nombre del tercero mencionado." },
                "fecha": { "type": "string", "description": "Fecha mencionada." },
                "cuenta": { "type": "string", "description": "Cuenta contable o descripción (ej: Caja General, Bancolombia)." },
                "concepto": { "type": "string", "description": "Descripción del movimiento o concepto general." },
                "debito": { "type": "number", "description": "Valor débito." },
                "credito": { "type": "number", "description": "Valor crédito." },
                "accion": { 
                    "type": "string", 
                    "enum": ["DEFINIR_CABECERA", "AGREGAR_LINEA", "FINALIZAR", "CANCELAR"],
                    "description": "Acción inferida según el contexto."
                }
            }
        }
    }
]

SYSTEM_PROMPT = f"""
Eres Finaxis AI, un asistente contable inteligente. Tu trabajo es interpretar la intención del usuario y mapearla a una función específica del sistema.
Hoy es: {datetime.now().strftime('%Y-%m-%d')}

Reglas:
1. Responde SIEMPRE con un JSON válido.
2. La estructura del JSON debe ser EXACTAMENTE: {{ "name": "nombre_funcion", "parameters": {{ ... }} }}
3. SELECCIÓN DE INFORMES (CRÍTICO):
   - Si piden "Balance General" o "Situación Financiera" -> USA 'generar_balance_general'.
   - Si piden "Balance de Prueba" -> USA 'generar_balance_prueba'.
   - Si piden "Estado de Resultados", "P&G", "Ganancias y Pérdidas" -> USA 'generar_estado_resultados'.
   - SOLO si piden explícitamente "Auxiliar por Terceros", "Módulo de Terceros", o "Reporte tradicional" -> USA 'generar_reporte_movimientos'.

4. PRIORIDAD MÁXIMA - MODO ASISTENTE / DOCUMENTOS:
   - Si el usuario dice "Crear [Tipo Documento]" (ej: "Crear Recibo", "Nueva Factura", "Hacer un comprobante") -> USA 'extraer_datos_documento' con accion='DEFINIR_CABECERA'.
   - Si el usuario está dando datos para un documento (valores, terceros, fechas) -> USA 'extraer_datos_documento'.
   - Si dice "Guardar", "Grabar", "Terminar" -> accion: "FINALIZAR".

5. NAVEGACIÓN Y APERTURA DE FORMULARIOS (Menor Prioridad):
   - Solo si piden explícitamente "Ir a crear...", "Abrir formulario de...", "Navegar a..." -> USA 'crear_recurso' o 'navegar_a_pagina'.
   - Si piden "Cliente", "Proveedor" (sin contexto de documento) -> USA 'crear_recurso' (tipo='tercero').
   - Otros recursos: item, compra, traslado, plantilla, empresa.

6. CONSULTAS, BÚSQUEDAS Y MOVIMIENTOS:
   - REPORTE TRADICIONAL: Si piden "Libro Auxiliar", "Auxiliar Contable", "Auxiliar por Cuenta" o "Reporte tradicional" -> USA 'generar_reporte_movimientos'.
   - SUPER INFORME (Default): Si piden "Ver movimientos", "Informe de [Tercero]", "Buscar facturas de..." -> USA 'consultar_documento'.
   - Si piden "Auxiliar" a secas -> PREFIERE 'consultar_documento' (Super Informe) salvo que digan "Auxiliar Contable".
   - Si hay AMBIGÜEDAD, PREFIERE 'consultar_documento'.
6. COPIAS DE SEGURIDAD:
   - Si piden "backup", "respaldo", "copia de seguridad", "guardar todo" -> USA 'generar_backup'.
7. Si no entiendes, devuelve un JSON con error: {{ "error": "No entendí la solicitud" }}.
"""

async def procesar_comando_natural(texto_usuario: str, contexto: dict = None):
    if not api_key:
        return {"error": "API Key no configurada"}

    # Lista de modelos a probar en orden de preferencia/costo/disponibilidad
    # Priorizamos versiones "Lite" y "Latest" que están disponibles para tu API Key
    # Lista ampliada con modelos disponibles detectados
    # para encontrar uno con cuota disponible (evitar el alias 'latest' que apunta a 2.5)
    models_to_try = [
        'gemini-2.0-flash',           # Tier Free Generoso
        'gemini-2.0-flash-lite-001',  # Alternativa ligera
        'gemini-1.5-flash',           # Fallback estable anterior
        'gemini-2.5-flash',           # Nueva versión flash (si la anterior falla)
        'gemini-2.0-flash-001'
    ]

    last_error = None

    for model_name in models_to_try:
        try:
            print(f"Probando modelo AI: {model_name}...")
            model = genai.GenerativeModel(model_name)
            
            # Construimos el prompt final con la instrucción y las herramientas
            ctx_str = f"\nCONTEXTO ACTUAL (FORM STATE): {json.dumps(contexto, ensure_ascii=False)}" if contexto else ""
            full_prompt = f"{SYSTEM_PROMPT}\n{ctx_str}\nUsuario dice: '{texto_usuario}'\n\nResponde SOLO con el JSON de la tool call."
            
            completion = model.generate_content(
                full_prompt,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json"
                )
            )
            
            # --- CÁLCULO DE COSTO ESTIMADO ---
            try:
                # Intentamos obtener metadatos de uso reales
                usage = completion.usage_metadata
                in_tokens = usage.prompt_token_count
                out_tokens = usage.candidates_token_count
                
                # Precios Gemini 1.5 Flash (Aprox.): $0.075 / 1M Input, $0.30 / 1M Output
                cost_in = (in_tokens / 1_000_000) * 0.075
                cost_out = (out_tokens / 1_000_000) * 0.30
                total_cost = cost_in + cost_out
                
                print(f"💰 COSTO ESTIMADO: ${total_cost:.7f} USD (In: {in_tokens}, Out: {out_tokens})")
                print(f"   --> {1/total_cost if total_cost > 0 else 0:.0f} peticiones por $1 USD")
            except Exception as e_cost:
                print(f"⚠️ No se pudo calcular costo exacto: {e_cost}")
            # ---------------------------------

            response_text = completion.text
            return json.loads(response_text)

        except Exception as e:
            print(f"Fallo modelo {model_name}: {str(e)}")
            last_error = e
            continue
    
    # Si todos fallan, intentamos listar los disponibles para debug
    try:
        available_models = [m.name for m in genai.list_models()]
        print(f"Modelos disponibles encontrados: {available_models}")
    except:
        available_models = "No se pudo listar"

    return {"error": f"Fallo en todos los modelos ({models_to_try}). Error: {str(last_error)}. Disponibles: {available_models}"}
