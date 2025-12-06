# -*- coding: utf-8 -*-
import os

# --- CONFIGURACIÓN ---
# Ruta a la carpeta que contiene todas tus plantillas HTML.
TEMPLATES_SOURCE_DIR = 'app/templates'

# Ruta y nombre del archivo Python que vamos a generar.
# Lo colocamos en 'services' para que sea fácilmente importable.
PYTHON_OUTPUT_FILE = 'app/services/_templates_empaquetados.py'
# -------------------


def precompile_templates():
    """
    Escanea el directorio de plantillas y empaqueta todo el contenido HTML
    en un único diccionario de Python.
    """
    print("--- Iniciando pre-compilación de plantillas Jinja2 ---")

    templates_dict = {}

    # os.walk nos permite recorrer todas las subcarpetas de forma automática.
    for root, _, files in os.walk(TEMPLATES_SOURCE_DIR):
        for filename in files:
            if filename.endswith('.html'):
                file_path = os.path.join(root, filename)

                try:
                    # Leemos el contenido de cada archivo de plantilla.
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    # Creamos una clave que Jinja2 pueda entender.
                    # Por ejemplo: 'E:\\Contab2\\backend\\app\\templates\\reports\\mi_reporte.html'
                    # se convierte en: 'reports/mi_reporte.html'
                    relative_path = os.path.relpath(file_path, TEMPLATES_SOURCE_DIR).replace('\\', '/')

                    templates_dict[relative_path] = content
                    print(f"  [+] Empaquetada: '{relative_path}'")

                except Exception as e:
                    print(f"  [!] ERROR al leer el archivo {file_path}: {e}")

    # Escribimos el diccionario en el archivo de salida de Python.
    try:
        with open(PYTHON_OUTPUT_FILE, 'w', encoding='utf-8') as f:
            f.write("# -*- coding: utf-8 -*-\n")
            f.write("# ¡¡¡ ARCHIVO AUTO-GENERADO !!!\n")
            f.write("# No editar este archivo manualmente. Ejecutar precompile_templates.py para actualizar.\n\n")
            f.write("TEMPLATES_EMPAQUETADOS = {\n")

            for key, value in sorted(templates_dict.items()):
                # Usamos triples comillas simples (r''') para manejar strings HTML multi-línea
                # de forma segura, sin necesidad de escapar caracteres.
                f.write(f"    '{key}': r'''\n{value}\n''',\n\n")

            f.write("}\n")

        print(f"\n--- ¡Éxito! ---")
        print(f"{len(templates_dict)} plantillas han sido empaquetadas en:")
        print(f"'{os.path.abspath(PYTHON_OUTPUT_FILE)}'")

    except Exception as e:
        print(f"\n[!] ERROR al escribir el archivo de salida {PYTHON_OUTPUT_FILE}: {e}")

if __name__ == "__main__":
    precompile_templates()