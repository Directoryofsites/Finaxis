from typing import Dict, Any
import datetime
import asyncio
from app.services.dataico_dispatcher import DataicoDispatcher
import logging

logger = logging.getLogger(__name__)

class DataicoProvider:
    """
    Adaptador para convertir el payload estándar (basado en Factus originalmente)
    al formato requerido por DATAICO y emitirlo.
    """
    def __init__(self, config: Dict):
        # La configuración viene de ConfiguracionFE (api_token json: {client_id, client_secret})
        # Dataico usa Dataico_account_id y Auth-token en su lugar.
        # Por convencion interna en ContaPY2, "client_id" sera "Account ID" y "client_secret" el "Auth token" 
        # en la conf de la empresa, ya que es la misma caja de texto del UI.
        self.account_id = config.get("client_id")
        self.auth_token = config.get("client_secret")
        self.env = config.get("environment", "PRUEBAS")
        self.dispatcher = DataicoDispatcher(self.account_id, self.auth_token)

    def emit(self, standard_payload: Dict) -> Dict[str, Any]:
        """
        Ejecuta la emisión principal usando asyncio para acoplar el código asíncrono
        del dispatcher a la sincronía actual de factura_electronica_service.
        """
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        return loop.run_until_complete(self._emit_async(standard_payload))

    async def _emit_async(self, payload: Dict) -> Dict[str, Any]:
        """
        Transcribe el payload y llama al dispatcher.
        Se apoya en 'bill_type' interno: Standard, SupportDocument, CreditNote, DebitNote.
        """
        bill_type = payload.get("bill_type", "Standard")
        
        # Mapeo universal de Invoice (Factura)
        dataico_invoice = self._map_to_dataico_invoice(payload, bill_type)
        
        # Opciones comunes (Enviar a DIAN y Cliente)
        actions = {
            "send_dian": True,
            "send_email": True
        }
        
        if bill_type == "SupportDocument":
            # Para Documento Soporte, Dataico espera "support_doc" en la raíz
            dataico_invoice["dataico_account_id"] = self.account_id
            final_payload = {
                "actions": actions,
                "support_doc": dataico_invoice
            }
            response = await self.dispatcher.create_support_document(final_payload)
        elif bill_type == "CreditNote":
            # Nota Crédito (CreditNote)
            note_payload = self._map_to_dataico_note(payload, dataico_invoice)
            note_payload["dataico_account_id"] = self.account_id
            final_payload = {
                "actions": actions,
                "credit_note": note_payload
            }
            response = await self.dispatcher._request("POST", "/credit_notes", data=final_payload)
        elif bill_type == "DebitNote":
            # Nota Débito (DebitNote)
            note_payload = self._map_to_dataico_note(payload, dataico_invoice)
            note_payload["dataico_account_id"] = self.account_id
            final_payload = {
                "actions": actions,
                "debit_note": note_payload
            }
            response = await self.dispatcher._request("POST", "/debit_notes", data=final_payload)
        else:
            # Factura FE
            dataico_invoice["dataico_account_id"] = self.account_id
            final_payload = {
                "actions": actions,
                "invoice": dataico_invoice
            }
            print(f"[DATAICO] Calling DISPATCHER for {bill_type}")
            response = await self.dispatcher.create_invoice(final_payload)
            
        print(f"[DATAICO] Response Summary: Success={response.get('success')}")
        return self._format_response(response, bill_type)

    def _map_to_dataico_invoice(self, data: Dict, bill_type: str = "Standard") -> Dict[str, Any]:
        """Mapea la estructura plana a la anidada de Dataico"""
        # Equivalencias de tipos de documento Dataico
        type_mapping = {
            "Standard": "FACTURA_VENTA",
            "SupportDocument": "DOCUMENTO_SOPORTE",
            "CreditNote": "NOTA_CREDITO",
            "DebitNote": "NOTA_DEBITO"
        }
        dataico_type = type_mapping.get(bill_type, "FACTURA_VENTA")
        # Extraemos customer o provider dependendiendo si es DS o Factura
        contact = data.get("customer") or data.get("provider") or {}
        
        # Extraer el número y prefijo de la referencia (Ej: "SETT-123" -> 123, SETT)
        reference = str(data.get("reference_code", "0"))
        doc_number = 0
        doc_prefix = data.get("prefix") # Prioridad al prefijo explicito si viene en el payload
        
        if "-" in reference:
            parts = reference.split("-")
            try:
                doc_number = int(parts[-1])
                if not doc_prefix:
                    doc_prefix = "-".join(parts[:-1])
            except:
                pass
        else:
            try:
                doc_number = int(reference)
            except:
                pass

        # Formatear fechas a DD/MM/YYYY
        issue_date_raw = data.get("date_issue") or datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            # Intentar parsear ISO para convertir a DD/MM/YYYY
            dt_obj = datetime.datetime.fromisoformat(issue_date_raw.replace("Z", ""))
            issue_date = dt_obj.strftime("%d/%m/%Y")
        except:
            issue_date = issue_date_raw # fallback si ya venia formateada o error
            
        payment_date_raw = data.get("payment_date") or data.get("date_issue") or ""
        payment_date = ""
        if payment_date_raw:
            try:
                dt_p = datetime.datetime.fromisoformat(payment_date_raw.split("T")[0])
                payment_date = dt_p.strftime("%d/%m/%Y")
            except:
                payment_date = payment_date_raw

        mapped = {
            "env": self.env, # PRUEBAS o PRODUCCION
            "dataico_account_id": self.account_id,
            "invoice_type_code": dataico_type,
            "number": str(data.get("number", doc_number)),
            "issue_date": issue_date,
            "payment_means_type": "DEBITO" if str(data.get("payment_method_code", "10")) == "10" else "CREDITO",
            "payment_date": payment_date,
            "payment_means": "CASH" if str(data.get("payment_method_code", "10")) == "10" else "CREDIT_TRANSFER",
            "currency_code": "COP",
            "numbering": {
                "prefix": doc_prefix,
                "flexible": True
            },
            "notes": [data.get("observation", "")],
            "customer": self._map_customer(contact)
        }
        
        # Solo incluir el número de resolución si no está vacío (previene error en ND/NC/DS que solo usan prefijo)
        resol_num = str(data.get("resolution_number") or "").strip()
        if resol_num:
            mapped["numbering"]["resolution_number"] = resol_num

        
        # Items
        items = []
        for item in data.get("items", []):
            tax_rate = float(item.get("tax_rate", 0))
            
            # Dataico crashea fuerte (Unable to find data source $__in__4) si el SKU es un string vacio ""
            sku_val = str(item.get("sku", item.get("id_producto", ""))).strip()
            if not sku_val:
                sku_val = "000"
                
            item_obj = {
                "sku": sku_val,
                "description": str(item.get("name", "")),
                "price": float(item.get("price", 0)),
                "quantity": float(item.get("quantity", 1)),
                "taxes": [
                    {
                        "tax_category": "IVA",
                        "tax_rate": tax_rate
                    }
                ] if tax_rate > 0 else []
            }
            
            # Dataico estalla con None para el descuento o falla ocasionalmente si se envia 0 de forma estricta. Lo removemos si no hay.
            discount_rate = float(item.get("discount_rate", 0)) if item.get("discount_rate") is not None else 0
            if discount_rate > 0:
                item_obj["discount_rate"] = discount_rate
                
            items.append(item_obj)
            
        mapped["items"] = items
        return mapped

    def _map_to_dataico_note(self, data: Dict, base_invoice: Dict) -> Dict[str, Any]:
        """Adiciones especiales para notas"""
        base_invoice["type_document_id"] = 1 # Según equivalencias Dataico
        
        # Formatear fecha a DD/MM/YYYY HH:mm:ss usando la hora exacta final del día actual (23:59:59)
        # Esto previene el error "La fecha no puede ser anterior a la de la factura" causado
        # por desfases de TimeZone (Dataico almacena la fra original en UTC +5H, haciendola ver 
        # falsamente posterior a la hora local actual en Colombia).
        issue_date = datetime.datetime.now().strftime("%d/%m/%Y") + " 23:59:59"
        base_invoice["issue_date"] = issue_date
        
        # Identificar la factura a la cual hace referencia
        # Dataico V2 requiere explícitamente el 'invoice_id' en la raíz (UUID o bill_id)
        base_invoice["invoice_id"] = str(data.get("bill_id", data.get("billing_reference", {}).get("uuid", "")))
        
        base_invoice["invoice_reference"] = {
            "uid": data.get("billing_reference", {}).get("uuid", ""),
            "issue_date": data.get("billing_reference", {}).get("issue_date", "")
        }
        # Agregar razón de la nota (Dataico V2 usa 'reason' como string)
        discrepancy = data.get("discrepancy_response", {})
        base_invoice["reason"] = str(discrepancy.get("correction_concept_id", "1"))
        
        # LIMPIEZA ADICIONAL PARA NO ENVIAR RESOLUCION EN LAS NOTAS (DATAICO 401 FIX)
        if "numbering" in base_invoice and "resolution_number" in base_invoice["numbering"]:
            del base_invoice["numbering"]["resolution_number"]
            
        return base_invoice

    def _map_customer(self, contact: Dict) -> Dict[str, Any]:
        """Traducción de cliente Third Party al modelo Dataico"""
        doc_type_mapping = {
            "1": "CC", "2": "CE", "3": "NIT", "4": "TI", 
            "5": "PA", "6": "NIT" # Default Factus a Dataico
        }
        party_id_type = doc_type_mapping.get(str(contact.get("identification_document_id", "3")), "NIT")
        # party_type: 1=Juridica, 2=Natural (según Factus/ContaPY2)
        legal_org = str(contact.get("legal_organization_id", "2"))
        party_type = "PERSONA_JURIDICA" if legal_org == "1" else "PERSONA_NATURAL"

        # DIVISION DE NOMBRES ESTRICTA DATAICO V2 (Para Persona Natural)
        raw_name = str(contact.get("names", "")).strip()
        first_name = raw_name
        family_name = ""
        
        if party_type == "PERSONA_NATURAL":
            name_parts = raw_name.split(" ", 1)
            if len(name_parts) > 1:
                first_name = name_parts[0]
                family_name = name_parts[1]
            else:
                first_name = raw_name
                family_name = "-" # Failsafe DIAN para apellidos obligatorios faltantes
        else:
             first_name = "" # En juridica no van los nombres personales, solo razon social

        # Mapear ciudad vs departamento según las estrictas reglas de Dataico V2
        mapped_city = "BOGOTA, D.C." if str(contact.get("city_code")) == "11001" else str(contact.get("city_name", contact.get("address", "")))
        mapped_dept = "BOGOTA" if str(contact.get("city_code")) == "11001" else "CUNDINAMARCA" # TODO: Mapping por dptos
        
        return {
            "party_type": party_type,
            "party_identification_type": party_id_type,
            "party_identification": str(contact.get("identification", "")), # V2 Dataico expected property
            "check_digit": str(contact.get("dv", "")),
            "first_name": first_name,
            "family_name": family_name, 
            "company_name": str(contact.get("company", "") or raw_name),
            "email": str(contact.get("email", "")),
            "phone": str(contact.get("phone", "")),
            "address": {
                "address_line": str(contact.get("address", "")),
                "city": mapped_city, 
                "department": mapped_dept, 
                "country": "CO"
            }
        }

    def _format_response(self, response: Dict, doc_type: str) -> Dict[str, Any]:
        """Da formato a la respuesta para que empate con lo que espera ContaPY2"""
        if not response.get("success"):
            details = response.get("detail", {})
            error_msg = details.get("message")
            
            # Si no hay message, buscar en el array de 'errors' que a veces manda Dataico
            if not error_msg and "errors" in details and isinstance(details["errors"], list):
                error_list = []
                for e in details["errors"]:
                    if isinstance(e, dict):
                        # Evitar NoneType concatenando de forma segura
                        e_str = str(e.get("error") or "")
                        p_str = ".".join([str(p) for p in e.get("path", [])]) if e.get("path") else ""
                        error_list.append(f"[{p_str}] {e_str}")
                    else:
                        error_list.append(str(e))
                error_msg = " | ".join(error_list)
            
            # Nuevo: Si el error es una respuesta de texto cruda (no JSON)
            if not error_msg and "raw_text" in details:
                error_msg = f"Respuesta Base: {details['raw_text'][:200]}"
            
            error_msg = error_msg or "Error desconocido en Dataico"
            
            print(f"[DATAICO] Formatting Error Response: {error_msg}")
            return {
                "success": False,
                "error": f"ERROR DATAICO: {error_msg}",
                "details": details
            }
            
        data = response.get("data", {})
        # Dataico suele devolver el UUID de DIAN en cufe, uuid, o qr
        cufe = data.get("cufe") or data.get("uuid") or data.get("dian_uuid") or "NoCUFE-Emitido"
        
        return {
            "success": True,
            "cufe": cufe,
            "xml_url": "DIAN", # Dataico guarda el XML y se puede descargar luego mediante GET invoice
            "public_url": f"https://api.dataico.com/direct/dataico_api/v2/invoices/{cufe}/pdf", # Placeholder URL
            "dian_status": "ACEPTADO",
            "provider_id": data.get("uuid", data.get("number")),
            "provider_response": data
        }
