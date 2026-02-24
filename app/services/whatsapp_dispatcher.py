import os
import json
import logging
from datetime import date
from sqlalchemy.orm import Session
from app.services.ai_agent import client

from app.services import documento as documento_service
from app.services import reports as reports_service
from app.models.plan_cuenta import PlanCuenta
from app.models.tercero import Tercero
from app.schemas import reporte_balance_prueba as schemas_bce

logger = logging.getLogger(__name__)

async def summarize_data_for_whatsapp(raw_data: dict, question: str) -> str:
    if not client:
        return "Los datos en bruto son: " + str(raw_data)[:500]
        
    prompt = f"""
Eres un experto asistente financiero llamado "Finaxis AI" conversando por WhatsApp.
El dueño o contador de la empresa te preguntó o solicitó: "{question}"

El sistema de base de datos extrajo este JSON con la información real:
{json.dumps(raw_data, default=str)}

Tu misión:
- Resume los datos y responde la pregunta de forma natural, clara y muy amigable.
- Formatea para WhatsApp: Usa *negritas* y emojis adecuados (💸, 📊, 📈).
- Muestra el dinero formateado (ej: *$1,500,000*). Asume pesos colombianos.
- Extrae la Utilidad/Pérdida (si viene en el dict), Ingresos, y Gastos principales sin abrumar con toda la lista.
- Si todo está en 0, indícale amablemente que no hay movimientos en ese periodo.
- ¡Sé directo y servicial!
"""
    try:
        completion = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Error AI summary: {e}")
        return "Obtuve los datos, pero falló la generación de lenguaje. Te dejo un adelanto técnico: " + str(raw_data)[:500]

async def dispatch_whatsapp_command(ai_response: dict, text_body: str, empresa_id: int, user_id: int, db: Session) -> str:
    """
    Busca la intención del LLM ('name') y ejecuta la función contable de lectura subyacente.
    Luego manda a ChatGPT a resumir el JSON resultante.
    """
    try:
        if "error" in ai_response:
            return ai_response["error"]
            
        action_name = ai_response.get("name")
        params = ai_response.get("parameters", {})
        
        # Si NO es un comando, es un Toast o Unknown intent
        if not action_name:
            # En la vieja lógica, el agent devolvía "respuesta" o "message"
            return str(ai_response.get("respuesta", ai_response.get("message", ai_response)))

        safe_log = f"WHATSAPP_DISPATCHER: Ejecutando {action_name} con parametros {params}".encode('ascii', 'replace').decode()
        logger.info(safe_log)

        # 1. ESTADO DE RESULTADOS (Ingresos y Gastos)
        if action_name == "generar_estado_resultados":
            f_ini_str = params.get("fecha_inicio", "2020-01-01")
            f_fin_str = params.get("fecha_fin", date.today().isoformat())
            try:
                f_ini = date.fromisoformat(f_ini_str)
                f_fin = date.fromisoformat(f_fin_str)
            except ValueError:
                f_ini = date(2020, 1, 1)
                f_fin = date.today()
                
            data = documento_service.generate_income_statement_report(db, empresa_id, f_ini, f_fin)
            return await summarize_data_for_whatsapp(data, text_body)
            
        # 2. BALANCE GENERAL
        elif action_name == "generar_estado_situacion_financiera":
            f_corte_str = params.get("fecha_corte", date.today().isoformat())
            try:
                f_corte = date.fromisoformat(f_corte_str)
            except ValueError:
                f_corte = date.today()
                
            data = documento_service.generate_balance_sheet_report(db, empresa_id, f_corte)
            return await summarize_data_for_whatsapp(data, text_body)

        # 3. RELACIÓN DE SALDOS (Terceros y Cuentas)
        elif action_name == "generar_relacion_saldos":
            f_ini_str = params.get("fecha_inicio", "2020-01-01")
            f_fin_str = params.get("fecha_fin", date.today().isoformat())
            try:
                f_ini = date.fromisoformat(f_ini_str)
                f_fin = date.fromisoformat(f_fin_str)
            except ValueError:
                f_ini = date(2020, 1, 1)
                f_fin = date.today()

            # Intentar buscar el ID de la cuenta por el nombre/código enviado
            cuenta_param = params.get("cuenta", "")
            cuenta_ids = []
            if cuenta_param:
                db_cuenta = db.query(PlanCuenta).filter(
                    (PlanCuenta.codigo == cuenta_param) | (PlanCuenta.nombre.ilike(f"%{cuenta_param}%")),
                    PlanCuenta.empresa_id == empresa_id
                ).first()
                if db_cuenta:
                    cuenta_ids = [db_cuenta.id]

            # Intentar buscar el ID del tercero si viene
            tercero_param = params.get("tercero", "")
            tercero_ids = []
            if tercero_param:
                db_tercero = db.query(Tercero).filter(
                    (Tercero.nit == tercero_param) | (Tercero.razon_social.ilike(f"%{tercero_param}%")),
                    Tercero.empresa_id == empresa_id
                ).first()
                if db_tercero:
                    tercero_ids = [db_tercero.id]

            filtros_saldos = {
                "fecha_inicio": f_ini,
                "fecha_fin": f_fin,
                "cuenta_ids": cuenta_ids,
                "tercero_ids": tercero_ids
            }
            data = reports_service.generate_relacion_saldos_report(db, empresa_id, filtros_saldos)
            # Acortamos lista si es muy larga para el resumen
            if len(data) > 30:
                data = data[:30]
            return await summarize_data_for_whatsapp(data, text_body)

        # 4. BALANCE DE PRUEBA
        elif action_name == "generar_balance_prueba":
            f_ini_str = params.get("fecha_inicio", date(date.today().year, date.today().month, 1).isoformat())
            f_fin_str = params.get("fecha_fin", date.today().isoformat())
            try:
                f_ini = date.fromisoformat(f_ini_str)
                f_fin = date.fromisoformat(f_fin_str)
            except ValueError:
                f_ini = date(date.today().year, date.today().month, 1)
                f_fin = date.today()

            filtros_bp = schemas_bce.FiltrosBalancePrueba(
                fecha_inicio=f_ini,
                fecha_fin=f_fin,
                nivel_maximo=params.get("nivel", 3), # Nivel 3 para que no sea gigante
                filtro_cuentas="CON_SALDO_O_MOVIMIENTO"
            )
            data_raw = reports_service.generate_balance_de_prueba_report(db, empresa_id, filtros_bp)
            # Transformar Pydantic a dict para el sumariador
            data = {
                "filas": [f.dict() for f in data_raw["filas"][:40]],
                "totales": data_raw["totales"].dict()
            }
            return await summarize_data_for_whatsapp(data, text_body)

        # 5. SALUDOS O COMANDOS NO ENCONTRADOS
        else:
            return f"He comprendido que deseas la función '{action_name}', pero aún no tengo los reportes de ese tipo integrados completamente en WhatsApp. Por favor descárgalos en la interfaz web."
            
    except Exception as e:
        logger.error(f"Error en dispatch_whatsapp_command: {e}", exc_info=True)
        return "❌ Ocurrió un error al buscar los datos en los libros contables. Intenta preguntar de otra manera."
