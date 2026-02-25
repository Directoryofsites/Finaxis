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
from app.services.ai_context_helper import apply_default_ai_context

logger = logging.getLogger(__name__)

async def summarize_data_for_whatsapp(raw_data: dict, question: str) -> str:
    if not client:
        return "Los datos en bruto son: " + str(raw_data)[:500]
        
    prompt = f"""
Eres un experto asistente financiero llamado "Finaxis AI" conversando por WhatsApp.
El dueño o contador de la empresa te preguntó o solicitó: "{question}"

En base a la información extraída de su base de datos, aquí están los SUMATORIAS / TOTALES DEL REPORTE SOLICITADO:
{json.dumps(raw_data, default=str)}

Tu misión:
- Resume los totales principales y responde la pregunta de forma natural, clara y muy amigable.
- NUNCA listes transacciones fila por fila. Menciona los saldos globales y cifras macro.
- Formatea para WhatsApp: Usa *negritas* y emojis adecuados (💸, 📊, 📈).
- Muestra el dinero formateado (ej: *$1,500,000*). Asume pesos colombianos.
- Dile al usuario que si desea ver el detalle transacción por transacción, debe generar el reporte en la plataforma (o a través del documento adjunto).
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
        return "Obtuve los datos, pero falló la generación de lenguaje. Te dejo el resumen técnico: " + str(raw_data)[:500]

async def dispatch_whatsapp_command(ai_response: dict, text_body: str, empresa_id: int, user_id: int, db: Session) -> str:
    """
    Busca la intención del LLM ('name') y ejecuta la función contable de lectura subyacente.
    Luego manda a ChatGPT a resumir el JSON resultante (ahora con soporte de Totales reales sin truncar info).
    """
    try:
        if "error" in ai_response:
            return ai_response["error"]
            
        action_name = ai_response.get("name")
        params = ai_response.get("parameters", {})
        
        if not action_name:
            return str(ai_response.get("respuesta", ai_response.get("message", ai_response)))

        # -------------------------------------------------------------------
        # NUEVO PARADIGMA: Inyectar Contexto y "Defaults inteligentes" al Dict
        # -------------------------------------------------------------------
        params = apply_default_ai_context(params, empresa_id, db)

        safe_log = f"WHATSAPP_DISPATCHER: Ejecutando {action_name} con parametros sanitizados {params}".encode('ascii', 'replace').decode()
        logger.info(safe_log)

        # 1. ESTADO DE RESULTADOS (Ingresos y Gastos)
        if action_name == "generar_estado_resultados":
            f_ini_str = params.get("fecha_inicio")
            f_fin_str = params.get("fecha_fin")
            try:
                f_ini = date.fromisoformat(f_ini_str)
                f_fin = date.fromisoformat(f_fin_str)
            except ValueError:
                f_ini = date(2020, 1, 1)
                f_fin = date.today()
                
            data = documento_service.generate_income_statement_report(db, empresa_id, f_ini, f_fin)
            # Para WhatsApp AI, solo enviamos los grupos de totales
            summary_data = {
                "Ingresos_Totales": data.get("ingresos", {}).get("total_ingresos", 0),
                "Costos_Totales": data.get("costos", {}).get("total_costos", 0),
                "Utilidad_Bruta": data.get("utilidad_bruta", 0),
                "Gastos_Totales": data.get("gastos", {}).get("total_gastos", 0),
                "Utilidad_Neta": data.get("utilidad_neta", 0)
            }
            return await summarize_data_for_whatsapp(summary_data, text_body)
            
        # 2. BALANCE GENERAL
        elif action_name == "generar_estado_situacion_financiera":
            f_corte_str = params.get("fecha_corte")
            try:
                f_corte = date.fromisoformat(f_corte_str)
            except ValueError:
                f_corte = date.today()
                
            data = documento_service.generate_balance_sheet_report(db, empresa_id, f_corte)
            summary_data = {
                "Total_Activo": data.get("total_activo", 0),
                "Total_Pasivo": data.get("total_pasivo", 0),
                "Total_Patrimonio": data.get("total_patrimonio", 0),
                "Ecuacion_Contable": "balancea" if data.get("total_activo", 0) == (data.get("total_pasivo", 0) + data.get("total_patrimonio", 0)) else "descuadre detectado"
            }
            return await summarize_data_for_whatsapp(summary_data, text_body)

        # 3. RELACIÓN DE SALDOS (Terceros y Cuentas)
        elif action_name == "generar_relacion_saldos":
            f_ini_str = params.get("fecha_inicio")
            f_fin_str = params.get("fecha_fin")
            try:
                f_ini = date.fromisoformat(f_ini_str)
                f_fin = date.fromisoformat(f_fin_str)
            except ValueError:
                f_ini = date(2020, 1, 1)
                f_fin = date.today()

            cuenta_param = params.get("cuenta", "")
            cuenta_ids = []
            if cuenta_param:
                db_cuenta = db.query(PlanCuenta).filter(
                    (PlanCuenta.codigo == cuenta_param) | (PlanCuenta.nombre.ilike(f"%{cuenta_param}%")),
                    PlanCuenta.empresa_id == empresa_id
                ).first()
                if db_cuenta:
                    cuenta_ids = [db_cuenta.id]

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
            data_list = reports_service.generate_relacion_saldos_report(db, empresa_id, filtros_saldos)
            
            # NUEVO: En vez de truncar las primeras 30, calculamos el total consolidado 
            total_saldo_filtrado = sum([float(item.get("saldo_final", 0)) for item in data_list])
            top_3 = data_list[:3] # Muestra solo el top 3 de los responsables como máximo detalle
            
            summary_data = {
                "Saldo_Total_Encontrado": total_saldo_filtrado,
                "Filas_Involucradas": len(data_list),
                "Mayores_involucrados_Muestra": top_3
            }
            return await summarize_data_for_whatsapp(summary_data, text_body)

        # 4. BALANCE DE PRUEBA
        elif action_name == "generar_balance_prueba":
            f_ini_str = params.get("fecha_inicio")
            f_fin_str = params.get("fecha_fin")
            try:
                f_ini = date.fromisoformat(f_ini_str)
                f_fin = date.fromisoformat(f_fin_str)
            except ValueError:
                f_ini = date(date.today().year, date.today().month, 1)
                f_fin = date.today()

            filtros_bp = schemas_bce.FiltrosBalancePrueba(
                fecha_inicio=f_ini,
                fecha_fin=f_fin,
                nivel_maximo=params.get("nivel", 3),
                filtro_cuentas="CON_SALDO_O_MOVIMIENTO"
            )
            data_raw = reports_service.generate_balance_de_prueba_report(db, empresa_id, filtros_bp)
            
            # Extraer solo el consolidado
            summary_data = {
                "resumen_totales": data_raw["totales"].dict() if data_raw.get("totales") else {},
                "aviso": "Reporte extenso. Estos son los resultados consolidados globales."
            }
            return await summarize_data_for_whatsapp(summary_data, text_body)

        # 5. SALUDOS O COMANDOS NO ENCONTRADOS
        else:
            return f"He comprendido que buscas la función '{action_name}', pero te recomiendo generar este reporte directamente en la plataforma web para un máximo nivel de detalle."
            
    except Exception as e:
        logger.error(f"Error en dispatch_whatsapp_command: {e}", exc_info=True)
        return "❌ Ocurrió un error al consultar tus datos en los libros contables. Asegúrate de pedir un reporte o saldo válido."

