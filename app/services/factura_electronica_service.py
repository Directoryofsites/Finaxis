
from sqlalchemy.orm import Session
from app.models.empresa import Empresa
from app.models.tercero import Tercero
from app.models.configuracion_fe import ConfiguracionFE

from datetime import datetime, date
import uuid
import json

class MockElectronicInvoiceProvider:
    """
    Simulador de Proveedor Tecnológico (Dataico/Factus).
    Permite desarrollar el flujo completo sin credenciales reales.
    """
    def emit(self, invoice_payload: dict):
        # Simular latencia de red
        import time
        time.sleep(1.5)
        
        # Generar CUFE falso
        fake_cufe = f"mock_{uuid.uuid4().hex}"
        
        return {
            "success": True,
            "message": "Factura emitida exitosamente en MOCK DIAN",
            "cufe": fake_cufe,
            "xml_url": "http://localhost:8000/mock/xml",
            "pdf_url": "http://localhost:8000/mock/pdf",
            "status": "ENVIADO",
            "dian_status": "ACEPTADO",
            "timestamp": datetime.now().isoformat()
        }

class FacturaElectronicaService:
    def __init__(self):
        self.provider = MockElectronicInvoiceProvider() # En futuro, leer de config para switch

    def calcular_dv(self, nit: str) -> str:
        """Calcula el Dígito de Verificación (DV) para un NIT"""
        if not nit or not nit.isdigit():
            return "0"
            
        nit_list = [int(d) for d in str(nit)]
        nit_list.reverse()
        primes = [3, 7, 13, 17, 19, 23, 29, 37, 41, 43, 47, 53, 59, 67, 71]
        
        suma = 0
        for i, digit in enumerate(nit_list):
            if i < len(primes):
                suma += digit * primes[i]
                
        mod = suma % 11
        if mod == 0 or mod == 1:
            return str(mod)
        else:
            return str(11 - mod)

    def validar_datos_emisor(self, db: Session, empresa_id: int):
        """
        Verifica que la empresa tenga los datos obligatorios para FE.
        Retorna: (bool, list[str]) -> (EsValido, ListaDeErrores)
        """
        empresa = db.query(Empresa).get(empresa_id)
        errores = []
        
        if not empresa.nit: errores.append("Falta NIT")
        if not empresa.dv: errores.append("Falta Dígito Verificación (DV)")
        if not empresa.direccion: errores.append("Falta Dirección")
        if not empresa.telefono: errores.append("Falta Teléfono")
        if not empresa.email: errores.append("Falta Email")
        if not empresa.municipio_dane: errores.append("Falta Código Municipio DANE")
        if not empresa.regimen_fiscal: errores.append("Falta Régimen Fiscal")
        
        return (len(errores) == 0), errores

    def validar_datos_receptor(self, db: Session, tercero_id: int):
        """
        Verifica que el cliente (tercero) tenga los datos obligatorios para FE.
        """
        tercero = db.query(Tercero).get(tercero_id)
        errores = []
        
        if not tercero.nit: errores.append("Falta Identificación (NIT/CC)")
        # DV es opcional en algunos casos (PN), pero obligatorio para PJ.
        # if not tercero.dv: errores.append("Falta DV") 
        if not tercero.direccion: errores.append("Falta Dirección")
        if not tercero.email: errores.append("Falta Email (Obligatorio para entrega XML)")
        if not tercero.municipio_dane: errores.append("Falta Código Municipio DANE")
        if not tercero.regimen_fiscal: errores.append("Falta Régimen Fiscal")
        
        return (len(errores) == 0), errores

    def verificar_habilitacion(self, db: Session, empresa_id: int):
        """Revisa si la empresa está configurada y habilitada para facturar"""
        config = db.query(ConfiguracionFE).filter_by(empresa_id=empresa_id).first()
        # En MOCK mode podemos ser más laxos, pero simulemos validación real
        if not config:
            return False, "Empresa no tiene configuración de Facturación Electrónica"
        
        # Para MOCK, asumimos habilitado si existe el registro, aunque sea fake
        # if not config.habilitado:
        #    return False, "Facturación Electrónica inhabilitada o en proceso de pruebas"
            
        return True, "Habilitado"

    def emitir_factura(self, db: Session, documento_id: int, usuario_id: int):
        from app.models.documento import Documento
        from app.services.providers.factus_provider import FactusProvider
        
        doc = db.query(Documento).get(documento_id)
        if not doc:
            return {"success": False, "error": "Documento no encontrado"}
            
        # 0. Identificar Tipo de Documento
        # is_ds = doc.tipo_documento.funcion_especial == 'documento_soporte'
        # Ahora detectamos también Notas
        # Usamos codigos DIAN estándar o flags en TipoDocumento
        # Por ahora, inferimos del nombre o código si no hay flag específico en BD
        # Ajustar según tu tabla `tipos_documento`:
        # 91 = Nota Crédito, 92 = Nota Débito
        
        doc_code = doc.tipo_documento.codigo or ""
        is_nc = doc_code == '91' or 'NOTA CREDITO' in doc.tipo_documento.nombre.upper()
        is_nd = doc_code == '92' or 'NOTA DEBITO' in doc.tipo_documento.nombre.upper()
        is_ds = doc.tipo_documento.funcion_especial == 'documento_soporte'

        # 1. Obterner Configuración
        config = db.query(ConfiguracionFE).filter_by(empresa_id=doc.empresa_id).first()
        if not config:
             return {"success": False, "error": "La empresa no tiene configuración de Facturación Electrónica."}
             
        if not config.habilitado:
             return {"success": False, "error": "Facturación Electrónica inhabilitada para esta empresa."}
        
        # Seleccionar Rango según tipo
        range_id = None
        doc_type_name = "Documento"
        if is_ds:
            range_id = config.ds_rango_id
            doc_type_name = "Documento Soporte"
        elif is_nc:
            range_id = config.nc_rango_id
            doc_type_name = "Nota Crédito"
        elif is_nd:
            range_id = config.nd_rango_id or config.nc_rango_id
            doc_type_name = "Nota Débito"
        else:
            # Factura Venta
            # Si no hay campo explicit, usar 8 (Sandbox por defecto) o derivar
            # TODO: Agregar campo factura_rango_id a ConfiguracionFE -> DONE
            range_id = config.factura_rango_id
            if not range_id and config.ambiente == 'PRUEBAS':
                 range_id = 8 # Hardcoded for Sandbox fallback
            
            doc_type_name = "Factura de Venta"
            
        if not range_id:
            return {"success": False, "error": f"No se ha configurado el ID de Rango para {doc_type_name}."}

        # VALIDACIÓN PADRE PARA NOTAS
        parent_doc = None
        if is_nc or is_nd:
            if not doc.documento_referencia_id:
                return {"success": False, "error": "Las Notas deben tener un documento referencia (Factura de Venta) asociado."}
            
            parent_doc = doc.documento_referencia
            if not parent_doc:
                 return {"success": False, "error": "El documento referencia no existe."}
            
            if not parent_doc.dian_cufe:
                 return {"success": False, "error": "El documento referencia no tiene CUFE (No ha sido enviado a la DIAN)."}

        # 2. Obtener Credenciales desde DB
        if not config.api_token:
            return {"success": False, "error": "Credenciales API no configuradas"}
        
        try:
            creds = json.loads(config.api_token)
        except json.JSONDecodeError:
            return {"success": False, "error": "Formato de credenciales inválido en DB"}
        
        try:
            # 3. Inicializar Provider
            provider_config = {
                "environment": config.ambiente, 
                "client_id": creds.get("client_id"),
                "client_secret": creds.get("client_secret"),
                "username": creds.get("username"),
                "password": creds.get("password")
            }
            provider = FactusProvider(provider_config)
            
            # 4. Construir Items con Limpieza de Cargos Globales
            
            cargos_globales = float(doc.cargos_globales_valor or 0.0)
            target_total_discount = float(doc.descuento_global_valor or 0.0)
            
            total_items_net = 0.0
            sum_line_discounts = 0.0
            
            valid_movs = []
            for mov in doc.movimientos:
                # Lógica de selección de movimientos
                # Para notas, usualmente se replican los movimientos de la factura original pero con valores ajustados
                # O se registran movimientos de devolución (Credito vs Debito invertido)
                # AQUÍ ASUMIMOS QUE EL DOCUMENTO NOTA EN LA BD TIENE SUS PROPIOS MOVIMIENTOS REFLEJANDO LA DEVOLUCIÓN
                
                is_valid = False
                if is_ds:
                     if mov.debito and mov.debito > 0 and (mov.cuenta.codigo if mov.cuenta else "").startswith(('1', '5', '6', '7')):
                        is_valid = True
                        base_val = float(mov.debito)
                else:
                    # FE, NC, ND: Usualmente ventas o devoluciones de ventas
                    # Para NC: La devolución mueve el DEBITO de la cuenta de Ingreso (4) para anular el credito original?
                    # O el sistema registra un nuevo documento con creditos negativos?
                    # GESTIÓN SIMPLIFICADA: Buscamos el valor positivo principal.
                    if mov.credito and mov.credito > 0: # Caso normal venta
                         # Filtrar solo cuentas de Ingreso (4) para items de venta
                         if (mov.cuenta.codigo if mov.cuenta else "").startswith('4'):
                             is_valid = True
                             base_val = float(mov.credito)
                    elif mov.debito and mov.debito > 0 and is_nc: # Caso devolución venta (Debito a ingreso)
                         # Filtrar solo cuentas de Ingreso (4) para items de devolución
                         # Excluir Costo (6), Inventario (1), Pasivo (2 - IVA)
                         if (mov.cuenta.codigo if mov.cuenta else "").startswith('4'):
                             is_valid = True
                             base_val = float(mov.debito)
                
                if is_valid:
                    valid_movs.append(mov)
                    sum_line_discounts += float(mov.descuento_valor or 0)
                    total_items_net += base_val # Usamos el valor capturado arriba

            # Calcular el componente EXTRA del descuento global
            extra_global_discount = 0.0
            if target_total_discount > sum_line_discounts:
                extra_global_discount = target_total_discount - sum_line_discounts

            items_payload = []
            for mov in valid_movs:
                product_name = mov.producto.nombre if mov.producto else (mov.concepto or "Producto/Servicio")
                tax_multiplier = mov.producto.impuesto_iva.tasa if mov.producto and mov.producto.impuesto_iva else 0.0
                tax_rate_str = f"{(tax_multiplier * 100):.2f}"

                # Valores del item
                if is_ds:
                    line_net = float(mov.debito)
                elif is_nc and mov.debito > 0:
                    line_net = float(mov.debito)
                else:
                    line_net = float(mov.credito)

                line_discount_val = float(mov.descuento_valor or 0)
                line_gross = line_net + line_discount_val
                
                # CORRECCIÓN DE INFLACIÓN POR CARGOS:
                cargo_proporcional = 0.0
                if total_items_net > 0 and cargos_globales > 0:
                    cargo_proporcional = (line_net / total_items_net) * cargos_globales
                
                # Precio Base Limpio (Sin cargo global)
                line_gross_clean = line_gross - cargo_proporcional
                original_base_line = line_gross_clean
                
                qty = float(mov.cantidad or 1.0)
                if qty == 0: qty = 1.0
                base_unit_price = original_base_line / qty
                unit_price = base_unit_price * (1 + tax_multiplier)
                
                # CÁLCULO DE DESCUENTO COMBINADO
                share_extra_discount = 0.0
                if total_items_net > 0 and extra_global_discount > 0:
                    share_extra_discount = (line_net / total_items_net) * extra_global_discount
                
                total_discount_money = line_discount_val + share_extra_discount
                
                final_discount_rate = 0.0
                if original_base_line > 0:
                    final_discount_rate = (total_discount_money / original_base_line) * 100
                
                items_payload.append({
                    "code_reference": str(mov.producto_id or ("GENERICO-DS" if is_ds else "GENERICO")),
                    "name": product_name,
                    "quantity": float(qty),
                    "discount_rate": float(f"{final_discount_rate:.6f}"),
                    "price": float(f"{unit_price:.2f}"),
                    "tax_rate": tax_rate_str,
                    "unit_measure_id": 70, 
                    "standard_code_id": 1,
                    "is_excluded": 0,
                    "tribute_id": 1,
                    "withholding_taxes": []
                })
            
            if not items_payload:
                 return {"success": False, "error": f"No hay items identificados para el documento."}

            # Manejar Cargo Global como Ítem Adicional
            if cargos_globales > 0:
                cargo_item = {
                    "code_reference": "OTROS-CARGOS",
                    "name": "Otros Cargos / Recargos",
                    "quantity": 1,
                    "discount_rate": 0,
                    "price": cargos_globales,
                    "tax_rate": "0.00",
                    "unit_measure_id": 70,
                    "standard_code_id": 1,
                    "is_excluded": 0,
                    "tribute_id": 1,
                    "withholding_taxes": []
                }
                items_payload.append(cargo_item)

            # Mapeo de Datos del Tercero
            tercero = doc.beneficiario
            dian_doc_type = tercero.tipo_documento or "13"
            mapping_docs = {"13": "3", "31": "6", "11": "1", "12": "2", "21": "4", "22": "5", "41": "9", "42": "0"}
            factus_doc_id = mapping_docs.get(str(dian_doc_type), "3")
            tipo_persona = tercero.tipo_persona or "2"
            
            partner_data = {
                "identification": tercero.nit,
                "dv": tercero.dv or "",
                "company": tercero.razon_social or "Proveedor Sin Nombre",
                "trade_name": tercero.nombre_comercial or tercero.razon_social or "Proveedor Sin Nombre",
                "names": tercero.razon_social or "Proveedor Sin Nombre",
                "address": tercero.direccion or "Calle 0 # 0-0",
                "email": tercero.email or "sin@correo.com",
                "phone": tercero.telefono or "0000000",
                "legal_organization_id": tipo_persona, 
                "tribute_id": "21" if tipo_persona == '2' else "01",
                # "identification_document_id": factus_doc_id, # Se asigna abajo
                "municipality_id": "980",
                "country_code": "CO"
            }
            
            # Lógica especial para Documento Soporte
            final_doc_id = factus_doc_id
            final_dv = partner_data["dv"]
            
            if is_ds and partner_data.get("country_code") == "CO" and final_doc_id == "3":
                final_doc_id = "6" # Forzar NIT
                if not final_dv:
                     final_dv = self.calcular_dv(partner_data["identification"])
            
            partner_data["identification_document_id"] = final_doc_id
            partner_data["dv"] = final_dv

            # Lógica Consumidor Final
            if not is_ds and tercero.nit == '222222222222':
                 partner_data.update({
                    "company": "Consumidor Final",
                    "names": "Consumidor Final",
                    "legal_organization_id": "2",
                    "tribute_id": "21",
                    "identification_document_id": "3"
                 })

            # Formatear fecha
            doc_date = doc.fecha if doc.fecha else datetime.now()
            if isinstance(doc_date, date) and not isinstance(doc_date, datetime):
                doc_date = datetime.combine(doc_date, datetime.min.time())
            formatted_date = doc_date.strftime("%Y-%m-%d %H:%M:%S")

            # Determinando Bill Type
            bill_type_str = "Standard"
            if is_ds: bill_type_str = "SupportDocument"
            elif is_nc: bill_type_str = "CreditNote"
            elif is_nd: bill_type_str = "DebitNote"

            # Payload Final
            factus_payload = {
                "numbering_range_id": range_id,
                "reference_code": f"{'DS' if is_ds else ('NC' if is_nc else ('ND' if is_nd else 'FE'))}-{doc.numero}-{uuid.uuid4().hex[:4]}",
                "observation": f"{doc_type_name} #{doc.numero} - {doc.observaciones or ''}",
                "payment_form": "1",
                "payment_method_code": "10",
                "bill_date": formatted_date,
                "date_issue": formatted_date, # Redundancia por compatibilidad
                "items": items_payload,
                "bill_type": bill_type_str
            }

            # AGREGAR DATOS RELACIONADOS A NOTAS
            if is_nc or is_nd:
                # Referencia a Factura Padre
                parent_date = parent_doc.fecha
                if isinstance(parent_date, date) and not isinstance(parent_date, datetime):
                     parent_date = datetime.combine(parent_date, datetime.min.time())
                
                factus_payload["billing_reference"] = {
                    "number": str(parent_doc.numero),
                    "uuid": parent_doc.dian_cufe,
                    "issue_date": parent_date.strftime("%Y-%m-%d")
                }
                factus_payload["bill_id"] = str(parent_doc.provider_id or parent_doc.numero)

                # DISCREPANCY / CORRECTION CONCEPTS
                # Factus documentacion: 
                # Credit Note: discrepancy_response (code, description)
                # Debit Note: discrepancy_response (code, description) ALSO? 
                
                # Códigos DIAN para Notas Débito:
                # 1. Intereses
                # 2. Gastos por cobrar
                # 3. Cambio del valor
                # 4. Otros
                
                # Códigos DIAN para Notas Crédito:
                # 1. Devolución parcial de los bienes y/o no aceptación parcial del servicio
                # 2. Anulación de factura electrónica
                # 3. Rebaja o descuento total o parcial
                # 4. Ajuste de precio

                # Extraer concepto de las observaciones si viene en formato [CODE] Description
                # O usar default '1' (Devolución) para NC, '3' (Cambio Valor) para ND
                
                concept_code = "1"
                if is_nd: concept_code = "3"
                
                obs = doc.observaciones or ""
                if obs.startswith("[") and "]" in obs:
                    try:
                        concept_code = obs.split("]")[0].replace("[", "").strip()
                        description = obs.split("]")[1].strip()
                    except:
                        description = obs
                else:
                    description = obs or ("Nota Débito Generada" if is_nd else "Nota Crédito Generada")

                # Factus usa 'correction_concept_code' en root O 'discrepancy_response'
                # Para v2 (UBL 2.1), suele ser discrepancy_response.
                
                factus_payload["discrepancy_response"] = {
                    "reference_code": str(parent_doc.numero),
                    "correction_concept_id": concept_code, # Factus field name might be correction_concept_id inside object
                    "description": description
                }
                # Algunos endpoints de Factus piden reference_code en la raiz de discrepancy
                
                # FIX: Factus Documentation says:
                # "correction_concept_code": "1" at root is deprecated or specific
                # Let's try filling both specifically for what worked for Credit Notes
                
                if is_nc:
                     factus_payload["correction_concept_code"] = concept_code
                elif is_nd:
                     # Para Notas Debito, Factus a veces pide lo mismo.
                     factus_payload["correction_concept_code"] = concept_code 
                


            if is_ds:
                 # En Documento Soporte: El tercero es el Proveedor
                 factus_payload["provider"] = partner_data
            else:
                 # En Venta/Nota: El tercero es el Cliente
                 factus_payload["customer"] = partner_data
            
            # --- ENVIO ---
            print(f"DEBUG PAYLOAD {bill_type_str} A FACTUS:")
            print(json.dumps(factus_payload, indent=2))
            response = provider.emit(factus_payload)
            
            # 5. Actualizar Documento
            if response.get("success"):
                doc.dian_estado = "ACEPTADO" 
                doc.dian_cufe = response.get("cufe")
                doc.dian_xml_url = response.get("xml_url")
                doc.provider_id = response.get("provider_id") # SAVE ID
                try:
                     doc.dian_error = json.dumps(response.get("provider_response", {})) 
                except: pass
                db.commit()
            else:
                doc.dian_estado = "ERROR"
                doc.dian_error = response.get("error", "Error proveedor") + " " + json.dumps(response.get("details", {}))
                db.commit()
                
            return response

        except Exception as e:
            import traceback
            print(traceback.format_exc())
            return {"success": False, "error": f"Excepción Interna: {str(e)}"}

factura_electronica_service = FacturaElectronicaService()
