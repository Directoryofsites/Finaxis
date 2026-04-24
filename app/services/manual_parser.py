import os
from html.parser import HTMLParser
import logging

logger = logging.getLogger(__name__)

class ManualHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text = []
        self.ignore_tags = {'script', 'style', 'head', 'title'}
        self.current_tag = None

    def handle_starttag(self, tag, attrs):
        self.current_tag = tag

    def handle_data(self, data):
        if self.current_tag not in self.ignore_tags:
            content = data.strip()
            if content:
                self.text.append(content)

    def get_text(self):
        return "\n".join(self.text)

def parse_manuals(manuals_dir):
    """
    Lee todos los archivos HTML de un directorio (RECURSIVAMENTE) y devuelve un diccionario
    con {nombre_archivo: texto_limpio}.
    """
    knowledge_base = {}
    
    if not os.path.exists(manuals_dir):
        logger.warning(f"Directorio de manuales no encontrado: {manuals_dir}")
        return knowledge_base

    # Usamos os.walk para que sea recursivo y entre a subcarpetas como /ph
    for root, dirs, files in os.walk(manuals_dir):
        for filename in files:
            if filename.endswith(".html"):
                file_path = os.path.join(root, filename)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        html_content = f.read()
                        parser = ManualHTMLParser()
                        parser.feed(html_content)
                        # Usamos el nombre del archivo como llave
                        module_key = filename.replace(".html", "")
                        knowledge_base[module_key] = parser.get_text()
                except Exception as e:
                    logger.error(f"Error parsing {filename}: {e}")
                
    return knowledge_base

def get_relevant_manuals_context(query, manuals_dir):
    """
    Selecciona los manuales relevantes basados en la consulta.
    """
    kb = parse_manuals(manuals_dir)
    query = query.lower()
    
    # Mapeo ampliado de términos clave a archivos de manual
    # Nota: Los nombres deben coincidir con los archivos .html (sin extensión)
    mapping = {
        "factura": ["capitulo_41_facturacion", "capitulo_24_nuevo_documento"],
        "articulo": ["capitulo_41_facturacion", "capitulo_38_gestion_inventario"],
        "producto": ["capitulo_38_gestion_inventario", "capitulo_44_rentabilidad_producto"],
        "inventario": ["capitulo_38_gestion_inventario", "capitulo_39_parametros_inventario"],
        "compra": ["capitulo_40_compras"],
        "gasto": ["capitulo_40_compras"],
        "recaudo": ["guia_configuracion_modulos_ph", "guia_configuracion_pagos_ph"],
        "pago": ["guia_configuracion_pagos_ph", "capitulo_36_estado_cuenta_cliente"],
        "unidad": ["guia_configuracion_modulos_ph"],
        "tercero": ["capitulo_34_gestion_terceros"],
        "cliente": ["capitulo_34_gestion_terceros", "capitulo_36_estado_cuenta_cliente"],
        "proveedor": ["capitulo_34_gestion_terceros"],
        "cartera": ["capitulo_37_auxiliar_cartera"],
        "contabilidad": ["capitulo_1_puc", "capitulo_27_libro_diario"],
        "puc": ["capitulo_1_puc"],
        "balance": ["capitulo_28_balance_general", "capitulo_30_balance_prueba"],
        "resultado": ["capitulo_29_estado_resultados"],
        "ia": ["capitulo_100_ia_reportes"],
        "reporte": ["capitulo_33_super_informe"],
        "remision": ["capitulo_64_gestion_remisiones"],
        "cotizacion": ["capitulo_3_plantillas"]
    }
    
    relevant_keys = set()
    
    # Buscar coincidencias en el mapping
    for term, files in mapping.items():
        if term in query:
            for f in files:
                relevant_keys.add(f)
                
    # Si no hay coincidencias, buscar directamente en los nombres de los archivos
    if not relevant_keys:
        for key in kb.keys():
            if any(word in key.lower() for word in query.split()):
                relevant_keys.add(key)

    # Fallback: si sigue vacío, enviar manuales de bienvenida/guía inicial
    if not relevant_keys:
        relevant_keys.add("GUIA_INICIAL_PC2")
        relevant_keys.add("MANUAL_NUEVA_ESTRUCTURA_2025")

    context_parts = []
    # Limitar a los 5 manuales más relevantes para no saturar tokens
    for key in list(relevant_keys)[:5]:
        if key in kb:
            title = key.replace("capitulo_", "").replace("_", " ").title()
            context_parts.append(f"--- MANUAL DE {title.upper()} ---\n{kb[key]}\n")
            
    return "\n".join(context_parts)
