
from sqlalchemy.orm import Session
from app.models.empresa import Empresa
from app.models.tercero import Tercero
from app.models.configuracion_fe import ConfiguracionFE

from datetime import datetime
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
            
        # 1. Obterner Configuración
        config = db.query(ConfiguracionFE).filter_by(empresa_id=doc.empresa_id).first()
        if not config:
             return {"success": False, "error": "La empresa no tiene configuración de Facturación Electrónica."}
             
        if not config.habilitado:
             return {"success": False, "error": "Facturación Electrónica inhabilitada para esta empresa."}
        
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
            target_total_discount = float(doc.descuento_global_valor or 0.0) # Valor total (Línea + Global)
            
            # Calcular bases para prorrateos y suma de descuentos de línea
            total_items_net = 0.0   # Suma de (Neto), base para distribuir el global
            sum_line_discounts = 0.0
            
            for mov in doc.movimientos:
                if mov.credito and mov.credito > 0 and (mov.cuenta.codigo if mov.cuenta else "").startswith('4'):
                    line_disc = float(mov.descuento_valor or 0)
                    sum_line_discounts += line_disc
                    total_items_net += float(mov.credito)
            
            # Calcular el componente EXTRA del descuento global (lo que excede a la suma de líneas)
            # Si target_total_discount es 10000 y sum_line_discounts es 5000, extra es 5000.
            extra_global_discount = 0.0
            if target_total_discount > sum_line_discounts:
                extra_global_discount = target_total_discount - sum_line_discounts

            items_payload = []
            for mov in doc.movimientos:
                if not (mov.credito and mov.credito > 0): continue
                if not (mov.cuenta.codigo if mov.cuenta else "").startswith('4'): continue

                product_name = mov.producto.nombre if mov.producto else (mov.concepto or "Producto")
                tax_multiplier = mov.producto.impuesto_iva.tasa if mov.producto and mov.producto.impuesto_iva else 0.0
                tax_rate_str = f"{(tax_multiplier * 100):.2f}"

                # Valores del item
                line_net = float(mov.credito)
                line_discount_val = float(mov.descuento_valor or 0)
                line_gross = line_net + line_discount_val
                
                # CORRECCIÓN DE INFLACIÓN POR CARGOS:
                # En POS-40 se vio que si no restamos el cargo, el precio unitario sube (1.380 vs 1.190).
                # Esto confirma que mov.credito INCLUYE la parte proporcional del cargo global.
                # Debemos limpiarlo para reportar el precio real del producto.
                
                cargo_proporcional = 0.0
                if total_items_net > 0 and cargos_globales > 0:
                    cargo_proporcional = (line_net / total_items_net) * cargos_globales
                
                # Precio Base Limpio (Sin cargo global)
                line_gross_clean = line_gross - cargo_proporcional
                original_base_line = line_gross_clean
                
                qty = float(mov.cantidad or 1.0)
                if qty == 0: qty = 1.0
                base_unit_price = original_base_line / qty

                # Factus requiere el precio CON IVA INCLUIDO.
                unit_price = base_unit_price * (1 + tax_multiplier)
                
                # CÁLCULO DE DESCUENTO COMBINADO (Línea + Extra Global)
                # 1. Descuento de Línea ya conocido: line_discount_val
                # 2. Porción del Descuento Global EXTRA: Prorrateado sobre el NETO del item
                share_extra_discount = 0.0
                if total_items_net > 0 and extra_global_discount > 0:
                    share_extra_discount = (line_net / total_items_net) * extra_global_discount
                
                # 3. Descuento Total en Dinero
                total_discount_money = line_discount_val + share_extra_discount
                
                # 4. Tasa Final Efectiva sobre el Bruto LIMPIO
                final_discount_rate = 0.0
                if original_base_line > 0:
                    final_discount_rate = (total_discount_money / original_base_line) * 100
                
                items_payload.append({
                    "code_reference": str(mov.producto_id or "GENERICO"),
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
                 return {"success": False, "error": "No hay items facturables"}

            # Código de post-procesamiento de tasas eliminado porque ya calculamos la tasa final arriba


            # Manejar Cargo Global como Ítem Adicional (Garantiza Total y no infla IVA de productos)
            if cargos_globales > 0:
                cargo_item = {
                    "code_reference": "OTROS-CARGOS",
                    "name": "Otros Cargos / Recargos",
                    "quantity": 1,
                    "discount_rate": 0,
                    "price": cargos_globales, # Se suma limpio al final
                    "tax_rate": "0.00",
                    "unit_measure_id": 70,
                    "standard_code_id": 1,
                    "is_excluded": 0,
                    "tribute_id": 1,
                    "withholding_taxes": []
                }
                items_payload.append(cargo_item)
            # 5. Lógica Consumidor Final (Cuantías Menores)
            is_consumidor_final = (doc.beneficiario.nit == '222222222222')
            
            if is_consumidor_final:
                customer_data = {
                    "identification": "222222222222",
                    "dv": "3",
                    "company": "Consumidor Final",
                    "trade_name": "Consumidor Final",
                    "names": "Consumidor Final",
                    "address": "Calle 123",
                    "email": doc.beneficiario.email or "consumidorfinal@correo.com",
                    "phone": "3000000000",
                    "legal_organization_id": "2",
                    "tribute_id": "21",
                    "identification_document_id": "3"
                }
            else:
                dian_doc_type = doc.beneficiario.tipo_documento or "13"
                mapping_docs = {"13": "3", "31": "6", "11": "1", "12": "2", "21": "4", "22": "5", "41": "9", "42": "0"}
                factus_doc_id = mapping_docs.get(str(dian_doc_type), "3")
                tipo_persona = doc.beneficiario.tipo_persona or "2"
                
                customer_data = {
                    "identification": doc.beneficiario.nit,
                    "dv": doc.beneficiario.dv or "",
                    "company": doc.beneficiario.razon_social,
                    "trade_name": doc.beneficiario.nombre_comercial or doc.beneficiario.razon_social,
                    "names": doc.beneficiario.razon_social,
                    "address": doc.beneficiario.direccion,
                    "email": doc.beneficiario.email or "sin@correo.com",
                    "phone": doc.beneficiario.telefono or "0000000",
                    "legal_organization_id": tipo_persona, 
                    "tribute_id": "21" if tipo_persona == '2' else "01",
                    "identification_document_id": factus_doc_id
                }

            # Payload Final
            factus_payload = {
                "numbering_range_id": config.rango_desde or 8,
                "reference_code": f"FE-{doc.numero}-{uuid.uuid4().hex[:4]}",
                "observation": f"Factura de Venta POS-{doc.numero}",
                "payment_form": "1",
                "payment_method_code": "10",
                "customer": {
                    **customer_data,
                    "municipality_id": "980"
                },
                "bill_type": "Standard",
                "items": items_payload
            }
            
            # --- ENVIO REAL ---
            print("DEBUG PAYLOAD A FACTUS:")
            print(json.dumps(factus_payload, indent=2))
            response = provider.emit(factus_payload)
            
            # 4. Actualizar Documento
            if response.get("success"):
                doc.dian_estado = "ACEPTADO" # En Sandbox sale Aceptado de una
                doc.dian_cufe = response.get("cufe")
                doc.dian_xml_url = response.get("xml_url")
                
                # Guardar traza JSON
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
            return {"success": False, "error": f"Excepción Interna: {str(e)}"}

factura_electronica_service = FacturaElectronicaService()
