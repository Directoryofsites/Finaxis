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
    Lee todos los archivos HTML de un directorio y devuelve un diccionario
    con {nombre_archivo: texto_limpio}.
    """
    knowledge_base = {}
    
    if not os.path.exists(manuals_dir):
        logger.warning(f"Directorio de manuales no encontrado: {manuals_dir}")
        return knowledge_base

    for filename in os.listdir(manuals_dir):
        if filename.endswith(".html"):
            file_path = os.path.join(manuals_dir, filename)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    html_content = f.read()
                    parser = ManualHTMLParser()
                    parser.feed(html_content)
                    # Usamos el nombre del archivo sin extensión como etiqueta de contexto
                    module_name = filename.replace(".html", "").replace("_", " ").title()
                    knowledge_base[module_name] = parser.get_text()
            except Exception as e:
                logger.error(f"Error parsing {filename}: {e}")
                
    return knowledge_base

def get_combined_manuals_context(manuals_dir):
    """
    Retorna un string formateado con todo el conocimiento de los manuales (SIN FILTRAR).
    """
    kb = parse_manuals(manuals_dir)
    context_parts = []
    for module, text in kb.items():
        context_parts.append(f"--- MANUAL DE {module.upper()} ---\n{text}\n")
    
    return "\n".join(context_parts)

def get_relevant_manuals_context(query, manuals_dir):
    """
    Selecciona solo los manuales relevantes basados en la consulta del usuario.
    """
    kb = parse_manuals(manuals_dir)
    query = query.lower()
    
    # Mapeo de términos clave a módulos/archivos
    mapping = {
        "factura": ["Facturacion"],
        "recibo": ["Manual Recaudos Super", "Pagos"],
        "pago": ["Pagos", "Manual Recaudos Super"],
        "recaudo": ["Manual Recaudos Super"],
        "unidad": ["Unidades", "Propietarios"],
        "propietario": ["Propietarios"],
        "configuracion": ["Configuracion"],
        "ajuste": ["Configuracion"],
        "reporte": ["Reportes", "Dashboard"],
        "estado": ["Estado Cuenta"],
        "saldos": ["Estado Cuenta", "Reportes"],
        "concepto": ["Conceptos"]
    }
    
    relevant_modules = {"Conceptos"} # Siempre incluimos conceptos básicos
    
    for term, modules in mapping.items():
        if term in query:
            for mod in modules:
                relevant_modules.add(mod)
                
    # Si no hay coincidencias claras, incluimos Configuración y Reportes por si acaso
    if len(relevant_modules) <= 1:
        relevant_modules.add("Configuracion")
        relevant_modules.add("Reportes")

    context_parts = []
    for module in relevant_modules:
        if module in kb:
            context_parts.append(f"--- MANUAL DE {module.upper()} ---\n{kb[module]}\n")
            
    return "\n".join(context_parts)
