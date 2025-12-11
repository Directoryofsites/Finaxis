
import os
import json
from pathlib import Path
from datetime import datetime

# Configuración
ROOT_DIR = "."
OUTPUT_FILE = os.path.join("Manual", "mapa_proyecto.html")

# Extensiones y directorios a excluir
EXCLUDE_DIRS = {
    '.git', '.venv', '.vscode', '__pycache__', 'node_modules', 
    '.next', 'build', 'dist', 'coverage', '.pytest_cache', 'venv', 'env'
}
EXCLUDE_FILES = {
    '.DS_Store', 'Thumbs.db', '.gitignore', 'poetry.lock', 
    'package-lock.json', 'yarn.lock', '__init__.py', '.env'
}

# Descripciones conocidas (en español)
DESCRIPTIONS = {
    'dirs': {
        'app': 'Lógica del Backend (API, Modelos, Servicios). Posiblemente FastAPI.',
        'frontend': 'Código fuente del Frontend (Interfaz de Usuario).',
        'alembic': 'Scripts de migración de base de datos (SQLAlchemy/Alembic).',
        'Manual': 'Documentación y manuales del proyecto.',
        'schemas': 'Esquemas de validación de datos (Pydantic/Marshmallow).',
        'routes': 'Definición de rutas y endpoints de la API.',
        'api': 'Endpoints de la API REST.',
        'services': 'Capa de lógica de negocio y servicios.',
        'models': 'Modelos de base de datos (ORM).',
        'core': 'Configuración central y utilidades del sistema.',
        'utils': 'Funciones de utilidad y helpers generales.',
        'components': 'Componentes reutilizables de UI.',
        'pages': 'Páginas y rutas del frontend.',
        'tests': 'Pruebas automatizadas (Unitarias/Integración).',
        'public': 'Archivos estáticos públicos (imágenes, favicons).',
        'styles': 'Archivos de estilo global (CSS/SASS).'
    },
    'files': {
        'run.py': 'Punto de entrada para ejecutar la aplicación.',
        'main.py': 'Archivo principal de la aplicación.',
        'requirements.txt': 'Lista de dependencias de Python.',
        'package.json': 'Configuración y dependencias de Node.js.',
        'docker-compose.yml': 'Orquestación de servicios con Docker.',
        'Dockerfile': 'Definición de imagen Docker.',
        'alembic.ini': 'Configuración de Alembic para migraciones.',
        'README.md': 'Documentación general del proyecto.'
    }
}

def get_description(name, is_dir, extension):
    if is_dir:
        return DESCRIPTIONS['dirs'].get(name, "Directorio del proyecto.")
    
    # Check exact filename
    if name in DESCRIPTIONS['files']:
        return DESCRIPTIONS['files'][name]
    
    # Check extension heuristics
    if extension == '.py':
        if 'test' in name:
            return 'Archivo de pruebas Python.'
        if 'service' in name:
            return 'Lógica de servicio.'
        if 'schema' in name:
            return 'Definición de esquema de datos.'
        return 'Archivo de código fuente Python.'
    elif extension in ['.js', '.jsx', '.ts', '.tsx']:
        if 'page' in name:
            return 'Página/Ruta del frontend.'
        return 'Código fuente JavaScript/TypeScript.'
    elif extension == '.css':
        return 'Hoja de estilos.'
    elif extension == '.html':
        return 'Plantilla HTML.'
    elif extension == '.sql':
        return 'Script SQL.'
    elif extension == '.md':
        return 'Documentación Markdown.'
    
    return "Archivo del proyecto."

def generate_tree_html(path, level=0):
    name = os.path.basename(path)
    if level == 0:
        name = "ContaPY2 (Raíz)"
    
    is_dir = os.path.isdir(path)
    extension = os.path.splitext(name)[1]
    
    # Description
    desc = get_description(name if level > 0 else "root", is_dir, extension)
    
    # HTML construction
    html = '<li class="node">'
    
    icon = "📁" if is_dir else "📄"
    
    html += f'<div class="node-content"><span class="icon">{icon}</span> <span class="name">{name}</span> <span class="desc">- {desc}</span></div>'
    
    if is_dir:
        try:
            children = sorted(os.listdir(path))
        except PermissionError:
            return html + "</li>"
        
        # Filter exclusions
        children = [c for c in children if c not in EXCLUDE_DIRS and c not in EXCLUDE_FILES]
        
        if children:
            html += '<ul class="nested">'
            for child in children:
                child_path = os.path.join(path, child)
                # Skip if it is the output file itself
                if child in [os.path.basename(OUTPUT_FILE), "generate_map_tool.py", "mapa_proyecto.html"]:
                    continue
                html += generate_tree_html(child_path, level + 1)
            html += '</ul>'
            
    html += '</li>'
    return html

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mapa del Proyecto ContaPY2</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f6f8; color: #333; padding: 20px; }}
        h1 {{ color: #2c3e50; }}
        .tree-container {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); }}
        ul, #myUL {{ list-style-type: none; padding-left: 20px; }}
        #myUL {{ padding-left: 0; }}
        .node {{ margin: 5px 0; }}
        .node-content {{ cursor: pointer; padding: 5px; border-radius: 4px; display: flex; align-items: center; }}
        .node-content:hover {{ background-color: #eee; }}
        .nested {{ display: none; }}
        .active {{ display: block; }}
        .icon {{ margin-right: 8px; font-size: 1.2em; }}
        .name {{ font-weight: 600; margin-right: 10px; color: #2980b9; }}
        .desc {{ color: #7f8c8d; font-size: 0.9em; font-style: italic; }}
        .caret::before {{ content: "▶"; color: black; display: inline-block; margin-right: 6px; font-size: 0.8em; transition: transform 0.2s; }}
        .caret-down::before {{ transform: rotate(90deg); }}
        .folder-open {{ background-color: #e8f4fc; }}
    </style>
</head>
<body>
    <h1>📂 Estructura del Proyecto: ContaPY2</h1>
    <p>Generado el: {date}</p>
    <div class="tree-container">
        <ul id="myUL">
            {content}
        </ul>
    </div>

    <script>
        var toggler = document.getElementsByClassName("node-content");
        for (var i = 0; i < toggler.length; i++) {{
            toggler[i].addEventListener("click", function() {{
                var nested = this.parentElement.querySelector(".nested");
                if (nested) {{
                    nested.classList.toggle("active");
                    this.parentElement.classList.toggle("folder-open");
                }}
            }});
        }}
        
        // Auto-expand first level
        document.querySelector("#myUL > li > .nested").classList.add("active");
    </script>
</body>
</html>
"""

def main():
    print("Iniciando análisis del proyecto...")
    # Asegurar que el directorio de salida exista
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    
    try:
        content = generate_tree_html(ROOT_DIR)
        final_html = HTML_TEMPLATE.format(
            date=datetime.now().strftime("%d/%m/%Y %H:%M"),
            content=content
        )
        
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            f.write(final_html)
            
        print(f"Mapa generado exitosamente en: {os.path.abspath(OUTPUT_FILE)}")
    except Exception as e:
        print(f"Error generando el mapa: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
